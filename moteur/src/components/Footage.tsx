import { AbsoluteFill, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { ReelProps } from "../types";

// Le clip (déjà coupé et recadré 9:16 par plan.py, avec de la marge de résolution) est zoomé par
// transformation CSS. Le zoom suit les keyframes du plan, lissé, et reste centré sur le visage
// du plan courant : le point (cx, cy) du cadre ne bouge pas quand l'échelle change.
export const useFootageTransform = (p: ReelProps, absoluteFrame?: number) => {
  const current = useCurrentFrame();
  const frame = absoluteFrame ?? current;
  const { fps, width, height } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  let scale = 1;
  if (p.zoom.length >= 2) {
    scale = interpolate(ms, p.zoom.map((k) => k.ms), p.zoom.map((k) => k.scale), {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: theme.ease.inOut,
    });
  } else if (p.zoom.length === 1) {
    scale = p.zoom[0].scale;
  }
  const face = p.faces.find((f) => ms >= f.fromMs && ms < f.toMs) ?? p.faces[p.faces.length - 1];
  const cx = (face?.cx ?? 0.5) * width;
  const cy = (face?.cy ?? 0.4) * height;
  return { scale, cx, cy, style: { transformOrigin: `${cx}px ${cy}px`, transform: `scale(${scale})` } as React.CSSProperties };
};

export const Footage: React.FC<{ p: ReelProps }> = ({ p }) => {
  const { width, height } = useVideoConfig();
  const t = useFootageTransform(p);
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.ink, overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 0, top: 0, width, height, ...t.style }}>
        <OffthreadVideo src={staticFile(p.clip)} style={{ width, height, objectFit: "cover" }} volume={1} />
      </div>
    </AbsoluteFill>
  );
};
