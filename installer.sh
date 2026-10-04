#!/bin/bash
# Installe le kit montage sur un Mac. Relançable sans risque : chaque étape est sautée si elle est déjà faite.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
fail() { printf '\n\033[31m%s\033[0m\n' "$1" >&2; exit 1; }

[ "$(uname)" = "Darwin" ] || fail "Ce kit n'est testé que sur Mac."

need_brew() {
  command -v brew >/dev/null || fail "Il manque $1 et Homebrew n'est pas installé. Installe Homebrew (https://brew.sh), puis relance ce script."
}

say "1/5 Outils système"
if ! command -v ffmpeg >/dev/null; then need_brew ffmpeg; brew install ffmpeg; fi
if ! command -v node >/dev/null; then need_brew Node.js; brew install node; fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 20 ] || fail "Node.js $NODE_MAJOR est trop ancien : il faut la version 20 ou plus récente (brew upgrade node)."

PY=""
for candidate in python3.12 python3.11 python3.13 python3.10 python3; do
  if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)'; then
    PY="$(command -v "$candidate")"; break
  fi
done
if [ -z "$PY" ]; then need_brew "Python 3.10 à 3.13"; brew install python@3.12; PY="$(brew --prefix python@3.12)/bin/python3.12"; fi
echo "ffmpeg, Node $(node -v), $("$PY" -V)"

say "2/5 Python : transcription et détection du visage (plusieurs minutes la première fois)"
[ -x "$KIT/moteur/.venv/bin/python" ] || "$PY" -m venv "$KIT/moteur/.venv"
"$KIT/moteur/.venv/bin/python" -m pip install --quiet --upgrade pip
"$KIT/moteur/.venv/bin/python" -m pip install --quiet -r "$KIT/requirements.txt"

say "3/5 Remotion et banque de sons"
(cd "$KIT/moteur" && npm ci --no-audit --no-fund)
"$KIT/moteur/.venv/bin/python" "$KIT/moteur/scripts/installer-sons.py"

say "4/5 Détourage de la personne (facultatif)"
if command -v swiftc >/dev/null; then
  swiftc -O "$KIT/moteur/personmask.swift" -o "$KIT/moteur/personmask" 2>/dev/null \
    && echo "personmask compilé" \
    || echo "compilation impossible : les b-rolls derrière la personne resteront indisponibles"
else
  echo "swiftc absent (xcode-select --install) : les b-rolls derrière la personne resteront indisponibles"
fi

say "5/5 Skills Claude Code"
mkdir -p "$HOME/.claude/skills"
for skill in "$KIT"/skills/*/; do
  name="$(basename "$skill")"
  target="$HOME/.claude/skills/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "$target existe déjà et n'est pas un lien : laissé tel quel"
  else
    ln -sfn "${skill%/}" "$target"
    echo "skill $name → $target"
  fi
done

say "Vérification"
"$KIT/montage" --verifier

cat <<FIN

Kit installé dans $KIT
Dans Claude Code, demande par exemple : « monte ce réel : ~/Movies/mon-rush.mp4 »
Le premier montage télécharge les modèles de transcription (environ 2 Go).

Pour l'éditeur avec timeline piloté par Claude (facultatif) :
https://github.com/impulsion-com/opencut-impulsion
FIN
