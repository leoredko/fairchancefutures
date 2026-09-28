/* The clock, kept in the corner of every shot after it starts.

   It exists so the product half of the trailer can never be watched as a
   feature tour. Three screens and a letter template are interesting; three
   screens and a letter template with a hundred and fifty-four days left on
   them are urgent, and the difference is one chip in the corner.

   It sits outside the scenes for the same reason the caption band does: a
   clock that re-lays itself on every cut is a clock a viewer stops reading. */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { body, c, mono } from "../theme";
import { CLIENT } from "../script";

export const Counter: React.FC<{ from: number; until: number }> = ({ from, until }) => {
  const frame = useCurrentFrame();
  if (frame < from - 20 || frame > until) return null;

  const opacity =
    interpolate(frame, [from - 20, from], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) *
    interpolate(frame, [until - 24, until], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "flex-start", padding: "52px 64px" }}>
      <div
        style={{
          opacity,
          display: "flex",
          alignItems: "center",
          gap: 14,
          border: `1px solid ${c.line}`,
          borderRadius: 999,
          padding: "10px 22px 10px 16px",
          backgroundColor: "rgba(8,18,14,.72)",
        }}
      >
        <div style={{ width: 9, height: 9, borderRadius: 999, backgroundColor: c.amber }} />
        <span style={{ fontFamily: mono, fontSize: 26, color: c.ink }}>{CLIENT.daysToGate}</span>
        <span style={{ fontFamily: body, fontSize: 21, color: c.muted }}>days to the gate</span>
      </div>
    </AbsoluteFill>
  );
};
