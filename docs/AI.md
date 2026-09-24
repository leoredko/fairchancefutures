# Where the model fits

Bridge currently contains no AI. Not a little, none. Every state in the product
is produced by rules a person could follow on paper: the four triage states are
a decision table in `app/triage.py`, the letters are templates in
`app/letters.py`, the course is hand written, and `app/scores.py` exists
specifically to refuse to show a number.

That is not an oversight and it is not a placeholder. It is the honest state of
the build, and this document says where a model belongs, what it would be given,
what it would return, who checks it, and what it must never be allowed to do.
It is a specification. Nothing here is implemented, and no dependency on a model
provider is in `requirements.txt`.

## The one job worth giving a model

**Reading a credit report that arrived as a picture, and turning it into
fields.**

This is the piece `docs/SCOPE.md` calls the genuinely hard engineering problem
and lists as out of scope. It is out of scope because the fallback works: the
coordinator types the accounts in. That fallback is also the reason the model
can be added safely, because it means there is already a human doing this job
correctly, and the model is proposing work to somebody who was going to do it
anyway.

Look at what that costs today. `app/report.py` orders the four inbound routes
best first, and the ordering is about human effort: a PDF costs the helper one
tap, typed data costs them twenty minutes, and a photograph costs the
*coordinator* an afternoon, which is why it is offered last. A coordinator runs
thirty clients. Three bureaus each. Transcribing photographed reports by hand is
the single largest block of coordinator time in the product, and it is the one
task in the whole system that is pure transcription with a correct answer.

## What it is given

One inbound report, as images or a PDF, plus the bureau it came from.

    input       the pages already in CreditReport.pages
    bureau      "Equifax" | "Experian" | "TransUnion"

Nothing else. Not the client's case file, not their intake answers, not their
triage state, not the course progress. The model is reading a document, not
forming a view about a person, and giving it the case file would let it fill a
gap with something plausible from elsewhere in the record instead of leaving the
gap empty. An empty field is a coordinator typing one line. A confidently wrong
field is a dispute letter about somebody else's account.

## What it returns

The fields already on `CreditReport` and `Account` in `app/report.py`, and
nothing invented alongside them:

    consumer_name, date_of_birth, addresses[]
    accounts[]      creditor, number, opened, status, balance
    inquiries[], public_records[]

Constrained to that schema rather than parsed out of prose, so a malformed
response is a rejected request instead of a field that silently reads wrong.
Every field also carries where on the page it was read from, so the coordinator
confirming it is looking at the same line rather than taking the model's word.

Two rules on the way out, both already in the codebase:

- **The Social Security number is masked on the way in.** `mask_ssn` runs on
  whatever the model returns, the same as it runs on whatever a coordinator
  types. Two locks on the same door. The report arrives truncated in the first
  place under 15 U.S.C. 1681g(a)(1)(A), and neither lock trusts the other.
- **A field the model could not read comes back empty.** Never a guess, never a
  nearby value, never a reconstructed account number. Empty is the correct
  answer to an unreadable line and it costs a coordinator one keystroke.

## The decision logic

There is none. That is the point, and it is the honest answer to "where does the
AI fit" rather than a hedge.

The model proposes fields. It does not decide whether an account is an error, it
does not decide the triage state, it does not decide whether a letter goes out,
and it does not decide what the person sees. A coordinator confirms every field
before any of that happens, and the confirmation is the same screen they already
use for a typed report.

This is not a gate bolted on for the model. It is a rule the product already
enforces for every inbound route: nothing arriving from outside is visible to
the person until a coordinator has confirmed it. `SELF_CONFIRMING` in
`app/report.py` is that rule in code, and it holds exactly two routes, both of
which are a coordinator reading the paper as they type. A model reading a
photograph is not one of them and never becomes one. It lands with
`confirmed=False`, on the coordinator's desk, saying so.

So the model changes how long the transcription takes. It changes nothing about
who is accountable for it.

## What it must never do

- **Never draft or edit a dispute letter.** `app/letters.py` says it plainly: a
  letter going to a bureau under a client's signature is not a place for a
  model. The letters are templates because a template is reviewable, and the
  edit rate on `/metrics` is a real accuracy measure precisely because the
  baseline is fixed.
- **Never decide a triage state.** Six answers in, one of four states out, with
  the path attached. It is the only screen whose output can be scored for
  accuracy, and it is deterministic. Putting a model there would trade the one
  thing in the product that can be audited for nothing.
- **Never write a lesson or a fact.** Every card that states a rule cites a key
  in `app/sources.py`, and a test fails if it cites one that is not there. A
  model cannot produce a primary source with a check date, and a generated
  sentence that reads like law is worse than no sentence.
- **Never score or judge the person.** Not a risk score, not an engagement
  score, not a readiness number. `app/scores.py` refuses to show a number even
  for real FICO scores, with sources, because a number without its model, bureau
  and date attached is a guess that feels precise. A number the app invented
  about somebody's behavior is that, minus the sources.
- **Never reach the tablet.** Nothing about this surfaces to the person inside.
  They see a confirmed report, the same as they do now.

## Failure modes, and what each one costs

| Failure | What happens | Who catches it |
| --- | --- | --- |
| Misread account number | Confirmed against the page by the coordinator | Coordinator, before save |
| Missed account entirely | Coordinator adds it, same as today | Coordinator, reading the page |
| Hallucinated account | The confirmation screen shows the page region it claims to come from, and there is nothing there | Coordinator |
| Unreadable page | Fields come back empty, route falls back to typing | Nobody needs to, it is the current behavior |
| Model unavailable | Route falls back to typing | Nobody, the product works |

Every row ends in the system it already has. That is the test of whether a model
belongs in a product like this one: take it away mid sentence and nothing
breaks, because the thing it replaced is still there.

## Model, and what it costs to run

Claude Opus 5 (`claude-opus-5`), through the official Anthropic Python SDK, with
the response constrained to the schema above.

A rough figure, because a demo audience will ask and a made up number is worse
than an estimate with its arithmetic shown. Call it ten pages per bureau at
roughly 1,500 input tokens per page image, so about 15,000 input tokens, and
perhaps 3,000 output tokens of structured fields. At $5 per million in and $25
per million out that is around 15 cents per bureau, so roughly 45 cents for the
three reports a case needs. Against an afternoon of coordinator time on the
photograph route.

Both halves of that need measuring before anybody says them out loud: the token
count with `count_tokens` against a real scanned report, and the coordinator
time against an actual coordinator. Neither has been done.

## How you would know it works

The instrument already exists and it is the right one. `/metrics` tracks the
rate at which a coordinator edits a drafted letter before approving it, as an
accuracy measure on the output side. The same measure works on the input side:
**the rate at which a coordinator changes a field the model proposed.**

That is a real eval, on real documents, scored by the person who would have
typed the field anyway, with no extra work asked of anybody. If the edit rate is
high the model is not helping. If it is near zero, check that coordinators are
actually reading rather than clicking through, because a confirmation nobody
performs is worse than no model at all.

## What this does not answer

Personalizing which lesson comes next is the other place a model could
plausibly go, and it is deliberately left out of this spec. The course is
eleven lessons in a deliberate order, and until there is evidence that the order
is wrong for somebody, a model rearranging it is a feature looking for a
problem. Revisit it when there is course completion data from real users.
