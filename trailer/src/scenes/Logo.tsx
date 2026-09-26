/* 0:55.5. The wordmark, the one line, and who built it.

   The E in the word is the mark stood on end: a stone arch bridge, which is
   also a B lying on its back. It wipes on from the left behind a bright edge
   rather than fading up, because a mark that assembles reads as a thing that
   was built. */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { body, c } from "../theme";
import { Backdrop, Rise } from "../components/atoms";
import { Wordmark } from "../components/Mark";

export const Logo: React.FC = () => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [6, 58], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <Backdrop hue={c.teal} drift={0.3} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 34, paddingBottom: 150 }}>
        <Wordmark width={620} reveal={reveal} />

        <Rise delay={52}>
          <div style={{ fontFamily: body, fontSize: 38, color: c.ink, letterSpacing: ".01em" }}>
            Credit repair that starts before the gate.
          </div>
        </Rise>

        <Rise delay={84} style={{ textAlign: "center" }}>
          <div style={{ fontFamily: body, fontSize: 23, lineHeight: 1.55, color: c.muted }}>
            A capstone by fellows of the Fair Chance Futures AI Lab, 2026.
            <br />
            An independent project, not affiliated with or endorsed by NYS DOCCS.
          </div>
        </Rise>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
