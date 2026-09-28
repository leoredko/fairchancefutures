/* 0:15. Who located him, how fast, and the one door that stayed shut.

   This is the turn the whole trailer hangs on. The industry with a motive to
   find somebody inside does it in an afternoon, off a lookup anybody can
   open. The industry he actually needs something from asks for a verified
   identity, a street address and a web browser, and he has none of the three.

   Both halves end up on screen together on purpose. The asymmetry is the
   argument, and an argument made in sequence is one a viewer has to hold in
   their head. Made side by side it is just visible.

   The lookup is real and already in the project: app/doccs.py names it, links
   it and records the date somebody checked it. The refusals are the reasons
   written in app/surfaces.py, shortened but not softened. */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { body, c, mono } from "../theme";
import { Backdrop, Display, Kicker, Rise } from "../components/atoms";
import { CLIENT } from "../script";

const SPLIT = 132;

const REFUSALS = [
  ["No camera", "No identity check happens on a facility tablet."],
  ["No mail out", "Outgoing mail goes through a person, never a screen."],
  ["No open web", "Every route a bureau offers runs through a web page."],
];

const Panel: React.FC<{ children: React.ReactNode; tone: string; style?: React.CSSProperties }> = ({
  children,
  tone,
  style,
}) => (
  <div
    style={{
      border: `1px solid ${c.line}`,
      borderTop: `3px solid ${tone}`,
      borderRadius: 20,
      backgroundColor: "rgba(16,32,26,.62)",
      padding: "34px 38px 32px",
      ...style,
    }}
  >
    {children}
  </div>
);

export const Found: React.FC = () => {
  const frame = useCurrentFrame();

  /* The lookup opens centred and then gives up half the frame. Moving it
     rather than cutting keeps it as the thing being compared against. */
  const slide = interpolate(frame, [SPLIT, SPLIT + 34], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <Backdrop hue={c.rose} drift={0.4} />

      <AbsoluteFill style={{ padding: "120px 110px 230px", alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", gap: 56, width: "100%", maxWidth: 1700, alignItems: "stretch" }}>
          <div style={{ flex: 1, transform: `translateX(${interpolate(slide, [0, 1], [430, 0])}px)` }}>
            <Rise delay={6}>
              <Kicker color={c.rose}>Anybody can open this</Kicker>
            </Rise>

            <Panel tone={c.rose} style={{ marginTop: 26 }}>
              <div style={{ fontFamily: body, fontSize: 22, color: c.muted }}>Public inmate lookup</div>

              <div
                style={{
                  marginTop: 18,
                  border: `1px solid ${c.lineStrong}`,
                  borderRadius: 10,
                  padding: "16px 20px",
                  fontFamily: mono,
                  fontSize: 32,
                  color: c.ink,
                  backgroundColor: "rgba(6,12,10,.6)",
                }}
              >
                {CLIENT.din}
                <span style={{ opacity: interpolate(frame % 30, [0, 15, 16], [1, 1, 0]), color: c.rose }}>|</span>
              </div>

              <Rise delay={46} style={{ marginTop: 22 }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {[
                    ["Name", CLIENT.name],
                    ["Status", "In custody"],
                    ["Conditional release", CLIENT.releaseDate],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 20 }}>
                      <span style={{ fontFamily: body, fontSize: 24, color: c.muted }}>{k}</span>
                      <span style={{ fontFamily: mono, fontSize: 24, color: c.ink }}>{v}</span>
                    </div>
                  ))}
                </div>
              </Rise>

              <Rise delay={70} style={{ marginTop: 24 }}>
                <div style={{ fontFamily: body, fontSize: 20, color: c.faint }}>
                  nysdoccslookup.doccs.ny.gov
                </div>
              </Rise>
            </Panel>

            <Rise delay={88} style={{ marginTop: 24 }}>
              <Display size={40} weight={700} color={c.rose}>
                Three weeks to find him.
              </Display>
            </Rise>
          </div>

          <div style={{ flex: 1, opacity: slide }}>
            <Rise delay={SPLIT + 10}>
              <Kicker>And still out of reach</Kicker>
            </Rise>

            <div style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 26 }}>
              {REFUSALS.map(([what, why], i) => (
                <Rise key={what} delay={SPLIT + 24 + i * 26} distance={22}>
                  <Panel tone={c.teal} style={{ padding: "26px 32px 24px" }}>
                    <Display size={40} weight={700}>
                      {what}
                    </Display>
                    <div style={{ fontFamily: body, fontSize: 23, color: c.ink2, marginTop: 8, lineHeight: 1.4 }}>
                      {why}
                    </div>
                  </Panel>
                </Rise>
              ))}
            </div>

            <Rise delay={SPLIT + 112} style={{ marginTop: 24 }}>
              <Display size={40} weight={700} color={c.teal}>
                No way to ask for his own file.
              </Display>
            </Rise>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
