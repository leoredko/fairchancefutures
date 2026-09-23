# Bridge

Fair Chance Futures AI Lab 2026. Leo Redko.

A credit-repair workflow for people coming home, split across three surfaces
because the three people involved genuinely cannot do each other's jobs.

Built from the design deck in `design/`. Every screen in the deck that the deck
itself marked in scope is implemented and runnable.

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

## The file you can just open

`standalone/bridge.html` is the whole product in one file: no server, no
install, no network. Double-click it, email it, put it on a USB stick, or open
it on a tablet and use Add to Home Screen. Everything a person does stays in
that browser and is sent nowhere.

```bash
python3 standalone/build.py     # regenerate it after changing the app
```

It is generated, not hand-maintained. The four triage states, the letter
templates, the verified facts and the bureau addresses come straight out of the
Python modules, and `tests/test_standalone.py` fails if the two ever disagree.

The server app in `app/` is the real architecture: three surfaces, one shared
case, enforcement server-side. The single file is the same product with the
server folded into the page so it can be handed to somebody.

## Signing in

New York only, because the identifiers are.

| Surface | What you sign in with |
| --- | --- |
| Inside | A DIN (`28-A-1187`) or a NYSID (`00000011L`), then a PIN you choose |
| Family | The code printed on the letter that came in the mail, then a PIN |
| Staff | A staff ID, then a PIN |

Accounts are created by a counselor from **New intake** on the caseload queue,
which is the New intake tab on screen 07 of the deck. That creates the case
file, a sign-in for each number entered, and the helper code that goes on the
letter to whoever is helping from outside. No PIN is set at creation: a PIN a
counselor could choose would be a PIN a counselor knows.

Every seeded DIN starts `28`, meaning a 2028 intake, which has not happened
yet, so none of them can collide with a real person in the public DOCCS
lookup.

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

## The access ladder

What a bureau demands varies per person and cannot be known in advance, so the
app starts at the cheapest rung and climbs only on a kickback.

1. Plain request. A signature. For many people this is the whole story.
2. Identity documents, when a bureau cannot match the file.
3. Limited POA, notarized, only when the helper must act alone.
4. Program release, when there is no outside helper at all.

Never make everyone pay the cost of the hardest case. Forcing a notary trip on
someone who would have cleared with a signature is how a tool gets abandoned at
step one. With no helper on file, rung 3 is skipped entirely, because a power of
attorney with nobody to hold it is a trip for nothing.

## What the app actually does

| Surface | Route | What it is |
| --- | --- | --- |
| Inside, tablet | `/inside/{id}` | Six intake questions, one per screen, offline-first. Position not score. Case timeline with named people. Cancel a helper's authorization. |
| Family, phone | `/family/{id}` | The invitation that rules out everything a scam would ask for. Exactly one task on screen. Print the rung 1 packet. Add photos of the report. |
| Caseworker, desktop | `/staff` | Work queue sorted by what expires first. Triage session. Letter draft and approval. The access ladder. |
| — | `/roles` | Generated from the capability table, so the scope slide cannot drift from the code. |
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

## Running it on a tablet

`app/static/manifest.webmanifest` plus a registered service worker means the
inside surface installs to a tablet home screen and runs standalone, no browser
chrome. The worker caches nothing on purpose: see the note in `app/static/sw.js`
and in [docs/DEPLOY.md](docs/DEPLOY.md). The tablet app assumes connectivity.

## What is deliberately not built

- Photo-to-text extraction of a mailed report. The deck already named the
  fallback, the caseworker types it in, so that is what happens. Uploaded images
  are counted and discarded rather than stored, which also means this build
  never holds a picture of somebody's credit report on disk.
- Referrals and outcomes reporting.
- Real offline support. The deck promises "nothing is lost if you lose access
  for a week" and this build does not keep that promise: writes go straight to
  the server. Doing it properly is IndexedDB plus replay-on-reconnect.
- Spanish. The design deck showed an EN / ES toggle on six screens; it has been
  removed rather than shipped as decoration over an English-only app.
- Real auth. Anyone who can reach the URL is the surface named in the URL. The
  surface split is enforced, the identity behind it is not.

## Layout

```
app/surfaces.py        capability table, constraint one
app/authorization.py   scoped grants and the access ladder, constraint two
app/triage.py          the classifier
app/redaction.py       per-surface, per-field minimization
app/letters.py         templated letters and the edit-rate log
app/bureaus.py         the three bureaus, addresses, and where they came from
app/sources.py         every legal fact, its primary source, and the check date
app/identifiers.py     DIN and NYSID parsing
app/auth.py            PINs, lockout, signed sessions
app/session.py         who is asking, from the cookie rather than the URL
standalone/            the single openable file, and its build script
app/questions.py       the two question sets, and why they differ
app/store.py           JSON persistence and the seed caseload
app/routes/            one router per surface
design/                the source design deck, unpacked
docs/                  scope and the verify-before-demo list
tests/                 157 tests
.github/workflows/     pytest on 3.11 and 3.12
Dockerfile, fly.toml   deploy; see docs/DEPLOY.md
scripts/make_icons.py  regenerates the app icons
```
