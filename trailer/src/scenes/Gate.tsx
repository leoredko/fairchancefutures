/* 0:00. What proving who you are actually costs.

   The list is not dramatised. It is the contents of the `mailed_dispute_identity`
   fact in app/sources.py, which is what the bureaus ask a free citizen to put
   in an envelope, and the citation stays on screen under it. Six lines is a
   lot of screen for eleven seconds, and that is the point: the length of the
   list is the argument. */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { body, c } from "../theme";
import { Backdrop, Display, Kicker, Rise, SourceChip, Sweep } from "../components/atoms";

const ASKS = [
  "Your full name, with any suffix",
  "Your date of birth",
  "Your Social Security number",
  "Every address for the past two years",
  "A copy of a government-issued ID",
  "Proof of your current address",
];

export const Gate: React.FC = () => {
  const frame = useCurrentFrame();

  /* The deck of the bridge, drawn across before anything is asked for. */
  const deck = interpolate(frame, [6, 54], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <Backdrop hue={c.teal} drift={0.6} />
      <AbsoluteFill style={{ padding: "96px 150px 220px", justifyContent: "center", alignItems: "center" }}>
        <div style={{ width: "100%", maxWidth: 1180 }}>
        <Sweep width={`${deck * 100}%`} height={3} style={{ marginBottom: 46, opacity: 0.85 }} />

        <Rise delay={10}>
          <Kicker>To dispute one error on your credit report</Kicker>
        </Rise>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 34 }}>
          {ASKS.map((ask, i) => (
            <Rise key={ask} delay={44 + i * 21} distance={18}>
              <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: 7,
                    border: `2px solid ${c.lineStrong}`,
                    flexShrink: 0,
                  }}
                />
                <Display size={44} weight={500} color={c.ink}>
                  {ask}
                </Display>
              </div>
            </Rise>
          ))}
        </div>

        <Rise delay={190} style={{ marginTop: 40 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
            <div style={{ fontFamily: body, fontSize: 26, color: c.ink2 }}>
              Then put all of it in an envelope.
            </div>
            <SourceChip text="Experian, disputing by mail · checked 2026-09-23" />
          </div>
        </Rise>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
