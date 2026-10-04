---
name: montage-reel
description: Monter une vidéo face cam à partir d'un rush et de consignes, avec le kit montage Impulsion (Remotion). Réels 9:16 (Instagram, TikTok, Shorts) ou vidéos 16:9 (YouTube, formation) - coupe des silences, sous-titres karaoké mot à mot avec mot-clé accentué, titre, zoom centré sur le visage, illustrations, habillages de motion design, sound design discret. Use when the user says monte ce réel, monte cette vidéo, fais le montage, ajoute des sous-titres dynamiques, montage face cam, motion design sur ma vidéo, or gives a rush of someone talking to the camera.
---

# Montage face cam avec le kit montage

Le kit vit là où la personne l'a cloné. Cette skill y est reliée par un lien symbolique, donc
le lanceur se trouve toujours ici :

```bash
~/.claude/skills/montage-reel/../../montage
```

Dans la suite, `montage` désigne ce chemin. Le moteur est dans `moteur/` du même dossier
(`plan.py` prépare tout, Remotion rend). Si `montage` répond « Kit non installé », lancer
`installer.sh` à la racine du kit. `montage --verifier` contrôle l'installation.

Lire `reference/regles-montage.md` (timing, cartes, zoom, illustrations, son, vérification)
avant tout montage, puis `reference/grammaire-hook.md` pour la structure d'un hook.

**Quand ne pas utiliser ce moteur.** Il est fait pour un rush où quelqu'un parle à la caméra.
Pour une vidéo sans rush (film de motion design, explainer, vidéo tirée d'un site web), regarder
si les skills HyperFrames sont installées (`/hyperframes`) : elles couvrent ces cas. Sinon,
proposer `installer.sh --hyperframes` à la racine du kit. Une vidéo rendue par l'un ou l'autre
moteur peut ensuite être importée dans OpenCut Impulsion pour être assemblée sur une timeline.

## Démarrer un projet

Un dossier par vidéo, hors du kit, avec un `build.py` :

```bash
mkdir -p ~/Movies/montages/<slug>/assets && cd ~/Movies/montages/<slug>
```

```python
from plan import run

CONFIG = dict(
    src="~/Movies/mon-rush.mp4",        # rush face cam (9:16 ou 16:9, recadré au centre)
    slug="hook-ventes",                 # nom court, sans espace
    title=dict(text="Des ventes… en dormant ??"),
    keywords=["des ventes", "je dormais", "j'y croyais pas"],   # un par phrase
    replacements=[("Petit d'âge", "Petit dej'")],               # corrections de transcription
)
if __name__ == "__main__":
    run(CONFIG)
```

```bash
montage build.py plan         # transcrit, affiche cartes, coupes et sons, sans rendre
montage build.py still 2400   # une image à 2,4 s, pour contrôler un cadrage
montage build.py              # rendu complet → exports/<slug>-remotion.mp4
```

Le premier `plan` télécharge les modèles de transcription (environ 2 Go) et prend plusieurs
minutes. Les suivants réutilisent `work/words_x.json`.

`exemples/exemple-reel.py` et `exemples/exemple-16-9.py`, à la racine du kit, montrent une
CONFIG complète.

## Méthode, dans l'ordre

1. **Lire le rush** : lancer `plan`, relire les mots (`work/words_x.json`). Corriger les mots
   mal transcrits avec `replacements`. Les pauses de plus de 0,35 s sont resserrées toutes
   seules (`tighten=False` pour les garder, `gap_cut` pour changer le seuil). `keep=[(a, b)]`
   en temps source ne garde que certains passages, coupés sur un silence, jamais dans un mot.
2. **Choisir les mots-clés** : un par phrase, le mot qui porte l'information (chiffre,
   résultat, émotion). Jamais un mot-outil. Plusieurs mots possibles (« j'y croyais pas »).
3. **Vérifier le découpage** affiché par `plan` : groupes de 1 à 3 mots, coupés avant les mots
   de liaison. Si un groupe est bancal, le fixer avec `cards=[dict(text=…, s=…, e=…, key=…)]`
   en temps de sortie.
4. **Titre** : la promesse du hook en question courte (32 caractères au plus).
5. **Illustrations** : une par idée, jamais sur le visage.
   `overlays=[dict(file="assets/x.png", anchor="mot-clé", offset=-0.05, dur=1.2, x=0.5, y=0.89, w=0.78, anim="rise")]`
   pose une image ou une vidéo devant la personne au moment du mot.
6. **Zoom** : automatique, centré sur le visage détecté, plus ample sur un plan large. Conseil
   de tournage : cadrer large (buste visible), le moteur fait le serrage.
   `zoom_params=dict(punch=1.15)` règle l'amplitude.
7. **Son** : effets posés tout seuls et volontairement discrets, ne pas les monter.
   `sfx=[(t, "nom", dB)]` remplace le plan sonore (noms dans `moteur/sfx/catalog.json`),
   `music="fichier.mp3"` ajoute un tapis baissé sous la voix.
8. **Relire avant de livrer** : suivre la section Vérification de `regles-montage.md`
   (planche contact, niveaux, aucun texte sur le visage).

## Format 16:9 et motion design

`aspect="16:9"` rend en 1920x1080, avec des sous-titres sur 2 lignes. `hide_captions=[(a, b)]`
masque les sous-titres quand un graphisme dit déjà le texte.

`graphics=[dict(kind=…, at="mot prononcé", until="mot prononcé", x=…, y=…, scale=…, props=dict(…))]`
ajoute des habillages ancrés sur les mots. `after=secondes` choisit la bonne occurrence quand
le mot revient plusieurs fois.

| `kind` | Ce que ça affiche |
| --- | --- |
| `headline` | Surtitre, grand titre et pastille |
| `program` | Liste de chapitres avec étiquettes qui s'allument au fil des mots |
| `prompt` | Barre de commande qui se tape, puis lignes de résultat |
| `growth` | Courbe de croissance |
| `stack` | Pile de cartes avec icône |
| `notify` | Notifications empilées |
| `cta` | Appel à l'action |
| `shot` | Plan de coupe plein écran : `props=dict(name="pillSlot" ou "scramble" ou "blurSlide", …)` |

Garder le centre libre pour le visage : panneaux ancrés à gauche (`x≈0.035`, `align="left"`)
ou à droite (`x≈0.965`, `align="right"`). Les props de chaque habillage sont décrites en tête
de son composant dans `moteur/src/components/Graphics.tsx`. `moteur/shotcraft/` contient 216
animations Remotion à adapter : en copier une dans `moteur/src/shots/index.tsx` (textes en
props, couleurs du thème) et l'inscrire dans `SHOTS`.

Les couleurs, courbes et ressorts vivent dans `moteur/src/theme.ts` : c'est là qu'on met la
charte de la personne, jamais en dur dans un composant.

## Look par défaut

Organique : police Figtree, tout en blanc, ombre douce, titre en texte nu à 12 % de la hauteur,
mot-clé marqué par la graisse et la taille, sans couleur d'accent. C'est le rendu des polices
des stories Instagram. `style=dict(look="creator")` donne l'ancien look (Inter, pastille
blanche, mot-clé jaune), à n'utiliser que sur demande. Polices fournies : Figtree, Inter,
Montserrat ExtraBold.

