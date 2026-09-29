# Working on Bridge

Bridge is a credit-repair workflow for people coming home in New York State.
A capstone project by a team of Fair Chance Futures AI Lab fellows, 2026.

Read `README.md` and `docs/SCOPE.md` before changing anything. This file is the
short version of what a session needs to not break things.

## Where to look first

    app/lessons.py         the credit course. Education is priority one.
    app/paths.py           the two things a person can be doing, and the choice
    app/facilities.py      the 41 DOCCS facilities, checked, with addresses
    app/surfaces.py        the capability table. Read this as the product spec.
    docs/SCOPE.md          what each of the three surfaces can and cannot do
    docs/VERIFY.md         every legal claim, its primary source and check date
    docs/RETENTION.md      what happens after release, and what is not answered
    docs/DESIGN-NOTES.md   rationale, deliberately kept out of the product
    docs/DEMO.md           seeded logins and the walkthrough
    docs/TRANSLATION.md    how the course gets into Spanish, for a translator

The product started from a wireframe deck. That deck has been deleted, and its
references stripped out of the code and the docs, because it stopped describing
the product and every change was being argued against a sketch. `docs/DESIGN-NOTES.md`
states the design principles on their own authority. Do not reintroduce a
screen-by-screen spec.

Where this is going: a progressive web app provisioned onto a facility tablet,
not a website somebody finds and installs. How it would actually get
there is not established, and that is in `SIMPLIFICATIONS` rather than dressed
up as a plan. The browser build is how it is
developed and demonstrated. `standalone/` is a demo artifact so the whole
journey can be walked in three windows; it is not the product, and nothing in
the app should tell a person to install anything.

## Two constraints everything follows from

**A person inside cannot verify identity, take delivery of a document, upload a
file, or browse out to a bureau.** Not a policy, not a setting: it is where the
tablet physically sits. This lives in `app/surfaces.py` and the router asks that
module before it does anything. Hiding a button in a template is decoration;
the capability table is the enforcement.

Do not overstate that constraint, and never as "cannot receive mail". That
includes what things are **named**: a capability in `app/surfaces.py` is named
for what a surface does, never for what a person does, because a name is what
gets lifted into a diagram or a slide while the paragraph under it does not.
`RECEIVE_MAIL` and `MAIL_LETTER` were renamed to `TAKE_DELIVERY` and
`PRINT_AND_POST` for exactly this: the prose had been corrected and the names
still said the false thing. People
inside receive their own mail, addressed to them at the facility under their
commitment name and DIN. It is opened and inspected, not generally read, and
not held more than 48 hours: DOCCS Directive 4422, in `app/sources.py` as
`incoming_mail_is_inspected_not_absent`. What the tablet cannot do is take
delivery of a document, because it has no camera and no scanner. That is a
fact about the device, not about the mail, and the two were conflated here
until somebody who would know said so.

**Bridge assumes the tablet is online**, so a write lands when it is made,
intake saves as it goes and the course keeps a place without a queue. Real
access is more limited than that and everything on it is monitored. That
difference is a **stated assumption of this build**, recorded once in
`SIMPLIFICATIONS` in `app/sources.py`, and it is settled: do not reopen it, and
do not add offline machinery nobody asked for. It is also why `sw.js` caches
nothing, which stays true for its own reason, that a worker serving a stale
timeline while a deadline moves is worse than no worker.

What is not an assumption: the device does not reach the open web, so no route
a bureau offers a free citizen is reachable from it. Every one runs through a
web page.

**A helper outside has no standing until they sign a scoped form.**
`app/authorization.py` holds scoped, expiring, revocable grants, checked on
every request, so a client who cancels from the tablet cuts access off at the
next tap. Some scopes raise on construction rather than being checked later.

## Rules that are not negotiable

- **Never put a camera on the tablet surface.** The helper has three ways to
  send a report in (PDF, typed, photographed, in that order of preference) and
  a fourth exists that needs no app: the paper goes to the coordinator, who
  scans it at their desk. The person inside reads; they never send.
- **Nothing arriving from outside is visible to the person until a coordinator
  has confirmed it.** These fields become a dispute letter, and a letter about
  the wrong account number is worse than no letter. The coordinator's own desk
  scan is the one exception, because they are reading the paper as they type.
- **Mask the Social Security number on the way in, never on the way out.** A
  report is stored already truncated. That it can be truncated at all is
  15 U.S.C. 1681g(a)(1)(A), not a courtesy we invented.
- **Line of sight is the boundary, not the desk.** The tablet is issued to one
  person and it is connected, but it is read in common areas and the facility
  administers it, so it and a helper's phone never render an SSN, a full
  account number or a date of birth. The
  coordinator does see them, because they hold the sentence and commitment
  paperwork and request the birth certificate, and hiding a number somebody is
  already holding protects nobody. `app/redaction.py` is per surface for this
  reason; do not make it global again.
- **The person says what they are doing, and can change it.** `app/paths.py`
  holds two paths, learn and credit. The first screen after a PIN asks which,
  in two sentences. It steers where they land and what the screens push
  toward; it never takes anything away, and the switch is in the header of
  every tablet screen. A path is not a rung: if a change would make one path
  hide the other, read `app/authorization.py` first.
