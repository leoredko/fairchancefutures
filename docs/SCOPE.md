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
| Real authentication | The surface split is the interesting control. Login is a solved problem and adds nothing to the demo. |
| Statutory citations | Nothing has been checked against a primary source. See VERIFY.md. |
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
