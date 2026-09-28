/* 0:25. A name, a date and a number of days.

   Everything before this is the problem and everything after it is the
   product, so this is the six seconds that says who any of it is for. One
   person, one date, and a count that then sits in the corner of every
   remaining shot so the product is never shown without the clock it is
   racing.

   The number is frozen in script.ts rather than computed at render time, and
   the reason is written down there: a trailer whose voiceover stops matching
   its own picture after a week is worse than one that is a fortnight stale. */

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { body, c, gradText, mono } from "../theme";
import { Backdrop, Display, Kicker, Rise, Sweep } from "../components/atoms";
import { CLIENT } from "../script";

export const Release: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  /* Counts up to the number rather than cutting to it, so the figure reads as
     a measurement of something rather than a headline. */
  const days = Math.round(
    interpolate(spring({ frame: frame - 14, fps, config: { damping: 200, mass: 1.6 } }), [0, 1], [0, CLIENT.daysToGate]),
  );

  return (
    <AbsoluteFill>
      <Backdrop hue={c.teal} drift={0.45} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 190, gap: 26 }}>
        <Rise delay={4}>
          <Kicker>One person, one clock</Kicker>
        </Rise>

        <div style={{ display: "flex", alignItems: "baseline", gap: 26 }}>
          <div
            style={{
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
              fontWeight: 700,
              fontSize: 260,
              lineHeight: 1,
              letterSpacing: "-.05em",
              paddingLeft: 14,
              marginLeft: -14,
              ...gradText,
            }}
          >
            {days}
          </div>
          <Display size={78} weight={500} color={c.ink2}>
            days to the gate
          </Display>
        </div>

        <Rise delay={54}>
          <Sweep width={520} />
        </Rise>

        <Rise delay={64} style={{ marginTop: 8 }}>
          <div style={{ display: "flex", gap: 44, fontFamily: mono, fontSize: 25, color: c.ink2 }}>
            <span>{CLIENT.name}</span>
            <span>DIN {CLIENT.din}</span>
            <span>Conditional release {CLIENT.releaseDate}</span>
          </div>
        </Rise>

        <Rise delay={84} style={{ marginTop: 14 }}>
          <div style={{ fontFamily: body, fontSize: 30, color: c.ink }}>
            Everything wrong on his file has to be fixed from in there.
          </div>
        </Rise>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
