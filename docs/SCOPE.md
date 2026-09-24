# Scope

## What is built

1. **The credit course (tablet).** Eleven lessons, about fifty minutes, always
   reachable from every screen, progress saved per card. Every card that states
   a rule cites a primary source. This is the first priority of the product and
   the part that keeps working after somebody goes home. — built
2. **Triage.** Six answers in, one of four states out, with the path attached.
   The only screen where the app does something a person could not do on paper,
   and the only one whose output can be scored for accuracy. — built
3. **Intake, the six questions (tablet).** — built
4. **The report arriving, and reading it (tablet).** The report announces
   itself, names who got it here, and is walked section by section with the
   teaching attached, ending on the question that opens the legal clock. — built
5. **Letter draft and approval (desktop).** — built
6. **Family task screen and report upload.** — built, minus photo-to-text
7. **Case status timeline (tablet).** — built

Each one works standing alone. Stop anywhere and there is still a demo.

## What an earlier design had that the product no longer does

**The four-rung access ladder is gone.** It modeled what a credit bureau would
demand and climbed a rung on each kickback. Nobody publishes how often the
cheapest route clears, and Experian asks for an ID copy with every mailed
dispute regardless, so the first rung may never have existed. It was replaced
by document readiness in `app/caseplan.py`, which is knowable, already tracked
quarterly by the coordinator, and carries a real deadline at 120 days before
release. See `app/authorization.py` for the full reasoning.

Bridge contains no AI today. [docs/AI.md](AI.md) says where a model would
fit if one were added, and why none of the other candidate places survive.

## Three roles, three surfaces

Who can do what is set by physics and law, not by preference. That is what
splits the app. `app/surfaces.py` is the capability table and the router asks
it before doing anything.

**Inside, facility tablet.** Can answer intake, work through the credit course,
read their own report and say what they do not recognize, see status, cancel a
helper. Cannot verify identity, receive mail, upload files, open accounts, or
browse the open web.

The tablet is **not offline**. Bridge is loaded onto it and reaches the
person's own record, which is why intake saves as it goes and the course keeps
a place. What it cannot reach is the open web, which is the part that matters:
every route a bureau offers a free citizen runs through a web page, and none of
them are reachable from this device. One question per screen, because a
session ends without warning.

**Family or friend, phone.** Can receive mail, send the report in (a PDF, typed
by hand, or photographed, offered in that order), print and mail letters, take a
call. Cannot act without a signed, scoped authorization.
Never asked to read or judge the report. One task on screen at a time, long
silences between tasks, by design.

**Caseworker, desktop.** Can triage, read the report, approve letters, hold the
deadline, run thirty clients at once. Sees the file they already hold: they
request the birth certificate, they hold the sentence and commitment paperwork,
and hiding a Social Security number from them protects nobody. The client's own
consent still narrows it, because that is the client's decision rather than a
constraint of the room. Work queue sorted by what
expires first, never a roster.

## Out of scope, and why

| Thing | Why not |
| --- | --- |
| Photo-to-text extraction | The genuinely hard engineering piece. The fallback is that the coordinator types it in, and that is what is built. Nothing else depends on it. This is the one place a model belongs, and [docs/AI.md](AI.md) specifies it: what it is given, what it returns, who confirms it, and what it is never allowed to do. |
| Referrals and outcomes | Never built past a sketch, and nothing depends on them. |
| Account creation | There is no self-serve signup. Accounts are seeded, which is right: a person does not enrol themselves into a caseload, a counselor adds them. |
| Password reset by email | Nobody inside has outside email. A counselor clears the PIN and the client sets a new one on their tablet. |
| Real offline support | The tablet reaches Bridge, so writes go to the server and save immediately. An earlier promise that "nothing is lost if you lose access for a week" was about a disconnected device, and it has been removed from the intake copy rather than left there untrue. If a facility turns out to have genuinely intermittent connectivity, IndexedDB plus replay is the real fix. |
| Spanish | An EN / ES toggle was drawn early and removed rather than shipped as decoration over an English-only app. For this population it is a real requirement rather than a nice-to-have, and it should come back as translation rather than as a pill. |
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

Nor is line of sight. The tablet is issued to one person, but it is read in
common areas with other people able to see the screen, and it is a vendor
device the facility administers, so a Social Security number, a full account
number and a date of birth never render on it. `app/redaction.py`
enforces that for the tablet and the helper's phone, and deliberately not for
the coordinator, who holds the file already.

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

**Vital documents, and the chain they form.** Reentry staff already assemble
Social Security cards, birth certificates and non-driver ID. The order matters
and it is strict: the birth certificate **and** the Social Security card must
both be on file **before** the non-driver ID application can be submitted at
all. The ORC prioritizes getting them and reviews each person's document status
**quarterly**. The Social Security card application goes in at **120 days
before release**.

Three things fall out of that, and all three are now in the product:

- The birth certificate is the one to chase first. It takes **ten weeks or
  more**, it gates everything downstream, and it has no deadline of its own,
  which is exactly why it gets left.
- The no-fee route runs on **New York** records. Somebody born in another state
  or country is not covered and needs to start earlier, which the app says
  rather than letting it be discovered late.
- There is a **second, different 120 days**: the release ID expires 120 days
  *after* release. Confusing the two costs somebody their ID, so the app names
  which one it means every time.

An earlier draft of this document claimed a free non-driver ID has been
available since October 2020 to people on public assistance, SNAP or Medicaid.
That could not be verified and has been removed. What the sources describe is a
DOCCS and DMV program established in 2022 that produces the ID before release.

**Scale, and the number worth putting on a slide.** About 3,700 IDs since 2022;
1,061 in the year to April 2026, down 15% on staffing shortages; and **493
people declined to engage** with the application in that same year. Roughly one
in three. That independently corroborates what Brianne Cornish told the team on
Sep 21: engagement is the unsolved problem, not the technology.

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
