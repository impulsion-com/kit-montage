import { AbsoluteFill } from "remotion";

// Étalonnage léger : vignette douce et un voile sombre en bas pour la lisibilité des sous-titres.
// Jamais sur le visage (le centre reste intact).
export const Grade: React.FC<{ light?: boolean }> = ({ light }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    {light ? null : (
      <AbsoluteFill
        style={{
          background: "radial-gradient(ellipse 80% 70% at 50% 42%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.28) 100%)",
        }}
      />
    )}
    <AbsoluteFill
      style={{
        background: `linear-gradient(to bottom, rgba(0,0,0,0) ${light ? 70 : 62}%, rgba(0,0,0,${light ? 0.14 : 0.22}) 100%)`,
      }}
    />
  </AbsoluteFill>
);
