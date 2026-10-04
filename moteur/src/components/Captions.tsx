import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import type { Card, ReelProps } from "../types";

const msToFrame = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

// Une carte : un groupe de 1 à 3 mots. Entrée à ressort (échelle + montée + flou), les mots
// s'allument un à un au fil de la voix (karaoké), le mot-clé est en accent et plus grand.
const CardView: React.FC<{ card: Card; p: ReelProps; y: number; size: number }> = ({ card, p, y, size }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const ms = card.startMs + (frame / fps) * 1000;

  const enter = spring({ frame, fps, config: card.key ? theme.spring.bouncy : theme.spring.snappy, durationInFrames: 14 });
  const scale = interpolate(enter, [0, 1], [0.82, 1]);
  const rise = interpolate(enter, [0, 1], [22, 0]);
  const blur = interpolate(enter, [0, 1], [6, 0], { extrapolateRight: "clamp" });
  const opacity = interpolate(frame, [0, 3], [0, 1], { extrapolateRight: "clamp" });

  const organic = p.style.look === "organic";
  const accent = p.style.accent;
  // organique : ombre douce façon Instagram / Edits, contour très fin ; créateur : contour épais
  const outline = organic ? Math.max(1.5, size * 0.022) : Math.max(4, size * 0.07);
  const shadow = organic
    ? `0 2px 6px rgba(0,0,0,0.55), 0 6px 22px rgba(0,0,0,0.35)`
    : `0 0 ${outline}px ${theme.colors.ink}, 0 0 ${outline}px ${theme.colors.ink}, 0 ${outline * 0.6}px ${outline * 1.6}px ${theme.colors.shadow}`;
  const dim = organic ? "rgba(255,255,255,0.62)" : "rgba(255,255,255,0.55)";

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        width,
        top: y,
        display: "flex",
        justifyContent: "center",
        alignItems: "baseline",
        gap: size * 0.24,
        transform: `translateY(${rise}px) scale(${scale})`,
        transformOrigin: "50% 50%",
        filter: `blur(${blur}px)`,
        opacity,
        whiteSpace: "pre",
      }}
    >
      {card.tokens.map((t, i) => {
        const active = ms >= t.fromMs;                         // déjà prononcé ou en cours
        const lit = card.key ? true : active;                  // un mot-clé est allumé d'un bloc
        const pop = card.key
          ? 1
          : interpolate(ms, [t.fromMs, t.fromMs + 90], [0.94, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <span
            key={i}
            style={{
              fontFamily: `'${p.style.font}', sans-serif`,
              fontWeight: card.key ? 800 : organic ? 600 : 800,
              fontSize: size,
              lineHeight: 1.05,
              letterSpacing: organic ? -0.3 : -0.5,
              color: card.key ? accent : lit ? theme.colors.white : dim,
              WebkitTextStroke: `${organic ? outline : outline * 0.55}px rgba(0,0,0,${organic ? 0.35 : 1})`,
              paintOrder: "stroke fill",
              textShadow: shadow,
              display: "inline-block",
              transform: `scale(${pop})`,
            }}
          >
            {t.text.trim()}
          </span>
        );
      })}
    </div>
  );
};

export const Captions: React.FC<{ p: ReelProps }> = ({ p }) => {
  const { fps, height } = useVideoConfig();
  const base = height * p.style.subY;
  const lh = p.style.subSize * 1.18;
  return (
    <AbsoluteFill>
      {p.cards.map((c, i) => {
        const from = msToFrame(c.startMs, fps);
        const dur = Math.max(2, msToFrame(c.endMs, fps) - from);
        const size = c.key ? p.style.subSize * p.style.keyScale : c.line === 0 ? p.style.subSize : p.style.subSize * p.style.minorScale;
        const y = base + c.line * lh - size * 0.5;
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <CardView card={c} p={p} y={y} size={size} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
