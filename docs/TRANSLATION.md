# Translating the course

The credit course is eleven lessons. This is how it gets into Spanish, and it
needs no engineer once the file exists.

## The short version

The Spanish lives in one file, `app/translations/es.po`. Somebody who speaks
Spanish opens it, types, and saves. That is the whole thing. There is no
service to call and nothing to turn on.

**Until a person signs a line off, the app shows the English.** That is the
rule the code enforces, and it is not adjustable.

## Why it works that way

These lessons state law. A person reads a card, believes it, and acts on it,
sometimes on a deadline that does not come back around.

So a Spanish sentence about a 30-day dispute clock that no Spanish speaker has
read is not a half-win. It is worse than the English, because it reads fluent
and confident and the reader has no way to tell. The app already refuses to
state a legal fact without a primary source. This is the same rule in a second
language.

English is not the failure case. It is what somebody gets today, and it is
correct.

## Doing the work

**1. Get a translation tool.** Poedit is free and runs on Mac and Windows:
[poedit.net](https://poedit.net). Any tool that opens `.po` files works.

**2. Open `app/translations/es.po`.** You will see the English on one side and
an empty box for the Spanish on the other, 173 of them.

**3. Type the Spanish.**

**4. Clear the "Needs work" flag** on each line you are happy with. In Poedit
that is the "Needs work" toggle in the toolbar. In the raw file it is the word
`fuzzy`.

That flag is the entire review gate. A line still marked "Needs work" shows in
English no matter what Spanish is sitting next to it. Some lines arrive with a
rough draft already filled in and flagged: read it, fix it, then clear the
flag. Nobody has to start from a blank box.

**5. Save the file and commit it.** That is the deployment. The Spanish ships
inside the app.

## What to watch for

Some lines carry a note that says **LEGAL**. Those sit on a card that cites a
statute. Slow down on those.

**Numbers and deadlines are the dangerous part.** There are two different
120-day clocks in this course, on opposite sides of release:

- The Social Security card application goes in **120 days before** release.
- The release ID expires **120 days after** release.

Getting those backwards in Spanish costs somebody their ID. If a sentence is
ambiguous in English, say so rather than guessing, and we will fix the English.

**Do not translate these:**

- Agency names: Equifax, Experian, TransUnion, DOCCS, DMV
- Statute references like 15 U.S.C. 1681i

Somebody may carry those to a law library, and they have to read the way they
read on the shelf.

## For whoever maintains the code

Run this after editing any lesson:

    python3 scripts/i18n_extract.py

It rebuilds the file from `app/lessons.py` and **never discards a
translator's work**:

| What happened | What the script does |
| --- | --- |
| New card added | New empty line, waiting |
| Card untouched | Left alone. A sign-off stays signed off. |
| English reworded | Spanish kept, flagged "Needs work" again |
| Card deleted | Kept at the bottom, in case it comes back |

`--check` fails if the file is behind the lessons, and a test runs it, so a
card added without re-extracting cannot quietly become a screen that can never
be translated.

The translation happens once, at the desk, and gets committed. Nothing about
this runs at request time, which is why it cannot fail during a demo.
