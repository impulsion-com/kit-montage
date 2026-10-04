import { Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { ReelProps } from "../types";

// Pastille blanche en haut : la promesse du hook en question. Ressort à l'entrée, sortie rapide.
const Pill: React.FC<{ p: ReelProps; durationInFrames: number }> = ({ p, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const enter = spring({ frame, fps, config: theme.spring.snappy, durationInFrames: 16 });
  const exitStart = durationInFrames - theme.timing.exitFrames;
  const exit = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: theme.ease.in,
  });
  const scale = interpolate(enter, [0, 1], [0.7, 1]) * interpolate(exit, [0, 1], [0.9, 1]);
  const y = interpolate(enter, [0, 1], [-30, 0]);
  const size = p.style.titleSize;
  const organic = p.style.look === "organic";
  const inner = organic ? (
    <div
      style={{
        color: theme.colors.white,
        fontFamily: `'${p.style.font}', sans-serif`,
        fontWeight: 700,
        fontSize: size,
        letterSpacing: -0.4,
        textAlign: "center",
        maxWidth: width * 0.84,
        lineHeight: 1.12,
        textShadow: "0 2px 6px rgba(0,0,0,0.55), 0 8px 26px rgba(0,0,0,0.35)",
        WebkitTextStroke: `${Math.max(1.5, size * 0.022)}px rgba(0,0,0,0.35)`,
        paintOrder: "stroke fill",
        transform: "translateY(-50%)",
      }}
    >
      {p.title?.text}
    </div>
  ) : (
    <div
      style={{
        background: theme.colors.white,
        color: theme.colors.ink,
        fontFamily: `'${p.style.font}', sans-serif`,
        fontWeight: 700,
        fontSize: size,
        padding: `${size * 0.42}px ${size * 0.8}px`,
        borderRadius: size * 1.2,
        boxShadow: "0 8px 30px rgba(0,0,0,0.25)",
        transform: "translateY(-50%)",
        whiteSpace: "nowrap",
      }}
    >
      {p.title?.text}
    </div>
  );
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        width,
        top: height * p.style.titleY,
        display: "flex",
        justifyContent: "center",
        opacity: Math.min(enter * 1.5, 1) * exit,
        transform: `translateY(${y}px) scale(${organic ? 1 : scale})`,
      }}
    >
      {inner}
    </div>
  );
};

export const TitlePill: React.FC<{ p: ReelProps }> = ({ p }) => {
  const { fps } = useVideoConfig();
  if (!p.title) return null;
  const from = Math.round((p.title.startMs / 1000) * fps);
  const dur = Math.max(4, Math.round((p.title.endMs / 1000) * fps) - from);
  return (
    <Sequence from={from} durationInFrames={dur} layout="none">
      <Pill p={p} durationInFrames={dur} />
    </Sequence>
  );
};
