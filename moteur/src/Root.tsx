import { Composition } from "remotion";
import { Reel } from "./Reel";
import { ReelPropsSchema } from "./types";

const defaults = ReelPropsSchema.parse({
  slug: "demo",
  durationMs: 5000,
  clip: "demo/clip.mp4",
  clipWidth: 1080,
  clipHeight: 1920,
  cards: [],
});

export const Root: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    schema={ReelPropsSchema}
    defaultProps={defaults}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={150}
    calculateMetadata={async ({ props }) => ({
      durationInFrames: Math.round((props.durationMs / 1000) * props.fps),
      fps: props.fps,
      width: props.width,
      height: props.height,
    })}
  />
);
