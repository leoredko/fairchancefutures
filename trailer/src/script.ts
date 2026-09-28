/* The voiceover, and the only place its timing is written down.

   Every caption on screen, every scene boundary and the recording sheet in
   VOICEOVER.md all come from this file, so a line cannot be reworded in one
   place and left stale in another. `npm run voiceover` regenerates the sheet.

   Frames are at FPS, and the durations were set at roughly one hundred words
   across the minute. That is slow for speech on purpose: a trailer that fills
   every second with talking has nowhere to land a point. If a read comes back
   long, stretch `len` here rather than talking faster, then rerun the sheet.

   The first fifteen seconds are deliberately almost silent. The mail arriving
   is the argument, and a voice explaining a joke while it happens is a voice
   that kills it. */

export const FPS = 30;
export const DURATION = 60 * FPS;
export const WIDTH = 1920;
export const HEIGHT = 1080;

/* Marcus W., DIN 28-A-1187, out of the seeded caseload in docs/DEMO.md. His
   dates come from app/doccs.py, which derives them from a hash of the DIN, so
   they are stable forever and cannot collide with a real person: every
   invented person in this project has a DIN starting 28, and 2028 has not
   happened.

   The day count is frozen rather than computed. `simulated_lookup` gives a
   conditional release date of 2027-03-01, which was 154 days out when this
   cut was made. Computing it at render time would mean the trailer quietly
   showed a different number every week and the voiceover stopped matching the
   picture, so the number is pinned here and the reference date is written
   down beside it. */
export const CLIENT = {
  name: "Marcus W.",
  din: "28-A-1187",
  releaseDate: "2027-03-01",
  asOf: "2026-09-28",
  daysToGate: 154,
} as const;

export type Line = {
  /* Frame the line starts on, and how many frames it holds. */
  from: number;
  len: number;
  /* What is said. The caption on screen is the same string, because a caption
     that paraphrases the read is worse than no caption. */
  text: string;
};

export type Scene = {
  name: string;
  from: number;
  len: number;
  /* One sentence on what the scene is doing, for the recording sheet. */
  note: string;
};

export const SCENES = [
  {
    name: "MailCall",
    from: 0,
    len: 450,
    note: "One letter, a pause, and then the rest of it. Played almost silent.",
  },
  {
    name: "Found",
    from: 450,
    len: 300,
    note: "Who located him, how fast, and the one door that stayed shut.",
  },
  {
    name: "Release",
    from: 750,
    len: 180,
    note: "A name, a date and a number of days. The clock starts here.",
  },
  {
    name: "Surfaces",
    from: 930,
    len: 510,
    note: "Three screens for three people. Tablet, phone, desk, one case.",
  },
  {
    name: "Deadline",
    from: 1440,
    len: 210,
    note: "Thirty days from receipt, three bureaus, and the two 120 day clocks.",
  },
  {
    name: "Logo",
    from: 1650,
    len: 150,
    note: "The wordmark draws itself. Tagline, then the credit line.",
  },
] as const satisfies readonly Scene[];

export const LINES = [
  { from: 60, len: 115, text: "Mail call is the best four minutes of the week." },
  { from: 235, len: 160, text: "Until somebody opens nine accounts in your name and stops paying." },

  { from: 475, len: 120, text: "Collections found him in three weeks." },
  { from: 620, len: 175, text: "The credit bureau still cannot send him his own report." },

  { from: 830, len: 110, text: "He goes home in a hundred and fifty-four days." },

  { from: 960, len: 150, text: "Bridge is three screens, for three people who cannot do each other's jobs." },
  { from: 1130, len: 125, text: "A course that cites every source it stands on." },
  { from: 1275, len: 120, text: "One task at a time for the person helping." },
  { from: 1410, len: 110, text: "And a letter, approved by a person." },

  { from: 1545, len: 120, text: "Thirty days from receipt. All three bureaus." },

  { from: 1700, len: 75, text: "Bridge. Start before the gate." },
] as const satisfies readonly Line[];

/* Seconds, to two places, for a recording sheet a person reads off a screen. */
export const at = (frame: number): string => (frame / FPS).toFixed(2);

/* mm:ss.ss, which is what a DAW shows. */
export const timecode = (frame: number): string => {
  const total = frame / FPS;
  const m = Math.floor(total / 60);
  const s = (total - m * 60).toFixed(2).padStart(5, "0");
  return `${m}:${s}`;
};

export const words = (text: string): number => text.trim().split(/\s+/).length;

/* Words per minute the line would have to be read at to fit its window. Over
   about 185 is a line that needs shortening or more frames, not a faster read. */
export const wpm = (line: Line): number => Math.round((words(line.text) * 60) / (line.len / FPS));
