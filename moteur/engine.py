"""
Moteur de montage « réel face cam » : sous-titres empilés avec mot-clé en accent, titre en
pastille, zoom continu centré sur le visage, illustrations animées (devant ou derrière la
personne), effets sonores discrets. Grammaire tirée du réel de Florian Boulay « Comment est
construit un hook ? » (voir skills/montage-reel/reference/grammaire-hook.md).

Dans ce kit, ce fichier sert de bibliothèque à plan.py (cartes, visages, cadrage, normalisation).
Son propre rendu ffmpeg + libass (`run`) est l'ancien moteur de preview : il n'est pas documenté
ici et ses sons (pop1.wav, whoosh1.wav...) ne sont pas fournis.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent
FONTS = TOOL / "fonts"
SFX_DIR = TOOL / "sfx"
PERSONMASK = TOOL / "personmask"

W, H = 1080, 1920          # canvas de sortie (9:16)
FPS = 30
SUPER = 2                  # sur-échantillonnage avant zoompan (précision sous-pixel)

# ----------------------------------------------------------------------------------------------
# Style par défaut (surchargé par CONFIG["style"])
# ----------------------------------------------------------------------------------------------
STYLE = dict(
    font="Inter",              # police des sous-titres (Bold). Alternative : "Montserrat ExtraBold"
    title_font="Inter",        # police du titre en pastille
    accent="#FFD23F",          # couleur du mot-clé (jaune chaud, lisible sur peau et fond clair)
    white="#FFFFFF",
    sub_size=88,               # taille d'une carte normale (px sur 1920 de haut)
    key_scale=1.2,            # facteur du mot-clé
    minor_scale=0.78,          # facteur des lignes secondaires d'une pile (« que j'ai fait »)
    sub_y=0.62,                # position verticale de la première ligne (fraction de H)
    line_gap=1.12,             # interligne relatif à la taille de police
    outline=5,                 # contour noir des sous-titres
    shadow=2,
    title_size=46,
    title_y=0.115,             # centre de la pastille (fraction de H)
    title_pad=(30, 18),        # marges internes de la pastille (x, y)
    title_bg="#FFFFFF",
    title_fg="#0A0A0A",
    anim_ms=140,               # durée d'apparition d'une carte (flou + pop)
)

DEFAULT_ZOOM = dict(
    punch=1.22,                # amplitude d'un zoom sur un mot-clé
    ramp=0.9,                  # durée de la montée (s)
    hold=0.5,                  # maintien avant la descente (s)
    release=0.8,               # durée de la descente (s)
)


# ----------------------------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------------------------
def sh(cmd: str, check=True, quiet=False):
    if not quiet:
        print("$", cmd if len(cmd) < 400 else cmd[:400] + " …")
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if check and r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(f"commande échouée ({r.returncode})")
    return r


def probe(path):
    r = sh(f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration "
           f"-show_entries format=duration -of json {shlex.quote(str(path))}", quiet=True)
    d = json.loads(r.stdout)
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    dur = float(st.get("duration") or d["format"]["duration"])
    return int(st["width"]), int(st["height"]), float(num) / float(den), dur


def hex_ass(h: str, alpha=0) -> str:
    h = h.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ass_time(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int((t % 3600) // 60):02d}:{t % 60:05.2f}"


def esc(s: str) -> str:
    return s.replace("\n", "\\N").replace("{", "").replace("}", "")


def rounded_rect(x, y, w, h, r):
    k = 0.5523 * r
    return (f"m {x+r:.0f} {y:.0f} l {x+w-r:.0f} {y:.0f} "
            f"b {x+w-r+k:.0f} {y:.0f} {x+w:.0f} {y+r-k:.0f} {x+w:.0f} {y+r:.0f} "
            f"l {x+w:.0f} {y+h-r:.0f} b {x+w:.0f} {y+h-r+k:.0f} {x+w-r+k:.0f} {y+h:.0f} {x+w-r:.0f} {y+h:.0f} "
            f"l {x+r:.0f} {y+h:.0f} b {x+r-k:.0f} {y+h:.0f} {x:.0f} {y+h-r+k:.0f} {x:.0f} {y+h-r:.0f} "
            f"l {x:.0f} {y+r:.0f} b {x:.0f} {y+r-k:.0f} {x+r-k:.0f} {y:.0f} {x+r:.0f} {y:.0f}")


FONT_FILES = {
    "Inter": "Inter-Bold.otf", "Inter SemiBold": "Inter-SemiBold.otf", "Inter Medium": "Inter-Medium.otf",
    "Montserrat ExtraBold": "Montserrat-ExtraBold.otf", "Montserrat Bold": "Montserrat-Bold.otf",
}


def text_width(txt, font, size):
    from PIL import ImageFont
    f = ImageFont.truetype(str(FONTS / FONT_FILES.get(font, "Inter-Bold.otf")), int(size))
    return f.getlength(txt)


# ----------------------------------------------------------------------------------------------
# 1. Transcription (faster-whisper, mots horodatés, temps source)
# ----------------------------------------------------------------------------------------------
def transcribe(src: Path, work: Path, language="fr"):
    wav = work / "audio16k.wav"
    out = work / "words.json"
    if out.exists():
        return json.load(open(out))
    sh(f"ffmpeg -loglevel error -y -i {shlex.quote(str(src))} -vn -ac 1 -ar 16000 {wav}")
    from faster_whisper import WhisperModel
    print("transcription faster-whisper large-v3-turbo …")
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(wav), language=language, word_timestamps=True,
                               vad_filter=True, vad_parameters=dict(min_silence_duration_ms=250))
    words = []
    for s in segs:
        if "Radio-Canada" in s.text or "Sous-titrage" in s.text:
            continue
        for w in s.words:
            tok = w.word.strip()
            if not tok:
                continue
            # faster-whisper sépare « d » + « 'âge », « moi » + « -même », « ? » : on recolle
            if words and (tok[0] in "'-" or re.fullmatch(r"[?!.,;:…]+", tok) or words[-1]["w"].endswith("'")):
                words[-1]["w"] += tok
                words[-1]["e"] = max(words[-1]["e"], round(w.end, 3))
                continue
            words.append(dict(w=tok, s=round(w.start, 3), e=round(max(w.end, w.start + 0.05), 3)))
    json.dump(words, open(out, "w"), ensure_ascii=False, indent=0)
    return words


def apply_replacements(words, replacements):
    """REPLACEMENTS = [("texte reconnu", "texte voulu")], appliqué sur la suite de mots."""
    for old, new in replacements or []:
        toks = old.split()
        i = 0
        while i <= len(words) - len(toks):
            if [norm(w["w"]) for w in words[i:i + len(toks)]] == [norm(t) for t in toks]:
                s, e = words[i]["s"], words[i + len(toks) - 1]["e"]
                newt = new.split()
                repl = []
                for k, t in enumerate(newt):
                    a = s + (e - s) * k / len(newt)
                    b = s + (e - s) * (k + 1) / len(newt)
                    repl.append(dict(w=t, s=round(a, 3), e=round(b, 3)))
                words[i:i + len(toks)] = repl
                i += len(newt)
            else:
                i += 1
    return words


# ----------------------------------------------------------------------------------------------
# 2. Coupes : KEEP = [(début, fin)] en temps source, mappées en temps de sortie
# ----------------------------------------------------------------------------------------------
def build_map(keep):
    m, off = [], 0.0
    for a, b in keep:
        m.append((a, b, off))
        off += b - a
    return m, off


def to_out(t, mapping):
    for a, b, off in mapping:
        if a <= t <= b:
            return off + (t - a)
    return None


def seg_of(t, mapping):
    for i, (a, b, off) in enumerate(mapping):
        if a <= t <= b:
            return i
    return None


def map_words(words, mapping):
    out = []
    for w in words:
        s = to_out(w["s"], mapping)
        if s is None:
            continue
        e = to_out(w["e"], mapping)
        if e is None:
            a, b, off = mapping[seg_of(w["s"], mapping)]
            e = off + (b - a)
        out.append(dict(w=w["w"], s=s, e=max(e, s + 0.05), seg=seg_of(w["s"], mapping)))
    return out


# ----------------------------------------------------------------------------------------------
# 3. Cartes : groupes de 1 à 3 mots, empilement par phrase, mot-clé en accent
# ----------------------------------------------------------------------------------------------
def norm(s):
    """minuscules, sans accents, sans apostrophes ni ponctuation : « Petit déj' » == « petit dej »"""
    import unicodedata
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9 -]", "", s.replace("'", "")).strip()


