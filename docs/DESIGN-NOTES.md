# Design notes

The rationale that used to render inside the product. Annotations on a live
screen are what make an application look like a wireframe, so they live here.
Each one is a decision somebody will eventually ask about.

## Inside, on the tablet

**One question per screen.** Facility tablets are slow, shared, and often
metered by the minute. A six-field form is six chances to lose the session.

**Position, never points.** Score shaming is a known engagement killer, so the
client sees where they are on a road rather than a number they can feel bad
about. Kept from Roshawn's v1.

**Every event carries a person's name and a real date.** From the Cornish
interview: automated nudges arrive on the same channels scammers use, so a
message with no human attached reads as fraud. Seeing named people do real work
on your behalf is the opposite of a silent app asking to be trusted.

**No file upload and no identity verification.** Both are physically impossible
from inside. They are not hidden, they are absent, and `app/surfaces.py`
refuses them server-side.

**The name is on the case screen.** On a shared tablet, seeing your own name is
how you know you are not looking at whoever used it before you.

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

**Staff see enough to act, never the whole file by default.** Enforced in
`app/redaction.py`, not by policy memo.

**The classifier is the actual product.** Everything else is letters and lists.
It is also the only piece whose output can be scored, which is what makes it
defensible. Measure how often the reviewer edits before approving; reporting
that honestly is the DoNotPay lesson.

## The access ladder

What a bureau asks for varies per person and cannot be known in advance, so the
app tries the cheapest rung first and climbs only on a kickback.

Never make everyone pay the cost of the hardest case. Forcing a notary trip on
somebody who would have cleared with a signature is how a tool gets abandoned
at step one. With no helper on file, rung 3 is skipped entirely: a power of
attorney with nobody to hold it is a trip for nothing.

## What the original wireframe got right, and what it did not

The eleven-screen deck in `design/` set the information architecture and most
of the copy, and both held up. Its palette did not: warm greys read as every
institutional form the audience has ever been handed. The application uses teal
for the things that move a case forward and amber for the things that need a
person.
