# Ce que ce kit doit à d'autres

Le code du kit (moteur, skill, scripts) est sous licence MIT, voir `LICENSE`. Il embarque ou
utilise les éléments suivants, chacun sous sa propre licence.

| Élément | Où | Licence |
| --- | --- | --- |
| video-shotcraft, bibliothèque d'animations Remotion | `moteur/shotcraft/` | Apache-2.0, voir `moteur/shotcraft/LICENSE` et `NOTICE.md` (une modification, décrite dans ce fichier) |
| Polices Inter, Montserrat, Figtree | `moteur/fonts/` | SIL Open Font License 1.1, textes dans `moteur/fonts/licences/` |
| Banque de sons VideoEditingSFX | téléchargée par `installer.sh` dans `moteur/sfx/` | Libre d'usage, y compris commercial et sans crédit, mais non redistribuable : les fichiers ne sont pas dans ce dépôt. `moteur/sfx/catalog.json` ne contient que nos mesures (durée, pic, attaque, niveau). |
| Remotion | dépendance npm | Licence Remotion : gratuite pour les particuliers et les entreprises de 3 personnes ou moins, payante au-delà. Voir https://remotion.dev/license |
| WhisperX, OpenCV, Pillow, NumPy | dépendances Python | BSD, Apache-2.0, HPND, BSD |

Le langage visuel des habillages de `moteur/src/components/Graphics.tsx` (verre sombre, texte
argenté, accent ambre) s'inspire de NullMotion (github.com/blixvip/NullMotion). Le code est
écrit pour ce moteur et n'en reprend aucun fichier.

La structure du « hook » décrite dans `skills/montage-reel/reference/grammaire-hook.md` est une
analyse d'un réel public de Florian Boulay, cité comme source. Sa vidéo n'est pas fournie.
