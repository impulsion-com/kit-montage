import { z } from "zod";

// Le plan est produit par plan.py (temps en millisecondes, temps de SORTIE après resserrage).
export const TokenSchema = z.object({ text: z.string(), fromMs: z.number(), toMs: z.number() });

export const CardSchema = z.object({
  text: z.string(),
  startMs: z.number(),      // apparition (déjà avancée de ~2 images par plan.py)
  endMs: z.number(),        // fin de la pile
  key: z.boolean(),         // mot-clé : accent, plus grand
  line: z.number(),         // ligne dans la pile (0, 1, 2)
  tokens: z.array(TokenSchema),
});

export const TitleSchema = z.object({ text: z.string(), startMs: z.number(), endMs: z.number() });

export const ZoomKeyframeSchema = z.object({ ms: z.number(), scale: z.number() });
export const FaceSchema = z.object({ fromMs: z.number(), toMs: z.number(), cx: z.number(), cy: z.number() });

export const OverlaySchema = z.object({
  src: z.string(),          // chemin public (staticFile)
  kind: z.enum(["image", "video"]),
  startMs: z.number(),
  endMs: z.number(),
  x: z.number(),            // centre, fraction de la largeur
  y: z.number(),            // centre, fraction de la hauteur
  w: z.number(),            // largeur, fraction
  anim: z.enum(["rise", "fade", "slide_left", "slide_right", "pop"]).default("rise"),
  behind: z.boolean().default(false),
  personSrc: z.string().optional(),   // webm avec alpha : la personne à reposer par-dessus
  key: z.enum(["none", "black", "green"]).default("none"),
});

// Motion design (couche Graphics) : habillages au langage visuel inspiré de NullMotion.
// Temps de sortie en ms ; les props portent leurs propres instants (clé `ms`) résolus par plan.py.
export const GraphicSchema = z.object({
  kind: z.enum(["headline", "program", "prompt", "growth", "stack", "notify", "cta", "shot"]),   // shot = plan de coupe shotcraft (src/shots)
  startMs: z.number(),
  endMs: z.number(),
  x: z.number().default(0.5),     // centre, fraction de la largeur
  y: z.number().default(0.5),     // centre, fraction de la hauteur
  scale: z.number().default(1),
  props: z.any().default({}),
});

// Mise en page « vidéo + carte » : la vidéo passe en moitié d'écran (split) ou en vignette (pip)
// pendant qu'un habillage occupe la place libérée. Temps de sortie en ms.
export const LayoutSchema = z.object({
  mode: z.enum(["split", "pip"]),
  startMs: z.number(),
  endMs: z.number(),
  side: z.enum(["left", "right", "top", "bottom"]).default("right"),                              // split : où va la vidéo
  ratio: z.number().default(0.5),                                                                 // split : part de l'écran laissée à la vidéo
  corner: z.enum(["top-left", "top-right", "bottom-left", "bottom-right"]).default("bottom-right"), // pip
  size: z.number().default(0.26),                                                                 // pip : largeur, fraction
});

export const SfxSchema = z.object({ src: z.string(), atMs: z.number(), gain: z.number() }); // gain linéaire

export const ReelPropsSchema = z.object({
  slug: z.string(),
  fps: z.number().default(30),
  width: z.number().default(1080),
  height: z.number().default(1920),
  durationMs: z.number(),
  clip: z.string(),
  clipWidth: z.number(),
  clipHeight: z.number(),
  cards: z.array(CardSchema),
  title: TitleSchema.nullable().default(null),
  cuts: z.array(z.number()).default([]),
  zoom: z.array(ZoomKeyframeSchema).default([]),
  faces: z.array(FaceSchema).default([]),
  overlays: z.array(OverlaySchema).default([]),
  graphics: z.array(GraphicSchema).default([]),
  layouts: z.array(LayoutSchema).default([]),
  sfx: z.array(SfxSchema).default([]),
  music: z.object({ src: z.string(), gain: z.number(), duckGain: z.number() }).nullable().default(null),
  speech: z.array(z.tuple([z.number(), z.number()])).default([]),  // plages de parole (ms) pour le ducking
  style: z.object({
    look: z.enum(["organic", "creator"]).default("organic"),   // organic = Instagram/Edits, creator = pastille + accent
    font: z.string().default("Figtree"),
    accent: z.string().default("#FFFFFF"),          // couleur du mot-clé (blanc en organique)
    subSize: z.number().default(80),
    subY: z.number().default(0.62),
    keyScale: z.number().default(1.12),
    minorScale: z.number().default(0.8),
    titleSize: z.number().default(54),
    titleY: z.number().default(0.12),
    grade: z.boolean().default(true),
  }).default({}),
});

export type ReelProps = z.infer<typeof ReelPropsSchema>;
export type Card = z.infer<typeof CardSchema>;
export type Overlay = z.infer<typeof OverlaySchema>;
export type Graphic = z.infer<typeof GraphicSchema>;
