import React from "react";
import { Composition, staticFile } from "remotion";
import { loadFont } from "@remotion/fonts";
import { DURATION, FPS, HEIGHT, WIDTH } from "./script";
import { Trailer } from "./Trailer";

/* Both families are vendored under public/fonts and loaded from there, so a
   render never reaches the network and a frame can never come out set in a
   fallback because a font request was slow. The app itself asks for these two
   by name and loads neither: app/static/bridge.css makes zero outbound
   requests on purpose, because the tablet is metered by the minute. */
loadFont({
  family: "Space Grotesk",
  url: staticFile("fonts/SpaceGrotesk.woff2"),
  weight: "300 700",
  format: "woff2",
});
loadFont({
  family: "IBM Plex Sans",
  url: staticFile("fonts/IBMPlexSans.woff2"),
  weight: "100 700",
  format: "woff2",
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Trailer"
    component={Trailer}
    durationInFrames={DURATION}
    fps={FPS}
    width={WIDTH}
    height={HEIGHT}
  />
);
