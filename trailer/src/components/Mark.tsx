/* The Bridge mark and wordmark.

   The path data is copied from the `markpath` and `wordmark` defs in
   app/templates/base.html, which scripts/make_icons.py also mirrors. Three
   copies of one drawing is two too many, but the alternative is the trailer
   reaching into the Python app at build time, and a trailer that cannot be
   rendered without the server checked out beside it is worse. If the mark
   changes in the app, it changes here in the same commit. */

import React from "react";
import { c } from "../theme";

/* A stone arch bridge, which is also a B lying on its back: the deck is the
   spine and the two arches are the bowls. */
export const MARK_PATH =
  "M2 7h44v4.5H2V7Zm2.5 6.5h39v16.5h-39V13.5Zm5 16.5v-6a6 6 0 0 1 12 0v6h-12Zm16 0v-6a6 6 0 0 1 12 0v6h-12Z";

/* B R I D G, and then the mark itself stood on end as the E. */
export const WORD_PATHS = [
  { d: "M0 0h6v48H0V0Zm6 0h9a11 11 0 0 1 0 22H6v-6h9a5 5 0 0 0 0-10H6V0Zm0 26h10a11 11 0 0 1 0 22H6v-6h10a5 5 0 0 0 0-10H6v-6Z", x: 0 },
  { d: "M0 0h6v48H0V0Zm6 0h9a11 11 0 0 1 4.6 21L31 48h-6.8l-10.6-24H6v-6h9a5 5 0 0 0 0-10H6V0Z", x: 34 },
  { d: "M0 0h6v48H0V0Z", x: 73 },
  { d: "M0 0h6v48H0V0Zm6 0h10a24 24 0 0 1 0 48H6v-6h10a18 18 0 0 0 0-36H6V0Z", x: 86 },
  { d: "M24 0a24 24 0 1 0 0 48 24 24 0 0 0 16-6V22H22v6h12v11a18 18 0 1 1 6-25h6.3A24 24 0 0 0 24 0Z", x: 129 },
] as const;

export const Gradient: React.FC<{ id: string }> = ({ id }) => (
  <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stopColor={c.tealDeep} />
    <stop offset=".55" stopColor={c.teal} />
    <stop offset="1" stopColor={c.cyan} />
  </linearGradient>
);

export const Mark: React.FC<{ size: number; fill?: string }> = ({ size, fill }) => {
  const id = React.useId();
  return (
    <svg width={size} height={(size * 34) / 48} viewBox="0 0 48 34" role="img" aria-label="Bridge">
      <defs>
        <Gradient id={id} />
      </defs>
      <path d={MARK_PATH} fillRule="evenodd" fill={fill ?? `url(#${id})`} />
    </svg>
  );
};

/* `reveal` is 0 to 1 and wipes the word in from the left behind a bright
   leading edge. The letters are filled paths rather than strokes, so there is
   no stroke to animate; a wipe is the honest way to draw a fill on. */
export const Wordmark: React.FC<{ width: number; reveal?: number }> = ({ width, reveal = 1 }) => {
  const id = React.useId();
  const VB_W = 210;
  const VB_H = 52;
  const edge = -2 + VB_W * Math.min(Math.max(reveal, 0), 1);

  return (
    <svg
      width={width}
      height={(width * VB_H) / VB_W}
      viewBox={`-2 -2 ${VB_W} ${VB_H}`}
      role="img"
      aria-label="Bridge"
    >
      <defs>
        <Gradient id={`${id}-g`} />
        <clipPath id={`${id}-c`}>
          <rect x={-2} y={-4} width={edge + 2} height={VB_H + 8} />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id}-c)`} fill={`url(#${id}-g)`} fillRule="evenodd">
        {WORD_PATHS.map((p) => (
          <g key={p.x} transform={`translate(${p.x},0)`}>
            <path d={p.d} />
          </g>
        ))}
        <g transform="translate(172,0)">
          <g transform="translate(0,48) rotate(-90)">
            <path d={MARK_PATH} fillRule="evenodd" />
          </g>
        </g>
      </g>
      {reveal > 0 && reveal < 1 ? (
        <rect x={edge - 1.5} y={-3} width={3} height={VB_H + 6} fill={c.tealInk} opacity={0.9} />
      ) : null}
    </svg>
  );
};
