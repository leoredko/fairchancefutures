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

## The cut

The first version of this opened on a checklist of document requirements. It
was accurate and nobody was going to watch it, because there was no person in
it and the first thing it did was ask the viewer to read a form.

This one opens on mail call. One envelope from somebody who loves him, a long
hold on nothing else arriving, and then ninety-six more from collection
agencies. Then the turn the whole minute hangs on: the people owed money found
him in three weeks off a lookup anybody can open, and the bureau he needs his
own file from still cannot reach him. Only then does the clock start, and the
product gets the middle twenty seconds with a hundred and fifty-four days
sitting in the corner of every shot.

Two rules the cut runs on, and both are worth keeping:

**No depiction of a person inside.** Not a face, not a hand, not a cell. The
sequence is built out of paper, a slot and type, which is also the only
register this project can shoot honestly. If somebody offers real footage
later, that is a different conversation and it belongs to whoever is in it.

**The pause is the joke.** MailCall spends eight seconds refusing to be funny
so the next seven land. Cutting that hold to save time kills the sequence, and
it will look like dead air in a timeline. It is not.

## What it says, and where that came from

The thirty days from receipt and the two 120 day clocks are facts in
`app/sources.py` with a primary source and a check date, and they carry their
citation on screen. The public lookup in the Found scene is the one named in
`app/doccs.py`. The three refusals are the reasons written in
`app/surfaces.py`, shortened but not softened.

The mail call sequence asserts nothing, on purpose. Every collection agency on
an envelope is invented, no facility is named, and the tally in the corner
counts the envelopes on screen rather than standing in for a statistic. It is a
picture of an afternoon, not a finding.

Marcus W. and his dates are the seeded record from `docs/DEMO.md`: DIN
`28-A-1187`, whose release dates `app/doccs.py` derives from a hash of the
number. Every invented person in this project has a DIN starting 28, and 2028
has not happened, so none of them can collide with somebody real.

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

    src/script.ts          the read, its timings, the scene boundaries, the client
    src/Trailer.tsx        the assembly: six scenes, one caption track, one clock
    src/theme.ts           the palette, lifted from app/static/bridge.css
    src/scenes/            one file per beat, in order
    src/components/Mark.tsx      the bridge mark and the wordmark
    src/components/Device.tsx    the bezel, and why a scaled element needs one
    src/components/Envelope.tsx  the paper, the senders and the slot
    src/components/Counter.tsx   the days-to-the-gate chip, laid over the scenes
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
its scaled result for that reason, and so is `Envelope`, which is drawn at a
fixed size and scaled ninety-nine times a frame. If you add a fourth surface,
do the same.

**The day count is frozen, not computed.** `CLIENT.daysToGate` in `src/script.ts`
is pinned with the date it was measured on beside it. Deriving it at render
time would mean the number changed every week while the recorded voiceover kept
saying the old one. If you re-cut this months from now, change both together.

**`background-clip: text` crops to the glyph box.** The hero number in Release
lost the flag off its 1 to this, which only showed up on a rendered still. The
fix is padding on the element plus a matching negative margin. Any large
gradient numeral with negative letter-spacing is a candidate.

**Look at the frames.** A typecheck cannot see a device off the edge of the
picture or a line of copy that says something the product does not do. Render
stills at the frames you changed and actually open them:

```bash
npx remotion still Trailer /tmp/f.png --frame=1440 --scale=0.5
```
