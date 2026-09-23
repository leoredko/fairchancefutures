# Bridge

A capstone project by a team of Fair Chance Futures AI Lab fellows, 2026.

A credit-repair workflow for people coming home, split across three surfaces
because the three people involved genuinely cannot do each other's jobs.

The destination is an application that arrives already on a facility tablet,
provisioned by whoever manages the devices. The browser version here is how it
is built and demonstrated, not how it would be handed to somebody.

```bash
./run.sh          # installs, tests, serves on http://127.0.0.1:8000
```

Tests run in CI on every push and pull request, on Python 3.11 and 3.12
(`.github/workflows/tests.yml`). To deploy it somewhere real, see
[docs/DEPLOY.md](docs/DEPLOY.md).

Or by hand:

```bash
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

## Three surfaces, one case

The server app in `app/` is the real architecture: three surfaces, one shared
case, enforcement server-side. That is what becomes the product.

`standalone/` is a demo artifact, and only that. Three single files, no server
and no network, so the whole journey can be shown by opening three browser
windows side by side without anybody installing anything:

    standalone/bridge-inside.html    the facility tablet
    standalone/bridge-family.html    the helper's phone
    standalone/bridge-staff.html     the coordinator's desktop

Served from the same folder or the same host all three share one caseload, so a
client the coordinator adds appears on the tablet. Each keeps its own session,
so signing in on one does not sign you out of another. Published to three
different origins they cannot see each other.

```bash
python3 standalone/build.py     # regenerate all three after changing the app
```

It is generated, not hand-maintained. The four triage states, the letter
templates, the verified facts and the bureau addresses come straight out of the
Python modules, and `tests/test_standalone.py` fails if the two ever disagree.

## Signing in

New York only, because the identifiers are.

| Surface | What you sign in with |
| --- | --- |
| Inside | A DIN (`28-A-1187`) or a NYSID (`00000011L`), then a PIN you choose |
| Family | The code printed on the letter that came in the mail, then a PIN |
| Coordinator | Nothing. They arrive already signed in to the vendor case plan system |

Any DIN starting `28` signs in and opens a case on the spot: 2028 has not
happened, so those cannot belong to a real person. Anything outside that range
is added by a coordinator from **New intake** on the caseload queue,
which creates the case
file, a sign-in for each number entered, and the helper code that goes on the
letter to whoever is helping from outside. No PIN is set at creation: a PIN a
counselor could choose would be a PIN a counselor knows.

Sign-ins for the seeded caseload are in [docs/DEMO.md](docs/DEMO.md), not in
the application: seeded logins on a landing page make a product look like a
sample.

Bridge is one domain inside the DOCCS **Offender Case Plan** rather than a
second system to maintain. See [docs/SCOPE.md](docs/SCOPE.md) for what that
integration assumes and `app/caseplan.py` for the code.

Design rationale lives in [docs/DESIGN-NOTES.md](docs/DESIGN-NOTES.md).

Nobody is issued a PIN. Everyone sets their own at first use, and a counselor
resetting one *clears* it rather than choosing a new one, so the only person who
ever knows a client's PIN is the client. PINs are PBKDF2-hashed with a per-user
salt and the plaintext never reaches the store. The DIN format is confirmed
from DOCCS; the NYSID check letter is not, so it is accepted and never
validated, because rejecting a real number at a kiosk is the worst thing this
code can do.

The threat model is the next person to pick up the tablet, not a remote
attacker: 15 minute idle timeout on the kiosk, a shift-length one for staff,
lockout after five wrong PINs, obvious PINs refused, sign-out on every screen.

## What is assumed away

Signed off for class, the same way the political red tape was: facility and DOC
approval, incumbent tablet vendor access, bureau data agreements, funding for
the counselor role, and the PII compliance regime a real deployment would sit
under. No BAA, no SOC 2, no state privacy filing, no encryption-at-rest story.
Data lives in a plain JSON file you can open and read.

That is a deliberate scoping decision for a prototype, and it is on the home
page rather than hidden. If this were going near a real person's Social Security
number it would need all of it.

## What is not assumed away

Two things, because no waiver makes them disappear. They are the spine of the
whole build.

**A person inside cannot verify identity online.** No camera roll, no document
scanner, no open web to reach a bureau's knowledge-based auth page. That is not
a permission setting, it is where the tablet sits. `app/surfaces.py` holds the
capability table, and every handler calls `require()` before doing anything.
There is no upload route on the inside surface at all, and
`test_tablet_has_no_upload_route` fails if somebody adds one.

**A helper outside has no standing without a signed form.** So standing is a
record: `app/authorization.py` defines a scoped, expiring, revocable
`Authorization`, and every family-side handler calls `require_scope()` against a
live one. A helper with no grant sees the invitation and nothing else. The
client cancels from the tablet and the helper loses access on the next request.
Four scopes can be granted; six can never be, and constructing an authorization
that names one of them raises.

## The documents, which gate everything

This replaced a four-rung access ladder that modeled what a bureau would demand
and climbed a rung on each kickback. Nobody publishes how often the cheapest
route clears, and Experian asks for an ID copy with every mailed dispute
regardless, so the first rung may never have existed. `app/authorization.py`
carries the full reasoning.

What is knowable is what a person has in their file, and there is a strict
order to it. The birth certificate **and** the Social Security card must both
be on file before the non-driver ID application can be submitted. The
coordinator prioritizes getting them and reviews the status quarterly. The
Social Security card application goes in at **120 days before release**.

Three things the app says that a person would otherwise find out too late:

- The birth certificate takes ten weeks or more and has no deadline of its own,
  which is exactly why it is the one that gets left.
- The no-fee route covers New York records. Born elsewhere and it does not
  apply to you, so start now.
- The release ID expires **120 days after** release, which is a different 120
  days from the one above.

`app/caseplan.py` holds this, and `docs/VERIFY.md` has every source.

## What the app actually does

| Surface | Route | What it is |
| --- | --- | --- |
| Inside, tablet | `/inside/learn` | **The credit course.** Eleven lessons, about fifty minutes, reachable from every screen, saved per card. Every rule cites a primary source. |
| Inside, tablet | `/inside/report` | The report arriving, credited to whoever got it here, then walked section by section with the teaching attached. Ends on the one question that opens a legal clock. |
| Inside, tablet | `/inside` | Six intake questions, one per screen. Position not score. Case timeline with named people. Cancel a helper's authorization. |
| Family, phone | `/family` | The invitation that rules out everything a scam would ask for. Exactly one task on screen. Print the request packet. Send the report in three ways. |
| Caseworker, desktop | `/staff` | Work queue sorted by what expires first. Triage session. Letter draft and approval. What is blocking the ID. What the client flagged on their own report. |
| — | `/citations` | Every verified fact with its source and check date, and the open questions alongside them. |
| — | `/metrics` | The edit rate. |

## The measurable part

`app/triage.py` is the classifier: six answers in, one of four states out, with
a path attached. It is the only screen where the app does something a person
could not do on paper, and the only one whose output can be scored.

Two rules in it are load-bearing. Errors jump the queue, because a dispute has a
legal clock and nothing else does. Restitution routes to the obligations list
and never to the credit path, because it is a different mechanism and putting it
in a list of credit cards misrepresents it.

`tests/test_triage.py` is the accuracy claim: labelled cases, one per judgement
worth arguing about. When a counselor disagrees with the output, the fix is a
new case in that file. `/metrics` reports the other half, how often a reviewer
edits a drafted letter before approving it. Reporting that number when it is
ugly is the DoNotPay lesson.

## What has been checked

Nothing in this app states a legal fact unless it is in `app/sources.py` with a
primary source and the date somebody looked. `/citations` renders that registry,
open questions alongside the checked ones, and the letter templates cite from
the same place. Full table in [docs/VERIFY.md](docs/VERIFY.md).

The load-bearing ones: a bureau has 30 days from **receipt** of a dispute, not
from the postmark, extendable to 45 if the client sends more information
mid-dispute. Child support arrears do reach credit reports. Civil judgments
mostly do not, since July 2017.

A dispute is drafted once per bureau. An item deleted at Equifax is still
sitting on the Experian and TransUnion files, and the first build quietly
pretended otherwise.

## Where this is going

A progressive web app, provisioned onto the tablet rather than installed by the
person using it. Nobody inside is going to be handed a URL and told to tap Add
to Home Screen, and a product that depends on them doing so does not get used.

`app/static/manifest.webmanifest` and the registered service worker are the
foundation for that: the app runs with its own icon and no browser chrome. The
worker caches nothing on purpose, which is the right call while the tablet is
connected. See `app/static/sw.js` and [docs/DEPLOY.md](docs/DEPLOY.md).

What still stands between this and a real deployment, roughly in order:
`app/store.py` is a JSON file rewritten whole on every write and needs to be a
database; the case plan integration is three simulated functions; and
encryption, audit logging and retention are assumed away, which for something
holding Social Security numbers is most of the work.

## What is deliberately not built

- Photo-to-text extraction of a mailed report. The fallback is that the
  caseworker types it in, so that is what happens. Uploaded images are counted
  and discarded rather than stored, which also means this build never holds a
  picture of somebody's credit report on disk.
- Referrals and outcomes reporting.
- Real offline support. The tablet reaches Bridge, so writes go straight to the
  server and save as they are made. An earlier promise that "nothing is lost if
  you lose access for a week" was about a disconnected device and has been taken
  out of the intake copy rather than left there untrue. If a facility
  turns out to have genuinely intermittent connectivity, IndexedDB plus
  replay-on-reconnect is the real fix.
- Spanish. An EN / ES toggle was drawn early and removed rather than shipped as
  decoration over an English-only app. For this population it is a real
  requirement rather than a nice-to-have, and it should come back as
  translation rather than as a pill.
- Real auth. Anyone who can reach the URL is the surface named in the URL. The
  surface split is enforced, the identity behind it is not.

## Layout

```
app/lessons.py         the credit course, and where somebody has got to in it
app/walkthrough.py     reading your own report, one section at a time
app/surfaces.py        capability table, constraint one
app/authorization.py   scoped, expiring, revocable grants, constraint two
app/triage.py          the classifier
app/redaction.py       per-surface, per-field minimization
app/letters.py         templated letters and the edit-rate log
app/bureaus.py         the three bureaus, addresses, and where they came from
app/sources.py         every legal fact, its primary source, and the check date
app/identifiers.py     DIN and NYSID parsing
app/auth.py            PINs, lockout, signed sessions
app/session.py         who is asking, from the cookie rather than the URL
app/caseplan.py        the DOCCS Offender Case Plan integration
app/vendor.py          the coordinator's single sign-on handoff
app/report.py          scanned reports, and masking the SSN on the way in
app/scores.py          why there is no such thing as one credit score
app/labels.py          human labels, so no column name reaches a screen
app/intake.py          adding somebody to the caseload
standalone/            the single openable file, and its build script
app/questions.py       the two question sets, and why they differ
app/store.py           JSON persistence and the seed caseload
app/routes/            one router per surface
docs/                  scope and the verify-before-demo list
tests/                 297 tests
.github/workflows/     pytest on 3.11 and 3.12
Dockerfile, fly.toml   deploy; see docs/DEPLOY.md
scripts/make_icons.py  regenerates the app icons
```

## The team

Bridge is a capstone project built by a team of fellows in the Fair Chance
Futures AI Lab, 2026. Fair Chance Futures, formerly Justice Through Code, is a
nonprofit affiliated with Columbia University.

Research, design and implementation are the team's shared work. The
practitioner interview cited throughout is with Brianne Cornish of FinEquity,
used with her permission.

Bridge is an independent project. It is not affiliated with, endorsed by, or
operated by the New York State Department of Corrections and Community
Supervision or any correctional facility.