- **Education is the first priority.** Every lesson card that states a rule
  cites a key in `app/sources.py`, and a test fails if it cites one that is not
  there. The course is reachable from every tablet screen and is never gated
  behind intake. Progress saves per card, because a session ends without
  warning: movement is called, the battery dies, the tablet gets set down.
- **No rungs.** The four-rung access ladder was removed deliberately: it
  modeled what a bureau would demand, which no public source establishes.
  Document readiness in `app/caseplan.py` replaced it. If you find yourself
  reintroducing a ladder, read the docstring in `app/authorization.py` first.
- **Say which 120 days you mean.** The Social Security card application goes in
  at 120 days *before* release. The release ID expires 120 days *after*. Two
  clocks, opposite sides of the gate, and confusing them costs somebody their
  ID.
- **A dispute goes to all three bureaus.** An item deleted at Equifax is still
  sitting on the other two files.
- **No legal sentence without a primary source, and that means credit
  reporting and the law.** A statute, a bureau's own instructions, a deadline,
  a score range, a right somebody has: those go in `app/sources.py` with a URL
  and a check date, or they are written as an open question. The `/citations`
  page renders that registry live; `docs/VERIFY.md` is the hand-kept
  companion, so update it in the same change.

  **It does not mean how we built this.** Product decisions are ours to
  assert and need no citation: what a surface can do, how a screen is laid
  out, what the redaction rules are, how long a grant lasts, what a PIN looks
  like. A rule that demanded a primary source for a design choice would be a
  rule nobody could follow, and it would drag the team into defending
  somebody else's operational detail instead of the credit work, which is the
  part this project is actually about.

  Where the build assumes something rather than establishing it, say so once
  in `SIMPLIFICATIONS` in `app/sources.py` and move on.
- **No column name reaches a screen.** `app/labels.py` is the registry, and a
  test fails if a raw field name renders.
- **An address nobody has read does not reach a screen.** Same rule as a legal
  sentence, for the same reason, and it applies to a government API too: data
  arriving from a city carries the city's authority, so an unchecked address is
  more dangerous there than in a guess. `app/centers.py` is hand-kept and each
  entry carries `verified_by_hand`. `app/facilities.py` is the same rule for
  the 41 DOCCS facilities, which are return addresses on dispute letters: it
  is a list to pick from, never a box to type in, and every entry carries the
  population DOCCS says it holds so a record that contradicts the person can
  be caught. Nothing guesses a facility. `app/doccs.py` used to pick one by
  hashing the DIN, which put a man in a facility for women; it now returns
  none, and the screen names the gap. `scripts/check_centers.py` reads NYC Open
  Data and only ever prints; nothing it fetches is served. `app/freshness.py`
  is what notices a check date getting old, across the facts, the bureau
  addresses and the centers together.
- **Never seed a PIN.** A PIN somebody else set is not a PIN.

## The standalone build, and how it has bitten before

`standalone/shell.html` is one shared source. `standalone/build.py` generates
three files from it, injecting the role and the rules payload out of the Python
modules, so the single-file version cannot quietly drift from the tested one.

    python3 standalone/build.py     # after ANY change to app/ or the shell

Editing that shell has gone wrong twice, both times the same way:

- **Never use a regex with `.*?` across route boundaries.** It spliced
  unrelated functions together and produced a syntax error that was painful to
  find. Use exact string swaps in a script that `sys.exit`s on a miss, so a
  pattern that no longer matches fails loudly instead of silently doing nothing
  or matching the wrong thing.
- **Syntax-check the shell after editing it**, before building. Extract the
  `<script>` block and run `node --check` on it.
- **Then drive the built files in a real browser.** Chromium is at
  `/opt/pw-browsers/chromium`; launch Playwright with that `executable_path`.
  `pytest` cannot see a broken route, a dead link, or a hash that does not
  match. Both real bugs found this way were invisible to the test suite: a
  router that ignored query strings, and a silent failure when `crypto.subtle`
  was unavailable.
- When asserting on what a page shows, read `#app`, not `page.content()`. The
  whole script is inlined, so every string literal in the source reads as
  "on the page" and your assertion passes or fails for the wrong reason.

## Checks before pushing

    pytest -q                       # 396 tests, all should pass
    python3 standalone/build.py     # rebuild if anything changed
    ./run.sh                        # installs, tests, serves on :8000

CI runs pytest on 3.11 and 3.12 on every push to main and every pull request.
3.12 has no pytest in the cloud container, so the matrix only fully runs in CI.

## Conventions

- **Sentence case** everywhere. Proper nouns keep their capitals, nothing
  shouts, and no underscores reach a person's eyes.
- **Every timeline event carries a person's name and a real date.** From the
  Cornish interview: automated nudges read as scams inside. An event with
  nobody attached does not go on the timeline.
- **Name the wait.** A screen that shows nothing while something is in progress
  cannot be told apart from a broken one. Say what is happening and who is
  doing it.
- **Comments explain why, not what.** Match the density already there.
- **Test names are sentences** that state the claim being defended.

## Test data

Every invented person has a DIN starting `28`. 2028 has not happened, so those
cannot collide with a real person in the public DOCCS lookup. Any DIN in that
range signs in and opens a case on the spot, which is also how anybody tries
the app. Keep new fixtures in that range.

The practitioner interview in `app/sources.py` is Brianne Cornish of FinEquity,
used with her permission. It is labelled as an interview wherever it is cited,
because it is evidence and it is not the same kind of evidence as a statute.