# Mots qui ouvrent un nouveau groupe de sens (on coupe AVANT eux), et mots de liaison qui
# restent collés au groupe suivant quand ils sont seuls (« et » + « je réalise »).
STARTERS = set("qu j c et que qui parce pendant mais non donc alors puis quand si car ou où comme pour avec sans "
               "dans sur chez je tu il elle on nous vous ils elles moi toi cest ca ce cette ces le la les un une "
               "des du au aux mon ma mes ton ta tes son sa ses notre votre leur".split())
GLUE = set("et que qui parce pendant mais non donc alors puis quand si car ou où comme pour avec sans dans sur "
           "chez le la les un une des du au aux mon ma mes ton ta tes son sa ses notre votre leur ne".split())


def auto_cards(words, keywords, max_words=3, max_chars=22, pause=0.28, phrase_pause=0.45):
    """Découpe les mots en cartes. Une carte = texte affiché d'un coup. Les cartes d'une même
    phrase s'empilent (jusqu'à 3 lignes) ; une carte mot-clé (accent) clôt la pile."""
    kws = [norm(k).split() for k in keywords or []]
    cards, cur = [], []

    def flush(key=False):
        nonlocal cur
        if cur:
            txt = re.sub(r"[.,;:…]+$", "", " ".join(w["w"] for w in cur))
            cards.append(dict(text=txt, s=cur[0]["s"], e=cur[-1]["e"], key=key, seg=cur[0]["seg"],
                              new_phrase=False, ends_sentence=re.search(r"[.?!…]$", cur[-1]["w"]) is not None))
            cur = []

    i = 0
    while i < len(words):
        w = words[i]
        # mot-clé multi-mots : carte à part entière
        hit = None
        for kw in kws:
            if [norm(x["w"]) for x in words[i:i + len(kw)]] == kw:
                hit = len(kw)
                break
        if hit:
            lead = cur if (len(cur) == 1 and norm(cur[0]["w"]) in GLUE) else []   # « le » + « media buying »
            if not lead:
                flush()
            cur = lead + words[i:i + hit]
            flush(key=True)
            i += hit
            continue
        gap = w["s"] - cur[-1]["e"] if cur else 0
        cand = " ".join(x["w"] for x in cur + [w])
        raw = w["w"].lower().replace("’", "'")
        head = norm(raw.split("'")[0]) if "'" in raw else norm(raw).split("-")[0]
        starts_group = head in STARTERS and not (len(cur) == 1 and norm(cur[0]["w"]) in GLUE)
        if cur and (len(cur) >= max_words or len(cand) > max_chars or gap > pause or starts_group
                    or re.search(r"[.?!…]$", cur[-1]["w"]) or w["seg"] != cur[-1]["seg"]):
            flush()
        cur.append(w)
        i += 1
    flush()

    # nouvelles phrases : après un mot-clé, une ponctuation, une pause longue, un changement de plan
    for k, c in enumerate(cards):
        if k == 0:
            c["new_phrase"] = True
            continue
        p = cards[k - 1]
        c["new_phrase"] = (p["key"] or p.get("ends_sentence")
                           or c["s"] - p["e"] > phrase_pause or c["seg"] != p["seg"])
    return cards


