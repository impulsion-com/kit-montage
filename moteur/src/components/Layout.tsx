import { AbsoluteFill, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { Grade } from "./Grade";
import { useFootageTransform } from "./Footage";
import type { ReelProps } from "../types";

// Mises en page « vidéo + carte » : sur une plage, la vidéo quitte le plein cadre pour une
// fenêtre (moitié d'écran ou vignette) et laisse la place à un habillage de la couche Graphics.
// La fenêtre part du plein cadre et y revient : à progress = 0 elle se confond avec Footage.
const IN_MS = 600;
const OUT_MS = 480;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

type Rect = { x: number; y: number; w: number; h: number };

export const useLayoutState = (p: ReelProps) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const layout = p.layouts.find((l) => ms >= l.startMs && ms < l.endMs);
  if (!layout) return null;
  const span = layout.endMs - layout.startMs;
  const enter = interpolate(ms, [layout.startMs, layout.startMs + Math.min(IN_MS, span / 2)], [0, 1], { ...clamp, easing: theme.ease.inOut });
  const exit = interpolate(ms, [layout.endMs - Math.min(OUT_MS, span / 2), layout.endMs], [1, 0], { ...clamp, easing: theme.ease.inOut });
  const progress = Math.min(enter, exit);

  // plan.py écrit tous les champs ; les valeurs de repli couvrent un plan écrit à la main
  const pad = Math.round(height * 0.033);
  const side = layout.side ?? "right";
  const ratio = layout.ratio ?? 0.5;
  let target: Rect;
  if (layout.mode === "pip") {
    const w = width * (layout.size ?? 0.26);
    const h = w * (height / width);
    const [v, hz] = (layout.corner ?? "bottom-right").split("-");
    target = { x: hz === "left" ? pad : width - pad - w, y: v === "top" ? pad : height - pad - h, w, h };
  } else if (side === "left" || side === "right") {
    const w = width * ratio - pad * 1.5;
    target = { x: side === "left" ? pad : width - pad - w, y: pad, w, h: height - pad * 2 };
  } else {
    const h = height * ratio - pad * 1.5;
    target = { x: pad, y: side === "top" ? pad : height - pad - h, w: width - pad * 2, h };
  }
  const rect: Rect = {
    x: lerp(0, target.x, progress),
    y: lerp(0, target.y, progress),
    w: lerp(width, target.w, progress),
    h: lerp(height, target.h, progress),
  };
  return { layout, progress, rect, radius: Math.round(height * 0.026) * progress };
};

// Fond de scène, sous les habillages : il masque le plan plein cadre dès que la fenêtre se referme.
export const LayoutBackdrop: React.FC<{ p: ReelProps }> = ({ p }) => {
  const s = useLayoutState(p);
  return s && s.progress > 0 ? <AbsoluteFill style={{ background: theme.stage }} /> : null;
};

// La vidéo dans sa fenêtre, au-dessus des habillages (une vignette doit passer devant un plan de coupe).
// Le visage du plan courant est ramené au centre de la fenêtre, le zoom du plan continue de jouer.
export const LayoutWindow: React.FC<{ p: ReelProps }> = ({ p }) => {
  const { width, height } = useVideoConfig();
  const s = useLayoutState(p);
  const t = useFootageTransform(p);
  if (!s || s.progress <= 0) return null;
  const { rect, progress } = s;
  const scale = Math.max(rect.w / width, rect.h / height) * t.scale;
  const fx = lerp(t.cx, rect.w / 2, progress);
  const fy = lerp(t.cy, rect.h * 0.42, progress);
  const tx = Math.min(0, Math.max(rect.w - width * scale, fx - t.cx * scale));
  const ty = Math.min(0, Math.max(rect.h - height * scale, fy - t.cy * scale));
  return (
    <div
      style={{
        position: "absolute",
        left: rect.x,
        top: rect.y,
        width: rect.w,
        height: rect.h,
        overflow: "hidden",
        borderRadius: s.radius,
        boxShadow: `0 24px 60px rgba(0,0,0,${0.42 * progress})`,
        backgroundColor: theme.colors.ink,
      }}
    >
      <div style={{ position: "absolute", left: 0, top: 0, width, height, transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${scale})` }}>
        <OffthreadVideo src={staticFile(p.clip)} style={{ width, height, objectFit: "cover" }} muted />
        {p.style.grade ? <Grade light={p.style.look === "organic"} /> : null}
      </div>
    </div>
  );
};

// Point d'ancrage des sous-titres : ils suivent la fenêtre en moitié d'écran, restent en bas en vignette.
export const useCaptionAnchor = (p: ReelProps) => {
  const { width, height } = useVideoConfig();
  const s = useLayoutState(p);
  const base = height * p.style.subY;
  if (!s || s.layout.mode === "pip") return { dx: 0, y: base };
  const { rect, progress } = s;
  const inWindow = rect.y + rect.h - p.style.subSize * 1.18 * 2.4;
  return { dx: rect.x + rect.w / 2 - width / 2, y: lerp(base, Math.min(base, inWindow), progress) };
};