## Fond derrière la personne (Mac, facultatif)

`broll=[dict(anchor="mot-clé", offset=-0.05, dur=1.4, file="assets/fond.jpg")]` pose un fond
plein écran derrière la personne détourée. `file` accepte une image ou une vidéo locale,
`query` cherche une vidéo sur Pexels (variable `PEXELS_API_KEY`). Il faut le binaire
`moteur/personmask`, compilé par `installer.sh` quand les outils Xcode sont présents. Un fond
par idée forte, 1,2 à 1,6 s, jamais deux d'affilée. Les séquences `moteur/public/<slug>/person_*`
pèsent environ 110 Mo par seconde : les supprimer après livraison.

## Pièges

- Les temps de `title`, `overlays`, `cards`, `sfx` sont en **temps de sortie** (après les
  coupes), `keep` en temps source.
- `work/words_x.json` est un cache : le supprimer pour retranscrire.
- La transcription sépare les apostrophes et invente des accents : `replacements` compare
  sans accents ni apostrophes.
- Un mot-clé donné avec sa préposition (« sur Instagram », « en freelance ») évite une carte
  d'un seul mot-outil.
- Pas de ponctuation dans les cartes : le moteur retire `. , ; :` en fin de carte et garde
  `?` et `!`.
- Les sons d'impact (impact-hit, cinematic-boom…) sont refusés par le moteur, même à la main.
