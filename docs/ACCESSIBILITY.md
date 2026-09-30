# Accessibility

What a person can change about how the tablet looks, what has been checked, and
what has not. The target is WCAG 2.2 AA. That is a target, not a certificate:
nobody has audited this with the assistive technology a person inside would
actually use, and this page says so rather than implying it.

## What a person can change

A **Display** link sits in the corner of every page, signed in or not, because
somebody who cannot read the sign-in screen cannot sign in to fix it. It opens
`/display`, which has four groups:

| Setting | Choices | Default |
| --- | --- | --- |
| Color | Dark, Light, High contrast | Dark |
| Text size | Normal, Large, Largest | Normal |
| Motion | Normal, Less motion | Normal |
| Read aloud | Off, On | Off |

They are cookies on the tablet (`bridge_theme`, `bridge_size`, `bridge_motion`,
`bridge_read`),
the same way the language is. They survive the idle timeout and the next person
can change them in one tap. They are not on the case file, so a coordinator never
sees them and nothing about how somebody reads the screen becomes a record.

The server writes them onto `<html>` before the page leaves, so nothing flashes
to the wrong theme and everything works with scripts off. A tablet nobody has
touched looks exactly as it did before.

**Not followed automatically:** the device's own light or dark preference. Dark
is the product's look, and following the device would change what a tablet
nobody touched looks like. `prefers-reduced-motion` is followed.

## Read aloud

Off until somebody turns it on. When it is on, a **Listen** button appears at the
top of each screen and reads that screen to the person, in the language the
tablet is set to. It is `app/static/listen.js`, loaded only when the setting is
on, so a tablet that has not asked for it never touches the speaker.

The rules it keeps, each of them a test on the script:

- **Only a voice that stays on the tablet.** Many browser voices stream the text
  to a cloud service, and the text sits next to a person's name and case. The
  script uses a voice only if the browser says `localService` is true. With no
  such voice for the language, the button never appears and the Display page
  says so. Spanish needs a local Spanish voice; it does not fall back to an
  English one reading Spanish.
- **It listens to nothing.** No microphone, no speech recognition, no request
  out of the file, nothing stored.
- **It says nothing until the button is pressed,** and leaving the page ends it.
- **It reads the content and not the chrome.** The header, buttons, the Display
  link and the citation line under a lesson card are skipped. A citation is an
  English source and a statute number, which is for a law library and not for the
  ear.

**Headphones cannot be enforced.** A browser cannot tell whether a jack is in
use, so a tablet speaker in a dayroom will be heard by the room. The setting
and the button both say to use headphones, and that is all the code can do. The
person, or the facility, has to do the rest.

**Untested on the real tablet.** It was driven in Chromium with a stand-in speech
engine, which proves what it picks and what it says, not what the facility
tablet's voices sound like or whether it has a local one at all.

### Dictation, deliberately not built

The tablet has almost nothing to dictate into: the person picks from choices, and
the only typed fields are the DIN, the PIN and the human check. Speaking a PIN or
a DIN in a common area is a privacy leak, and a microphone is a bigger thing to
ask a facility for than a speaker. If the facility turns on the device's own
voice control, the fields carry names that match what is on screen, so it can
target them. Revisit this if a screen ever asks for free text.

## What was checked, and how

- **Contrast.** `tests/test_accessibility.py` reads the colour values out of
  `app/static/bridge.css` and checks every pair a person has to read, in every
  theme: body text 4.5 to 1, the edge of a field and the focus ring 3 to 1, and
  high contrast at 7 to 1. Change a colour and that test says whether it still
  reads. It found real failures in the existing dark theme (small print at 3.1,
  field borders at 1.6) and a button label that went white on the bright green
  on hover (1.9).
- **Structure.** axe-core was run over every page in all three themes and at the
  largest text size, as each role. It finds no violations. The tests check the
  parts of that a browser is not needed for: one `main` per page, a skip link
  that lands on it, a level-one heading, and a name on every field.
- **Fields.** The sign-in number and the PIN fields were named by a placeholder,
  which axe accepts and which is not a label (it is gone when you type). They are
  now named by the heading above them.

To repeat the axe run:

    pip install axe-playwright-python     # not in requirements.txt
    # start the app, then drive each page with Axe().run(page)

Chromium is at `/opt/pw-browsers/chromium`; launch Playwright with that
`executable_path`.

## What has not been done

- **No screen reader has been run against this.** VoiceOver, TalkBack and NVDA
  are the check that matters and need a person with one. axe and the tests
  catch what a machine can; they do not tell you whether it is pleasant.
- **Dictation is not built,** for the reasons above.
- **The standalone build is not covered.** `standalone/shell.html` has its own
  styles and does not use `bridge.css`, so it is dark only and none of the above
  applies to it.
- **The helper's and coordinator's screens** get the themes and the structure
  fixes, but they are English only and have had the same automated checks, not a
  manual pass.
- **The letters** a coordinator prints stay ink on paper whatever the theme.

## Conventions

- Sizes in the stylesheet are in `rem`, so the text-size setting moves all of it
  together and a device that already enlarges text keeps doing so.
- A colour that is read as text or as an edge goes through a token
  (`--link`, `--focus`, `--field-bd`, `--tag-*`). A colour typed into a rule
  bypasses the theme and the test.
- Meaning is never carried by colour alone. The chosen option on `/display` says
  "Selected" as well as being outlined, and the tags say what they mean.
