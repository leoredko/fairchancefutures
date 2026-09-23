# Scope

## Build order, from the deck

1. **Triage.** Six answers in, one of four states out, with the path attached.
   The only screen where the app does something a person could not do on paper,
   and the only one whose output can be scored for accuracy. — built
2. **Intake, the six questions (tablet).** — built
3. **Letter draft and approval (desktop).** — built
4. **Family task screen and report upload.** — built, minus photo-to-text
5. **Case status timeline (tablet).** — built

Each one works standing alone. Stop anywhere and there is still a demo.

## Three roles, three surfaces

Who can do what is set by physics and law, not by preference. That is what
splits the app, and `/roles` renders it straight from the capability table so
the slide cannot drift from the code.

**Inside, facility tablet.** Can answer intake, learn, see status, approve what
is said about them, cancel a helper. Cannot verify identity, receive mail,
upload files, open accounts, browse the open web. Offline-first, metered by the
minute, one question per screen.

**Family or friend, phone.** Can receive mail, photograph the report, print and
mail letters, take a call. Cannot act without a signed, scoped authorization.
Never asked to read or judge the report. One task on screen at a time, long
silences between tasks, by design.

**Caseworker, desktop.** Can triage, read the report, approve letters, hold the
deadline, run thirty clients at once. Cannot see more of the file than consent
covers, locked by default rather than by policy memo. Work queue sorted by what
expires first, never a roster.

## Out of scope, and why

| Thing | Why not |
| --- | --- |
| Photo-to-text extraction | The genuinely hard engineering piece. The deck named the fallback and the fallback is what is built. Nothing else depends on it. |
| Referrals and outcomes | Static in the deck, static here. |
| Account creation | There is no self-serve signup. Accounts are seeded, which is right: a person does not enrol themselves into a caseload, a counselor adds them. |
| Password reset by email | Nobody inside has email. A counselor clears the PIN and the client sets a new one at the kiosk. |
| Real offline support | The deck's "nothing is lost if you lose access for a week" is not kept. Writes go to the server. IndexedDB plus replay is the real fix. |
| Spanish | The deck showed an EN / ES toggle. Removed rather than shipped as decoration over an English-only app. |
| Encryption, audit logging, retention policy | Assumed away with the rest of the compliance regime, for class. Named on the home page rather than hidden. |

## Assumed away, with the instructors' sign-off

Facility and DOC approval, incumbent tablet vendor access, bureau data
agreements, funding for the counselor role, and the PII compliance regime a real
deployment would sit under.

Say this on a slide rather than hoping nobody asks.

## Not assumed away

A person inside cannot verify identity online, and a helper outside has no
standing without a signed form. Those two shape the product, and no waiver makes
them disappear. They are `app/surfaces.py` and `app/authorization.py`, and
`tests/test_constraints.py` fails if either quietly stops being true.

## Integrating with the Offender Case Plan

Researched 2026-09-23. New York already keeps the record Bridge would otherwise
duplicate, so Bridge is one domain inside it rather than a second system.

At the initial interview an **Offender Rehabilitation Coordinator** establishes
a program plan of goals and tasks. That plan follows the person through
incarceration and out into community supervision, and the ORC reviews it at
**scheduled quarterly reviews**. It was the Transitional Accountability Plan and
is now the **Offender Case Plan**. Reentry planning intensifies in the **six
months before release**, which is the same window in which a credit file can
realistically be moved, and the same window the team's problem statement names.

Two consequences, both of which made the product better:

**Vital documents.** Reentry staff already assemble Social Security cards,
birth certificates and non-driver ID, and the state can request a birth
certificate at no cost using sentence and commitment paperwork. Since October
2020 a free non-driver ID is available to people receiving public assistance,
SNAP or Medicaid. That packet is exactly what **rung 2 of the access ladder**
asks for. When the plan says the documents are on file, rung 2 stops being a
wall.

**Cadence.** Bridge reports progress on the ORC's quarterly review schedule
rather than inventing one, and shows how many reviews are left before release,
because that is the deadline a coordinator actually works to.

`app/caseplan.py` holds the integration. Bridge writes only into the financial
domain; housing, employment, education and treatment belong to the coordinator,
and an app that started editing those would be a different and much worse idea.

Sources, all DOCCS: Legislative Report on Reentry Planning and Access to Social
Services; Transitional Services Program; Re-Entry Services; Parolee Lookup
glossary.

**Assumed, with the team's sign-off:** that DOCCS grants API access to the case
plan. Nothing calls a real endpoint. `simulated_plan()` is the only function a
real integration would replace.

**Not established:** the name of the software the plan lives in. A DOCCS URL
path suggests a Facility Population Management System, but nothing public
confirms what it is or whether it is the system of record, so the integration
is written against the *case plan* as an artifact rather than against a guessed
product name.
