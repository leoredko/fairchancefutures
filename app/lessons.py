"""The credit course, and where somebody has got to in it.

This is the part of Bridge a person uses most and the part that keeps working
after they go home. The case work happens on somebody else's schedule: a letter
takes six weeks, a bureau takes thirty days, a coordinator has thirty other
people. The course is the one thing that is available on every screen, moves
when they move it, and is theirs.

Three rules it is built on.

Always reachable. Not a step in a flow, not a thing that appears once after
intake and is gone. Every tablet screen carries a way in, and a lesson can be
opened at any point in a case, including before intake and long after the
dispute is settled.

Progress is saved per card, not per lesson. A session ends when movement is
called, the battery dies, or the tablet gets set down. Losing four screens of
reading because of that is how a person decides an app is not worth starting. Sign back in and the course opens exactly where it stopped.

Nothing here states a rule without a source. Every card that makes a legal or
numeric claim carries a key into `app.sources`, and `cited()` resolves it, so a
claim whose source got deleted fails a test rather than quietly turning into an
opinion on a screen.

On the check questions: they are not a test and nothing is scored. A wrong
answer shows the same explanation as a right one, because the explanation is
the teaching and the question is only there to make somebody commit to an
answer first, which is what makes the explanation stick.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.sources import FACTS


@dataclass(frozen=True)
class Card:
    """One screen inside a lesson. One idea, and the source it rests on."""

    title: str
    body: str
    fact_key: str = ""
    aside: str = ""

    @property
    def cited(self) -> str:
        """The source line, or empty for a card that states no rule."""
        if not self.fact_key:
            return ""
        fact = FACTS[self.fact_key]
        return f"{fact.source}, checked {fact.checked_on.isoformat()}"

    @property
    def source_url(self) -> str:
        return FACTS[self.fact_key].url if self.fact_key else ""


@dataclass(frozen=True)
class Choice:
    value: str
    label: str


@dataclass(frozen=True)
class Check:
    """The question at the end of a lesson.

    `answer` is the defensible one. It is not marked right or wrong on screen,
    because a person working through this between counts does not need a
    red cross in front of whoever is waiting for the tablet next.
    """

    prompt: str
    choices: tuple[Choice, ...]
    answer: str
    why: str


@dataclass(frozen=True)
class Lesson:
    slug: str
    title: str
    minutes: int
    hook: str
    cards: tuple[Card, ...]
    check: Check
    # Case states this lesson answers most directly. Used to pick what to
    # suggest next, never to hide anything: every lesson is open to everybody
    # from the day they sign in.
    urgent_for: tuple[str, ...] = ()
    # True when the lesson's urgency comes from a release date rather than
    # from the subject. The documents lesson is the only one: its deadline is
    # 120 days before release, so leading with it for somebody nine years out
    # tells them this product is not for them yet, which is both wrong and the
    # fastest way to lose them. It stays in the list and stays openable; it
    # just does not go first.
    release_dependent: bool = False

    @property
    def screens(self) -> int:
        """Cards plus the check. What the progress bar counts."""
        return len(self.cards) + 1


# The order is deliberate and it is not the order of a textbook. It starts with
# the thing that has a deadline attached this month, because a first lesson
# somebody can act on the same day is the only one that earns the second.
CURRICULUM: tuple[Lesson, ...] = (
    Lesson(
        slug="three-papers",
        title="The three pieces of paper",
        minutes=5,
        hook="Two documents decide whether you walk out with ID. One has a "
             "deadline near release; the other is worth starting years out.",
        urgent_for=("not_yet_triaged", "credit_invisible", "thin_file",
                    "damaged_file", "errors_present"),
        release_dependent=True,
        cards=(
            Card(
                title="Everything runs through your ID",
                body="A bank account, an apartment, a job, and every single "
                     "thing you will ever do with a credit bureau needs a "
                     "photo ID. And the ID itself needs two other documents "
                     "first. Get this chain wrong and nothing downstream of it "
                     "can start.",
                aside="If your date is years away, this lesson still has one "
                      "thing in it for you: the birth certificate. It has no "
                      "deadline, it takes ten weeks or more, and asking for it "
                      "early costs you nothing. The rest of this course does "
                      "not wait for a release date at all.",
            ),
            Card(
                title="Birth certificate and Social Security card, in that order of worry",
                body="Both have to be in your file before the non-driver ID "
                     "application can even be sent. Your coordinator is the "
                     "one who requests them, and they check where everyone's "
                     "documents stand every three months. The birth "
                     "certificate is the slow one. It can take ten weeks or "
                     "more to come back, so it is the one to ask about first.",
                fact_key="documents_gate_the_id",
            ),
            Card(
                title="120 days out, ask for the Social Security card",
                body="That is the mark. At 120 days before you go home, the "
                     "Social Security card application goes in. If you are "
                     "inside that window right now and nobody has raised it "
                     "with you, raise it with them. If you are years out, this "
                     "is the date to know about rather than the date to act "
                     "on, and it will come round.",
                fact_key="social_security_card_at_120_days",
                aside="Write the date down. It is the one deadline in this "
                      "whole course that is yours to chase rather than "
                      "somebody else's.",
            ),
            Card(
                title="The birth certificate is free, unless you were born somewhere else",
                body="When the department requests your birth certificate for "
                     "your release, there is no fee, and your sentence and "
                     "commitment paperwork counts as your permission, so you "
                     "do not have to sign anything separately. That covers New "
                     "York records only. Born in another state, or another "
                     "country, and none of that applies to you. Say so early, "
                     "because yours takes longer and costs money.",
                fact_key="birth_certificate_no_fee",
            ),
            Card(
                title="The other 120 days, which is not the same 120 days",
                body="After you are released, the DOCCS ID you walk out with "
                     "expires in 120 days. That is your window to get to a DMV "
                     "office and trade it for a real non-driver photo ID. Two "
                     "different 120-day clocks, one before the gate and one "
                     "after, and mixing them up is how people end up with no "
                     "ID at all.",
                fact_key="release_id_expires_at_120_days",
            ),
        ),
        check=Check(
            prompt="You are 130 days from release and have no birth "
                   "certificate on file. What is the most useful thing to do?",
            choices=(
                Choice("both", "Ask your coordinator about both documents now"),
                Choice("wait", "Wait until 120 days, then ask about both"),
                Choice("id", "Apply for the photo ID and sort the rest later"),
            ),
            answer="both",
            why="The birth certificate has no deadline attached, which is "
                "exactly why it gets left. It is also the slow one, ten weeks "
                "or more, and the ID application cannot be submitted without "
                "it. The 120-day mark is for the Social Security card. The "
                "birth certificate wants to be moving before that.",
        ),
    ),
    Lesson(
        slug="what-a-report-is",
        title="What a credit report actually is",
        minutes=4,
        hook="It is a file about you that you have never read, and there are "
             "rules about who gets to look at it.",
        urgent_for=("not_yet_triaged", "credit_invisible"),
        cards=(
            Card(
                title="It is a list, not a judgement",
                body="A credit report is a record of accounts in your name: "
                     "who you borrowed from, how much, whether you paid on "
                     "time, and whether anybody is chasing you for it. That is "
                     "it. It is closer to a bank statement than to a grade.",
            ),
            Card(
                title="There are three of them, and they disagree",
                body="Equifax, Experian and TransUnion each keep their own "
                     "file on you. Not every lender reports to all three, so "
                     "an account can sit on one report and be missing from "
                     "another. This is why anything we do, we do three times.",
            ),
            Card(
                title="Not everybody can just look you up",
                body="A report can only be handed out for a reason the law "
                     "lists: you applied for credit, an insurer is making a "
                     "decision, a court ordered it, child support enforcement, "
                     "or you told them in writing to release it. Somebody "
                     "being curious about you is not on that list.",
                fact_key="who_may_pull_a_report",
            ),
            Card(
                title="An employer needs your written permission",
                body="An employer has to tell you clearly and in writing that "
                     "they want to pull your credit, and get your written "
                     "permission before they do. If they then decide not to "
                     "hire you because of what is in it, they have to give you "
                     "a copy of the report and a written statement of your "
                     "rights before they act. Not after. Before.",
                fact_key="employer_needs_written_permission",
                aside="This one matters on the outside. Most people never ask "
                      "for the copy they are owed.",
            ),
        ),
        check=Check(
            prompt="An employer turns you down and mentions your credit. What "
                   "are you owed?",
            choices=(
                Choice("copy", "A copy of the report and a statement of your rights"),
                Choice("nothing", "Nothing, it is their decision"),
                Choice("reason", "A written explanation of their reasoning"),
            ),
            answer="copy",
            why="You get a copy of the report they used and a written "
                "statement of your rights, and you are supposed to get it "
                "before they finalize the decision, so there is a window to "
                "point out an error. Separately, a denial like this entitles "
                "you to a free copy from the bureau itself. That comes up in "
                "the lesson on free reports.",
        ),
    ),
    Lesson(
        slug="report-and-score",
        title="The report and the score are different things",
        minutes=4,
        hook="One is a file. The other is somebody's opinion about the file, "
             "and you are owed the first one but not the second.",
        urgent_for=("not_yet_triaged",),
        cards=(
            Card(
                title="The file is the facts. The score is an opinion about them",
                body="The report lists what happened. A score is a number a "
                     "company calculates from that list, using a formula they "
                     "own. Change the file and the score follows. Argue with "
                     "the score and nothing happens, because there is nothing "
                     "there to argue with.",
            ),
            Card(
                title="Your free report may come with no number on it",
                body="What you are owed by law is the file. A score is "
                     "specifically not part of what they have to disclose. So "
                     "when your report arrives in the mail and there is no "
                     "number anywhere on it, nothing has gone wrong and nobody "
                     "has cheated you. You got exactly what you were owed, and "
                     "it is the more useful half.",
                fact_key="no_score_in_the_disclosure",
            ),
            Card(
                title="Your Social Security number can be blacked out",
                body="You can require them to leave the first five digits of "
                     "your Social off your own copy. That is a right you can "
                     "insist on, not a favour. It is also the reason you can "
                     "read your own report on a tablet in a room full of "
                     "people.",
                fact_key="ssn_truncation_right",
            ),
        ),
        check=Check(
            prompt="Your free report arrives and there is no score on it. What "
                   "happened?",
            choices=(
                Choice("normal", "Nothing. A file disclosure does not have to include one"),
                Choice("error", "They made a mistake and you should write back"),
                Choice("nofile", "It means you have no score at all"),
            ),
            answer="normal",
            why="The law says they owe you the file, and specifically says "
                "scores are not part of that. Most mailed reports arrive "
                "without one. It says nothing about whether you have a score, "
                "and the file is the part that can actually be corrected.",
        ),
    ),
    Lesson(
        slug="no-single-score",
        title="There is no such thing as your credit score",
        minutes=5,
        hook="Not one number. Dozens, all real at the same time, and the free "
             "app on somebody's phone is showing a different one from the bank.",
        urgent_for=("thin_file", "damaged_file"),
        cards=(
            Card(
                title="Three things multiply together",
                body="Which bureau's file it was run against, which company's "
                     "model did the running, and what the score is for. Three "
                     "bureaus, several models in active use, and separate "
                     "versions tuned for car loans and credit cards. Multiply "
                     "those out and one person honestly has dozens of scores "
                     "on the same day.",
                fact_key="many_scores",
            ),
            Card(
                title="They do not even share a scale",
                body="Most scores run 300 to 850. The ones car dealers and "
                     "card companies pull run 250 to 900. So a 700 in one "
                     "place is not the same as a 700 in another, and comparing "
                     "them straight across tells you nothing.",
                fact_key="many_scores",
            ),
            Card(
                title="Why the free app disagrees with the bank",
                body="Free apps usually show a VantageScore. Most lenders use "
                     "a FICO. Different companies, different formulas. Neither "
                     "is lying to you. They are not measuring the same thing.",
                fact_key="many_scores",
            ),
            Card(
                title="So which one is real?",
                body="The one belonging to whoever is deciding about you. That "
                     "is the whole answer. A landlord, a car dealer and a card "
                     "company will each pull a different one, and all of them "
                     "are real. Which is why the work is on the file, not on "
                     "chasing a number.",
                aside="It is also why this app does not show you a number. A "
                      "score with no model, bureau and date attached is a "
                      "guess that looks precise.",
            ),
        ),
        check=Check(
            prompt="A free app shows 640. A car dealer says you are at 590. "
                   "Who is wrong?",
            choices=(
                Choice("neither", "Neither. Different model, different bureau, different scale"),
                Choice("app", "The app, those are never accurate"),
                Choice("dealer", "The dealer, they lowball to sell you a worse rate"),
            ),
            answer="neither",
            why="The app is almost certainly showing a VantageScore. The "
                "dealer pulled an auto-specific FICO, which runs on a 250 to "
                "900 scale rather than 300 to 850, probably from a different "
                "bureau's file. Both numbers can be correct at once. Worth "
                "knowing before you assume somebody is running a game on you.",
        ),
    ),
    Lesson(
        slug="what-moves-it",
        title="What actually moves a score",
        minutes=5,
        hook="Five things, and two of them are most of it.",
        urgent_for=("thin_file", "credit_invisible"),
        cards=(
            Card(
                title="The five, by weight",
                body="Payment history is about 35 percent. How much you owe "
                     "against what is available to you is about 30 percent. "
                     "How long you have had credit, about 15 percent. Your mix "
                     "of types of credit, about 10 percent. Recently opened "
                     "accounts, about 10 percent.",
                fact_key="score_factor_weights",
            ),
            Card(
                title="Two of them are two thirds",
                body="Paying on time and not using too much of what you have "
                     "available are roughly 65 percent of it between them. "
                     "Everything else is noise by comparison. If you only ever "
                     "remember one thing from this course, remember that the "
                     "boring answer is most of the answer.",
                fact_key="score_factor_weights",
            ),
            Card(
                title="The one nobody explains",
                body="That second one is about the ratio, not the amount. A "
                     "card with a 500 dollar limit carrying a 450 balance "
                     "looks worse than a card with a 5,000 dollar limit "
                     "carrying the same 450. Same debt. Very different "
                     "picture. Paying a card down below about a third of its "
                     "limit is the fastest legitimate move there is.",
            ),
            Card(
                title="Time is the one you cannot rush",
                body="Length of history only goes one way and only at one "
                     "speed. Which is the real argument for starting inside "
                     "rather than at the gate: an account opened now is "
                     "already months old by the time anybody asks you for a "
                     "credit check.",
            ),
        ),
        check=Check(
            prompt="You have 450 dollars and two cards, each with a 500 dollar "
                   "limit and a 450 balance. What helps your score most?",
            choices=(
                Choice("one", "Pay one card down to near zero"),
                Choice("split", "Split it evenly across both"),
                Choice("save", "Keep it in savings and pay the minimums"),
            ),
            answer="one",
            why="Clearing one card takes it from 90 percent used to nearly "
                "nothing, which is the part of the formula that moves fastest. "
                "Splitting it leaves both cards around 45 percent used, which "
                "is better than 90 but not by as much. Keep paying at least "
                "the minimum on the other one either way, because payment "
                "history is the bigger slice and a missed payment undoes this.",
        ),
    ),
    Lesson(
        slug="old-debt",
        title="Old debt does not last forever",
        minutes=4,
        hook="Most of it has to come off after seven years, and paying it does "
             "not restart the clock.",
        urgent_for=("damaged_file",),
        cards=(
            Card(
                title="Seven years, ten for bankruptcy",
                body="Collection accounts and charge-offs have to come off "
                     "seven years after the account first went delinquent. So "
                     "do civil judgments and paid tax liens, and most other "
                     "bad marks. Bankruptcy runs ten. After that they are not "
                     "allowed to report it.",
                fact_key="negative_information_ages_off",
            ),
            Card(
                title="The clock starts at the original delinquency",
                body="This is the part that gets people. The seven years runs "
                     "from when you first fell behind on the original account, "
                     "not from when a collector bought it and not from when "
                     "you paid it. Paying an old debt does not restart "
                     "anything. A collector who tells you it will is selling "
                     "you something.",
                fact_key="negative_information_ages_off",
            ),
            Card(
                title="Court debt is a different animal",
                body="Restitution, fines and child support do not work like "
                     "credit accounts. Civil judgments largely came off credit "
                     "reports back in 2017, and in New York restitution is "
                     "collected by probation rather than reported as a debt. "
                     "Child support arrears are the exception: states are "
                     "required to report those. They all matter, and they "
                     "belong in a different list from your credit accounts.",
                fact_key="child_support_reports",
            ),
        ),
        check=Check(
            prompt="A collector says paying a five-year-old debt will help "
                   "your credit. Is that right?",
            choices=(
                Choice("partly", "Partly, but it will not reset the seven years"),
                Choice("yes", "Yes, paying always helps"),
                Choice("no", "No, never pay an old debt"),
            ),
            answer="partly",
            why="It may help, and on some newer scoring models a paid "
                "collection stops counting against you entirely. But it does "
                "not restart or extend the seven years, and it does not erase "
                "the entry. Anyone telling you that you have to pay to make it "
                "go away has it backwards: time makes it go away. Get any "
                "agreement in writing before money moves.",
        ),
    ),
    Lesson(
        slug="free-reports",
        title="Every way to get your report free",
        minutes=5,
        hook="There are more routes than the one everybody knows, and coming "
             "home qualifies you for several of them at once.",
        urgent_for=("not_yet_triaged", "credit_invisible"),
        cards=(
            Card(
                title="One a year, from all three, by mail",
                body="Every nationwide bureau owes you one free copy of your "
                     "file every 12 months, through one central request, and "
                     "they have 15 days from getting the request to send it. "
                     "One letter to one address covers all three.",
                fact_key="free_report_entitlement",
            ),
            Card(
                title="The mail route is the one that works from here",
                body="The Annual Credit Report Request Form goes to the Annual "
                     "Credit Report Request Service in Atlanta. No internet, "
                     "no phone, no fee. The weekly free reports everyone talks "
                     "about are online only and are a voluntary arrangement "
                     "rather than a right, so they are no use to you in here.",
                fact_key="free_report_mail_route",
            ),
            Card(
                title="Turned down for something? That is another free one",
                body="If you are denied credit, an apartment, insurance or a "
                     "job because of your credit report, you can get a free "
                     "copy of the file they used, as long as you ask within 60 "
                     "days of being told. This is separate from your annual "
                     "one and does not use it up.",
                fact_key="free_report_after_a_denial",
            ),
            Card(
                title="Unemployed or on assistance? Another one",
                body="A free report is also owed once a year to anyone who "
                     "certifies in writing that they are unemployed and "
                     "planning to look for work in the next 60 days, that they "
                     "receive public assistance, or that they think their file "
                     "has errors from fraud. Somebody just home often "
                     "qualifies under two or three of those at the same time.",
                fact_key="free_report_unemployed_or_on_assistance",
                aside="Almost nobody knows this one. It is worth remembering "
                      "for the first year out, when you will want to check "
                      "more than once.",
            ),
        ),
        check=Check(
            prompt="You used your annual free report in March. In July a "
                   "landlord turns you down over your credit. Do you have to pay?",
            choices=(
                Choice("free", "No. A denial entitles you to another free copy"),
                Choice("pay", "Yes, you already used this year's"),
                Choice("wait", "No, but you have to wait until next March"),
            ),
            answer="free",
            why="Being turned down because of a report starts its own "
                "entitlement, separate from the annual one, as long as you ask "
                "within 60 days. If you were also unemployed or on assistance "
                "at the time, that is another separate route again. These "
                "stack. Most people pay for something they were already owed.",
        ),
    ),
    Lesson(
        slug="disputes",
        title="What a dispute is, and the clock it starts",
        minutes=5,
        hook="It is the one part of this where somebody else is on a deadline "
             "instead of you.",
        urgent_for=("errors_present",),
        cards=(
            Card(
                title="You are telling them their file is wrong",
                body="A dispute is a letter saying a specific item on your "
                     "report is not accurate, and why. Not a complaint, not a "
                     "request for sympathy. One item, one reason, in writing.",
            ),
            Card(
                title="Thirty days, counted from when they get it",
                body="They have 30 days to investigate, starting the day the "
                     "letter lands, not the day you posted it. If you send "
                     "more information during those 30 days they get up to 15 "
                     "more, so it can run to 45. Then they have five business "
                     "days to write and tell you the outcome.",
                fact_key="reinvestigation_window",
            ),
            Card(
                title="Wrong, incomplete, or unprovable all count",
                body="If what they find is inaccurate, incomplete, or they "
                     "simply cannot verify it, they have to delete or fix it. "
                     "That last one matters more than people expect. An old "
                     "debt sold on three times may have nobody left who can "
                     "prove it was ever yours.",
                fact_key="results_notice",
            ),
            Card(
                title="All three, every time",
                body="An item deleted at Equifax is still sitting on the "
                     "Experian and TransUnion files. One letter fixes one "
                     "third of the problem. This is why every dispute here "
                     "goes out as three letters.",
            ),
            Card(
                title="It works more often than people think",
                body="In the FTC's study, about one in four people found at "
                     "least one error on a report that could have mattered, "
                     "and about one in twenty had one bad enough to cost them "
                     "worse terms on a loan. One in five had an error put "
                     "right after they disputed it. Disputing is not a long "
                     "shot.",
                fact_key="dispute_outcomes",
            ),
        ),
        check=Check(
            prompt="You mail a dispute on the 1st. It arrives on the 5th. When "
                   "is the answer due?",
            choices=(
                Choice("receipt", "30 days from the 5th, when they received it"),
                Choice("posted", "30 days from the 1st, when you posted it"),
                Choice("either", "There is no fixed deadline"),
            ),
            answer="receipt",
            why="The clock runs from receipt, not from the postmark, which is "
                "why anything sent from here should be tracked if possible. "
                "And if you send extra paperwork while they are investigating, "
                "you hand them up to 15 extra days, so send everything at once "
                "rather than in pieces.",
        ),
    ),
    Lesson(
        slug="building-from-nothing",
        title="Building a file from nothing",
        minutes=5,
        hook="No file is not the same as bad credit, and it is the faster of "
             "the two to fix.",
        urgent_for=("credit_invisible", "thin_file"),
        cards=(
            Card(
                title="Empty moves faster than damaged",
                body="Having no credit history is a different problem from "
                     "having a bad one, and it is the better problem. There is "
                     "nothing to argue with and nothing to wait out. You are "
                     "building on clear ground.",
            ),
            Card(
                title="A secured card is your own money, held",
                body="You put down a deposit, say 200 dollars, and that "
                     "becomes your limit. Use a little of it, pay it off every "
                     "month, and it reports as an ordinary credit card. The "
                     "deposit comes back. The risk to the bank is nil, which "
                     "is exactly why they will say yes to somebody with no "
                     "history.",
            ),
            Card(
                title="A builder loan runs backwards",
                body="The bank holds the money in an account, you make "
                     "payments, and you get the money at the end. You are not "
                     "borrowing anything. What you are buying is 12 months of "
                     "on-time payment history, which is the single heaviest "
                     "thing in the formula.",
            ),
            Card(
                title="The cheapest route is somebody else's card",
                body="Being added as an authorized user on a family member's "
                     "long-standing card can put their history on your file "
                     "without you ever touching the card. It costs nothing and "
                     "takes one phone call from them. Ask somebody who has had "
                     "the same card a long time and always paid it.",
                aside="It works both ways, so only ask somebody whose own "
                      "record is solid.",
            ),
            Card(
                title="Rent, phone and power can count",
                body="Payments you are already making can be reported, through "
                     "services set up for it. It is the least work for the "
                     "biggest effect, because you are getting credit for "
                     "money that was leaving your pocket anyway.",
            ),
        ),
        check=Check(
            prompt="You have no credit file and 200 dollars. What starts the "
                   "clock fastest?",
            choices=(
                Choice("secured", "A secured card, used lightly and paid in full monthly"),
                Choice("wait", "Wait until you have more money saved"),
                Choice("loan", "Apply for a regular loan and see what happens"),
            ),
            answer="secured",
            why="The 200 becomes your limit and the account starts reporting "
                "straight away. Applying for regular credit with no file "
                "mostly produces refusals, and each one leaves a mark. Waiting "
                "costs you the one thing you cannot buy later, which is time "
                "on the account. Getting added as an authorized user on "
                "somebody else's card costs nothing at all and can run "
                "alongside it.",
        ),
    ),
    Lesson(
        slug="identity-theft",
        title="If somebody has been using your name",
        minutes=4,
        hook="It happens more to people inside than to anybody else, and the "
             "tools to stop it are free.",
        urgent_for=("errors_present", "damaged_file"),
        cards=(
            Card(
                title="Why this hits this population hardest",
                body="Your Social Security number has been on paperwork in a "
                     "lot of hands. You have not seen a statement in years. "
                     "Mail goes to an address that is not yours. Accounts "
                     "opened in your name can run for a long time before "
                     "anybody who cares finds out. If your report shows "
                     "accounts you have never heard of, you are not confused, "
                     "and it is not your fault.",
            ),
            Card(
                title="A freeze is free and it is the strong one",
                body="A security freeze stops anybody opening new credit in "
                     "your name. It has to be placed free of charge, within "
                     "one business day of an electronic or phone request and "
                     "three business days of a mailed one. Lifting it when you "
                     "actually want credit is free too, within an hour if you "
                     "do it electronically.",
                fact_key="security_freeze_is_free",
            ),
            Card(
                title="A fraud alert is the lighter version",
                body="An initial alert lasts at least a year and comes with a "
                     "free copy of your file. File an identity theft report "
                     "and you can get an extended alert: seven years, two free "
                     "copies in the first year, and your name kept off "
                     "unsolicited credit offers for five.",
                fact_key="extended_fraud_alert",
            ),
            Card(
                title="An account you never opened is a dispute, not a debt",
                body="Do not pay it and do not negotiate it. It goes down the "
                     "dispute route, and unverifiable items have to be "
                     "removed. Tell your coordinator which items you do not "
                     "recognize. That sentence is the one that starts the "
                     "legal clock.",
            ),
        ),
        check=Check(
            prompt="Your report shows a card opened two years ago that you "
                   "have never heard of. What is the first move?",
            choices=(
                Choice("dispute", "Tell your coordinator you do not recognize it"),
                Choice("pay", "Pay it off so it stops growing"),
                Choice("ignore", "Ignore it, it will age off in seven years"),
            ),
            answer="dispute",
            why="Saying you do not recognize it is what turns this into a "
                "dispute, and a dispute puts the bureau on a 30-day clock. "
                "Paying it can be read as agreeing it is yours. Waiting seven "
                "years means seven years of it sitting on your file while you "
                "are trying to rent somewhere. A freeze on top of that stops "
                "the next one.",
        ),
    ),
    Lesson(
        slug="scams",
        title="Spotting the people who will take your money",
        minutes=4,
        hook="Coming home with a bit of money and a bad report makes you a "
             "target. Two rules cover most of it.",
        urgent_for=("damaged_file", "errors_present"),
        cards=(
            Card(
                title="Rule one: nobody may charge you before the work is done",
                body="A credit repair company cannot legally take any money "
                     "before it has fully performed what it promised. Not a "
                     "deposit, not a setup fee, not a first month. If money is "
                     "wanted up front, the law has already been broken and you "
                     "have learned everything you need to know about them.",
                fact_key="credit_repair_cannot_charge_up_front",
            ),
            Card(
                title="Rule two: anybody telling you to change your identity is setting you up",
                body="Advising you to alter your identifying information to "
                     "hide a bad record is specifically prohibited, and the "
                     "person doing it is walking you into a fraud charge while "
                     "they keep the fee. The same goes for anyone telling you "
                     "to misstate your history.",
                fact_key="credit_repair_cannot_charge_up_front",
            ),
            Card(
                title="There is nothing they can do that you cannot",
                body="Every dispute a paid company files is one you can file "
                     "yourself, free, in a letter. There is no special channel "
                     "and no relationship with the bureaus. What they are "
                     "selling is the letter you are already getting help with "
                     "here.",
            ),
            Card(
                title="Accurate is accurate",
                body="If a debt is genuinely yours and correctly reported, "
                     "nobody can remove it early. Anybody promising to delete "
                     "accurate information is either lying or planning to "
                     "dispute things they know are true, which wastes your "
                     "time and can get the disputes dismissed as frivolous.",
            ),
        ),
        check=Check(
            prompt="A company offers to fix your credit for 99 dollars a month "
                   "starting now. What does that tell you?",
            choices=(
                Choice("illegal", "They are already breaking the law by charging before the work"),
                Choice("fair", "It is a fair price if it works"),
                Choice("check", "Nothing yet, check their reviews first"),
            ),
            answer="illegal",
            why="Taking money before the service is fully performed is "
                "prohibited outright. You do not need to read a single review: "
                "the payment structure alone tells you what they are. And the "
                "disputes they would file are ones you can file yourself for "
                "the price of a stamp.",
        ),
    ),
)

BY_SLUG: dict[str, Lesson] = {lesson.slug: lesson for lesson in CURRICULUM}

TOTAL_MINUTES = sum(lesson.minutes for lesson in CURRICULUM)


def lesson(slug: str) -> Lesson:
    return BY_SLUG[slug]


# --------------------------------------------------------------------------
# progress
# --------------------------------------------------------------------------
#
# Stored on the client as a plain dict so it survives in the JSON file without
# a schema. One entry per lesson the
# person has opened; a lesson never opened has no entry, which is how "not
# started" is told apart from "on card one".


def _blank() -> dict:
    return {"card": 0, "done": False, "answered": "", "opened_on": "", "done_on": ""}


def progress(client, slug: str) -> dict:
    """What this person has done in one lesson. Never returns None."""
    store = getattr(client, "lesson_progress", None) or {}
    return {**_blank(), **store.get(slug, {})}


def open_at(client, slug: str, today: date | None = None) -> dict:
    """Mark a lesson as started, without moving anybody backwards.

    Called on every view of card zero, so it has to be idempotent: somebody
    coming back to re-read a lesson they finished keeps their completion.
    """
    today = today or date.today()
    if not hasattr(client, "lesson_progress") or client.lesson_progress is None:
        client.lesson_progress = {}
    row = client.lesson_progress.setdefault(slug, _blank())
    row.setdefault("opened_on", "")
    if not row["opened_on"]:
        row["opened_on"] = today.isoformat()
    return row


def record_card(client, slug: str, index: int, today: date | None = None) -> dict:
    """Remember the furthest card reached.

    Furthest, not latest. Paging back to re-read card one should not throw away
    the fact that somebody had got to card four.
    """
    row = open_at(client, slug, today)
    row["card"] = max(int(row.get("card", 0)), int(index))
    return row


def record_answer(client, slug: str, choice: str,
                  today: date | None = None) -> dict:
    """Answering the check completes the lesson, whatever the answer was.

    Completion is for working through it, not for getting it right. A person
    who picked the wrong option and then read the explanation has learned the
    thing; withholding the tick would teach them to guess safely instead.
    """
    today = today or date.today()
    row = open_at(client, slug, today)
    row["answered"] = choice
    if not row["done"]:
        row["done"] = True
        row["done_on"] = today.isoformat()
    return row


def completed_slugs(client) -> list[str]:
    store = getattr(client, "lesson_progress", None) or {}
    return [s.slug for s in CURRICULUM if store.get(s.slug, {}).get("done")]


def is_complete(client, slug: str) -> bool:
    return bool(progress(client, slug)["done"])


def finished_course(client) -> bool:
    return len(completed_slugs(client)) == len(CURRICULUM)


def standing(client) -> dict:
    """The one-line summary the tablet shows everywhere the course is linked."""
    done = len(completed_slugs(client))
    total = len(CURRICULUM)
    return {
        "done": done,
        "total": total,
        "percent": round(done * 100 / total) if total else 0,
        "finished": done == total,
        "minutes_left": sum(
            l.minutes for l in CURRICULUM if not is_complete(client, l.slug)
        ),
    }


def far_from_release(client, today: date | None = None) -> bool:
    """More than a year out, so nothing on a release clock is urgent yet.

    Bridge was built around the six months before release, because that is
    when a credit file can be moved. The course is not: reading your own
    report, learning what a score is, freezing your file against somebody
    using your name, and the free report you are owed once every twelve months
    are all available on day one of a ten-year sentence. Somebody with nine
    years left has more time to build a file than anyone, not less.
    """
    raw = getattr(client, "release_date", "") or ""
    try:
        return (date.fromisoformat(raw) - (today or date.today())).days > 365
    except ValueError:
        return False


def next_up(client, today: date | None = None) -> Lesson | None:
    """What to offer next.

    In progress first, because an unfinished thing is the easiest thing to
    return to. Then whatever answers the state this person's case is actually
    in. Then curriculum order.

    One exception, and it is the whole reason this takes a date. The documents
    lesson leads the curriculum because its deadline is the one thing somebody
    can act on the same day. For a person nine years out that deadline is not
    theirs yet, and opening the course with it says this product is for people
    on their way out. So for them it steps aside and something useful today
    goes first. Nothing is hidden: the index still lists every lesson and any
    of them opens.
    """
    started = [
        l for l in CURRICULUM
        if progress(client, l.slug)["card"] > 0 and not is_complete(client, l.slug)
    ]
    if started:
        return started[0]

    skip_release_clock = far_from_release(client, today)
    state = getattr(client, "case_state", "") or ""

    for pass_ in ("urgent", "any"):
        for lesson_ in CURRICULUM:
            if is_complete(client, lesson_.slug):
                continue
            if skip_release_clock and lesson_.release_dependent:
                continue
            if pass_ == "urgent" and state not in lesson_.urgent_for:
                continue
            return lesson_

    # Everything else done, so the release-dependent one is what is left.
    for lesson_ in CURRICULUM:
        if not is_complete(client, lesson_.slug):
            return lesson_
    return None


def index_rows(client) -> list[dict]:
    """The course list, in order, with where this person stands on each."""
    rows = []
    state = getattr(client, "case_state", "") or ""
    far_out = far_from_release(client)
    for lesson_ in CURRICULUM:
        row = progress(client, lesson_.slug)
        rows.append({
            "lesson": lesson_,
            "done": bool(row["done"]),
            "started": row["card"] > 0 and not row["done"],
            "card": row["card"],
            "screens": lesson_.screens,
            # "For you now" on a deadline that is nine years away is noise.
            "for_you": (state in lesson_.urgent_for and not row["done"]
                        and not (far_out and lesson_.release_dependent)),
        })
    return rows


# How many sentences of a card or an intro stay on screen before the rest folds
# behind "Read more". One number, so the course can be tightened or loosened
# without touching a template. A card is one screen and its body is the lesson,
# so this is deliberately a little more generous than "a couple".
COLLAPSE_AFTER = 3

_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡"“(\d])')
# An abbreviation's full stop is not the end of a sentence ("U.S.", "EE. UU.").
_ABBREVIATION = re.compile(
    r'(?:\b(?:U\.S|Mr|Mrs|Ms|Dr|Dra|Sr|Sra|No|Núm|vs|etc|e\.g|i\.e|St)|\bEE|\bUU)\.$')


def lead_and_rest(text: str, keep: int = COLLAPSE_AFTER) -> tuple[str, str]:
    """The first `keep` sentences, and whatever follows them.

    Text that is already short comes back whole with nothing after it, so a
    template can ask unconditionally and only fold what is long. Works on the
    translated text as well, since it splits on punctuation and not on words.
    """
    text = (text or "").strip()
    sentences: list[str] = []
    for piece in _SENTENCE_END.split(text):
        if sentences and _ABBREVIATION.search(sentences[-1]):
            sentences[-1] = f"{sentences[-1]} {piece}"
        else:
            sentences.append(piece)
    if len(sentences) <= keep:
        return text, ""
    return " ".join(sentences[:keep]), " ".join(sentences[keep:])
