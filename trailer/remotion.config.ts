import { Config } from "@remotion/cli/config";
import { existsSync } from "node:fs";

/* H.264 in an mp4, which is the one thing that plays on a conference room
   projector, in a Slack thread, and in a browser tab without anybody having
   to install a codec. */
Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setOverwriteOutput(true);

/* Remotion downloads its own Chrome Headless Shell the first time it renders.
   In the cloud container one is already sitting there for Playwright, so
   pointing at it saves the download and, more to the point, means a render
   works on a machine with no outbound access at all.

   REMOTION_BROWSER=default hands the choice back to Remotion, which is what
   you want on a laptop that has no /opt/pw-browsers. */
const CANDIDATES = [
  process.env.REMOTION_BROWSER,
  "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
  "/opt/pw-browsers/chromium",
];

if (process.env.REMOTION_BROWSER !== "default") {
  const found = CANDIDATES.find((p) => p && existsSync(p));
  if (found) {
    Config.setBrowserExecutable(found);
  }
}
