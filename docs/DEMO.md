# Driving it

Sign-ins for the seeded caseload. These are not shown in the application,
because seeded logins on a landing page make a product look like a sample.

## The coordinator never signs in

The staff app opens straight on the caseload queue. A coordinator is already
authenticated by the vendor case plan system that Bridge opens inside, so
there is no staff ID, no PIN and no enrolment. To try a different coordinator,
send an `X-Vendor-Coordinator` header to the server build.

The other two surfaces do authenticate, because there is nowhere else they
could have: a person on a facility tablet has no other system to be signed in
to, and a helper on their phone has no institutional identity at all.

## Any DIN starting 28 works

2028 has not happened, so a DIN in that range cannot belong to a real person in
the public DOCCS lookup. Type any one of them into the tablet app and a case
opens on the spot, with a PIN you choose.

    28-A-1187      28-Q-7788      28-K-0001      any 28-?-####

Anything outside that range is never auto-created, because it could be somebody
real. Those are added by a coordinator from **New intake**.

## Showing that the course reorders itself

A DIN carries a release date, and the course reads it. Somebody near the gate
opens on the documents lesson, because the Social Security card deadline at 120
days before release is the one thing they can act on today. Somebody years out
opens on what a credit report is, because leading a person with five years left
on a deadline that is not theirs yet says this product is not for them. Nothing
is hidden either way: the full list is open from the first screen.

Four numbers that land in different places, so the difference can be shown on
purpose rather than hoped for:

| Type this | Releases in | Opens on | Shows |
| --- | --- | --- | --- |
| `28-B-1111` | about 68 days | The three pieces of paper | Inside the 120-day window. The Social Security card deadline has already passed and the screen says so. |
| `28-B-1000` | about 257 days | The three pieces of paper | Near the gate, deadline still ahead |
| `28-K-1000` | about 2.4 years | What a credit report actually is | The documents lesson steps aside |
| `28-A-1111` | about 4.2 years | What a credit report actually is | Longest runway, and the course is the whole point |

The day count is stable because the dates are derived from the DIN, so these
stay true whenever you run the demo. `tests/test_access.py` checks it, so the
table cannot quietly stop being true.

`app/doccs.py` invents these dates. It is one function, marked as the one a
real integration replaces, and DOCCS publishes no API, so a real version is a
data agreement or a scraper rather than a coding job.

## The seeded caseload

| Who | Signs in with | Where |
| --- | --- | --- |
| Marcus W. | DIN `28-A-1187` or NYSID `00000011L` | tablet |
| M. Alvarez | DIN `28-B-0042` | tablet |
| J. Whitfield, not yet triaged | DIN `28-A-0931` | tablet, and the one seeded person who has not chosen a path, so he is who to sign in as to show the first screen |
| Denise, helping Marcus | code `BRIDGE-4417` | phone |
| Rosa, helping M. Alvarez | code `BRIDGE-8802` | phone |
| D. Reyes, coordinator | nothing, the vendor system already signed them in | desktop |

Everyone picks their own PIN the first time. Six digits, not all the same, not
a run, and not a stretch of their own number.

## A walkthrough that shows the whole thing

Start with the course if you only have five minutes. It is the part of the
product that matters most and the part that needs no setup: sign in on the
tablet with any DIN starting 28 and open **Learn**.

1. **Coordinator** opens the staff app. There is no sign-in: it opens on the
   queue, because they are already signed in to the vendor case plan system.
   Use **New intake** to add somebody, and note the helper code it issues.
2. **That person** opens the tablet app, signs in with the DIN just entered,
   picks a PIN, and is asked what they want to do first. Both answers are
   worth showing: **Learn how credit works** opens the course and never
   mentions the questions again, and **Work on my credit** starts intake.
   The switch is in the header of every screen, so a room can watch
   somebody change their mind. Pick the credit path and answer the intake
   questions to carry on with this walkthrough.
3. **Coordinator** opens them from the queue and runs triage. The intake
   answers, one of four states, with the path attached. Errors jump the queue.
4. **Coordinator** drafts the dispute letters. One flagged item produces three
   letters, one per bureau. Edit one before approving and watch the edit rate
   on `/metrics` move.
5. **Helper** opens the phone app with the code, agrees to the scoped
   authorization, and prints the packet. The prisoner ID is on the envelope
   instructions, which is what the bureaus ask for on mail from a facility.
6. **That person** opens **My reports** on the tablet. The report announces
   itself and names who got it here, then walks section by section with the
   teaching attached, ending on "does anything on here look wrong to you". Tick
   an item that is not theirs.
7. **Coordinator** reloads the client page. What the person flagged is at the
   top, as a claim to check against the paper rather than a dispute already in
   flight.
8. **That person** works through a lesson or two from **Learn**, signs out
   mid-lesson, and signs back in. It opens on the screen they left.
9. **That person** cancels the authorization from the tablet. The helper loses
   access on their next tap.

Close every tab and reopen them. Everything is still there.

## Showing the tablet on its own

Some rooms only get the tablet. Set `BRIDGE_TABLET_ONLY=on` and the helper and
coordinator doors come off the landing page and off the sign-in screen, so
there is nothing on a projector to click into by accident.

    BRIDGE_TABLET_ONLY=on ./run.sh

It hides doors, not people. The coordinator is still named on the case screen
and the helper is still named where the tablet explains who sends what, because
an event with nobody attached reads as an automated nudge and that reads as a
scam inside.

Both routes stay reachable by URL. Open `/staff` in a window the room does not
see, run triage, draft the letters, and the tablet in front of them shows the
result, which is the point: the walkthrough above still works with one screen
facing the audience. It is a presentation setting and not a permission, so it
is not in `app/surfaces.py`: what a surface can do is enforced there, and a
second copy of that in an environment variable would be a weaker one.

The single-file build needs no switch. `standalone/build.py` already emits one
application per surface, so opening `bridge-inside.html` on its own is the same
thing: it has only the tablet door and no way to reach the other two.

## Three files, one caseload

`standalone/bridge-inside.html`, `bridge-family.html` and `bridge-staff.html`
are three separate applications, the way they would be deployed separately in
the real thing. Served from the same folder or the same host they share one
caseload, so a client the coordinator adds appears on the tablet. Each keeps
its own session, so signing in on one does not sign you out of another.

Published to three different origins they cannot see each other. For a
walkthrough that crosses roles, open all three from one folder or run the
server app.

## Starting over

**The served app, including the deployed one:** open `/demo/restart`, linked
from the bottom of the home page. Pick a person and they go back to the day
the seed describes: the PIN they set is cleared so the next sign-in enrolls a
new one, and the intake answers, course progress, report notes and drafted
letters go with it. Their seeded reports come back, so Marcus has his three
files and their disagreement again.

One person at a time, on purpose. Two people are usually on the URL at once
and rewinding the one who wandered off should not take the other one with
them. It is reachable signed out, because a forgotten PIN is the usual reason
to be there and the PIN is the thing being cleared.

It is a demo control and it is labelled as one on the screen. A real case file
holds a coordinator's work and a person cannot erase it from their tablet,
which is why this is not in the capability table in `app/surfaces.py`.

**The single-file build:** clear the site data for the page, or run
`localStorage.clear()` in the browser console. The seeded caseload comes back
on the next load.
