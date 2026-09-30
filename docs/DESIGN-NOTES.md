# Design notes

The rationale that used to render inside the product. Annotations on a live
screen are what make an application look like a prototype, so they live here.
Each one is a decision somebody will eventually ask about.

These are principles, stated on their own authority. An earlier version of this
file argued each one against a wireframe deck that the product started from.
That deck has been deleted: it stopped describing the product some time ago,
and a design that has to be justified as a diff against a sketch is a design
nobody can argue with on the merits.

## Inside, on the tablet

**The course is the product, not a feature of it.** Everything else on this
surface runs on somebody else's schedule. A letter takes six weeks. A bureau
takes thirty days. A coordinator has thirty other people. The course is the one
thing that moves when the person moves it, is available on every screen, and
keeps working after they go home. It is reachable from every screen and never
gated behind intake.

**Progress saves per card, not per lesson.** A tablet session ends when
movement is called, the battery dies, or the tablet gets set down. Losing four screens
of reading to that is how a person decides an app is not worth starting.
Furthest card reached rather than latest, so paging back to re-read costs
nothing.

**Nothing is ever marked wrong.** The check question at the end of a lesson
exists to make somebody commit to an answer before they read the explanation,
because that is what makes the explanation stick. A verdict, delivered where other
people can read the screen, teaches people to stop answering.

**One question per screen.** Facility tablets are slow, and reading happens in
short bursts. A six-field form is six chances to lose the session.

**Position, never points.** Score shaming is a known engagement killer, so the
client sees where they are on a road rather than a number they can feel bad
about.

**Every event carries a person's name and a real date.** From the Cornish
interview: automated nudges arrive on the same channels scammers use, so a
message with no human attached reads as fraud. Seeing named people do real work
on your behalf is the opposite of a silent app asking to be trusted.

**The report arriving is a moment, not a row.** It is the first time in years
anybody has told this person the truth about their own financial record. It
interrupts, it names who got it here, and it is read one section at a time with
the teaching attached to their own data. A lesson read cold is homework; the
same lesson attached to a line on your own report is the best teaching moment
this product will ever get.

**The person answers the question that opens the clock.** Whether they
recognise every item on their report is the one field with a statutory
consequence, and they are the only human alive who knows the answer. It used to
be answered on the staff form because the tablet could not show a report. It
can now.

**No file upload and no identity verification.** Both are physically impossible
from inside. They are not hidden, they are absent, and `app/surfaces.py`
refuses them server-side.

**Nothing on this screen tells anybody to install anything.** The destination
is an app provisioned onto the tablet. A product that depends on somebody
inside being handed a URL and tapping Add to Home Screen does not get used.

**The name is on the case screen.** A counselor entered these details, not the
person reading them, so seeing your own name is how you confirm they got it
right before anything is sent anywhere in it.

## Family, on a phone

**Rule out the scam in the first ten seconds.** The invitation leads with what
will never be asked for: SSN, bank login, card, money, access to their own
credit. Trust has to be earned before there is a second screen.

**One task on screen at a time.** A helper with a to-do list of six items does
none of them. Long silences between tasks are the design, not a gap.

**Never asked to read or judge the report.** Their part is the mail.

## Caseworker, on a desktop

**A work queue, not a roster.** Nothing sorts by name. The only ordering that
matters is what expires first.

**They see the file they already hold.** The coordinator requests the birth
certificate, holds the sentence and commitment paperwork, and has the vital
documents packet in their own folder. Hiding a Social Security number from
somebody who is already holding it is not protection, it is performance.

**The boundary that is real is physical.** The tablet is issued to one person,
so nobody inherits their session, but it is read in common areas with other
people in line of sight and the facility administers the device, and a helper
was promised they would never be asked to handle these fields. So
`app/redaction.py` is strict for the tablet and the phone and empty for the
desk. Two separate protections survive that: a scanned report stays truncated
because that is how the document arrived, and the printed letter leaves the
number blank for a pen because the envelope travels through the helper's hands.

**The client's own words lead.** What somebody flagged reading their own report
is the one thing on the client page nobody else could have supplied, so it sits
at the top as a claim to check against the paper rather than in a footnote.

**The classifier is the measurable part.** Everything else is letters and
lists. It is the only piece whose output can be scored, which is what makes it
defensible. Measure how often the reviewer edits before approving; reporting
that honestly is the DoNotPay lesson.

## The documents, and why there is no ladder

An earlier design had a four-rung access ladder: try the cheapest request
first, climb a rung each time a bureau pushed back. It was removed because it
modelled what a bureau would demand, and nobody publishes that. No source says
how often a plain signed request clears, and Experian asks for an ID copy with
every mailed dispute as standard, which suggests the first rung was fiction for
at least one of the three.

What a person has in their file is knowable. The coordinator already tracks it,
reviews it quarterly, and works to a real deadline: the Social Security card
application goes in at 120 days before release, and the birth certificate and
the card both have to be on file before the ID application can be submitted at
all. Same shape of decision, grounded in something checkable.

Never make everyone pay the cost of the hardest case still holds. It is just
attached to something true now.

## What this is built toward

A progressive web app provisioned onto a facility tablet, not a website
somebody finds. The browser build is how it is developed and shown.

The gap between here and that, roughly in order: `app/store.py` is a JSON file
rewritten whole on every write and has to become a database; the case plan
integration is three simulated functions; encryption, audit logging and
retention are assumed away, and for something holding Social Security numbers
those are most of the work rather than a footnote.
