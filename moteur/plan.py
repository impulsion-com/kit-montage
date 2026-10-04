"""
Planificateur de réel face cam pour le moteur Remotion.

Prend un rush et une CONFIG (même forme que reel-facecam), produit :
  work/words_x.json     mots alignés WhisperX (wav2vec2 français), fins recalées sur l'énergie
  public/<slug>/clip.mp4  rush coupé (pauses resserrées), recadré 9:16 avec marge de zoom, voix normalisée
  public/<slug>/plan.json  cartes, titre, coupes, zoom, visages, illustrations, SFX, musique
  exports/<slug>-remotion.mp4  rendu Remotion (h264 crf 17)

Règles appliquées (voir skills/montage-reel/reference/regles-montage.md) :
  - texte 2 images AVANT le mot, mots allumés un à un (karaoké), mot-clé d'un bloc en accent
  - pauses > 0,45 s ramenées à ~0,22 s (jump cut), 0,15 s de silence avant le premier mot
  - une nouveauté visuelle au moins toutes les 2 s (coupe, mot-clé, illustration, sinon dérive de zoom)
  - SFX posés pour que leur PIC tombe 2 images avant l'évènement, réservés aux moments forts
  - sous-titres sous le menton, zoom réduit quand le visage est grand

    montage build.py            # plan + rendu
    montage build.py plan       # plan seulement (affiche cartes, coupes, SFX)
    montage build.py still 2400 # une image à 2,4 s pour contrôle

`montage` est le lanceur à la racine du kit : il utilise le Python de moteur/.venv.
"""
from __future__ import annotations

import json
import math
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as E  # noqa: E402  (auto_cards, layout_cards, detect_faces, crop_box_for, norm…)

TOOL = Path(__file__).resolve().parent
PUBLIC = TOOL / "public"
SFX_CATALOG = json.load(open(TOOL / "sfx/catalog.json"))
SFX = {r["name"]: r for r in SFX_CATALOG}

FPS = 30
W, H = 1080, 1920
CLIP_SCALE = 1.25                     # marge de résolution pour le zoom (1350x2400)
CW, CH = int(W * CLIP_SCALE) // 2 * 2, int(H * CLIP_SCALE) // 2 * 2


def set_format(aspect="9:16"):
    """9:16 (réel, par défaut) ou 16:9 (YouTube, formation). Fixe W, H et la taille du clip intermédiaire."""
    global W, H, CW, CH
    W, H = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    CW, CH = int(W * CLIP_SCALE) // 2 * 2, int(H * CLIP_SCALE) // 2 * 2


