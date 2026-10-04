import { AbsoluteFill, staticFile } from "remotion";
import { loadFont } from "@remotion/fonts";
import { Footage } from "./components/Footage";
import { Captions } from "./components/Captions";
import { TitlePill } from "./components/TitlePill";
import { Overlays } from "./components/Overlays";
import { SoundDesign } from "./components/SoundDesign";
import { Grade } from "./components/Grade";
import { Graphics } from "./components/Graphics";
import type { ReelProps } from "./types";

// Polices locales (public/fonts). Le nom de famille est celui utilisé dans style.font.
loadFont({ family: "Inter", url: staticFile("fonts/Inter-Bold.otf"), weight: "800" });
loadFont({ family: "Inter", url: staticFile("fonts/Inter-Bold.otf"), weight: "700" });
loadFont({ family: "Montserrat ExtraBold", url: staticFile("fonts/Montserrat-ExtraBold.otf"), weight: "800" });
loadFont({ family: "Montserrat ExtraBold", url: staticFile("fonts/Montserrat-ExtraBold.otf"), weight: "700" });
loadFont({ family: "Figtree", url: staticFile("fonts/Figtree-Medium.ttf"), weight: "500" });
loadFont({ family: "Figtree", url: staticFile("fonts/Figtree-SemiBold.ttf"), weight: "600" });
loadFont({ family: "Figtree", url: staticFile("fonts/Figtree-Bold.ttf"), weight: "700" });
loadFont({ family: "Figtree", url: staticFile("fonts/Figtree-ExtraBold.ttf"), weight: "800" });
loadFont({ family: "Figtree", url: staticFile("fonts/Figtree-ExtraBold.ttf"), weight: "900" });

// Pile des couches, du fond vers l'avant : plan → illustrations d'ambiance (+ personne) →
// étalonnage → illustrations devant → sous-titres → pastille titre. Son : voix du clip + SFX + musique.
export const Reel: React.FC<ReelProps> = (p) => (
  <AbsoluteFill style={{ backgroundColor: "#000" }}>
    <Footage p={p} />
    <Overlays p={p} layer="behind" />
    {p.style.grade ? <Grade light={p.style.look === "organic"} /> : null}
    <Overlays p={p} layer="front" />
    <Graphics p={p} />
    <Captions p={p} />
    <TitlePill p={p} />
    <SoundDesign p={p} />
  </AbsoluteFill>
);
