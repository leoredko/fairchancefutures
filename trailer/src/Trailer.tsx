/* The assembly. Six scenes, one caption track laid over all of them, and the
   voiceover if somebody has recorded one.

   Scenes overlap by CROSSFADE frames: each sequence runs that much past its
   own end while the next one fades up on top of it. Cutting instead would
   work, but six hard cuts in a minute reads as a slideshow, and the whole
   point of the middle of this video is that the three surfaces are one thing.

   The caption track deliberately sits outside the scenes. The read does not
   stop where a cut does, and a caption that re-lays itself per scene is a
   caption people lose. */

import React from "react";
import { AbsoluteFill, Audio, getStaticFiles, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { c } from "./theme";
import { SCENES } from "./script";
import { Captions } from "./components/atoms";
import { Gate } from "./scenes/Gate";
import { Gap } from "./scenes/Gap";
import { Constraints } from "./scenes/Constraints";
import { Surfaces } from "./scenes/Surfaces";
import { Clock } from "./scenes/Clock";
import { Logo } from "./scenes/Logo";

const CROSSFADE = 14;

const SCENE_COMPONENTS: Record<string, React.FC> = {
  Gate,
  Gap,
  Constraints,
  Surfaces,
  Clock,
  Logo,
};

/* Fades itself up over the first CROSSFADE frames of its own sequence. The
   scene underneath is still at full opacity for exactly that long, which is
   what makes it a dissolve rather than a dip to black. */
const Dissolve: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, CROSSFADE], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

/* The voiceover is optional by design: with no file in public/ the trailer
   plays silent and the captions carry the whole script, which is also how it
   plays on a muted phone. Looking the file up rather than importing it means
   dropping voiceover.mp3 in and rendering again is the entire workflow. */
const useVoiceover = (): string | null => {
  const files = getStaticFiles();
  const found = files.find((f) => f.name === "voiceover.mp3" || f.name === "voiceover.wav");
  return found ? staticFile(found.name) : null;
};

export const Trailer: React.FC = () => {
  const voiceover = useVoiceover();

  return (
    <AbsoluteFill style={{ backgroundColor: c.surface }}>
      {SCENES.map((scene, i) => {
        const Component = SCENE_COMPONENTS[scene.name];
        const isLast = i === SCENES.length - 1;
        return (
          <Sequence
            key={scene.name}
            name={scene.name}
            from={scene.from}
            durationInFrames={scene.len + (isLast ? 0 : CROSSFADE)}
          >
            <Dissolve>
              <Component />
            </Dissolve>
          </Sequence>
        );
      })}

      <Captions />

      {voiceover ? <Audio src={voiceover} /> : null}
    </AbsoluteFill>
  );
};