def crop_for(sw, sh):
    """Zone centrée du rush au ratio de sortie."""
    if sw / sh > W / H:
        cw = int(sh * W / H) // 2 * 2
        return ((sw - cw) // 2, 0, cw, sh)
    ch = int(sw * H / W) // 2 * 2
    return (0, (sh - ch) // 2, sw, ch)
FRAME_MS = 1000 / FPS
AUDIO_LATENCY_MS = 45                 # mesuré le 8 sept. 2026 : Remotion rend l'audio ~45 ms après l'image
LEAD_MS = 1 * FRAME_MS + AUDIO_LATENCY_MS   # le texte tombe ≈ 80 ms avant le mot entendu
SFX_LEAD_MS = 2 * FRAME_MS            # le pic d'un son tombe 2 images avant le visuel (latence incluse par le mix)

# Pauses
GAP_CUT = 0.35          # au-delà, on coupe
KEEP_AFTER = 0.12       # silence gardé après le mot avant la coupe
KEEP_BEFORE = 0.10      # silence gardé avant le mot suivant
LEAD_IN = 0.15          # avant le premier mot
TAIL = 0.45             # après le dernier mot
BEAT_MAX_MS = 2000      # une nouveauté visuelle au moins toutes les 2 s

# Sons : (fichier, cible de pic en dBFS). Voix normalisée à -14 LUFS (pics ≈ -2 dBFS).
# Un impact sur le dernier mot-clé (impact-hit-3) ne fait pas professionnel. Pas d'impact de payoff par défaut, et les sons listés dans BANNED ne sont
# jamais utilisés, même demandés à la main.
BANNED = {"impact-hit-3", "impact-hit", "impact-hit-1", "impact-hit-2", "impact-hit-4", "impact-hit-launch",
          "cinematic-bang", "cinematic-boom", "cinematic-heavy-hit", "cinematic-glass-hit", "deep-hit",
          "deep-hit-2", "deep-hit-3", "inception-thump", "impact-and-subdrop", "dramatic-impact"}
SOUNDS = dict(
    cut=("simple-whoosh-1", -19),
    key=("pop-sound", -23),
    title=("swish-2", -20),
    payoff=None,                       # pas d'impact sur le dernier mot-clé (banni)
    riser=("dramatic-buildup-2", -25),
    overlay=("ui-sound-6", -24),       # illustrations devant seulement, pas les b-rolls
)


def sh(cmd, quiet=True):
    return E.sh(cmd, quiet=quiet)


# ----------------------------------------------------------------------------------------------
# 1. Transcription alignée (WhisperX) + fins de mots recalées sur l'énergie
# ----------------------------------------------------------------------------------------------
def transcribe_x(src: Path, work: Path, language="fr"):
    out = work / "words_x.json"
    if out.exists():
        return json.load(open(out))
    wav = work / "audio16k.wav"
    if not wav.exists():
        sh(f"ffmpeg -loglevel error -y -i {shlex.quote(str(src))} -vn -ac 1 -ar 16000 {wav}")
    os.environ.setdefault("SSL_CERT_FILE", subprocess.run([sys.executable, "-m", "certifi"], capture_output=True, text=True).stdout.strip())
    import whisperx
    print("transcription WhisperX (large-v3-turbo + alignement wav2vec2 fr)…")
    audio = whisperx.load_audio(str(wav))
    model = whisperx.load_model("large-v3-turbo", "cpu", compute_type="int8", language=language)
    res = model.transcribe(audio, batch_size=8, language=language)
    ma, meta = whisperx.load_align_model(language_code=language, device="cpu")
    al = whisperx.align(res["segments"], ma, meta, audio, "cpu", return_char_alignments=False)
    words = []
    for s in al["segments"]:
        for w in s["words"]:
            if w.get("start") is None:
                # mot non alignable (nombre, symbole) : on l'accroche au précédent
                if words:
                    words[-1]["w"] += " " + w["word"].strip()
                continue
            words.append(dict(w=w["word"].strip(), s=round(float(w["start"]), 3), e=round(float(w["end"]), 3)))
    words = trim_ends(words, wav)
    json.dump(words, open(out, "w"), ensure_ascii=False, indent=0)
    return words


def trim_ends(words, wav):
    """WhisperX étire la fin d'un mot sur la pause qui suit : on la recale sur la chute d'énergie."""
    import wave
    import numpy as np
    f = wave.open(str(wav)); sr = f.getframerate()
    a = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    win = int(sr * 0.01); n = len(a) // win
    env = 20 * np.log10(np.sqrt(np.mean(a[:n * win].reshape(n, win) ** 2, axis=1)) + 1e-6)
    floor = np.percentile(env, 20)
    for i, w in enumerate(words):
        nxt = words[i + 1]["s"] if i + 1 < len(words) else w["e"] + 1
        if w["e"] - w["s"] < 0.35:
            continue
        i0, i1 = int(w["s"] * 100), int(min(w["e"], nxt) * 100)
        seg = env[i0:i1]
        if len(seg) < 5:
            continue
        thr = max(floor + 8, seg.max() - 25)
        above = np.where(seg > thr)[0]
        if len(above):
            new_e = w["s"] + (above[-1] + 3) / 100
            w["e"] = round(min(w["e"], max(new_e, w["s"] + 0.12)), 3)
    return words


# ----------------------------------------------------------------------------------------------
# 2. Coupes : resserrage des pauses à l'intérieur des segments demandés
# ----------------------------------------------------------------------------------------------
def tighten(words, base, dur, gap_cut=GAP_CUT):
    keep = []
    for a, b in base:
        ws = [w for w in words if a <= w["s"] <= b]
        if not ws:
            keep.append((a, b)); continue
        start = max(a, ws[0]["s"] - LEAD_IN)
        cur = start
        for w1, w2 in zip(ws, ws[1:]):
            if w2["s"] - w1["e"] > gap_cut:
                keep.append((cur, min(b, w1["e"] + KEEP_AFTER)))
                cur = max(a, w2["s"] - KEEP_BEFORE)
        keep.append((cur, min(b, ws[-1]["e"] + TAIL, dur)))
    return [(round(a, 3), round(b, 3)) for a, b in keep if b - a > 0.2]


# ----------------------------------------------------------------------------------------------
# 3. Clip intermédiaire : coupes + recadrage 9:16 + marge + voix normalisée
# ----------------------------------------------------------------------------------------------
def build_clip(src, keep, crop, out, force=False):
    if out.exists() and not force:
        return
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    x0, y0, cw, ch = crop
    vf = (f"select='{sel}',setpts=N/FRAME_RATE/TB,fps={FPS},crop={cw}:{ch}:{x0}:{y0},"
          f"scale={CW}:{CH}:flags=lanczos,format=yuv420p")
    af = f"aselect='{sel}',asetpts=N/SR/TB,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=9"
    sh(f"ffmpeg -loglevel error -y -i {shlex.quote(str(src))} -vf \"{vf}\" -af \"{af}\" "
       f"-c:v libx264 -preset fast -crf 16 -c:a aac -ar 48000 -b:a 192k -movflags +faststart {out}", quiet=False)


# ----------------------------------------------------------------------------------------------
# 4. Sons : le pic tombe 2 images avant l'évènement
# ----------------------------------------------------------------------------------------------
def sfx_at(kind, event_ms):
    if not SOUNDS.get(kind):
        return None
    name, target = SOUNDS[kind]
    if name in BANNED:
        raise SystemExit(f"son banni : {name}")
    r = SFX[name]
    gain = 10 ** ((target - r["peak_db"]) / 20)
    at = event_ms - r["peak"] * 1000 - SFX_LEAD_MS - AUDIO_LATENCY_MS
    if at < 0:   # pas de pré-roll possible : on aligne l'attaque plutôt que le pic
        at = max(0.0, event_ms - r["onset"] * 1000 - SFX_LEAD_MS - AUDIO_LATENCY_MS)
    return dict(src=f"sfx/{name}.mp3", atMs=round(at), gain=round(min(gain, 1.0), 4), kind=kind, eventMs=round(event_ms))


# ----------------------------------------------------------------------------------------------
# 5. Illustrations : copie dans public, couche personne (webm alpha) si « derrière »
# ----------------------------------------------------------------------------------------------
def person_frames(clip, s_ms, e_ms, work, pub):
    """Séquence PNG (RGBA) de la personne détourée pour [s, e] : Vision « accurate », bord adouci.
    Une image par frame de la Sequence Remotion (00001.png = première image de l'illustration)."""
    out = pub / f"person_{int(s_ms)}_{int(e_ms)}"
    if (out / "00001.png").exists():
        return out.name
    d = work / f"mask_{int(s_ms)}_{int(e_ms)}"
    (d / "in").mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=True)
    s, e = s_ms / 1000, e_ms / 1000
    sh(f"ffmpeg -loglevel error -y -ss {s:.3f} -to {e:.3f} -i {clip} -vf fps={FPS},scale={W}:{H} {d}/in/%05d.png")
    if not (TOOL / "personmask").exists():
        raise SystemExit("détourage indisponible : binaire personmask absent (Mac avec les outils Xcode, voir installer.sh)")
    sh(f"{TOOL}/personmask {d}/in {d}/out accurate", quiet=False)
    sh(f"ffmpeg -loglevel error -y -framerate {FPS} -i {d}/in/%05d.png -framerate {FPS} -i {d}/out/%05d.png "
       f"-filter_complex \"[1:v]format=gray,boxblur=1.5[m];[0:v][m]alphamerge,format=rgba\" "
       f"-compression_level 3 {out}/%05d.png")
    return out.name


def fetch_broll(b, root, work):
    ratio = "16:9" if W > H else "9:16"
    """B-roll pour un mot-clé : `file` (local), `query` (Pexels, vidéo verticale, clé PEXELS_API_KEY),
    ou `prompt` (image générée par la skill nanobanana, clé GEMINI_API_KEY)."""
    import urllib.parse, urllib.request
    assets = root / "assets"; assets.mkdir(exist_ok=True)
    if b.get("file"):
        return Path(b["file"]) if Path(b["file"]).is_absolute() else root / b["file"]
    slug = E.norm(b.get("anchor", b.get("query", b.get("prompt", "broll"))))[:40].replace(" ", "-")
    if b.get("query"):
        key = os.environ.get("PEXELS_API_KEY")
        if not key:
            raise SystemExit("PEXELS_API_KEY absent : utiliser `prompt` (génération) ou `file`")
        out = assets / f"broll-{slug}.mp4"
        if out.exists():
            return out
        req = urllib.request.Request(f"https://api.pexels.com/videos/search?query={urllib.parse.quote(b['query'])}&orientation={'landscape' if W > H else 'portrait'}&size=medium&per_page=5",
                                     headers={"Authorization": key})
        data = json.load(urllib.request.urlopen(req))
        vids = data.get("videos") or []
        if not vids:
            raise SystemExit(f"Pexels : rien pour « {b['query']} »")
        v = vids[b.get("pick", 0)]
        files = sorted(v["video_files"], key=lambda f: abs((f.get("height") or 0) - H))
        urllib.request.urlretrieve(files[0]["link"], out)
        print(f"b-roll Pexels : {v['url']} → {out.name}")
        return out
    if b.get("prompt"):
        out = assets / f"broll-{slug}.png"
        if out.exists():
            return out
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY absent : utiliser `file` (image ou vidéo locale) ou `query` (Pexels)")
        gen = Path.home() / ".claude/skills/nanobanana/scripts/generate.py"
        if not gen.exists():
            raise SystemExit("skill nanobanana absente : utiliser `file` (image ou vidéo locale) ou `query` (Pexels)")
        prompt = (b["prompt"] + f". {ratio} background plate for a talking-head video: the centre of the frame "
                  "stays calm and uncluttered (a person will be composited in front), no text, no logos, no people, "
                  "cinematic lighting, shallow depth of field, photorealistic.")
        r = subprocess.run([sys.executable, str(gen), prompt, "--ratio", ratio, "-o", str(out)],
                           env=dict(os.environ, GEMINI_API_KEY=key), capture_output=True, text=True)
        if r.returncode or not out.exists():
            print(r.stdout[-800:], r.stderr[-800:])
            raise SystemExit("génération Nano Banana échouée")
        print(f"b-roll généré : {out.name}")
        return out
    raise SystemExit("broll : il faut `file`, `query` ou `prompt`")


# ----------------------------------------------------------------------------------------------
# 6. Le plan
# ----------------------------------------------------------------------------------------------
def run(cfg, mode=None, arg=None):
    argv = sys.argv[1:]
    mode = mode or (argv[0] if argv else "render")
    arg = arg or (argv[1] if len(argv) > 1 else None)
    root = Path(cfg.get("root") or Path(sys.argv[0]).resolve().parent)
    set_format(cfg.get("aspect", "9:16"))
    landscape = W > H
    work, exports = root / "work", root / "exports"
    work.mkdir(exist_ok=True); exports.mkdir(exist_ok=True)
    slug = cfg["slug"]
    pub = PUBLIC / slug
    pub.mkdir(parents=True, exist_ok=True)
    src = Path(cfg["src"]).expanduser()
    style = dict(look="organic", font="Figtree", accent="#FFFFFF", subSize=80, subY=0.62, keyScale=1.12,
                 minorScale=0.8, titleSize=54, titleY=0.12, grade=True)
    if landscape:   # 16:9 : sous-titres à l'échelle d'un 1080 de haut
        style.update(subSize=64, titleSize=64, titleY=0.1)
    if cfg.get("style", {}).get("look") == "creator":   # ancien look : Inter, pastille blanche, mot-clé jaune
        style.update(font="Inter", accent="#FFD23F", subSize=88, keyScale=1.2, minorScale=0.78, titleSize=46, titleY=0.115)
    style.update(cfg.get("style", {}))

    sw, sh_, sfps, sdur = E.probe(src)
    crop = cfg.get("crop_box") or crop_for(sw, sh_)

    # --- mots (source) et coupes
    words = E.apply_replacements(transcribe_x(src, work, cfg.get("language", "fr")), cfg.get("replacements"))
    base = cfg.get("keep") or [(0.0, sdur)]
    keep = tighten(words, base, sdur, cfg.get("gap_cut", GAP_CUT)) if cfg.get("tighten", True) else base
    mapping, total = E.build_map(keep)
    words_out = E.map_words(words, mapping)
    cuts_ms = [round(off * 1000) for a, b, off in mapping[1:]]

    # --- clip intermédiaire
    clip = pub / "clip.mp4"
    stamp = work / "clip.stamp"
    sig = json.dumps([keep, crop, str(src)])
    if not clip.exists() or not stamp.exists() or stamp.read_text() != sig:
        build_clip(src, keep, crop, clip, force=True)
        stamp.write_text(sig)
        for f in [work / "faces.json"]:
            f.unlink(missing_ok=True)
    _, _, _, clip_dur = E.probe(clip)
    total = min(total, clip_dur)

    # --- cartes
    if cfg.get("cards"):
        cards = [dict(text=c["text"], s=c["s"], e=c["e"], key=c.get("key", False), seg=E.seg_of(c["s"], mapping) or 0,
                      new_phrase=c.get("new_phrase", False)) for c in cfg["cards"]]
        for k, c in enumerate(cards):
            if k == 0 or cards[k - 1]["key"] or c["s"] - cards[k - 1]["e"] > 0.45:
                c["new_phrase"] = True
    else:
        cards = E.auto_cards(words_out, cfg.get("keywords"))
    cards = [c for c in cards if any(ch.isalnum() for ch in c["text"])]   # guillemets seuls, tirets…
    # sous-titres masqués sur des plages (texte déjà incrusté dans le rush, graphisme plein cadre…)
    for a, b in cfg.get("hide_captions") or []:
        cards = [c for c in cards if not (a <= c["s"] < b)]
    E.layout_cards(cards, total, cfg.get("max_lines", 2 if landscape else 3))
    # jetons (karaoké) : les mots du flux compris dans la carte
    for c in cards:
        toks = [w for w in words_out if c["s"] - 1e-3 <= w["s"] <= c["e"] + 1e-3]
        c["tokens"] = [dict(text=(" " if i else "") + w["w"].rstrip(".,;:…"), fromMs=round(w["s"] * 1000), toMs=round(w["e"] * 1000))
                       for i, w in enumerate(toks)] or [dict(text=c["text"], fromMs=round(c["s"] * 1000), toMs=round(c["e"] * 1000))]

    # --- visage, zoom, sous-titres
    clip_mapping = [(off, off + (b - a), off) for a, b, off in mapping]
    faces = E.detect_faces(clip, clip_mapping, work, (0, 0, CW, CH), size=(960, 540) if landscape else (540, 960))
    face_h = max(f[2] for f in faces)
    punch = cfg.get("zoom_params", {}).get("punch") or round(min(1.24, max(1.06, 1.22 - (face_h - 0.15) * 0.7)), 3)
    shots = cfg.get("shots_scale") or [1.0 if i % 2 == 0 else 1.08 for i in range(len(mapping))]
    if "subY" not in cfg.get("style", {}):
        chin = 0.0
        for i, f in enumerate(faces):
            zmax = punch * shots[i]
            bottom = f[3] + 0.12 * f[2]
            chin = max(chin, f[1] + (bottom - f[1]) * zmax)
        style["subY"] = round(min(0.86 if landscape else 0.78, max(0.62, chin + 0.04)), 3)

    # keyframes de zoom : base par plan (marche à chaque coupe) + rampes sur les mots-clés + dérive anti-vide
    ramp, hold, release = 0.9, 0.5, 0.8
    kf = []
    for i, (a, b, off) in enumerate(mapping):
        s0, s1 = off * 1000, (off + (b - a)) * 1000
        kf += [(s0, shots[i]), (s1 - 1, shots[i])]
    events = sorted(set([0] + cuts_ms + [round(c["s"] * 1000) for c in cards if c["key"]]))
    for c in cards:
        if not c["key"]:
            continue
        seg = c["seg"]; base_s = shots[seg]
        peak = max(c["s"] + 0.15, mapping[seg][2] + 0.25)
        t0 = max(mapping[seg][2], peak - ramp)
        seg_end = mapping[seg][2] + (mapping[seg][1] - mapping[seg][0])
        kf += [(t0 * 1000, base_s), (peak * 1000, base_s * punch), (min(peak + hold, seg_end) * 1000, base_s * punch),
               (min(peak + hold + release, seg_end - 0.01) * 1000, base_s)]
    # dérive : si plus de 2 s sans évènement, on pousse doucement de +5 % jusqu'au prochain évènement
    ev = events + [round(total * 1000)]
    for e0, e1 in zip(ev, ev[1:]):
        if e1 - e0 > BEAT_MAX_MS:
            seg = E.seg_of((e0 + 1) / 1000, [(off, off + (b - a), off) for a, b, off in mapping]) or 0
            kf += [(e0 + 400, shots[seg]), (e1 - 60, shots[seg] * 1.05)]
    kf.sort(key=lambda k: k[0])
    zoom = []
    for t, z in kf:
        if zoom and t - zoom[-1][0] < 15:
            zoom[-1] = (zoom[-1][0], max(zoom[-1][1], z))
        else:
            zoom.append((round(t), round(z, 4)))

    # --- titre
    title = cfg.get("title")
    title_end_default = (cuts_ms[0] / 1000) if cuts_ms else min(3.0, total - 0.5)
    title_p = dict(text=title["text"], startMs=round(title.get("start", 0) * 1000),
                   endMs=round(title.get("end", title_end_default) * 1000)) if title else None

    # --- illustrations (start/end en temps de sortie, ou ancrées sur un mot-clé : anchor + offset + dur)
    def resolve_anchor(o):
        if "anchor" in o:
            target = E.norm(o["anchor"])
            c = next((c for c in cards if E.norm(c["text"]) == target or target in E.norm(c["text"])), None)
            if c is None:
                raise SystemExit(f"ancre introuvable dans les cartes : {o['anchor']}")
            o = dict(o, start=max(0.0, c["s"] + o.get("offset", -0.25)))
            o["end"] = min(total, o["start"] + o.get("dur", 1.5))
        return o
    broll_items = []
    for b in cfg.get("broll") or []:
        f = fetch_broll(b, root, work)
        broll_items.append(dict(b, file=str(f), behind=True, w=1.0, x=0.5, y=0.5, anim=b.get("anim", "fade")))
    overlays = []
    for o in [resolve_anchor(o) for o in (cfg.get("overlays") or []) + broll_items]:
        f = Path(o["file"]) if Path(o["file"]).is_absolute() else root / o["file"]
        dst = pub / f.name
        if not dst.exists() or dst.stat().st_mtime < f.stat().st_mtime:
            shutil.copy(f, dst)
        item = dict(src=f"{slug}/{f.name}", kind="video" if f.suffix.lower() in (".mp4", ".mov", ".webm") else "image",
                    startMs=round(o["start"] * 1000), endMs=round(o["end"] * 1000), x=o.get("x", 0.5), y=o.get("y", 0.8),
                    w=o.get("w", 0.6), anim=o.get("anim", "rise"), behind=bool(o.get("behind")), key=o.get("key", "none"))
        if item["behind"]:
            item["personSrc"] = f"{slug}/" + person_frames(clip, item["startMs"], item["endMs"], work, pub)
        overlays.append(item)

    # --- motion design (composante Graphics) : temps ancrés sur les mots prononcés
    def word_time(phrase, after=0.0):
        target = E.norm(phrase).split()
        toks = [E.norm(w["w"]) for w in words_out]
        for i, w in enumerate(words_out):
            if w["s"] + 1e-3 < after:
                continue
            if toks[i:i + len(target)] == target or (len(target) == 1 and target[0] in toks[i]):
                return w["s"]
        raise SystemExit(f"mot introuvable pour le graphisme : {phrase}")

    def resolve_times(v, base_after):
        if isinstance(v, dict):
            v = {k: resolve_times(x, base_after) for k, x in v.items()}
            if isinstance(v.get("at"), str):
                v["ms"] = round((word_time(v["at"], base_after) + v.get("offset", 0)) * 1000)
            return v
        if isinstance(v, list):
            return [resolve_times(x, base_after) for x in v]
        return v

    graphics = []
    for g in cfg.get("graphics") or []:
        start = (word_time(g["at"], g.get("after", 0)) + g.get("offset", -0.2)) if isinstance(g.get("at"), str) else g.get("start", 0)
        start = max(0.0, start)
        if "until" in g:
            end = word_time(g["until"], start) + g.get("until_offset", 0.0)
        else:
            end = g.get("end", start + g.get("dur", 3.0))
        graphics.append(dict(kind=g["kind"], startMs=round(start * 1000), endMs=round(min(end, total) * 1000),
                             x=g.get("x", 0.5), y=g.get("y", 0.5), scale=g.get("scale", 1.0),
                             props=resolve_times(g.get("props", {}), max(0.0, start - 0.5))))

    # --- sons
    sfx = cfg.get("sfx")
    if sfx is None:
        sfx = []
        if title_p:
            sfx.append(sfx_at("title", title_p["startMs"]))
        for c in cuts_ms:
            sfx.append(sfx_at("cut", c))
        keys = [c for c in cards if c["key"]]
        for i, c in enumerate(keys):
            ev_ms = c["s"] * 1000
            kind = "payoff" if (i == len(keys) - 1 and cfg.get("payoff", False)) else "key"
            sfx.append(sfx_at(kind, ev_ms) or sfx_at("key", ev_ms))
        if keys and keys[0]["s"] * 1000 > 1200:
            sfx.append(sfx_at("riser", keys[0]["s"] * 1000))
        for o in overlays:
            if not o.get("behind"):        # un b-roll d'ambiance n'a pas de blip
                sfx.append(sfx_at("overlay", o["startMs"]))
        for g in graphics:
            if g["kind"] == "shot":   # plan de coupe : whoosh à l'entrée et à la sortie
                sfx += [sfx_at("cut", g["startMs"]), sfx_at("cut", g["endMs"])]
            else:
                sfx.append(sfx_at("title" if g["kind"] in ("headline", "cta") else "overlay", g["startMs"] + 200))
        sfx = [x for x in sfx if x]
    else:
        for t, n, g in sfx:
            if n.replace("sfx/", "").replace(".mp3", "") in BANNED:
                raise SystemExit(f"son banni : {n}")
        def _src(n):   # "nom" (catalogue), "sfx/nom.mp3", ou "memes/17-dun-dun-duuun" (banque mèmes, à la main)
            if n.startswith(("sfx/", "memes/")):
                return n if n.endswith(".mp3") else n + ".mp3"
            return f"sfx/{n}.mp3"
        sfx = [dict(src=_src(n), atMs=round(t * 1000), gain=10 ** (g / 20), kind="manuel", eventMs=round(t * 1000))
               for t, n, g in sfx]
    sfx = [s for s in sfx if s["atMs"] < total * 1000]

    # --- musique
    music = None
    if cfg.get("music"):
        m = Path(cfg["music"]).expanduser()
        shutil.copy(m, pub / m.name)
        music = dict(src=f"{slug}/{m.name}", gain=cfg.get("music_gain", 0.22), duckGain=cfg.get("music_duck", 0.09))
    speech = [[round(w["s"] * 1000), round(w["e"] * 1000)] for w in words_out]

    plan = dict(
        slug=slug, fps=FPS, width=W, height=H, durationMs=round(total * 1000),
        clip=f"{slug}/clip.mp4", clipWidth=CW, clipHeight=CH,
        cards=[dict(text=c["text"], startMs=max(0, round(c["s"] * 1000 - LEAD_MS)), endMs=round(c["end"] * 1000),
                    key=c["key"], line=c["line"], tokens=c["tokens"]) for c in cards],
        title=title_p, cuts=cuts_ms, zoom=[dict(ms=t, scale=z) for t, z in zoom],
        faces=[dict(fromMs=round(off * 1000), toMs=round((off + (b - a)) * 1000), cx=f[0], cy=f[1]) for (a, b, off), f in zip(mapping, faces)],
        overlays=overlays, graphics=graphics, sfx=[{k: v for k, v in s.items() if k in ("src", "atMs", "gain")} for s in sfx],
        music=music, speech=speech, style=style,
    )
    json.dump(plan, open(pub / "plan.json", "w"), ensure_ascii=False, indent=1)

    # --- journal
    print(f"\nRush {sdur:.2f} s → sortie {total:.2f} s, {len(keep)} plan(s) : " + ", ".join(f"{a:.2f}-{b:.2f}" for a, b in keep))
    print(f"visage max {face_h:.2f} → zoom {punch}, sous-titres à {style['subY']}")
    print("Cartes (temps de sortie) :")
    for c in cards:
        print(f"  {c['s']:6.2f}-{c['end']:6.2f}  L{c['line']}  {c['text']}{' ★' if c['key'] else ''}")
    if graphics:
        print("Graphismes :")
        for g in graphics:
            print(f"  {g['startMs']/1000:6.2f}-{g['endMs']/1000:6.2f}  {g['kind']}")
    print("Sons :")
    for s in sfx:
        print(f"  {s['atMs']/1000:6.2f}  {s['src'].split('/')[-1]:<24} gain {s['gain']:.3f}  ({s.get('kind','')} @ {s.get('eventMs',0)/1000:.2f})")
    if mode == "plan":
        return

    if mode == "still":
        out = work / f"still_{arg}.png"
        sh(f"cd {TOOL} && node render.mjs {pub}/plan.json {out} --still {arg}", quiet=False)
        print("→", out); return out

    out = exports / f"{slug}-remotion.mp4"
    raw = work / f"{slug}-remotion-raw.mp4"
    sh(f"cd {TOOL} && node render.mjs {pub}/plan.json {raw} --crf {cfg.get('crf', 17)}", quiet=False)
    # mix final : la voix est déjà à -14 LUFS, les SFX s'y ajoutent → limiteur à -1,5 dBTP, vidéo recopiée telle quelle
    sh(f"ffmpeg -loglevel error -y -i {raw} -c:v copy -af \"alimiter=limit=0.84:attack=3:release=60:level=false\" "
       f"-c:a aac -b:a 192k -movflags +faststart {out}")
    print(f"→ {out}")
    return out
