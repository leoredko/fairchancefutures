"""There is no such thing as "your credit score".

A person coming home is told to check their score, checks one, and then gets
turned down by a landlord and quoted a rate by a car dealer that neither match
the number they saw. Nobody lied to them. They were looking at a different
score from a different model built on a different bureau's file.

This module is the reference behind that explanation. It exists because the
question a coordinator gets asked most is some version of "which one is real?",
and the honest answer is "the one the person deciding about you pulled."

Three things multiply together:

    which bureau       Equifax, Experian and TransUnion hold different files,
                       because furnishers do not all report to all three

    which model        FICO and VantageScore are different companies, and FICO
                       alone has base versions 2 through 10T in active use

    which industry     auto lenders and card issuers use scores tuned to their
                       own risk, on a different numeric range entirely

So the same person, on the same day, honestly has dozens of scores. The app
does not show a number for exactly this reason: a number without its model,
bureau and date attached is not information, it is a guess that feels precise.

    Sources, checked 2026-09-23
    CFPB, What is a credit score?
    myFICO, FICO Score Versions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SOURCES = {
    "cfpb": ("CFPB, What is a credit score?",
             "https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-score-en-315/"),
    "myfico": ("myFICO, FICO Score Versions",
               "https://www.myfico.com/credit-education/credit-scores/fico-score-versions"),
}

# Base scores and industry scores do not even share a scale, which is the
# single most confusing fact in the whole subject.
BASE_RANGE = (300, 850)
INDUSTRY_RANGE = (250, 900)


class Use(str, Enum):
    GENERAL = "general"
    AUTO = "auto"
    CARD = "card"
    MORTGAGE = "mortgage"
    RENTAL = "rental"


USE_LABEL: dict[Use, str] = {
    Use.GENERAL: "General lending",
    Use.AUTO: "Buying a car",
    Use.CARD: "A credit card",
    Use.MORTGAGE: "A mortgage",
    Use.RENTAL: "Renting somewhere to live",
}


@dataclass(frozen=True)
class Model:
    name: str
    use: Use
    low: int
    high: int
    note: str
    source: str = "myfico"

    @property
    def range_label(self) -> str:
        return f"{self.low} to {self.high}"


MODELS: tuple[Model, ...] = (
    Model("FICO Score 8", Use.GENERAL, *BASE_RANGE,
          note="The base score most lenders use. If somebody says 'your FICO' "
               "with no other detail, this is usually the one they mean."),
    Model("FICO Score 9", Use.GENERAL, *BASE_RANGE,
          note="The version worth knowing about. A third-party collection that "
               "has been PAID no longer counts against you at all, and an "
               "unpaid medical collection counts for less. Whether a lender "
               "uses it is up to them, which is why paying a collection can "
               "move one score and not another."),
    Model("FICO Score 10 and 10T", Use.GENERAL, *BASE_RANGE,
          note="The newest base versions. 10T reads trended data, meaning the "
               "direction your balances have moved over time rather than just "
               "where they sit today."),
    Model("FICO Auto Score", Use.AUTO, *INDUSTRY_RANGE,
          note="What a car lender pulls. Note the range: 250 to 900, not 300 "
               "to 850. A 700 here is not the same 700 you saw somewhere else."),
    Model("FICO Bankcard Score", Use.CARD, *INDUSTRY_RANGE,
          note="What a card issuer pulls, also on the 250 to 900 scale."),
    Model("FICO Score 2, 4 and 5", Use.MORTGAGE, *BASE_RANGE,
          note="Mortgage lenders use older versions, and a different one per "
               "bureau: 2 at Experian, 4 at TransUnion, 5 at Equifax. Somebody "
               "who improved their FICO 8 has not necessarily moved these."),
    Model("VantageScore", Use.GENERAL, *BASE_RANGE,
          note="A different company's model entirely, not a FICO version. Many "
               "free score apps show a VantageScore, which is part of why the "
               "number in a free app often does not match a lender's.",
          source="cfpb"),
)


def models_for(use: Use) -> list[Model]:
    return [m for m in MODELS if m.use is use]


def how_many() -> int:
    """Rough count of distinct scores one person can have at one moment.

    Deliberately conservative and deliberately stated as an estimate. The point
    is the order of magnitude, not a figure to put on a slide.
    """
    return len(MODELS) * 3  # each model, run against each bureau's file


# The questions people actually ask, and the answers, in order of how often a
# coordinator hears them.
EXPLAINERS: tuple[dict, ...] = (
    {
        "question": "Which one is my real score?",
        "answer": "The one belonging to whoever is deciding about you. A "
                  "landlord, a car dealer and a card issuer will each pull a "
                  "different model from a different bureau, and all three "
                  "numbers are real.",
    },
    {
        "question": "Why is the free app's number different from the bank's?",
        "answer": "Free apps usually show a VantageScore, and most lenders use "
                  "a FICO. Different company, different model. Neither is "
                  "wrong; they are not measuring the same thing.",
    },
    {
        "question": "Why do the three bureaus disagree?",
        "answer": "They hold different files. Not every lender reports to all "
                  "three, so an account on one report can be missing from "
                  "another. Same model, different input, different answer.",
    },
    {
        "question": "I paid off a collection and nothing changed. Why?",
        "answer": "On FICO 9 a paid third-party collection stops counting "
                  "against you. On FICO 8, which more lenders still use, it "
                  "does not. Paying it was still the right call, and the "
                  "change shows up unevenly.",
    },
    {
        "question": "I have no score at all. Is that worse than a bad one?",
        "answer": "No. Empty moves faster than damaged does. Building a file "
                  "from nothing is the fastest of the four situations; "
                  "repairing a damaged one takes years.",
    },
    {
        "question": "Does the free report I get by mail show a score?",
        "answer": "It does not have to, and usually will not. A file "
                  "disclosure has to show what is in your file. A score is a "
                  "number somebody calculates from that file, and it is not "
                  "part of what they owe you.",
    },
)


def summary_line() -> str:
    return (
        f"About {how_many()} different scores can describe one person on one "
        f"day: {len(MODELS)} widely used models against 3 bureau files. Base "
        f"scores run {BASE_RANGE[0]} to {BASE_RANGE[1]}; auto and card scores "
        f"run {INDUSTRY_RANGE[0]} to {INDUSTRY_RANGE[1]}."
    )


# The model the seeded files were scored with. Named on screen beside every
# number, because a score with no model, bureau and date attached is a guess
# that looks precise, and this module exists to say so.
SHOWN_MODEL = "FICO Score 8"


def across_bureaus(reports) -> dict:
    """The same person's score at each bureau, side by side.

    The point of showing three numbers rather than one. This product refuses
    to print *a* credit score, and it is right to: there is no such thing. But
    refusing to show anything taught the lesson only in words, and a person
    who has never seen their own file wants to see it. Three numbers on one
    screen, each carrying the bureau and the day it was pulled, is the same
    lesson made out of their own data instead of an argument about it.

    The spread is not decoration either. It is the account-level disagreement
    one line up: a bureau missing a collection, or reporting a paid car loan
    as open, is why its number differs.
    """
    rows = []
    for report in reports:
        if not report.score:
            continue
        rows.append({
            "bureau": report.bureau,
            "score": report.score,
            "model": SHOWN_MODEL,
            "pulled_on": report.pulled_on,
            "accounts": len(report.accounts),
        })
    if len(rows) < 2:
        return {"rows": rows, "spread": 0, "low": None, "high": None}

    numbers = [r["score"] for r in rows]
    # Two different contrasts, and picking the wrong one produces a sentence
    # that says nothing. The score spread is the headline; the account counts
    # are the explanation, and the bureaus at each end are often not the same
    # pair, because the highest score is not always the fullest file.
    counts = [r["accounts"] for r in rows]
    return {
        "rows": rows,
        "spread": max(numbers) - min(numbers),
        "low": min(rows, key=lambda r: r["score"]),
        "high": max(rows, key=lambda r: r["score"]),
        "fewest": min(rows, key=lambda r: r["accounts"]),
        "most": max(rows, key=lambda r: r["accounts"]),
        # Only worth saying out loud when the files actually differ in size.
        "counts_differ": max(counts) != min(counts),
    }
