/* 0:49. Why any of this has to be on a schedule.

   Two things are load-bearing here and both are easy to get wrong. The thirty
   days run from receipt, not from the postmark, which is the difference
   between a deadline you can count and one you can only guess at. And a
   dispute goes to all three bureaus, because an item deleted at Equifax is
   still sitting on the other two files. The first build of this product
   quietly pretended otherwise. */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { body, c, gradText } from "../theme";
import { Backdrop, Display, Rise, SourceChip } from "../components/atoms";

const BUREAUS = ["Equifax", "Experian", "TransUnion"];

export const Clock: React.FC = () => {
  const frame = useCurrentFrame();
  const sweep = interpolate(frame, [10, 100], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <Backdrop hue={c.amber} drift={0.5} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 180, gap: 26 }}>
        <Rise delay={4} style={{ display: "flex", alignItems: "baseline", gap: 22 }}>
          <div style={{ fontFamily: "'Space Grotesk', system-ui, sans-serif", fontWeight: 700, fontSize: 168, lineHeight: 1, letterSpacing: "-.04em", ...gradText }}>
            30 days
          </div>
          <Display size={54} weight={500} color={c.ink2}>
            from receipt
          </Display>
        </Rise>

        <Rise delay={16}>
          <div style={{ fontFamily: body, fontSize: 31, color: c.ink }}>
            Not from the postmark. Which is why somebody has to be counting.
          </div>
        </Rise>

        {/* Three envelopes going out at once, filling as the clock runs. */}
        <div style={{ display: "flex", gap: 22, marginTop: 14 }}>
          {BUREAUS.map((b, i) => (
            <Rise key={b} delay={40 + i * 14}>
              <div
                style={{
                  width: 320,
                  border: `1px solid ${c.lineStrong}`,
                  borderRadius: 16,
                  padding: "20px 24px 18px",
                  backgroundColor: "rgba(22,42,34,.5)",
                }}
              >
                <div style={{ fontFamily: body, fontWeight: 600, fontSize: 30, color: c.ink }}>{b}</div>
                <div style={{ fontFamily: body, fontSize: 20, color: c.muted, margin: "6px 0 12px" }}>
                  Drafted, approved, mailed
                </div>
                <div style={{ height: 7, borderRadius: 999, backgroundColor: c.track, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${Math.min(1, sweep + i * 0.06) * 100}%`,
                      height: "100%",
                      background: `linear-gradient(90deg, ${c.tealDeep}, ${c.teal})`,
                    }}
                  />
                </div>
              </div>
            </Rise>
          ))}
        </div>

        <Rise delay={96} style={{ marginTop: 10 }}>
          <SourceChip text="15 U.S.C. 1681i(a)(1)(A) · checked 2026-09-23" />
        </Rise>

        {/* The other pair of deadlines, and the reason the product says which
            120 days it means every single time it says 120 days. Two clocks on
            opposite sides of the gate, and confusing them costs somebody their
            ID. */}
        <Rise delay={112} style={{ marginTop: 22, display: "flex", gap: 20 }}>
          {[
            ["120 days before release", "The Social Security card application goes in", c.teal],
            ["120 days after release", "The release ID expires", c.amber],
          ].map(([when, what, tone]) => (
            <div
              key={when}
              style={{
                width: 480,
                borderLeft: `3px solid ${tone}`,
                paddingLeft: 18,
                textAlign: "left",
              }}
            >
              <div style={{ fontFamily: body, fontWeight: 600, fontSize: 25, color: c.ink }}>{when}</div>
              <div style={{ fontFamily: body, fontSize: 21, color: c.muted }}>{what}</div>
            </div>
          ))}
        </Rise>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
