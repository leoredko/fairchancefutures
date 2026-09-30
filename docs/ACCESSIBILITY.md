# Accessibility

What a person can change about how the tablet looks, what has been checked, and
what has not. The target is WCAG 2.2 AA. That is a target, not a certificate:
nobody has audited this with the assistive technology a person inside would
actually use, and this page says so rather than implying it.

## What a person can change

A **Display** link sits in the corner of every page, signed in or not, because
somebody who cannot read the sign-in screen cannot sign in to fix it. It opens
`/display`, which has three groups:

| Setting | Choices | Default |
| --- | --- | --- |
| Color | Dark, Light, High contrast | Dark |
| Text size | Normal, Large, Largest | Normal |
| Motion | Normal, Less motion | Normal |

They are cookies on the tablet (`bridge_theme`, `bridge_size`, `bridge_motion`),
the same way the language is. They survive the idle timeout and the next person
can change them in one tap. They are not on the case file, so a coordinator never
sees them and nothing about how somebody reads the screen becomes a record.

The server writes them onto `<html>` before the page leaves, so nothing flashes
to the wrong theme and everything works with scripts off. A tablet nobody has
touched looks exactly as it did before.

**Not followed automatically:** the device's own light or dark preference. Dark
is the product's look, and following the device would change what a tablet
nobody touched looks like. `prefers-reduced-motion` is followed.

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
- **Dictation and read aloud are not built.** Both depend on the tablet's
  hardware and the facility's rules. Browser dictation usually sends audio to a
  cloud service, which does not belong next to a PIN and a credit file. Read
  aloud can run on the device with no network, and should go to headphones only,
  since a speaker in a dayroom is a privacy leak. Neither should be built until
  somebody establishes what the tablet has and allows.
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
