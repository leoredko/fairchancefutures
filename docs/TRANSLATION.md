# Translating the course

The credit course is eleven lessons, 173 sentences, and the screens that carry
a person to it (the door, the PIN, the first question, the lesson list and the
buttons inside a lesson), the Display settings and the read-aloud and voice
typing controls are another 157, 330 strings in all. All of them are in Spanish
now, and Leo Redko approved the Spanish on 2026-09-30. This is how that works
and how to change it.

## The short version

The Spanish lives in one file, `app/translations/es.po`. Somebody who speaks
Spanish opens it, reads, fixes what is wrong, saves. That is the whole thing.

Nothing about this runs while the app is running. There is no service to call,
no model, no key, no network. The Spanish is part of the app the same way the
English is, which is why it cannot fail during a demo.

## The switch

If a line turns out to be wrong at a bad moment, set this on the host:

    BRIDGE_SPANISH=off

The language disappears: no choice at the sign-in door, everything in English,
including on a tablet that was already set to Spanish. It takes effect on the
next page load. No deploy, no code change, no rollback.

Set it back to anything else, or remove it, and Spanish returns.

## What a person sees

At the sign-in door, before anything else, three options: **English**,
**Español**, and **Other**. Other cannot be picked as a language. It opens the Language page, where a person types the language they need and gets a thank you; the asks are kept in `language_requests` in the case file. The Language link in the corner of every screen reaches the same page after sign-in. Somebody who reads neither should find that out on the first screen,
from something that admits it, rather than after working through a course they
cannot read.

The choice is a cookie on the tablet, so it survives the idle timeout and the
next person can change it in one tap.

## Checking the Spanish

1. Get Poedit. It is free, Mac and Windows: [poedit.net](https://poedit.net)
2. Open `app/translations/es.po`
3. English on the left, Spanish on the right. Read it and fix what is off.
4. No line is marked **Needs work** now, because the team approved the file as a
   whole. A line whose English is reworded gets the flag back on its own, so the
   next reader sees what changed. If you fix a line, that is a change like any
   other: save and commit.
5. Save, commit.

**"Needs work" does not hide anything.** The Spanish shows on the tablet
either way. The flag is a bookmark for whoever is reading, not a gate.

## What to watch

57 lines carry a note saying **LEGAL**. Those sit on a card that cites a law.
Numbers and deadlines are where a translation can actually hurt somebody:

- The Social Security card application goes in **120 days before** release.
- The release ID expires **120 days after** release.

Two different clocks, opposite sides of the gate. If the Spanish gets those
backwards, somebody loses their ID. If an English sentence is ambiguous, say
so and we will fix the English rather than guess in the Spanish.

**Left in English on purpose:**

- Agency names: Equifax, Experian, TransUnion, DOCCS, DMV
- Law references like 15 U.S.C. 1681i
- The source line under each card

Somebody may carry those to a law library, and they have to read the way they
read on the shelf. The code never translates them.

## Known gaps

- Every screen on the tablet is in Spanish, approved by the team on 2026-10-01:
  the course, intake, the explanation after question two, where you stand, the
  case screen with its papers card, the report and its walkthrough, the scores
  page, the request, the authorization and when you go home, plus the landing
  page. A test walks them all in Spanish and fails on a line that reads as
  English.
- Still English on purpose: the dispute and request letters, because they go to
  a bureau that reads English; the source line under a lesson card and every
  citation; agency names; the helper's phone and the coordinator's desk, which
  were never part of this; the page that explains why a screen is not available
  from a surface, which a person only reaches by a wrong turn; and any
  free-text a coordinator types (a note on an account, a name) which is shown
  as written.
- Case data that Bridge writes itself (timeline sentences, bureau statuses on
  the seeded files) is recognised and shown in Spanish by `translate_text` in
  `app/i18n.py`, matched against the `timeline.*` and `data.*` keys. A status
  nobody wrote a line for shows as stored. Dates like "March 18" become "18 de
  marzo"; ISO dates are left as printed.
- Sign-in errors are raised in code that does not know the language, so the
  screen recognises the English sentence and swaps in the Spanish. Reword one in
  `app/auth.py` or `app/identifiers.py` and it falls back to English until its
  line in `app/ui_strings.py` is reworded to match. A test catches this.
- Timeline entries are written into the case file in English at the moment
  they happen, so a Spanish reader sees English history. Fixing that means
  storing a key instead of a sentence.

## For whoever maintains the code

The screen strings live in `app/ui_strings.py`, keyed, with the English beside
the key. Run this after editing any lesson or that file:

    python3 scripts/i18n_extract.py

It rebuilds the file from `app/lessons.py` and `app/ui_strings.py` and never
discards anyone's work:

| What happened | What the script does |
| --- | --- |
| New card added | New empty line, waiting |
| Card untouched | Left alone |
| English reworded | Spanish kept, flagged Needs work again |
| Card deleted | Kept at the bottom, in case it comes back |

`--check` fails if the file is behind the lessons, and a test runs it, so a
card added without re-extracting cannot quietly become a screen nobody can
translate.

Two safety rules are in the code and not adjustable. If a card's English has
changed since its Spanish was written, that line falls back to English on its
own. And on a screen string, a translation that drops or renames a `{blank}`
the screen fills in (a number, a name) falls back to English too, because a
sentence with a hole in it reads as broken. A fluent translation of a sentence the product no longer says is worse
than no translation, because it reads finished.