def layout_cards(cards, mapping_end, max_lines=3):
    """Attribue à chaque carte sa ligne dans la pile et son instant de fin (fin de la pile)."""
    piles, pile = [], []
    for c in cards:
        if c["new_phrase"] and pile:
            piles.append(pile)
            pile = []
        if len(pile) >= max_lines:
            piles.append(pile)
            pile = []
        pile.append(c)
    if pile:
        piles.append(pile)
    for pi, pile in enumerate(piles):
        nxt = piles[pi + 1][0]["s"] if pi + 1 < len(piles) else mapping_end
        end = min(nxt, pile[-1]["e"] + 0.35)
        end = max(end, pile[-1]["s"] + 0.35)
        for li, c in enumerate(pile):
            c["line"] = li
            c["end"] = end
            c["pile_len"] = len(pile)
    return cards


# ----------------------------------------------------------------------------------------------
# 4. ASS : titre en pastille + cartes empilées
# ----------------------------------------------------------------------------------------------
def build_ass(cards, title, st):
    white, black = hex_ass(st["white"]), hex_ass("#000000")
    accent = hex_ass(st["accent"])
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{st['font']},{st['sub_size']},{white},{white},{black},&H90000000,-1,0,0,0,100,100,0,0,1,{st['outline']},{st['shadow']},5,0,0,0,1
Style: Title,{st['title_font']},{st['title_size']},{hex_ass(st['title_fg'])},{hex_ass(st['title_fg'])},{hex_ass(st['title_fg'])},{hex_ass(st['title_fg'])},-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Shape,Arial,20,{hex_ass(st['title_bg'])},{hex_ass(st['title_bg'])},{hex_ass(st['title_bg'])},{hex_ass(st['title_bg'])},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    ms = st["anim_ms"]
    # --- titre en pastille blanche
    if title and title.get("text"):
        tw = text_width(title["text"], st["title_font"], st["title_size"])
        pw, ph = tw + 2 * st["title_pad"][0], st["title_size"] * 1.25 + 2 * st["title_pad"][1]
        cx, cy = W / 2, H * st["title_y"]
        x, y = cx - pw / 2, cy - ph / 2
        s, e = title.get("start", 0.0), title.get("end", 3.0)
        fad = f"\\fad(120,120)"
        rise = f"\\move({0},{-18},0,0,0,{ms})"  # (pos relative avec \\an7 + dessin absolu)
        ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Shape,,0,0,0,,{{\\an7\\pos(0,0){fad}\\p1}}"
                  f"{rounded_rect(x, y, pw, ph, ph / 2)}{{\\p0}}")
        ev.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Title,,0,0,0,,{{\\an5\\pos({cx:.0f},{cy:.0f}){fad}}}"
                  f"{esc(title['text'])}")
    # --- cartes empilées
    base_y = H * st["sub_y"]
    lh = st["sub_size"] * st["line_gap"]
    for c in cards:
        if c["key"]:
            size = st["sub_size"] * st["key_scale"]
            col = f"\\c{accent}"
        elif c["line"] == 0:
            size = st["sub_size"]
            col = ""
        else:
            size = st["sub_size"] * st["minor_scale"]
            col = ""
        y = base_y + c["line"] * lh
        anim = (f"\\fad(70,50)\\blur5\\t(0,{ms},\\blur0)"
                f"\\fscx90\\fscy90\\t(0,{ms},\\fscx100\\fscy100)")
        ev.append(f"Dialogue: 2,{ass_time(c['s'])},{ass_time(c['end'])},Sub,,0,0,0,,"
                  f"{{\\an5\\pos({W/2:.0f},{y:.0f})\\fs{size:.0f}{col}{anim}}}{esc(c['text'])}")
    return header + "\n".join(ev) + "\n"


