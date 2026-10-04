# Kit montage Impulsion

Monte tes vidéos face cam en donnant des consignes à Claude Code. Tu lui confies un rush, il
coupe les silences, pose les sous-titres mot à mot, le titre, les zooms sur ton visage, les
illustrations, le motion design et un sound design discret, puis il rend la vidéo.

Formats : réels 9:16 (Instagram, TikTok, Shorts) et vidéos 16:9 (YouTube, formation).

Tout tourne sur ton ordinateur. Tes rushes ne partent nulle part.

## Installation

Le plus simple : ouvre Claude Code et demande-lui

> Installe https://github.com/impulsion-com/kit-montage en suivant son README.

### Ce qu'il te faut

- Un Mac (c'est la seule plateforme testée).
- [Claude Code](https://claude.com/claude-code), connecté à ton abonnement Claude.
- [Homebrew](https://brew.sh), pour que le script installe ce qui manque (ffmpeg, Node.js, Python).
- Environ 5 Go libres : les bibliothèques et les modèles de transcription sont lourds.

### Les étapes

```sh
git clone https://github.com/impulsion-com/kit-montage.git ~/kit-montage
~/kit-montage/installer.sh
```

Le script vérifie les outils, installe le moteur, télécharge la banque de sons, branche la
skill `montage-reel` dans Claude Code et termine par un contrôle. Compte 5 à 15 minutes selon ta connexion la
première fois. Tu peux le relancer sans risque : il saute ce qui est déjà fait.

## Utilisation

Dans Claude Code, demande par exemple :

> Monte ce réel : ~/Movies/mon-rush.mp4. Le titre est « Google Ads en freelance ? ».

Claude crée un dossier de projet, transcrit le rush, te montre le découpage et rend la vidéo
dans `exports/`. Tu ajustes ensuite en parlant : « mets le mot-clé sur freelance », « ajoute
cette capture d'écran quand je dis Instagram », « passe en 16:9 ».

Le premier montage télécharge les modèles de transcription (environ 2 Go) et prend plusieurs
minutes. Les suivants sont bien plus rapides.

Pour lancer un projet à la main :

```sh
~/kit-montage/montage build.py plan         # découpage, coupes et sons, sans rendre
~/kit-montage/montage build.py still 2400   # une image à 2,4 s
~/kit-montage/montage build.py              # rendu complet
```

## Ce qu'il y a dans le kit

| Dossier | Rôle |
| --- | --- |
| `moteur/` | Le planificateur (`plan.py` : transcription, coupes, cartes, visage, zoom, sons) et la composition Remotion (`src/`). |
| `moteur/shotcraft/` | 216 animations Remotion à adapter en plans de coupe (video-shotcraft, Apache-2.0). |
| `skills/montage-reel/` | La skill Claude Code : la méthode et les règles de montage. |
| `exemples/` | Deux configurations complètes, réel 9:16 et vidéo 16:9 avec motion design. |

Ta charte (couleurs, courbes d'animation) se règle dans `moteur/src/theme.ts`.

## Pour retoucher à la main

Le kit monte à partir de consignes. Si tu veux aussi une timeline pour retoucher, avec Claude
qui pilote l'éditeur, installe [OpenCut Impulsion](https://github.com/impulsion-com/opencut-impulsion).

## Limites connues

- Mac uniquement pour l'instant.
- Le fond derrière la personne détourée demande les outils Xcode (`xcode-select --install`).
- Remotion est gratuit pour les particuliers et les entreprises de 3 personnes ou moins, payant
  au-delà : voir [remotion.dev/license](https://remotion.dev/license).

## Licences

Code du kit sous licence MIT. Les éléments tiers (animations, polices, sons, Remotion) gardent
la leur : voir [`NOTICE.md`](NOTICE.md).
