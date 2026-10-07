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
| D. Marsh, not yet triaged | DIN `28-A-0931` | tablet, a spare person who has not chosen a path. Not part of the five-minute run: that is Armando, below |
| A. Torres (Armando), nothing done yet | DIN `28-E-3306` or NYSID `00000066G` | tablet, and the open one: see [Armando Torres, the journey from the front](#armando-torres-the-journey-from-the-front) |
| Denise, helping Marcus | code `BRIDGE-4417` | phone |
| Rosa, helping M. Alvarez | code `BRIDGE-8802` | phone |
| D. Reyes, coordinator | nothing, the vendor system already signed them in | desktop |

Everyone picks their own PIN the first time. Six digits, not all the same, not
a run, and not a stretch of their own number.

## Demo shortcuts

- **Sign-in link with the DIN filled in.** `/signin?identifier=28-E-3306` opens
  the tablet sign-in with Armando's DIN already in the box. It fills the
  identifier and nothing else: the PIN is still his to choose, and no PIN is
  seeded.
- **Armando's reports are already there.** His three confirmed reports are in
  the seed, so nothing needs loading before a five-minute run. **Start over**
  puts them back, because they are part of the day the seed describes.
- **Sample reports for anybody else.** On `/demo/restart`, **Load sample reports for ...** puts
  three confirmed files on a person's case so **My reports** has something to
  open without waiting for paper. It is a demo control and not the product: in
  the product a report reaches the person only after a coordinator has
  confirmed it. Pressing it twice does not stack a second set, and **Start
  over** takes them away again for anybody who was not seeded with them.

## A walkthrough that shows the whole thing

Short on time? Use [the five-minute showcase run](#the-five-minute-showcase-run).
The course is the part of the product that matters most and the part that needs
no setup: sign in on the tablet with any DIN starting 28 and open **Learn**.

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

## Armando Torres, the journey from the front

Everyone else in the seed is partway through a story. Armando starts at the
beginning, so the whole route can be walked live: DIN `28-E-3306`, Fishkill,
releasing in about 140 days. There is no path, no intake and no
helper signed up, and none of the three vital documents is on file. His three credit reports are already on the case (see **Demo shortcuts**), so **My reports** opens the moment he asks. The Social
Security card deadline (120 days before release) is about 20 days ahead, so it
reads as something to act on rather than something already missed. The helper
code `BRIDGE-3306` is issued and not yet used.

1. **Tablet.** Sign in, choose a PIN, pick a path, read the documents lesson.
   **Your case** shows a **Your papers** card with all three documents as
   "Not yet", so the tablet alone tells the story in five minutes. It only
   reads status.
2. **Coordinator.** `/staff/a-torres` shows all three documents as needed and
   what is blocking the ID application. **Mark ... on file** records each one
   with Ms. Reyes's name and the date, and the timeline picks it up. Only the
   coordinator can do this, because the tablet cannot take delivery of paper.
   Marking one flips the card on the tablet on the next load.
3. **Coordinator.** Run triage.
4. **Post the request, with proof.** On the phone, enter `BRIDGE-3306`, sign
   the scoped form and open **Print the packet**. The packet says to send it
   certified, with a return receipt, and says plainly who pays: whoever posts
   it, and from inside that is the person's own account, because DOCCS will not
   advance the money for certified service. **I mailed it** takes the tracking
   number from the receipt. On the tablet, **Your case** now has an **In the
   mail** card with the number and where it is. Leave the number empty and the
   card says there is no way to prove it went. The status behind it is a
   stand-in, not USPS: see `SIMPLIFICATIONS`.
5. **Get the credit report onto the file.** There are two routes, and the demo
   should show both, because not everybody has someone outside to help. The
   report itself is mailed to the person at the facility, who takes the paper
   to the coordinator.
   - **With a helper.** On the phone, send the report in (a PDF, typed, or
     photographed). It stays invisible to Armando until the coordinator
     confirms it.
   - **With no one outside.** Armando carries the paper to Ms. Reyes, who uses
     **Scan a report in** at her desk. She is reading the paper as she types, so
     it is visible to Armando straight away. Nobody outside is needed for any
     of this, and nothing about the route is lesser.
6. **Tablet.** **My reports** walks the report, section by section.
7. **Coordinator.** Flag an item, draft the dispute letters and approve them.
   One item makes three letters, so the **Posting the approved letters** card
   has three rows, one per bureau, each with its own envelope and its own
   tracking number. There are two routes, and the demo shows both:
   - **Handed to the coordinator.** Press **Handed to me** and the day is
     recorded with Ms. Reyes's name. The tablet says "Ms. Reyes has it and will
     post it". When it goes in the post, press **Mailed** with the day and the
     number from the receipt, which is the second step.
   - **Mailed directly.** On the phone, **Open the letters** shows the approved
     letters. **I mailed it** takes the day and the receipt number, with no
     hand-in. A day cannot be in the future.
8. **Tablet.** **In the mail** now has a row per letter, from handed in to
   mailed, with the number. The status is the stand-in described above.

**Starting over:** `/demo/restart`, pick A. Torres.

## The five-minute showcase run

The showcase ends on a live walkthrough of Armando Torres, DIN `28-E-3306`, on
the deployed `bridge-fcf` service. It is the same app and the same screens as
[the journey above](#armando-torres-the-journey-from-the-front), cut down to
what fits in five minutes. This describes what the app does and in what order.

**Before the room arrives**

1. Open `/demo/restart`, pick A. Torres and restart him. He is the one seeded
   person with nothing done, so the first screen is the point. Do it
   beforehand, not in front of people: the restart clears his PIN, course
   progress, helper standing and anything mailed.
2. Sign in once yourself to check it works. Nobody's PIN is seeded, so the
   first sign-in asks you to choose one. A free instance that has slept
   reseeds, which clears the PIN again, so check within the hour, and restart
   him once more afterwards.
3. The deployed sign-in does not ask the arithmetic question (`BRIDGE_CAPTCHA`
   is `off` in `render.yaml` for the showcase). Set it to `1` to bring it back
   if the link starts to attract scripts.
4. The deployed landing page shows the tablet door only (`BRIDGE_TABLET_ONLY`
   is on). The other two surfaces are reachable by URL, `/helper` and `/staff`,
   and are not toured unless you choose the optional ending below.

5. **If the link goes to the room.** `render.yaml` already sets `BRIDGE_PRACTICE=on`, so everybody
   who opens it gets their own practice number already typed in and their own
   case with the three reports on it, so nobody shares your Armando and nobody
   is sent to a demo control. It also generates `BRIDGE_DESK_KEY`, so only you can
   reach `/staff`, `/demo` and `/metrics`: copy the key from the service's
   Environment tab in Render and type it once at `/staff`. Sign in as Armando yourself
   before you share the link: the first person to sign in with a number sets
   its PIN, and his number is in this file.

**The walkthrough**

1. **Choose a path.** After the PIN, Armando is asked what to do first, in two
   sentences. Pick **Learn how credit works**. The switch to change it is in
   the header of every tablet screen. Switch the language once, to show the
   Spanish is the same product and not a different one.
2. **Learn about credit.** The course opens on *The three pieces of paper*,
   because he releases in about 140 days. The Social Security card deadline is
   120 days before release, so it is about 20 days ahead and reads as
   something to act on. Say the two 120-day clocks out loud: this one is
   before release, the ID expiry is after. Open one lesson and let it save
   where you stop.
3. **See the case status.** **Your case** in the header. It reads "People are
   working on this while you wait", shows **Your papers** with all three
   documents as "Not yet", says his reports have not arrived, and names Ms.
   Reyes as handling it through the program because nobody outside is
   authorized yet. "Not yet triaged" is where a coordinator has to do human
   review. It is not a failed automated step.

**Optional ending, if the room has a second screen**

4. **A paper arrives.** In a window the room does not see, open `/staff/a-torres`
   and press **Mark birth certificate on file**. Reload **Your case**: one row
   flips, with Ms. Reyes's name and the day.
5. **Proof that it was sent.** On a phone or private window, `/helper` with
   code `BRIDGE-3306`, sign the form, **Print the packet**, **I mailed it**
   with a made-up tracking number. **Your case** now has **In the mail**. Say
   plainly that the status is a stand-in until live carrier tracking is
   connected.

If he is already past the first choice, follow the live state. If the app
stalls, play the recording and keep talking.

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

## Three windows, one caseload

The tablet (`/signin`), the helper's phone (`/family`) and the coordinator's desk
(`/staff`) all read the same case, so a client the coordinator adds appears on the
tablet. The coordinator needs no sign-in. The tablet and the helper keep their
session in a cookie, and one browser holds one session, so signing in as the helper
signs the tablet out. For a walkthrough that crosses roles, give the tablet and the
helper each their own browser profile or a private window.

## Starting over

Open `/demo/restart`, linked
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
