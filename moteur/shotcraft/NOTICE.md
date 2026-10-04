# video-shotcraft (bibliothèque de démos Remotion)

Copie de `demos/` de https://github.com/Vincentwei1021/video-shotcraft (Apache-2.0, voir LICENSE),
révision indiquée dans SOURCE.txt, copiée le 23 sept. 2026.

Modifications apportées ici :
- `_fixtures/Motion.tsx` : `useT()` lit d'abord la durée du plan fournie par `ShotDurationContext`
  (le moteur place chaque composant dans une Sequence, alors que `useVideoConfig()` renvoie la durée
  de toute la vidéo). Sans contexte, comportement d'origine.

Les versions adaptées à nos textes et à notre charte vivent dans `../src/shots/` (chaque fichier
indique le composant d'origine).
