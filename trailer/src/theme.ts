/* The palette, lifted from app/static/bridge.css so the trailer and the app
   are the same material. Emerald through cyan carries anything moving
   forward; amber still means a person has to do something. If a token here
   stops matching the stylesheet, the stylesheet is right. */

export const c = {
  ink: "#EFF6F2",
  ink2: "#B2CBC1",
  muted: "#7E9990",
  faint: "#5D766E",

  surface: "#08120E",
  page: "#0F1E18",
  surface2: "#162A22",
  line: "#1F3830",
  lineStrong: "#2C4D40",
  track: "#142520",

  teal: "#2DD4A0",
  tealDeep: "#0E9B6E",
  tealSoft: "#0E2A22",
  tealInk: "#6BE8C0",
  cyan: "#22D3EE",

  amber: "#F0A93C",
  amberSoft: "#2E1F0B",
  amberInk: "#F3BE6B",
  sky: "#5BA9EE",
  skySoft: "#10202F",
  green: "#3ECF97",
  rose: "#FF7D93",
  roseSoft: "#2E1019",
} as const;

export const display = "'Space Grotesk', system-ui, sans-serif";
export const body = "'IBM Plex Sans', system-ui, sans-serif";
export const mono = "ui-monospace, Menlo, monospace";

export const grad = `linear-gradient(103deg, ${c.tealDeep} 0%, ${c.teal} 55%, ${c.cyan} 100%)`;

/* Text painted with the brand sweep rather than a flat fill. Used on the
   numbers and the wordmark, never on a paragraph: a gradient on body copy is
   unreadable at projector distance. */
export const gradText = {
  background: grad,
  WebkitBackgroundClip: "text",
  backgroundClip: "text",
  color: "transparent",
} as const;
