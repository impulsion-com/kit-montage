"""
Télécharge la banque de sons gratuite de VideoEditingSFX depuis son site et la range dans moteur/sfx/.

Ces sons sont libres d'usage (y compris commercial, sans crédit) mais leur licence interdit de les
redistribuer : le kit ne les contient donc pas, chacun les récupère à la source.
Licence : https://videoeditingsfx.com

    python3 moteur/scripts/installer-sons.py
"""
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PACK_URL = "https://videoeditingsfx.com/downloads/videoeditingsfx-free-pack.zip"
SFX = Path(__file__).resolve().parent.parent / "sfx"
# Noms du catalogue qui diffèrent du nom de fichier dans le pack.
ALIASES = {
    "camera-focus-shutter": "camera-focus-and-shutter",
    "cinematic-riser-fast-stuttery-cyberpunk-futuristic": "cyberpunk-stutter-riser",
    "cinematic-riser-fast-tremolo-big-hit": "tremolo-riser-big-hit",
    "impact-subdrop": "impact-and-subdrop",
    "swoosh-sharp-hit-mp3": "swoosh-sharp-hit-2",
}


def slug(name):
    stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return ALIASES.get(stem, stem)


def main():
    wanted = {r["name"] for r in json.load(open(SFX / "catalog.json"))}
    missing = sorted(n for n in wanted if not (SFX / f"{n}.mp3").exists())
    if not missing:
        print(f"sons : {len(wanted)} déjà en place")
        return
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "pack.zip"
        print("téléchargement de la banque de sons (30 Mo)…")
        request = urllib.request.Request(PACK_URL, headers={"User-Agent": "kit-montage"})
        with urllib.request.urlopen(request) as response, open(archive, "wb") as out:
            out.write(response.read())
        with zipfile.ZipFile(archive) as pack:
            for member in pack.namelist():
                if not member.lower().endswith((".mp3", ".wav")):
                    continue
                name = slug(member)
                target = SFX / f"{name}.mp3"
                if name not in wanted or target.exists():
                    continue
                source = Path(pack.extract(member, tmp))
                if member.lower().endswith(".mp3"):
                    source.replace(target)
                else:
                    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(source),
                                    "-codec:a", "libmp3lame", "-q:a", "2", str(target)], check=True)
    still = sorted(n for n in wanted if not (SFX / f"{n}.mp3").exists())
    if still:
        sys.exit(f"sons introuvables dans le pack : {', '.join(still)}")
    print(f"sons : {len(wanted)} en place dans {SFX}")


if __name__ == "__main__":
    main()
