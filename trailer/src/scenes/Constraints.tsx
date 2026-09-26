/* 0:20. The two facts no waiver makes disappear.

   Nearly silent on purpose. Everything else in the product is downstream of
   these two sentences, and they are the only text in the trailer a viewer is
   given room to read twice. The wording is the wording in CLAUDE.md and in
   app/surfaces.py, not a friendlier paraphrase of it. */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { body, c, gradText } from "../theme";
import { Backdrop, Display, Rise, Sweep } from "../components/atoms";

const CONSTRAINTS = [
  {
    n: "01",
    text: "A person inside cannot verify identity, receive mail, upload a file, or browse out to a bureau.",
    note: "Not a policy and not a setting. It is where the tablet physically sits.",
    where: "app/surfaces.py",
  },
  {
    n: "02",
    text: "A helper outside has no standing until they sign a scoped form.",
    note: "Scoped, expiring, revocable, and checked on every single request.",
    where: "app/authorization.py",
  },
];

export const Constraints: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill>
      <Backdrop hue={c.teal} drift={0.5} />
      <AbsoluteFill style={{ padding: "110px 110px 220px", justifyContent: "center", gap: 46 }}>
        <div style={{ display: "flex", gap: 46, alignItems: "stretch" }}>
          {CONSTRAINTS.map((k, i) => (
            <Rise key={k.n} delay={12 + i * 78} distance={34} style={{ flex: 1, display: "flex" }}>
              <div
                style={{
                  flex: 1,
                  border: `1px solid ${c.line}`,
                  borderRadius: 22,
                  backgroundColor: "rgba(22,42,34,.55)",
                  padding: "40px 40px 34px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 22,
                }}
              >
                <div style={{ fontFamily: "'Space Grotesk', system-ui, sans-serif", fontWeight: 700, fontSize: 56, lineHeight: 1, ...gradText }}>
                  {k.n}
                </div>
                <Display size={42} weight={700} style={{ lineHeight: 1.2 }}>
                  {k.text}
                </Display>
                <div style={{ fontFamily: body, fontSize: 25, lineHeight: 1.45, color: c.ink2 }}>{k.note}</div>
                <div
                  style={{
                    marginTop: "auto",
                    fontFamily: "ui-monospace, Menlo, monospace",
                    fontSize: 21,
                    color: c.faint,
                  }}
                >
                  {k.where}
                </div>
              </div>
            </Rise>
          ))}
        </div>

        <Rise delay={196} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
          <Sweep width={interpolate(frame, [196, 250], [0, 420], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
          <Display size={38} weight={500} color={c.ink2}>
            Everything the product is follows from these.
          </Display>
        </Rise>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
