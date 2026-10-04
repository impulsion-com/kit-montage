# Règles de montage court format (réels face cam)

Synthèse des sources lues le 8 sept. 2026 : skill officielle Remotion, claude-shorts,
claude-remotion-skill (design-rules.md), guides d'éditeurs short form (flowshorts, EseCut,
Sonilo, CapCut), et la déconstruction du réel de Florian Boulay (`grammaire-hook.md`).
Les valeurs chiffrées sont celles implémentées dans `moteur/plan.py`.

## Timing

- **Le texte précède la voix** : une carte apparaît 1 image + latence audio avant le mot
  (≈ 80 ms avant ce qu'on entend). En retard, ça paraît cassé ; légèrement en avance, ça paraît
  synchro.
- **Alignement mot à mot par WhisperX** (wav2vec2 français), jamais les timestamps bruts de
  Whisper ou faster-whisper : mesuré sur un rush de test, faster-whisper plaçait « sur Instagram »
  0,6 s trop tôt et « et » 0,57 s trop tôt. WhisperX étire la fin du mot sur la pause qui
  suit : la fin est recalée sur la chute d'énergie.
- **Latence audio de Remotion** : 45 ms mesurés (rendu vs clip). Compensée dans le plan pour
  le texte et les SFX.
- **Pauses** : toute pause > 0,35 s est ramenée à ≈ 0,22 s (0,12 s gardé après le mot,
  0,10 s avant le suivant). 0,15 s de silence avant le premier mot, 0,45 s après le dernier.
  Une pause plus longue (0,3 à 0,6 s) ne se garde que devant une révélation.
- **Un beat toutes les 2 s maximum** : coupe, mot-clé, illustration. Si rien ne se passe
  pendant plus de 2 s, le plan pousse doucement de +5 % jusqu'au prochain évènement.

## Cartes (sous-titres)

- 1 à 3 mots par carte, coupées avant les mots de liaison et les élisions (et, que, parce,
  qu'on, j'ai, moi-même), jamais un mot-outil seul (il rejoint le mot-clé qui suit :
  « le media buying »).
- Les cartes d'une phrase s'empilent (3 lignes max), le mot-clé clôt la pile. Un mot-clé par
  phrase, celui qui porte l'information.
- Karaoké : les mots s'allument un à un (blanc 55 % → blanc), un mot-clé s'allume d'un bloc
  en accent, plus grand (×1,2), avec un ressort plus rebondissant.
- Entrée : ressort 14 images, échelle 0,82 → 1, montée 22 px, flou 6 → 0 px. Les lignes déjà
  posées ne bougent pas.
- Position : première ligne sous le menton le plus bas du plan (après zoom), entre 62 % et
  78 % de la hauteur. Zone sûre : rien sous 85 % ni au-dessus de 10 % (interface des apps).
- Typographie (look organique, défaut depuis le 9 sept. 2026) : Figtree 600, mot-clé 800,
  80 px sur 1080, blanc, ombre douce (0 2px 6px à 55 % + 0 6px 22px à 35 %), contour 1,5 px
  à 35 % d'opacité, interlignage 1,18. Pas de couleur d'accent, pas de pastille : le titre est
  un texte blanc nu (Figtree 700, 54 px, 12 % de la hauteur). Look « creator » (Inter 800,
  contour épais, pastille, jaune) disponible, mais il date.

## Zoom

- Continu, jamais linéaire : easeInOutQuint entre keyframes. Rampe 0,9 s vers le mot-clé,
  maintien 0,5 s, redescente 0,8 s. Amplitude 1,22 sur un plan large (visage ≈ 15 % de la
  hauteur), 1,06 sur un plan serré (≈ 45 %).
- Centré sur le visage (OpenCV à 4 images/s, médiane du plan). Le point du visage ne bouge
  pas pendant le zoom.
- Chaque coupe alterne le cadrage de base 1,00 / 1,08 (punch-in de jump cut).
- Conseil de tournage : cadrer large, tête sous le tiers supérieur, le montage serre.

## Illustrations

- Une par idée, ancrée sur le mot-clé (`anchor`), qui apparaît avec lui (offset ≈ 0) et
  dure 1 à 1,5 s. Jamais sur le visage. Devant le buste pour une capture (largeur 0,6 à 0,8,
  y ≈ 0,89), plein écran derrière la personne pour une ambiance (masque Vision → webm alpha).
- Entrée à ressort « smooth » (18 images) : montée 70 px ou glissement 90 px, sortie en
  8 images. Micro-respiration (±0,4 %) tant qu'elle est posée.

## B-roll détouré (« background remover »)

- Le sujet est détouré image par image (Vision, qualité accurate, flou de bord 1,5 px) et
  reposé devant un fond plein écran, avec la transformation de zoom exacte du plan : sans
  ça, le fond et le sujet se dédoublent pendant le fondu d'entrée.
- Séquence PNG alpha plutôt que webm VP9 alpha : Remotion perdait les premières images du
  webm (sujet fantôme pendant 0,3 s).
- Fond : image générée (Nano Banana, 9:16) avec Ken Burns lent 1,04 → 1,12, ou vidéo
  Pexels verticale. Fondu d'entrée 10 images, sortie 8 images, petit son « ui » au pic.
- Une ombre portée douce (18 px, 50 %) autour de la silhouette donne l'effet « détourage ».
- Le prompt décrit une plaque de fond : centre calme, pas de texte ni de logo ni de
  personne, profondeur de champ courte. Le b-roll illustre l'idée, il ne la commente pas.

## Son

- Voix : passe-haut 80 Hz, loudnorm -14 LUFS, limiteur final à -1,5 dBTP après le mix.
- SFX réservés aux 3 à 5 moments forts : whoosh sur la coupe, pop sur le mot-clé, swish
  sur le titre, buildup court (0,9 s) qui culmine sur le premier mot-clé, petit « ui » sur
  une illustration posée devant (jamais sur un b-roll d'ambiance).
- **Bannis (ils ne font pas professionnel)** : tous les
  impacts et hits cinéma (impact-hit-*, deep-hit-*, cinematic-bang/boom/heavy-hit/glass-hit,
  inception-thump, impact-and-subdrop, dramatic-impact). `plan.py` refuse de les poser, même à
  la main. Plus d'impact sur le dernier mot-clé (`payoff=False` par défaut).
- Le **pic** du son tombe 2 images avant le visuel. Le catalogue (`sfx/catalog.json`) donne
  la position du pic et de l'attaque de chacun des 100 sons de VideoEditingSFX (libres d'usage, téléchargés à l'installation).
- Niveaux de pic visés (voix à -14 LUFS, pics ≈ -2 dBFS) : whoosh -19, pop -23, swish -20,
  impact -17, buildup -25, ui -24 dBFS. Les SFX restent discrets : ne pas monter.
- Musique (si fournie) : 0,22 en fond, 0,09 sous la voix, fondu de 1 s à la fin. Aucune
  piste libre de droits n'est encore dans l'outillage.

## Vérification (obligatoire avant de livrer)

1. Planche contact 4 images/s, 3 images plein format sur des mots-clés.
2. Décalage audio rendu vs clip par corrélation croisée (doit rester ≈ 45 ms).
3. Niveaux : I ≈ -14 LUFS, pic ≤ -1,5 dBFS.
4. Aucun texte sur le visage, aucune illustration sous la pile de sous-titres.
5. Faire relire le rendu par la personne filmée avant de publier.
