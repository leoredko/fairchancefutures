/* The small pieces every scene shares: the ground the video sits on, the
   caption band, the citation chip, and one rise-in wrapper so a hundred
   elements are not each inventing their own easing. */

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { body, c, display, grad } from "../theme";
import { LINES } from "../script";

/* Dark, with green in the blacks rather than neutral grey, so the accent reads
   as part of the same material. The glow drifts because a completely static
   black frame looks like a dropped signal on a projector. */
export const Backdrop: React.FC<{ hue?: string; drift?: number }> = ({ hue = c.teal, drift = 1 }) => {
  const frame = useCurrentFrame();
  const x = 50 + Math.sin(frame / 190) * 14 * drift;
  const y = 42 + Math.cos(frame / 240) * 11 * drift;
  return (
    <AbsoluteFill style={{ backgroundColor: c.surface }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(58% 62% at ${x}% ${y}%, ${hue}22 0%, transparent 68%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: "radial-gradient(75% 75% at 50% 50%, transparent 38%, rgba(0,0,0,.62) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

/* Spring in from below. `delay` is in frames from the start of the sequence
   the element sits in, not from the start of the video. */
export const Rise: React.FC<{
  delay?: number;
  distance?: number;
  damping?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ delay = 0, distance = 28, damping = 200, style, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = spring({ frame: frame - delay, fps, config: { damping, mass: 0.9 } });
  return (
    <div
      style={{
        opacity: interpolate(t, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(t, [0, 1], [distance, 0])}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/* Fade out over the last `len` frames of whatever sequence wraps it, so a
   scene hands over rather than cutting to black. */
export const FadeOutAt: React.FC<{ start: number; len?: number; children: React.ReactNode }> = ({
  start,
  len = 14,
  children,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{ opacity: interpolate(frame, [start, start + len], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}
    >
      {children}
    </AbsoluteFill>
  );
};

/* Where a claim came from. Every number on screen carries one, the same rule
   the app itself runs on: no legal sentence without a primary source. */
export const SourceChip: React.FC<{ text: string; style?: React.CSSProperties }> = ({ text, style }) => (
  <div
    style={{
      fontFamily: body,
      fontSize: 19,
      letterSpacing: ".01em",
      color: c.muted,
      border: `1px solid ${c.line}`,
      borderRadius: 999,
      padding: "8px 20px",
      display: "inline-block",
      backgroundColor: "rgba(8,18,14,.55)",
      ...style,
    }}
  >
    {text}
  </div>
);

export const Kicker: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = c.tealInk }) => (
  <div
    style={{
      fontFamily: body,
      fontSize: 21,
      fontWeight: 600,
      letterSpacing: ".18em",
      textTransform: "uppercase",
      color,
    }}
  >
    {children}
  </div>
);

/* The caption band. It runs across the whole video rather than inside the
   scenes, because the read does not stop where a cut does, and because a
   caption that moves with the layout is a caption people lose.

   This is the accessibility floor and the mute floor at once: with no
   voiceover recorded, or on a phone with the sound off, these lines are the
   entire script. */
export const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const line = LINES.find((l) => frame >= l.from - 8 && frame < l.from + l.len + 10);
  if (!line) return null;

  const enter = interpolate(frame, [line.from - 8, line.from + 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exit = interpolate(frame, [line.from + line.len, line.from + line.len + 10], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 66 }}>
      <div
        style={{
          opacity: enter * exit,
          transform: `translateY(${interpolate(enter, [0, 1], [10, 0])}px)`,
          maxWidth: 1240,
          textAlign: "center",
          fontFamily: body,
          fontSize: 34,
          lineHeight: 1.35,
          color: c.ink,
          textShadow: "0 2px 18px rgba(0,0,0,.85), 0 0 3px rgba(0,0,0,.9)",
        }}
      >
        {line.text}
      </div>
    </AbsoluteFill>
  );
};

/* A hairline in the brand sweep. Used as a rule under a heading and as the
   deck of the bridge in the gate scene. */
export const Sweep: React.FC<{ width: number | string; height?: number; style?: React.CSSProperties }> = ({
  width,
  height = 3,
  style,
}) => <div style={{ width, height, background: grad, borderRadius: 999, ...style }} />;

export const Display: React.FC<{
  size: number;
  weight?: number;
  color?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ size, weight = 700, color = c.ink, style, children }) => (
  <div
    style={{
      fontFamily: display,
      fontWeight: weight,
      fontSize: size,
      lineHeight: 1.08,
      letterSpacing: "-.022em",
      color,
      ...style,
    }}
  >
    {children}
  </div>
);
