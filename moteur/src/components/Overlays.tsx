import { AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { useFootageTransform } from "./Footage";
import type { Overlay, ReelProps } from "../types";

const Item: React.FC<{ o: Overlay; durationInFrames: number }> = ({ o, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const enter = spring({ frame, fps, config: theme.spring.smooth, durationInFrames: 18 });
  const exit = interpolate(frame, [durationInFrames - theme.timing.exitFrames, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: theme.ease.in,
  });
  const w = width * o.w;
  let dx = 0, dy = 0, sc = 1;
  if (o.anim === "rise") dy = interpolate(enter, [0, 1], [70, 0]);
  if (o.anim === "slide_left") dx = interpolate(enter, [0, 1], [90, 0]);
  if (o.anim === "slide_right") dx = interpolate(enter, [0, 1], [-90, 0]);
  if (o.anim === "pop") sc = interpolate(enter, [0, 1], [0.8, 1]);
  const opacity = (o.anim === "fade" ? interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" }) : Math.min(enter * 1.4, 1)) * exit;
  const breathe = 1 + Math.sin(frame / fps * 1.6) * 0.004;   // micro-mouvement des éléments posés
  const full = o.w >= 0.99;
  // b-roll plein écran : lent Ken Burns (1,04 → 1,12) pour que l'arrière-plan vive
  const kb = full ? interpolate(frame, [0, durationInFrames], [1.04, 1.12], { extrapolateRight: "clamp" }) : 1;
  const style: React.CSSProperties = {
    position: "absolute",
    left: width * o.x - w / 2 + dx,
    top: o.w >= 0.99 ? 0 : undefined,
    width: w,
    opacity,
    transform: `translateY(${dy}px) scale(${sc * breathe * kb})`,
    transformOrigin: "50% 50%",
    filter: o.key === "black" ? "none" : undefined,
    mixBlendMode: o.key === "black" ? "screen" : "normal",
  };
  if (o.kind === "video") {
    return (
      <OffthreadVideo
        src={staticFile(o.src)}
        muted
        loop
        transparent={o.src.endsWith(".webm")}
        style={{ ...style, height: o.w >= 0.99 ? height : undefined, objectFit: "cover", top: o.w >= 0.99 ? 0 : height * o.y - (w * 9) / 16 / 2 }}
      />
    );
  }
  if (full) {
    return <Img src={staticFile(o.src)} style={{ ...style, left: 0, top: 0, width, height, objectFit: "cover", transform: `scale(${kb})` }} />;
  }
  return <Img src={staticFile(o.src)} style={{ ...style, top: undefined, transform: `translateY(calc(${height * o.y}px - 50% + ${dy}px)) scale(${sc * breathe})` }} />;
};

// La couche « personne » : séquence PNG avec alpha (une image par frame, décodage sûr), posée par-dessus
// le b-roll avec exactement la transformation de zoom du plan, pour se superposer au pixel près.
const Person: React.FC<{ dir: string; p: ReelProps; absoluteFrom: number }> = ({ dir, p, absoluteFrom }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const t = useFootageTransform(p, absoluteFrom + frame);
  const name = String(frame + 1).padStart(5, "0");
  return (
    <Img
      src={staticFile(`${dir}/${name}.png`)}
      style={{ position: "absolute", left: 0, top: 0, width, height, ...t.style, filter: "drop-shadow(0 0 18px rgba(0,0,0,0.5))" }}
    />
  );
};

export const Overlays: React.FC<{ p: ReelProps; layer: "behind" | "front" }> = ({ p, layer }) => {
  const { fps } = useVideoConfig();
  const items = p.overlays.filter((o) => (layer === "behind" ? o.behind : !o.behind));
  return (
    <AbsoluteFill>
      {items.map((o, i) => {
        const from = Math.round((o.startMs / 1000) * fps);
        const dur = Math.max(4, Math.round((o.endMs / 1000) * fps) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <Item o={o} durationInFrames={dur} />
            {o.behind && o.personSrc ? <Person dir={o.personSrc} p={p} absoluteFrom={from} /> : null}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
