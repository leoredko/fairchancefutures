# The trailer

Sixty seconds of Bridge, built in [Remotion](https://www.remotion.dev): React
components rendered frame by frame into an mp4, so the video is source code and
a diff to it is reviewable like anything else in this repository.

```bash
npm install
npm run studio     # the editor, on http://localhost:3000
npm run render     # out/bridge-trailer.mp4, 1920x1080, 30fps
npm run voiceover  # regenerate VOICEOVER.md from the script
npm run typecheck
```

It is not a walkthrough. A minute is not enough to show the product working,
and a minute spent trying is a minute that never says what the product is for.
So the trailer states the problem, names the two constraints everything else
follows from, shows the three surfaces once, and stops.

## What it says, and where that came from

Every claim on screen is one the app itself is allowed to make. The list of
what a mailed dispute has to carry, the fifty point gap, the thirty days from
receipt, the two 120 day clocks: each is a fact in `app/sources.py` with a
primary source and a check date, and each carries its citation on screen. The
one number the team has heard and cannot source, the thirty-two points per year
of confinement, is an open question in that file and is deliberately not here.

The three screens in the middle are drawings of the product rather than
captures of it, and that is a decision rather than a shortcut. A real 1080p
capture is a wall of 15px type nobody reads off a projector, and cropping it to
the readable part shows one card and no context. So the layout, the palette and
the copy are the app's, set two or three steps larger. The lesson card is from
`app/lessons.py`, its citation from `app/sources.py`, the helper's three ways to
send a report from `docs/SCOPE.md`, the letter from the template in
`app/letters.py`. **If a screen here stops matching the app, the app is right.**

## The voiceover

There is none recorded. `VOICEOVER.md` is the sheet to read from, generated
from `src/script.ts` so the lines and their timings cannot drift apart. Drop
the recording in as `public/voiceover.mp3` and the next render picks it up;
with no file there the trailer plays silent and the captions carry the whole
script, which is also how it plays on a muted phone.

To change a line, change it in `src/script.ts` and run `npm run voiceover`. The
captions, the scene boundaries and the sheet all read from that one file.

## Layout

    src/script.ts          the read, its timings, and the scene boundaries
    src/Trailer.tsx        the assembly: six scenes, one caption track
    src/theme.ts           the palette, lifted from app/static/bridge.css
    src/scenes/            one file per beat, in order
    src/components/Mark.tsx      the bridge mark and the wordmark
    src/components/Device.tsx    the bezel, and why a scaled element needs one
    src/components/surfaces.tsx  the three screens, rebuilt at trailer size
    public/fonts/          Space Grotesk and IBM Plex Sans, vendored
    scripts/voiceover.mjs  regenerates VOICEOVER.md

## Notes for the next person

**The rendered mp4 is not committed.** `out/` is ignored, because the file is
twelve megabytes and it will be re-rendered the moment the voiceover lands.
Render it when you need it, and attach it to a release or a drive folder rather
than to the history.

**Fonts are vendored, not fetched.** `public/fonts/` holds the latin subsets of
the two families `app/static/bridge.css` names. A render never touches the
network, so it works on a locked-down machine and a frame can never come out
set in a fallback because a font request was slow.

**The browser.** `remotion.config.ts` points at the Chromium already installed
in the cloud container before Remotion downloads its own. On a laptop with no
`/opt/pw-browsers` it falls through and Remotion does the normal thing; set
`REMOTION_BROWSER=default` to force that.

**A CSS transform does not change layout.** This already cost one render: three
devices scaled down to a third still claimed their full width in the flex row
and two of the three ended up off the side of the frame. `Device` is sized to
its scaled result for that reason. If you add a fourth surface, do the same.

**Look at the frames.** A typecheck cannot see a device off the edge of the
picture or a line of copy that says something the product does not do. Render
stills at the frames you changed and actually open them:

```bash
npx remotion still Trailer /tmp/f.png --frame=1440 --scale=0.5
```
