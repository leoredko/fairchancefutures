/* 0:00. One letter, a pause, and then the rest of it.

   The joke is volume, so the scene spends its first eight seconds refusing to
   be funny: a slot, one envelope from somebody who loves him, and a long hold
   on nothing else arriving. That hold is what makes the next seven seconds
   land. Cutting it to save time kills the whole sequence.

   Nothing here is asserted. No number on screen is a statistic, no agency on
   an envelope is a real company, and no facility is named. It is a picture of
   an afternoon, and the only claim it makes is the one the product is built
   on: the people owed money can find somebody inside, and they do. */

import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { body, c, mono } from "../theme";
import { Kicker, Rise } from "../components/atoms";
import { COLLECTORS, ENVELOPE_H, ENVELOPE_W, Envelope, FROM_DENISE, Slot } from "../components/Envelope";
import { CLIENT } from "../script";

const SLOT_X = 960;
const SLOT_Y = 232;

/* The single letter arrives at 55, the flood starts at 246. Everything between
   those two numbers is the point of the scene. */
const FIRST = 55;
const FLOOD = 246;

type Piece = {
  seed: number;
  spawn: number;
  scale: number;
  x: number;
  y: number;
  rot: number;
  fall: number;
};

/* Where each piece of the flood ends up. Later arrivals rest higher and wider,
   so the pile grows upward and outward the way a pile does, rather than every
   envelope landing in one heap in the middle. `random` is Remotion's seeded
   one, so the same frame renders the same picture every time. */
const flood: Piece[] = Array.from({ length: 96 }, (_, i) => {
  const t = i / 95;
  const seed = i + 1;
  /* Arrivals accelerate: the first few are separable, the last forty are not. */
  const spawn = FLOOD + Math.round(interpolate(t, [0, 1], [0, 150]) - t * t * 44);
  return {
    seed,
    spawn,
    scale: interpolate(random(`s${seed}`), [0, 1], [0.3, 0.52]),
    x: interpolate(random(`x${seed}`), [0, 1], [60, 1860]),
    y: interpolate(t, [0, 1], [880, 300]) + interpolate(random(`y${seed}`), [0, 1], [-90, 90]),
    rot: interpolate(random(`r${seed}`), [0, 1], [-46, 46]),
    fall: Math.round(interpolate(random(`f${seed}`), [0, 1], [16, 30])),
  };
});

/* Three that a viewer can actually read, landing in front of the heap. Without
   these the flood is grey texture and nobody learns what the paper is. */
const HEROES = [
  { sender: COLLECTORS[0], spawn: 268, x: 430, y: 470, rot: -9, scale: 0.86, fall: 34 },
  { sender: COLLECTORS[2], spawn: 318, x: 1090, y: 380, rot: 7, scale: 0.86, fall: 34 },
  { sender: COLLECTORS[4], spawn: 372, x: 720, y: 660, rot: -3, scale: 0.86, fall: 34 },
];

/* A piece of mail coming through the slot and settling. Gravity on the way
   down, because paper dumped through a slot accelerates and paper that eases
   gently into place reads as a user interface. */
const Falling: React.FC<{
  spawn: number;
  fall: number;
  x: number;
  y: number;
  rot: number;
  scale: number;
  children: React.ReactNode;
}> = ({ spawn, fall, x, y, rot, scale, children }) => {
  const frame = useCurrentFrame();
  if (frame < spawn) return null;

  const p = Math.min(1, (frame - spawn) / fall);
  const drop = p * p;
  const w = ENVELOPE_W * scale;
  const h = ENVELOPE_H * scale;

  return (
    <div
      style={{
        position: "absolute",
        left: interpolate(drop, [0, 1], [SLOT_X - w / 2, x - w / 2]),
        top: interpolate(drop, [0, 1], [SLOT_Y - h / 2, y - h / 2]),
        transform: `rotate(${interpolate(p, [0, 1], [rot * 0.2, rot])}deg)`,
        opacity: interpolate(p, [0, 0.08], [0, 1], { extrapolateRight: "clamp" }),
      }}
    >
      {children}
    </div>
  );
};

export const MailCall: React.FC = () => {
  const frame = useCurrentFrame();

  /* How many have landed. The tally is the punchline said in numbers, and it
     counts what is on screen rather than standing in for a statistic. */
  const landed =
    (frame >= FIRST + 30 ? 1 : 0) + flood.filter((p) => frame >= p.spawn + p.fall).length;

  /* The room dims as the paper takes over. */
  const dim = interpolate(frame, [FLOOD, FLOOD + 120], [1, 0.55], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: c.surface }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(46% 40% at 50% 20%, ${c.teal}1A 0%, transparent 70%)`,
          opacity: dim,
        }}
      />

      <AbsoluteFill style={{ alignItems: "center", paddingTop: 92 }}>
        <Rise delay={8}>
          <Kicker>Tuesday. Mail call.</Kicker>
        </Rise>
      </AbsoluteFill>

      <AbsoluteFill style={{ alignItems: "center", paddingTop: 178 }}>
        <div style={{ opacity: interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" }) }}>
          <Slot width={520} open={interpolate(frame, [FLOOD, FLOOD + 24], [1, 2.1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        </div>
      </AbsoluteFill>

      {/* The one letter anybody was waiting for. It stays on screen under
          everything that follows, which is the whole shape of the joke. */}
      <Falling spawn={FIRST} fall={40} x={960} y={620} rot={-2} scale={0.94}>
        <Envelope sender={FROM_DENISE} to={{ name: CLIENT.name, din: CLIENT.din }} scale={0.94} />
      </Falling>

      {flood.map((p) => (
        <Falling key={p.seed} spawn={p.spawn} fall={p.fall} x={p.x} y={p.y} rot={p.rot} scale={p.scale}>
          <Envelope sender={COLLECTORS[p.seed % COLLECTORS.length]} scale={p.scale} />
        </Falling>
      ))}

      {HEROES.map((h) => (
        <Falling key={h.sender.from} spawn={h.spawn} fall={h.fall} x={h.x} y={h.y} rot={h.rot} scale={h.scale}>
          <Envelope sender={h.sender} to={{ name: CLIENT.name, din: CLIENT.din }} scale={h.scale} />
        </Falling>
      ))}

      {/* Keeps the caption band readable once the frame is three quarters
          paper. Without it the last four seconds have white envelopes sitting
          directly behind white type. */}
      <AbsoluteFill
        style={{ background: "linear-gradient(180deg, transparent 58%, rgba(6,12,10,.86) 92%)" }}
      />

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-end", padding: "104px 70px 0" }}>
        <div style={{ opacity: interpolate(frame, [FIRST + 30, FIRST + 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), textAlign: "right" }}>
          <div style={{ fontFamily: mono, fontSize: 92, fontWeight: 500, color: landed > 1 ? c.rose : c.ink2, lineHeight: 1 }}>
            {landed}
          </div>
          <div style={{ fontFamily: body, fontSize: 21, color: c.muted, marginTop: 8 }}>
            {landed === 1 ? "piece of mail" : "pieces of mail"}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
