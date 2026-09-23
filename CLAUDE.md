# Working on Bridge

Bridge is a credit-repair workflow for people coming home in New York State.
A capstone project by a team of Fair Chance Futures AI Lab fellows, 2026.

Read `README.md` and `docs/SCOPE.md` before changing anything. This file is the
short version of what a session needs to not break things.

## Where to look first

    app/lessons.py         the credit course. Education is priority one.
    app/surfaces.py        the capability table. Read this as the product spec.
    docs/SCOPE.md          what each of the three surfaces can and cannot do
    docs/VERIFY.md         every legal claim, its primary source and check date
    docs/DESIGN-NOTES.md   rationale, deliberately kept out of the product
    docs/DEMO.md           seeded logins and the walkthrough

The product started from a wireframe deck. That deck has been deleted, and its
references stripped out of the code and the docs, because it stopped describing
the product and every change was being argued against a sketch. `docs/DESIGN-NOTES.md`
states the design principles on their own authority. Do not reintroduce a
screen-by-screen spec.

Where this is going: a progressive web app provisioned onto a facility tablet,
not a website somebody finds and installs. The browser build is how it is
developed and demonstrated. `standalone/` is a demo artifact so the whole
journey can be walked in three windows; it is not the product, and nothing in
the app should tell a person to install anything.

## Two constraints everything follows from

**A person inside cannot verify identity, receive mail, upload a file, or
browse out to a bureau.** Not a policy, not a setting: it is where the tablet
physically sits. This lives in `app/surfaces.py` and the router asks that
module before it does anything. Hiding a button in a template is decoration;
the capability table is the enforcement.

The tablet is not offline. Bridge is loaded onto it and reaches the person's
own record, which is why intake saves as it goes and the course keeps a place.
What it cannot reach is the open web, and every route a bureau offers a free
citizen runs through a web page. Do not write copy promising that anything
survives a week without connectivity: writes go to the server.

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
- **The dayroom is the boundary, not the desk.** A shared tablet and a helper's
  phone never render an SSN, a full account number or a date of birth. The
  coordinator does see them, because they hold the sentence and commitment
  paperwork and request the birth certificate, and hiding a number somebody is
  already holding protects nobody. `app/redaction.py` is per surface for this
  reason; do not make it global again.
- **Education is the first priority.** Every lesson card that states a rule
  cites a key in `app/sources.py`, and a test fails if it cites one that is not
  there. The course is reachable from every tablet screen and is never gated
  behind intake. Progress saves per card, because a tablet session ends when
  the dayroom closes.
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
- **No legal sentence without a primary source.** Add the fact to
  `app/sources.py` with its URL and check date, or write it as an open question
  instead. The `/citations` page renders that registry live; `docs/VERIFY.md`
  is the hand-kept companion, so update it in the same change.
- **No column name reaches a screen.** `app/labels.py` is the registry, and a
  test fails if a raw field name renders.
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

    pytest -q                       # 297 tests, all should pass
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
