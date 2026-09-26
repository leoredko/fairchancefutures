/* The voiceover, and the only place its timing is written down.

   Every caption on screen, every scene boundary and the recording sheet in
   VOICEOVER.md all come from this file, so a line cannot be reworded in one
   place and left stale in another. `npm run voiceover` regenerates the sheet.

   Frames are at FPS, and the durations were set at roughly one hundred words
   across the minute. That is slow for speech on purpose: a trailer that fills
   every second with talking has nowhere to land a point. If a read comes back
   long, stretch `len` here rather than talking faster, then rerun the sheet. */

export const FPS = 30;
export const DURATION = 60 * FPS;
export const WIDTH = 1920;
export const HEIGHT = 1080;

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
    name: "Gate",
    from: 0,
    len: 330,
    note: "The demand. What proving who you are actually costs, one line at a time.",
  },
  {
    name: "Gap",
    from: 330,
    len: 270,
    note: "The refusal, then the number. Fifty points, with its source on screen.",
  },
  {
    name: "Constraints",
    from: 600,
    len: 330,
    note: "The two facts no waiver removes. Held in near silence.",
  },
  {
    name: "Surfaces",
    from: 930,
    len: 540,
    note: "Three screens for three people. Tablet, phone, desk, one case.",
  },
  {
    name: "Clock",
    from: 1470,
    len: 195,
    note: "Thirty days from receipt, three bureaus, and the two 120 day clocks.",
  },
  {
    name: "Logo",
    from: 1665,
    len: 135,
    note: "The wordmark draws itself. Tagline, then the credit line.",
  },
] as const satisfies readonly Scene[];

export const LINES = [
  { from: 24, len: 150, text: "The day you walk out, the world asks you to prove who you are." },
  { from: 200, len: 125, text: "The list is long, and every line on it is paper." },

  { from: 355, len: 150, text: "Inside there is no camera, no mail out, no open web." },
  { from: 525, len: 70, text: "So the errors wait." },

  { from: 620, len: 105, text: "Bridge starts from two facts no waiver removes." },

  { from: 945, len: 145, text: "Three screens, for three people who cannot do each other's jobs." },
  { from: 1110, len: 110, text: "A course that cites every source it stands on." },
  { from: 1240, len: 105, text: "One task at a time for the person helping." },
  { from: 1365, len: 100, text: "And a letter, approved by a person." },

  { from: 1485, len: 110, text: "Because the clock is real. Thirty days from receipt." },
  { from: 1605, len: 55, text: "All three bureaus." },

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
