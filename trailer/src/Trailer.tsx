/* The assembly. Six scenes, one caption track and one clock laid over all of
   them, and the voiceover if somebody has recorded one.

   Scenes overlap by CROSSFADE frames: each sequence runs that much past its
   own end while the next one fades up on top of it. Cutting instead would
   work, but six hard cuts in a minute reads as a slideshow, and the whole
   point of the middle of this video is that the three surfaces are one thing.

   One cut is hard on purpose. MailCall does not dissolve into Found: the
   mail stops and the frame changes, because a pile of paper that melts
   politely into the next idea is a pile of paper nobody flinched at.

   The caption track and the counter both sit outside the scenes. The read
   does not stop where a cut does, the clock does not restart where a cut
   does, and anything that re-lays itself per scene is something people stop
   reading. */

import React from "react";
import { AbsoluteFill, Audio, getStaticFiles, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { c } from "./theme";
import { SCENES } from "./script";
import { Captions } from "./components/atoms";
import { Counter } from "./components/Counter";
import { MailCall } from "./scenes/MailCall";
import { Found } from "./scenes/Found";
import { Release } from "./scenes/Release";
import { Surfaces } from "./scenes/Surfaces";
import { Deadline } from "./scenes/Deadline";
import { Logo } from "./scenes/Logo";

const CROSSFADE = 14;

/* The one scene that is cut to rather than dissolved into. */
const HARD_CUT_INTO = "Found";

const SCENE_COMPONENTS: Record<string, React.FC> = {
  MailCall,
  Found,
  Release,
  Surfaces,
  Deadline,
  Logo,
};

/* Fades itself up over the first `len` frames of its own sequence. The scene
   underneath is still at full opacity for exactly that long, which is what
   makes it a dissolve rather than a dip to black. */
const Dissolve: React.FC<{ len: number; children: React.ReactNode }> = ({ len, children }) => {
  const frame = useCurrentFrame();
  const opacity = len === 0 ? 1 : interpolate(frame, [0, len], [0, 1], {
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

/* The clock runs from the moment the product appears to the moment the last
   deadline leaves the screen. It is deliberately absent from the first
   twenty-five seconds, because nobody in that part of the story knows there
   is a clock, and absent from the wordmark, which needs a clean frame. */
const CLOCK_FROM = 930;
const CLOCK_UNTIL = 1650;

export const Trailer: React.FC = () => {
  const voiceover = useVoiceover();

  return (
    <AbsoluteFill style={{ backgroundColor: c.surface }}>
      {SCENES.map((scene, i) => {
        const Component = SCENE_COMPONENTS[scene.name];
        const isLast = i === SCENES.length - 1;
        const hardCut = scene.name === HARD_CUT_INTO;
        const next = SCENES[i + 1];
        /* Run past our own end only if the next scene is going to dissolve
           over the top of us. Holding a scene under a hard cut would leave the
           old frame showing through for half a second. */
        const tail = isLast || next?.name === HARD_CUT_INTO ? 0 : CROSSFADE;

        return (
          <Sequence
            key={scene.name}
            name={scene.name}
            from={scene.from}
            durationInFrames={scene.len + tail}
          >
            <Dissolve len={hardCut ? 0 : CROSSFADE}>
              <Component />
            </Dissolve>
          </Sequence>
        );
      })}

      <Counter from={CLOCK_FROM} until={CLOCK_UNTIL} />

      <Captions />

      {voiceover ? <Audio src={voiceover} /> : null}
    </AbsoluteFill>
  );
};
