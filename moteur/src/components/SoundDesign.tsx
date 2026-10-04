import { Audio, Sequence, interpolate, staticFile, useVideoConfig } from "remotion";
import type { ReelProps } from "../types";

// Effets sonores posés par plan.py : atMs est déjà l'instant où le fichier doit DÉMARRER pour que
// son pic tombe sur l'évènement (2 à 3 images avant le visuel). Musique duckée sous la voix.
export const SoundDesign: React.FC<{ p: ReelProps }> = ({ p }) => {
  const { fps, durationInFrames } = useVideoConfig();
  return (
    <>
      {p.sfx.map((s, i) => {
        const from = Math.max(0, Math.round((s.atMs / 1000) * fps));
        return (
          <Sequence key={i} from={from} layout="none">
            <Audio src={staticFile(s.src)} volume={s.gain} />
          </Sequence>
        );
      })}
      {p.music ? (
        <Audio
          src={staticFile(p.music.src)}
          loop
          volume={(f) => {
            const ms = (f / fps) * 1000;
            const speaking = p.speech.some(([a, b]) => ms >= a - 120 && ms <= b + 250);
            const tail = interpolate(f, [durationInFrames - fps, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (speaking ? p.music!.duckGain : p.music!.gain) * tail;
          }}
        />
      ) : null}
    </>
  );
};
