/* 0:31. Three screens for three people who genuinely cannot do each other's
   jobs, which is the whole reason the product is split at all rather than one
   app with three logins.

   They arrive in the order the work does: the course on the tablet first,
   because it is the first priority and the part that survives release; then
   the helper, who is the only one of the three who can touch paper; then the
   desk, where a person and not the app approves the letter. */

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { c } from "../theme";
import { Backdrop, Kicker, Rise } from "../components/atoms";
import { Device } from "../components/Device";
import { DESK, DeskScreen, PHONE, PhoneScreen, TABLET, TabletScreen } from "../components/surfaces";

/* Each device holds its own entrance so the group can be re-timed by moving
   one number, and so a late device never pops in at full opacity on the cut. */
const Entering: React.FC<{ delay: number; from: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay,
  from,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = spring({ frame: frame - delay, fps, config: { damping: 180, mass: 1.1 } });
  return (
    <div
      style={{
        opacity: t,
        transform: `translateX(${interpolate(t, [0, 1], [from, 0])}px) translateY(${interpolate(t, [0, 1], [40, 0])}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Surfaces: React.FC = () => {
  const frame = useCurrentFrame();

  /* A slow pull back once all three are in, so the shot keeps moving through
     four seconds of held frame without anything actually changing. */
  const pull = interpolate(frame, [330, 540], [1.05, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <Backdrop hue={c.cyan} drift={0.8} />

      <AbsoluteFill style={{ padding: "54px 0 0", alignItems: "center" }}>
        <Rise delay={6}>
          <Kicker>Three surfaces, one case</Kicker>
        </Rise>
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          paddingBottom: 118,
          transform: `scale(${pull})`,
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "center", gap: 56 }}>
          <Entering delay={22} from={-70}>
            <Device
              width={TABLET.w}
              height={TABLET.h}
              scale={0.6}
              tilt={7}
              glow={c.teal}
              label="Inside, the tablet"
            >
              <TabletScreen />
            </Device>
          </Entering>

          <Entering delay={172} from={0}>
            <Device width={PHONE.w} height={PHONE.h} scale={0.53} glow={c.amber} label="Outside, a phone">
              <PhoneScreen />
            </Device>
          </Entering>

          <Entering delay={322} from={70}>
            <Device
              width={DESK.w}
              height={DESK.h}
              scale={0.5}
              tilt={-7}
              glow={c.sky}
              label="At the desk"
            >
              <DeskScreen />
            </Device>
          </Entering>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
