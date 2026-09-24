# What happens after release

The hardest question asked of this product, and the one it does not yet answer.
This document says what Bridge can honestly claim today, what the evidence
actually says the problem is, and which of the plausible answers are ruled out
by evidence we already collected.

Nothing here adds a new fact. Every number and claim below is already in
`docs/VERIFY.md`, `app/sources.py` or `app/caseplan.py` with its source.

## The honest state

Bridge has three surfaces and none of them belongs to a person who has gone
home. The tablet stays in the facility. The helper's phone belongs to the
helper, and their authorization is scoped and expiring by design. The desktop
belongs to the coordinator. A person walks out of a facility and walks away
from every screen this product currently has.

That is the gap. It is not hidden in the code and it should not be hidden on a
slide.

## The problem is not the notification

The obvious answer is reminders: text them, email them, nudge them back. Two
pieces of evidence already in this repo say that is answering the wrong
question.

**The drop-off starts before release, not after.** In the year to April 2026,
DOCCS issued 1,061 pre-release IDs and **493 people declined to engage** with
the application at all. Roughly one in three, for a free state ID, offered by a
staffed human, to somebody sitting in front of them. Whatever causes that is
not a missing reminder, and it is already happening on the side of the gate
where Bridge does have a surface.

**A nudge is the wrong instrument for this population.** From the Cornish
interview, Sep 21: automated nudges arrive on the same channels scammers use,
so a text about connecting a bank account reads as fraud. That finding is
already load-bearing in the product. `docs/DESIGN-NOTES.md` requires every
timeline event to carry a person's name and a real date, for exactly this
reason. A retention strategy built on automated messaging would contradict the
one piece of primary practitioner evidence the team collected.

So the answer is not a better notification. It is a named human, or it is a
reason to come back that the person already cares about.

## The three things that actually survive release

**The case plan, which is the strongest answer.** The Offender Case Plan
follows the person through incarceration and out into community supervision,
and the Offender Rehabilitation Coordinator reviews it at scheduled quarterly
reviews. Bridge writes into the financial domain of that plan and reports on
its cadence rather than inventing one. That means the credit work does not end
at the gate because the plan does not end at the gate, and the person who asks
about it is somebody they have already met. This is a handoff to an existing
human on an existing schedule, which is the shape the evidence says works and
the opposite of an automated message.

It is also the honest limit of the claim: continuity exists because New York
already built it, not because Bridge built it.

**The statutory clock, which the product creates itself.** A dispute sent
before release starts a reinvestigation the bureau must complete within 30 days
of receiving it, extendable to 45 (15 U.S.C. 1681i(a)(1)). A dispute filed in
the last months inside lands its answer after release. That is a real reason to
come back, with a date attached and a specific outcome the person wants, which
is a better retention mechanism than any reminder because the person is the one
waiting.

**The course, with a caveat.** `docs/DESIGN-NOTES.md` already says the course is
the one thing that keeps working after somebody goes home. That is true of the
content and not yet true of the delivery: eleven lessons that live on a facility
tablet do not follow anybody anywhere. What makes this tractable rather than
hypothetical is that the account already exists and the person already set the
PIN themselves, because Bridge never seeds one. Nothing about the sign-in
assumes the facility. What is missing is a surface they can reach from outside,
and that is a build, not a redesign.

## What is ruled out, and why

| Answer | Why not |
| --- | --- |
| Push notifications and reminder texts | Reads as a scam to this population, per the Cornish interview. Contradicts the rule already enforced on the timeline. |
| Gamification, streaks, points | `docs/DESIGN-NOTES.md`: position, never points. Score shaming is a known engagement killer, and the product deliberately shows a road rather than a number. |
| A behavioral engagement score | `app/scores.py` refuses to show a number even for real FICO scores, with sources, because a number without its model and date is a guess that feels precise. |
| Lender matching at release | Out of scope, never built past a sketch. It is a partnership and a referral pathway, not a feature, and calling it a feature now would be the fourth thing on this list the product refuses. |

Every row is a refusal the product already makes for a stated reason. Retention
does not get to reopen them.

## The answer to give out loud

> Bridge does not solve post-release retention today, and the honest reason is
> that it has no surface a person keeps after they walk out. What it has is a
> handoff. The Offender Case Plan follows the person into community supervision
> and their coordinator reviews it quarterly, so the credit work continues
> inside a relationship that already exists. Our own evidence says the
> engagement problem starts before release, not after: one in three people
> declined a free state ID last year with a staffed human offering it. That is
> the number we would have to move, and a reminder text is not what moves it.

That answer is better than a roadmap slide because it is checkable, it names
the mechanism, and it does not promise a feature nobody has built.

## What would have to be built

Milestones, in the order they unlock each other. None of these is in scope for
the current demo and none should be described as if it is.

1. **A surface the person keeps.** The account and the PIN already work. What is
   missing is somewhere to sign in from outside a facility, and a decision about
   what it shows: almost certainly the course and the status of anything already
   in flight, and almost certainly not the full case file.
2. **The handoff made visible.** A person leaving should be able to see who now
   holds their case, on the plan, by name. `app/caseplan.py` already tracks the
   coordinator and the review cadence; what is missing is the transition itself.
3. **The clock as the reason to return.** A dispute answer that lands after
   release is the one piece of mail the product can promise, and it should be
   what the last screen inside points at.

## What we do not know

**We have no post-release retention data of our own, and no way to get any from
this build.** Everything above is reasoning from a practitioner interview and
one state agency's reporting. That is enough to rule things out and not enough
to claim a number.

**The direct user evidence is still missing.** The Cornish interview is expert
validation and it is not the same thing as hearing from the primary user, who
is the incarcerated person. A survey of people inside would be the evidence that
settles which of the three mechanisms above actually matters, and until somebody
runs one, this document is a set of defensible guesses with their reasoning
shown.
