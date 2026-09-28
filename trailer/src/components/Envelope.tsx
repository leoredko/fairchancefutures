/* Paper, which is the only thing this trailer can honestly show a person.

   The rule for the whole cut is objects and type, never a depiction of a
   person inside. An envelope carries the entire mail call sequence on its own:
   it has a sender, a recipient, a tone and a volume, and none of those need a
   face. It is also the one shape CSS draws well at a hundred copies a frame.

   Everything here is addressed the way mail to somebody inside is actually
   addressed, name and DIN together, because that is the detail that tells a
   viewer who has lived it that this was not guessed at. No facility is named:
   the seeded record in app/doccs.py assigns one from a hash and it is not a
   claim this video needs to make. */

import React from "react";
import { c, body, mono } from "../theme";

export type Sender = {
  /* Who it is from, as it reads on the corner of the envelope. */
  from: string;
  place: string;
  /* A red block in the corner. The collectors stamp them; family does not. */
  stamp?: string;
  /* Handwritten mail sits differently in the hand than a window envelope. */
  personal?: boolean;
};

/* Invented, every one of them. Naming a real agency would be asserting that a
   particular company did a particular thing to a particular person, which is
   not a claim this video is in a position to make and not one it needs. They
   are built to sound like what they are: a portfolio bought for pennies and
   worked by whoever bought it. */
export const COLLECTORS: readonly Sender[] = [
  { from: "Meridian Recovery Group", place: "Buffalo, NY", stamp: "Final notice" },
  { from: "Atlas Portfolio Services", place: "Wilmington, DE", stamp: "Second notice" },
  { from: "Crestline Asset Management", place: "Phoenix, AZ", stamp: "Final notice" },
  { from: "Northgate Receivables", place: "Columbus, OH", stamp: "Past due" },
  { from: "Harbor Point Recovery", place: "Tampa, FL", stamp: "Final notice" },
  { from: "Pinnacle Credit Solutions", place: "Las Vegas, NV", stamp: "Amount due" },
  { from: "Sable Ridge Collections", place: "Newark, NJ", stamp: "Final notice" },
  { from: "Keystone Account Services", place: "Allentown, PA", stamp: "Past due" },
];

/* The one piece of mail anybody was expecting. Denise is the helper on the
   phone surface later in the cut, so the person who wrote the first envelope
   is the person who ends up doing the work. */
export const FROM_DENISE: Sender = { from: "Denise", place: "Bronx, NY", personal: true };

export const ENVELOPE_W = 460;
export const ENVELOPE_H = 280;

export const Envelope: React.FC<{
  sender: Sender;
  /* Name and DIN of whoever it is addressed to, or nothing at small sizes
     where the block would render as four grey smears. */
  to?: { name: string; din: string };
  scale?: number;
  style?: React.CSSProperties;
}> = ({ sender, to, scale = 1, style }) => {
  const paper = sender.personal ? "#E8E2D4" : "#EFEFE9";
  const ink = sender.personal ? "#3A3428" : "#2B322F";

  return (
    <div
      style={{
        /* Sized to the scaled result, not the logical size. A CSS transform
           does not change what an element takes up in its parent, and that has
           already cost this project one render. */
        width: ENVELOPE_W * scale,
        height: ENVELOPE_H * scale,
        ...style,
      }}
    >
      <div
        style={{
          width: ENVELOPE_W,
          height: ENVELOPE_H,
          transform: `scale(${scale})`,
          transformOrigin: "top left",
          position: "relative",
          borderRadius: 6,
          backgroundColor: paper,
          boxShadow: "0 18px 50px rgba(0,0,0,.55), inset 0 0 0 1px rgba(0,0,0,.09)",
          overflow: "hidden",
        }}
      >
        {/* The flap, as a pair of edges rather than a filled triangle, so the
            envelope reads as closed and face up. */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(135deg, rgba(0,0,0,.05) 0 50%, transparent 50%), linear-gradient(225deg, rgba(0,0,0,.05) 0 50%, transparent 50%)`,
            backgroundSize: "50.5% 62%, 50.5% 62%",
            backgroundPosition: "left top, right top",
            backgroundRepeat: "no-repeat",
          }}
        />

        <div style={{ position: "absolute", left: 26, top: 22, maxWidth: 250 }}>
          <div
            style={{
              fontFamily: sender.personal ? body : mono,
              fontSize: sender.personal ? 22 : 18,
              fontWeight: sender.personal ? 500 : 400,
              fontStyle: sender.personal ? "italic" : "normal",
              color: ink,
              lineHeight: 1.3,
            }}
          >
            {sender.from}
            <br />
            {sender.place}
          </div>
        </div>

        {sender.stamp ? (
          <div
            style={{
              position: "absolute",
              right: 24,
              top: 20,
              transform: "rotate(-7deg)",
              border: "2px solid #B2242F",
              color: "#B2242F",
              borderRadius: 3,
              padding: "5px 12px",
              fontFamily: body,
              fontWeight: 700,
              fontSize: 20,
              letterSpacing: ".04em",
            }}
          >
            {sender.stamp}
          </div>
        ) : null}

        {to ? (
          <div
            style={{
              position: "absolute",
              left: 150,
              bottom: 40,
              fontFamily: sender.personal ? body : mono,
              fontStyle: sender.personal ? "italic" : "normal",
              fontSize: 25,
              lineHeight: 1.36,
              color: ink,
            }}
          >
            {to.name}
            <br />
            DIN {to.din}
            <br />
            <span style={{ opacity: 0.68 }}>NYS Department of Corrections</span>
          </div>
        ) : null}
      </div>
    </div>
  );
};

/* A steel door with a slot in it. Deliberately not a drawing of a cell: bars
   and a bunk would be set dressing, and the only part of the room this video
   has any business showing is the hole the paper comes through. */
export const Slot: React.FC<{ width: number; open?: number }> = ({ width, open = 1 }) => (
  <div
    style={{
      width,
      height: width * 0.2,
      borderRadius: 10,
      background: "linear-gradient(180deg, #16211D 0%, #0B120F 100%)",
      border: `1px solid ${c.lineStrong}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxShadow: "0 30px 90px rgba(0,0,0,.7)",
    }}
  >
    <div
      style={{
        width: width * 0.76,
        height: Math.max(2, width * 0.026 * open),
        borderRadius: 999,
        backgroundColor: "#030705",
        boxShadow: "inset 0 2px 6px rgba(0,0,0,.9), 0 1px 0 rgba(255,255,255,.05)",
      }}
    />
  </div>
);
