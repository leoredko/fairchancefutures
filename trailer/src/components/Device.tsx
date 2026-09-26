/* A bezel around a screen, so the three surfaces read as three different
   objects at a glance rather than three rectangles at three sizes. The whole
   product argument is that these are different devices in different rooms
   belonging to different people, and the frame is what says so before a word
   of the caption lands.

   The screen inside is laid out once at a readable size and then scaled down,
   which is what lets surfaces.tsx set type in real pixels instead of guessing
   per shot. The scaling is the part that has already bitten once: a CSS
   transform does not change what an element takes up in a flex row, so three
   devices scaled to a third of their size still tried to claim their full
   width and two of the three ended up off the side of the frame. The wrapper
   below is sized to the scaled result and the transform hangs off its top
   left corner, so layout and picture agree. */

import React from "react";
import { body, c } from "../theme";

const PAD = 18;
const RADIUS = 34;

export const Device: React.FC<{
  /* Logical pixels of the screen inside, before scaling. */
  width: number;
  height: number;
  scale: number;
  /* Degrees of Y rotation. Small numbers: past about twelve, type on the far
     edge starts to smear once the frame has been through the codec. */
  tilt?: number;
  glow?: string;
  label?: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ width, height, scale, tilt = 0, glow = c.teal, label, children, style }) => {
  const outerW = width + PAD * 2;
  const outerH = height + PAD * 2;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20, ...style }}>
      <div style={{ width: outerW * scale, height: outerH * scale, perspective: 2400 }}>
        <div
          style={{
            width: outerW,
            height: outerH,
            transform: `scale(${scale}) rotateY(${tilt}deg)`,
            transformOrigin: "top left",
            padding: PAD,
            borderRadius: RADIUS,
            backgroundColor: "#060D0A",
            border: `1px solid ${c.lineStrong}`,
            boxShadow: `0 40px 120px rgba(0,0,0,.72), 0 0 0 1px rgba(255,255,255,.03), 0 18px 90px ${glow}26`,
          }}
        >
          <div style={{ width, height, borderRadius: RADIUS - PAD, overflow: "hidden", backgroundColor: c.page }}>
            {children}
          </div>
        </div>
      </div>

      {label ? (
        <div
          style={{
            fontFamily: body,
            fontSize: 25,
            letterSpacing: ".15em",
            textTransform: "uppercase",
            fontWeight: 600,
            color: glow,
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </div>
      ) : null}
    </div>
  );
};