# ----------------------------------------------------------------------------------------------
# 5. Visage (OpenCV) : centre du zoom par segment
# ----------------------------------------------------------------------------------------------
def detect_faces(src, mapping, work, crop_box, size=(540, 960)):
    """Visage par segment KEEP : [centre x médian, centre y médian, hauteur max, bas max] en fractions
    du cadre (9:16 par défaut, `size` pour un autre format), mesuré à 4 images/s sur tout le segment
    (le sujet bouge). Cache : faces.json."""
    cache = work / "faces.json"
    if cache.exists():
        return json.load(open(cache))
    try:
        import cv2
    except ImportError:
        print("cv2 absent : centre par défaut (0.5, 0.40)")
        return [[0.5, 0.40, 0.2, 0.5]] * len(mapping)
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cx0, cy0, cw, ch = crop_box
    fdir = work / "faces"
    fdir.mkdir(exist_ok=True)
    rate = 4
    dw, dh = size
    sh(f"ffmpeg -loglevel error -y -i {shlex.quote(str(src))} -vf fps={rate},crop={cw}:{ch}:{cx0}:{cy0},scale={dw}:{dh} "
       f"-q:v 4 {fdir}/%05d.jpg", quiet=True)
    frames = sorted(fdir.glob("*.jpg"))
    res = []
    for a, b, _ in mapping:
        pts = []
        for i, f in enumerate(frames):
            t = i / rate
            if not (a <= t <= b):
                continue
            img = cv2.imread(str(f))
            faces = casc.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(60, 60))
            if len(faces):
                x, y, w, h = max(faces, key=lambda ff: ff[2] * ff[3])
                pts.append(((x + w / 2) / dw, (y + h / 2) / dh, h / dh, (y + h) / dh))
        if pts:
            xs = sorted(p[0] for p in pts); ys = sorted(p[1] for p in pts)
            res.append([round(xs[len(xs) // 2], 3), round(ys[len(ys) // 2], 3),
                        round(max(p[2] for p in pts), 3), round(max(p[3] for p in pts), 3)])
        else:
            res.append([0.5, 0.40, 0.2, 0.5])
    json.dump(res, open(cache, "w"))
    print("visage par segment [cx, cy, hauteur, bas] :", res)
    return res


# ----------------------------------------------------------------------------------------------
# 6. Zoom continu : liste de (t, échelle) → expression ffmpeg lissée (smoothstep)
# ----------------------------------------------------------------------------------------------
def auto_zoom(cards, mapping, total, zp):
    """Zoom sur chaque mot-clé : montée douce avant, maintien, redescente. Un changement de plan
    (KEEP) remet l'échelle à 1 (le punch-in du plan est géré par shots_scale)."""
    kf = [(0.0, 1.0)]
    for c in cards:
        if not c["key"]:
            continue
        t_peak = c["s"] + 0.15
        if t_peak < zp["ramp"]:          # mot-clé dès l'ouverture : montée lente depuis le début
            t_peak = zp["ramp"] * 0.9
        kf += [(max(0.0, t_peak - zp["ramp"]), 1.0), (t_peak, zp["punch"]),
               (t_peak + zp["hold"], zp["punch"]), (t_peak + zp["hold"] + zp["release"], 1.0)]
    for a, b, off in mapping[1:]:
        kf += [(off - 0.01, 1.0), (off, 1.0)]
    kf.append((total, 1.0))
    kf.sort()
    # supprime les conflits : garde la plus grande échelle à un instant donné, temps strictement croissants
    clean = []
    for t, z in kf:
        if clean and t - clean[-1][0] < 0.02:
            clean[-1] = (clean[-1][0], max(clean[-1][1], z))
        else:
            clean.append((t, z))
    return clean


def zoom_expr(keyframes, shots_scale, mapping, var="T"):
    """Expression ffmpeg de l'échelle en fonction de T (temps de sortie)."""
    def base(t):  # échelle de base du plan (jump cut punch-in)
        i = next((k for k, (a, b, off) in enumerate(mapping) if off <= t < off + (b - a)), len(mapping) - 1)
        return shots_scale[i] if shots_scale and i < len(shots_scale) else 1.0
    pieces = []
    for (t0, z0), (t1, z1) in zip(keyframes, keyframes[1:]):
        if t1 <= t0:
            continue
        u = f"clip(({var}-{t0:.3f})/{t1-t0:.3f},0,1)"
        ss = f"({u}*{u}*(3-2*{u}))"
        pieces.append((t1, f"({z0:.4f}+({z1-z0:.4f})*{ss})"))
    expr = f"{keyframes[-1][1]:.4f}"
    for t1, e in reversed(pieces):
        expr = f"if(lt({var},{t1:.3f}),{e},{expr})"
    # multiplie par l'échelle de base du plan
    if shots_scale and any(abs(s - 1.0) > 1e-3 for s in shots_scale):
        b = f"{base(mapping[-1][2] + 0.001):.4f}"
        for a, bb, off in reversed(mapping[:-1]):
            b = f"if(lt({var},{off+(bb-a):.3f}),{base(off+0.001):.4f},{b})"
        expr = f"({expr})*({b})"
    return expr


def center_expr(faces, mapping, axis, var="T"):
    vals = [f[0 if axis == "x" else 1] for f in faces]
    e = f"{vals[-1]:.3f}"
    for (a, b, off), v in reversed(list(zip(mapping[:-1], vals[:-1]))):
        e = f"if(lt({var},{off+(b-a):.3f}),{v:.3f},{e})"
    return e


# ----------------------------------------------------------------------------------------------
# 7. Effets sonores
# ----------------------------------------------------------------------------------------------
def auto_sfx(cards, mapping, title):
    sfx = []
    if title and title.get("text"):
        sfx.append((title.get("start", 0.0), "whoosh2.wav", -13))
    for a, b, off in mapping[1:]:
        sfx.append((off, "whoosh1.wav", -12))
    for c in cards:
        if c["key"]:
            sfx.append((c["s"], "pop1.wav", -8))
    return sfx


# ----------------------------------------------------------------------------------------------
# 8. Illustrations : devant ou derrière la personne
# ----------------------------------------------------------------------------------------------
def person_masks(video_out_tmp, s, e, work):
    """Masques de personne (Vision) pour la plage [s, e] du rendu de base. Retourne le dossier."""
    d = work / f"mask_{s:.2f}_{e:.2f}"
    if (d / "done").exists():
        return d
    frames = d / "in"
    frames.mkdir(parents=True, exist_ok=True)
    sh(f"ffmpeg -loglevel error -y -ss {s:.3f} -to {e:.3f} -i {video_out_tmp} -vf fps={FPS} {frames}/%05d.png")
    sh(f"{PERSONMASK} {frames} {d}/out balanced")
    (d / "done").touch()
    return d


# ----------------------------------------------------------------------------------------------
# 9. Rendu
# ----------------------------------------------------------------------------------------------
def crop_box_for(src_w, src_h):
    """Zone du rush à garder pour un 9:16 (centrée)."""
    if src_w / src_h > W / H:  # plus large que 9:16 : on rogne les côtés
        cw = int(src_h * W / H) // 2 * 2
        return ((src_w - cw) // 2, 0, cw, src_h)
    ch = int(src_w * H / W) // 2 * 2
    return (0, (src_h - ch) // 2, src_w, ch)


def run(cfg, mode=None):
    mode = mode or (sys.argv[1] if len(sys.argv) > 1 else "preview")
    root = Path(cfg.get("root") or Path(sys.argv[0]).resolve().parent)
    work, exports = root / "work", root / "exports"
    work.mkdir(exist_ok=True)
    exports.mkdir(exist_ok=True)
    src = Path(cfg["src"]).expanduser()
    slug = cfg["slug"]
    st = dict(STYLE, **cfg.get("style", {}))
    zp = dict(DEFAULT_ZOOM, **cfg.get("zoom_params", {}))

    sw, sh_, sfps, sdur = probe(src)
    keep = cfg.get("keep") or [(0.0, sdur)]
    mapping, total = build_map(keep)
    crop = cfg.get("crop_box") or crop_box_for(sw, sh_)

    words = apply_replacements(transcribe(src, work, cfg.get("language", "fr")), cfg.get("replacements"))
    words_out = map_words(words, mapping)

    cards = cfg.get("cards")
    if cards:  # cartes manuelles : [{text, s, e, key}] en temps de sortie
        cards = [dict(text=c["text"], s=c["s"], e=c["e"], key=c.get("key", False), seg=seg_of(c["s"], mapping) or 0,
                      new_phrase=c.get("new_phrase", False)) for c in cards]
        for k, c in enumerate(cards):
            if k == 0 or cards[k - 1]["key"] or c["s"] - cards[k - 1]["e"] > 0.45:
                c["new_phrase"] = True
    else:
        cards = auto_cards(words_out, cfg.get("keywords"))
    layout_cards(cards, total)
    print("\nCartes (temps de sortie) :")
    for c in cards:
        flag = " ★" if c["key"] else ""
        print(f"  {c['s']:6.2f}-{c['end']:6.2f}  L{c['line']}  {c['text']}{flag}")
    json.dump(cards, open(work / "cards.json", "w"), ensure_ascii=False, indent=1)
    if mode == "cards":
        return

    title = cfg.get("title")

    faces = cfg.get("zoom_center")
    faces = [list(faces) + [0.2, 0.5]] * len(mapping) if faces else detect_faces(src, mapping, work, crop)
    shots = cfg.get("shots_scale")
    face_h = max(f[2] for f in faces)
    if "punch" not in cfg.get("zoom_params", {}):
        # visage petit (plan large, réel de référence ≈ 0,15) : 1,22 ; visage grand (plan serré) : moins
        zp["punch"] = round(min(1.24, max(1.06, 1.22 - (face_h - 0.15) * 0.7)), 3)
    if "sub_y" not in cfg.get("style", {}):
        # première ligne sous le menton, menton mesuré après le zoom maximal, jamais sur le visage
        chin = 0.0
        for i, f in enumerate(faces):
            zmax = zp["punch"] * (shots[i] if shots and i < len(shots) else 1.0)
            bottom = f[3] + 0.12 * f[2]      # la boîte Haar s'arrête à la bouche : on ajoute le menton
            chin = max(chin, f[1] + (bottom - f[1]) * zmax)
        st["sub_y"] = round(min(0.78, max(STYLE["sub_y"], chin + 0.04)), 3)
    print(f"visage : hauteur max {face_h:.2f} → zoom {zp['punch']}, sous-titres à {st['sub_y']:.2f} de la hauteur")
    (work / "subs.ass").write_text(build_ass(cards, title, st))
    zoom_kf = cfg.get("zoom") or auto_zoom(cards, mapping, total, zp)
    zexpr = zoom_expr(zoom_kf, shots, mapping, var="(on/%d)" % FPS)
    cxe, cye = center_expr(faces, mapping, "x", var="(on/%d)" % FPS), center_expr(faces, mapping, "y", var="(on/%d)" % FPS)

    # ---- sélection des segments + normalisation 9:16
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    x0, y0, cw, ch = crop
    vbase = (f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB,fps={FPS},crop={cw}:{ch}:{x0}:{y0},"
             f"scale={W*SUPER}:{H*SUPER}:flags=lanczos,"
             f"zoompan=z='{zexpr}':x='clip({cxe}*iw*(1-1/zoom),0,iw-iw/zoom)':y='clip({cye}*ih*(1-1/zoom),0,ih-ih/zoom)'"
             f":d=1:s={W}x{H}:fps={FPS}[base]")
    abase = f"[0:a]aselect='{sel}',asetpts=N/SR/TB,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=9[voice]"

    inputs = [f"-i {shlex.quote(str(src))}"]
    chains = [vbase]
    cur = "base"
    n_in = 1

    # ---- illustrations
    overlays = cfg.get("overlays") or []
    behind = [o for o in overlays if o.get("behind")]
    overlays = behind + [o for o in overlays if not o.get("behind")]   # derrière d'abord, devant ensuite
    if behind:
        # rendu de base intermédiaire pour calculer les masques de personne
        tmp = work / "base_tmp.mp4"
        if not tmp.exists() or mode == "final":
            sh(f"ffmpeg -loglevel error -y {inputs[0]} -filter_complex \"{vbase}\" -map '[base]' -an "
               f"-c:v libx264 -preset veryfast -crf 16 {tmp}")
    for k, o in enumerate(overlays):
        f = root / o["file"] if not Path(o["file"]).is_absolute() else Path(o["file"])
        s, e = o["start"], o["end"]
        wfrac = o.get("w", 0.5)
        is_video = f.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv")
        opts = "-stream_loop -1 " if (is_video and o.get("loop", True)) else ""
        if not is_video:
            opts += "-loop 1 -framerate 30 "
        inputs.append(f"{opts}-i {shlex.quote(str(f))}")
        ow = int(W * wfrac) // 2 * 2
        pre = f"[{n_in}:v]format=rgba,scale={ow}:-2,setpts=PTS+{s:.3f}/TB"
        key = o.get("key")
        if key == "green":
            pre += ",chromakey=0x00FF00:0.3:0.1"
        elif key == "black":
            pre += ",colorkey=0x000000:0.25:0.2"
        fade_d = o.get("fade", 0.28)
        pre += f",fade=t=in:st={s:.3f}:d={fade_d}:alpha=1,fade=t=out:st={e - fade_d:.3f}:d={fade_d}:alpha=1"
        pre += f",trim=start={s:.3f}:end={e:.3f}[ov{k}]"
        chains.append(pre)
        X = int(W * o.get("x", 0.5)) - ow // 2
        Y = f"{int(H * o.get('y', 0.75))}-h/2"
        anim = o.get("anim", "rise")
        if anim == "rise":
            Y = f"({Y})+50*(1-min(1,(t-{s:.3f})/0.35))"
        elif anim == "slide_left":
            X = f"{X}+80*(1-min(1,(t-{s:.3f})/0.35))"
        elif anim == "slide_right":
            X = f"{X}-80*(1-min(1,(t-{s:.3f})/0.35))"
        n_in += 1
        nxt = f"v{k}"
        if o.get("behind"):
            # couche « personne » = rendu de base (fichier intermédiaire) découpé par le masque Vision,
            # posée par-dessus l'illustration pendant [s, e] seulement
            md = person_masks(work / "base_tmp.mp4", s, e, work)
            inputs.append(f"-i {work}/base_tmp.mp4")
            inputs.append(f"-framerate {FPS} -itsoffset {s:.3f} -i {md}/out/%05d.png")
            chains.append(f"[{cur}][ov{k}]overlay=x='{X}':y='{Y}':enable='between(t,{s:.3f},{e:.3f})':eof_action=pass[bg{k}]")
            chains.append(f"[{n_in}:v]format=rgba[pb{k}];[{n_in+1}:v]format=gray,scale={W}:{H}[m{k}];"
                          f"[pb{k}][m{k}]alphamerge[person{k}]")
            chains.append(f"[bg{k}][person{k}]overlay=x=0:y=0:enable='between(t,{s:.3f},{e:.3f})':eof_action=pass[{nxt}]")
            n_in += 2
        else:
            chains.append(f"[{cur}][ov{k}]overlay=x='{X}':y='{Y}':enable='between(t,{s:.3f},{e:.3f})':eof_action=pass[{nxt}]")
        cur = nxt

    # ---- sous-titres + fondu final
    ass_path = str(work / "subs.ass").replace(":", "\\:")
    chains.append(f"[{cur}]ass='{ass_path}':fontsdir={FONTS},format=yuv420p[v]")

    # ---- effets sonores
    sfx = cfg.get("sfx")
    if sfx is None:
        sfx = auto_sfx(cards, mapping, title)
    chains.append(abase)
    amix = ["[voice]"]
    for k, (t, name, gain) in enumerate(sfx):
        p = SFX_DIR / name if not Path(name).is_absolute() else Path(name)
        inputs.append(f"-i {shlex.quote(str(p))}")
        chains.append(f"[{n_in}:a]volume={gain}dB,adelay={int(t*1000)}|{int(t*1000)},apad=whole_dur={total:.3f}[s{k}]")
        amix.append(f"[s{k}]")
        n_in += 1
    if len(amix) > 1:
        chains.append("".join(amix) + f"amix=inputs={len(amix)}:normalize=0:dropout_transition=0,"
                      f"alimiter=limit=0.95:level=false[a]")
    else:
        chains.append("[voice]anull[a]")

    fc = ";".join(chains)
    fc_file = work / "filter.txt"
    fc_file.write_text(fc)
    out = exports / f"{slug}-{mode}.mp4"
    if mode == "final":
        venc = "-c:v h264_videotoolbox -b:v 14M -profile:v high -pix_fmt yuv420p"
    else:
        venc = "-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p"
    cmd = (f"ffmpeg -loglevel error -stats -y {' '.join(inputs)} -filter_complex_script {fc_file} "
           f"-map '[v]' -map '[a]' -t {total:.3f} {venc} -c:a aac -b:a 192k -movflags +faststart {out}")
    sh(cmd)
    print(f"\n→ {out}  ({total:.1f} s)")

    return out
