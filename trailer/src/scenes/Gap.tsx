/* 0:11. The refusal, and then the number.

   Three stamps, because there is no softer way to say it: the device this
   product runs on sits somewhere that has none of those three things, and
   that is a fact about a building rather than a setting somebody can turn on.

   The fifty points is the one statistic in the trailer and it carries its
   source on screen, the same rule the app runs on. The other number the team
   has heard, thirty-two points per year of confinement, is an open question in
   app/sources.py and is deliberately not here. */

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { body, c, gradText } from "../theme";
import { Backdrop, Display, Rise, SourceChip } from "../components/atoms";

const STAMPS = ["No camera", "No mail out", "No open web"];

export const Gap: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  /* The stamps hand over to the number rather than cutting: both live in this
     scene so the crossfade is one opacity ramp instead of a hard edit. */
  const stampsOut = interpolate(frame, [118, 140], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const numberIn = interpolate(frame, [134, 150], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  /* Counts to fifty. About, because the CFPB number is an average and a
     counter that lands on a precise 50 would be claiming more than that. */
  const count = Math.round(
    interpolate(spring({ frame: frame - 140, fps, config: { damping: 200, mass: 1.4 } }), [0, 1], [0, 50]),
  );

  return (
    <AbsoluteFill>
      <Backdrop hue={c.rose} drift={0.4} />

      <AbsoluteFill style={{ opacity: stampsOut, justifyContent: "center", alignItems: "center", gap: 22, paddingBottom: 170 }}>
        {STAMPS.map((s, i) => {
          const t = spring({ frame: frame - (6 + i * 26), fps, config: { damping: 190, mass: 0.7 } });
          return (
            <div
              key={s}
              style={{
                opacity: t,
                transform: `scale(${interpolate(t, [0, 1], [1.16, 1])})`,
              }}
            >
              <Display size={92} color={i === 2 ? c.rose : c.ink} style={{ letterSpacing: "-.03em" }}>
                {s}
              </Display>
            </div>
          );
        })}
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: numberIn, justifyContent: "center", alignItems: "center", paddingBottom: 170 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 24 }}>
          <div style={{ fontFamily: "'Space Grotesk', system-ui, sans-serif", fontWeight: 700, fontSize: 300, lineHeight: 1, letterSpacing: "-.05em", ...gradText }}>
            {count}
          </div>
          <Display size={84} color={c.ink2} weight={500}>
            points lower
          </Display>
        </div>
        <Rise delay={168} style={{ marginTop: 18, maxWidth: 1180, textAlign: "center" }}>
          <div style={{ fontFamily: body, fontSize: 34, lineHeight: 1.4, color: c.ink }}>
            The average credit score of a formerly imprisoned person, set against
            somebody who was never incarcerated.
          </div>
        </Rise>
        <Rise delay={190} style={{ marginTop: 24 }}>
          <SourceChip text="CFPB, Justice-Involved Individuals and the Consumer Financial Marketplace, January 2022" />
        </Rise>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
