# Grammaire d'un hook face cam, déconstruite

Source : réel de Florian Boulay (monteur vidéo), « Comment est construit un Hook ? »,
facebook.com/reel/27662325850130916, 31 s, 24 000 vues. La vidéo appartient à son auteur et
n'est pas fournie avec ce kit : la regarder à la source.

Le réel rejoue **six fois le même plan de 5,13 s** en ajoutant une couche de montage à chaque
passage. Mesures faites image par image (5 et 10 images/s), par estimation d'échelle contre le
passage brut, et par comparaison des enveloppes audio.

## Le texte du hook (5 s, 22 mots)

> Petit dej' tranquille et je réalise que j'ai fait **des ventes** pendant que **je dormais**.
> Non mais il faut que je t'explique, parce que moi-même **j'y croyais pas**.

Structure : situation banale (petit dej') → révélation surprenante (des ventes en dormant) →
promesse d'explication (il faut que je t'explique) → preuve d'authenticité (moi-même j'y croyais
pas). Un jump cut à 3,3 s sépare la révélation de la promesse, avec un cadrage plus serré.

## Les six couches, dans l'ordre

| # | Couche | Ce qu'on voit |
| --- | --- | --- |
| 1 | Brute | Plan large, sans rien. |
| 2 | Titre + Texte | Pastille blanche en haut (« Des ventes… en dormant ?? ») et sous-titres blancs simples, un groupe de 1 à 3 mots à la fois. |
| 3 | Mise en forme + Zooms | Groupes empilés jusqu'à 3 lignes, mot-clé en jaune et plus grand, zoom continu lent. |
| 4 | Animations de texte | Chaque groupe apparaît avec un flou qui se résout et un léger pop d'échelle (≈ 140 ms). |
| 5 | Illustrations + Animations | Capture d'un graphique de ventes glissée devant le buste, pluie de billets derrière la personne (masque de personne). |
| 6 | Sound design | Effets sonores sur la coupe et les apparitions, discrets sauf sur le jump cut. |

## Couche 2 : titre et sous-titres

- **Pastille titre** : rectangle blanc très arrondi, texte noir gras, centré, centre à ≈ 11 % de la
  hauteur, texte ≈ 2,3 % de la hauteur. Elle reformule la promesse du hook sous forme de question
  et disparaît au jump cut (elle ne couvre que le premier plan).
- **Sous-titres** : un « groupe de sens » à la fois, jamais un mot isolé sauf pour l'accent :
  « Petit dej' » / « tranquille » / « et je réalise » / « que j'ai fait » / « des ventes » /
  « pendant que » / « je dormais » / « Non mais il faut » / « que je t'explique » / « parce que » /
  « moi-même » / « j'y croyais pas ». Cadence ≈ 0,4 s par groupe. Police géométrique grasse
  (type Montserrat/Poppins ExtraBold), blanc, contour noir fin, centré, à ≈ 62 % de la hauteur
  (sous le visage, au-dessus des mains). Pas de ponctuation.

## Couche 3 : empilement, accent, zoom

- **Empilement** : les groupes d'une même phrase restent à l'écran et s'empilent vers le bas
  (« et je réalise » puis « que j'ai fait » dessous, plus petit, puis « des ventes » dessous en
  jaune, plus grand). Le mot-clé clôt la pile ; la phrase suivante repart d'une pile vide.
  Trois lignes maximum.
- **Hiérarchie** : première ligne taille normale, lignes suivantes ≈ 0,8, mot-clé ≈ 1,2 en jaune
  chaud (proche #F5B800). Un mot-clé par phrase, toujours le mot qui porte l'information
  (ventes, dormais, croyais pas) et jamais un mot-outil.
- **Zoom continu** (échelle mesurée par rapport au passage brut) :

  | Temps | Échelle | Ce qui se dit |
  | --- | --- | --- |
  | 0,0 → 1,0 s | 1,00 → 1,24 | montée lente sur « Petit dej' tranquille et je réalise » |
  | 1,0 → 1,5 s | 1,24 | maintien sur « que j'ai fait des ventes » |
  | 1,6 → 2,4 s | 1,24 → 1,00 | redescente sur « pendant que je dormais » |
  | 2,4 → 4,0 s | 1,00 | jump cut, plan serré, « Non mais il faut que je t'explique parce que » |
  | 4,0 → 4,8 s | 1,00 → 1,28 | montée sur « moi-même j'y croyais pas » |

  Donc : pas de punch-in sec, des rampes de 0,8 à 1 s, amplitude ≈ 1,25, centrées sur le visage,
  une montée par idée forte, une redescente avant la suivante. Le jump cut fait le punch-in sec à
  sa place.

## Couche 4 : animations de texte

Chaque groupe apparaît en ≈ 140 ms : flou net → net, échelle 90 → 100 %, fondu. Les lignes
déjà affichées ne bougent pas. Pas de karaoké mot par mot, pas de rebond.

## Couche 5 : illustrations

- **Capture d'écran** (graphique de ventes avec deux pics entourés en rouge) : glisse depuis le bas
  avec fondu à « et je réalise » (≈ 1,1 s), reste jusqu'au jump cut, posée devant le buste,
  largeur ≈ 60 % de l'écran, bord arrondi. Elle illustre « des ventes » avant même que le mot
  soit dit.
- **Pluie de billets** : de « que j'ai fait » à « je dormais » (≈ 1,6 → 3,1 s), plein écran, derrière
  la personne (détourage), fondu d'entrée et de sortie. Elle illustre l'argent, littéralement.
- Règle : une illustration par idée, synchronisée sur le groupe qu'elle illustre, jamais sur le
  visage.

## Couche 6 : son

Enveloppe audio du passage 6 moins passage 5 :

| Temps | Différence | Interprétation |
| --- | --- | --- |
| 1,1 s, 1,8 s, 2,3 s | +2 à +3 dB | pops discrets sur les apparitions de texte et d'illustrations |
| 2,9 → 3,4 s | +9 à +27 dB | whoosh + impact sur le jump cut, dans un silence de la voix |
| 4,8 → 5,0 s | +7 à +10 dB | whoosh de sortie, transition vers le passage suivant |

Les effets forts tombent dans les silences de la voix, jamais dessus. Réglage retenu dans ce kit : SFX très
discrets, ≈ 14 dB sous la voix.

## Ce que ça donne comme règles pour nos réels

1. Écrire le hook avant de tourner : banal → surprise → promesse → preuve, 20 à 25 mots, 5 s.
2. Tourner deux cadrages (large puis serré) ou prévoir le jump cut au montage avec un punch-in.
3. Titre en pastille = la promesse en question, visible sur le premier plan seulement.
4. Sous-titres par groupe de sens, empilés par phrase, un seul mot-clé en accent par phrase.
5. Zoom en rampes lentes vers le visage sur les idées fortes, redescente entre deux.
6. Une illustration par idée : capture d'écran devant, ambiance plein écran derrière la personne.
7. SFX sur les coupes et les apparitions, forts seulement dans les silences.
