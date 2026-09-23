"""Verified facts, with the primary source and the date it was checked.

The rule this module exists to enforce: nothing in the app states a legal fact
unless it is in here, and everything in here carries the URL it came from and
the date somebody looked. A fact with no source renders as an open question,
not as a confident sentence.

Re-check anything older than about six months. Bureau mailing addresses in
particular are the kind of thing that moves without announcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Fact:
    key: str
    statement: str
    source: str
    url: str
    checked_on: date

    def cite(self) -> str:
        return f"{self.statement} ({self.source}, checked {self.checked_on.isoformat()})"


CHECKED = date(2026, 9, 23)

FACTS: dict[str, Fact] = {
    "reinvestigation_window": Fact(
        key="reinvestigation_window",
        statement=(
            "A credit reporting agency must complete its reinvestigation of a "
            "disputed item within 30 days beginning on the date it receives the "
            "notice of dispute. The clock starts on receipt, not on the day the "
            "letter is mailed."
        ),
        source="15 U.S.C. 1681i(a)(1)(A)",
        url="https://www.law.cornell.edu/uscode/text/15/1681i",
        checked_on=CHECKED,
    ),
    "reinvestigation_extension": Fact(
        key="reinvestigation_extension",
        statement=(
            "The 30 days may be extended by not more than 15 additional days if "
            "the agency receives relevant information from the consumer during "
            "that 30-day period. So sending more paperwork mid-dispute can push "
            "the deadline out to 45 days."
        ),
        source="15 U.S.C. 1681i(a)(1)(B)",
        url="https://www.law.cornell.edu/uscode/text/15/1681i",
        checked_on=CHECKED,
    ),
    "results_notice": Fact(
        key="results_notice",
        statement=(
            "The agency must send written notice of the results within 5 business "
            "days of completing the reinvestigation, and must promptly delete or "
            "modify any item found inaccurate, incomplete, or unverifiable."
        ),
        source="15 U.S.C. 1681i(a)(5)-(6)",
        url="https://www.law.cornell.edu/uscode/text/15/1681i",
        checked_on=CHECKED,
    ),
    "free_report_entitlement": Fact(
        key="free_report_entitlement",
        statement=(
            "Every nationwide agency must provide one free file disclosure per "
            "12-month period on request through the centralized source, and must "
            "deliver it within 15 days of receiving the request."
        ),
        source="15 U.S.C. 1681j(a)",
        url="https://www.law.cornell.edu/uscode/text/15/1681j",
        checked_on=CHECKED,
    ),
    "free_report_mail_route": Fact(
        key="free_report_mail_route",
        statement=(
            "The mail route is the Annual Credit Report Request Form, sent to "
            "Annual Credit Report Request Service, P.O. Box 105281, Atlanta, GA "
            "30348-5281. This is the route that works without internet access."
        ),
        source="FTC, Free Credit Reports",
        url="https://consumer.ftc.gov/articles/free-credit-reports",
        checked_on=CHECKED,
    ),
    "weekly_free_reports": Fact(
        key="weekly_free_reports",
        statement=(
            "Beyond the statutory annual disclosure, the three nationwide bureaus "
            "currently offer a free report every week through "
            "AnnualCreditReport.com. That is a voluntary program, not a statutory "
            "entitlement, and it is online only, so it does not help a client "
            "inside."
        ),
        source="FTC, Free Credit Reports",
        url="https://consumer.ftc.gov/articles/free-credit-reports",
        checked_on=CHECKED,
    ),
    "child_support_reports": Fact(
        key="child_support_reports",
        statement=(
            "States are required to report child support delinquencies to consumer "
            "reporting agencies periodically, after the noncustodial parent has "
            "had notice and a chance to contest accuracy. So child support arrears "
            "can and do reach a credit report."
        ),
        source="42 U.S.C. 666(a)(7)",
        url="https://www.law.cornell.edu/uscode/text/42/666",
        checked_on=CHECKED,
    ),
    "civil_judgments_removed": Fact(
        key="civil_judgments_removed",
        statement=(
            "Under the National Consumer Assistance Plan, from July 2017 civil "
            "public records needed a name, address, and SSN or date of birth to "
            "appear on a credit file. Civil judgments disappeared from credit "
            "reports almost entirely and tax liens fell by about half."
        ),
        source="CFPB, Quarterly Consumer Credit Trends: Public Records",
        url="https://www.consumerfinance.gov/data-research/research-reports/"
            "quarterly-consumer-credit-trends-public-records-credit-scores-and-"
            "credit-performance/",
        checked_on=CHECKED,
    ),
    "ssn_truncation_right": Fact(
        key="ssn_truncation_right",
        statement=(
            "A consumer can require the agency to leave the first five digits "
            "of their Social Security number out of their own file disclosure. "
            "On request, with proof of identity, the agency SHALL truncate it. "
            "This is a right, not a courtesy, and it is why the report can be "
            "read on a shared tablet at all."
        ),
        source="15 U.S.C. 1681g(a)(1)(A)",
        url="https://www.law.cornell.edu/uscode/text/15/1681g",
        checked_on=CHECKED,
    ),
    "no_score_in_the_disclosure": Fact(
        key="no_score_in_the_disclosure",
        statement=(
            "A file disclosure does not have to include a credit score. The "
            "statute expressly excludes credit scores and other risk predictors "
            "from what must be disclosed. So the free report a person gets by "
            "mail shows the file, and may show no number at all."
        ),
        source="15 U.S.C. 1681g(a)(1)",
        url="https://www.law.cornell.edu/uscode/text/15/1681g",
        checked_on=CHECKED,
    ),
    "many_scores": Fact(
        key="many_scores",
        statement=(
            "There is no single credit score. A score depends on which model "
            "produced it, which bureau's file it was run against, and the day "
            "it was calculated. Most scores run 300 to 850, but the "
            "industry-specific FICO scores that car lenders and card issuers "
            "use run 250 to 900, so the same number means different things."
        ),
        source="CFPB, What is a credit score?; myFICO, FICO Score Versions",
        url="https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-score-en-315/",
        checked_on=CHECKED,
    ),
    "fico_nine_collections": Fact(
        key="fico_nine_collections",
        statement=(
            "On FICO Score 9, a third-party collection that has been paid off "
            "no longer counts against the consumer at all, and an unpaid "
            "medical collection counts for less than other debt. Older "
            "versions still in wide use do not do either, which is why paying "
            "a collection can move one score and leave another unchanged."
        ),
        source="myFICO, FICO Score Versions",
        url="https://www.myfico.com/credit-education/credit-scores/fico-score-versions",
        checked_on=CHECKED,
    ),
    "mortgage_uses_old_versions": Fact(
        key="mortgage_uses_old_versions",
        statement=(
            "Mortgage lending uses older FICO versions, and a different one "
            "per bureau: Score 2 at Experian, Score 4 at TransUnion, Score 5 "
            "at Equifax. Improving the FICO 8 a free app shows does not "
            "necessarily move any of them."
        ),
        source="myFICO, FICO Score Versions",
        url="https://www.myfico.com/credit-education/credit-scores/fico-score-versions",
        checked_on=CHECKED,
    ),
    "mail_request_from_a_facility": Fact(
        key="mail_request_from_a_facility",
        statement=(
            "For a mail request from a prison or jail the bureaus ask for: full "
            "name with any suffix, a PRISONER IDENTIFICATION NUMBER, current "
            "address, every address during the two years PRECEDING "
            "incarceration, SSN and date of birth. The correctional "
            "institution's name goes on the envelope as the return address, "
            "with the prisoner ID number on it. One letter can request all "
            "three bureaus by naming them."
        ),
        source="CFPB, Requesting your free credit reports by mail from a "
               "correctional facility",
        url="https://files.consumerfinance.gov/f/documents/"
            "cfpb_request-free-credit-report_handout_2021-08.pdf",
        checked_on=CHECKED,
    ),
    "facility_record_rules": Fact(
        key="facility_record_rules",
        statement=(
            "Correctional facilities have different rules about retaining "
            "personal information, so how a person keeps a copy of their own "
            "credit report has to be checked facility by facility. This is a "
            "reason the report is read by the counselor and the helper rather "
            "than held on the tablet."
        ),
        source="CFPB, Requesting your free credit reports by mail from a "
               "correctional facility",
        url="https://files.consumerfinance.gov/f/documents/"
            "cfpb_request-free-credit-report_handout_2021-08.pdf",
        checked_on=CHECKED,
    ),
    "credit_score_gap": Fact(
        key="credit_score_gap",
        statement=(
            "The average credit score of formerly imprisoned people is about 50 "
            "points lower than that of people who were never incarcerated. This "
            "is the number behind the problem statement."
        ),
        source="CFPB, Justice-Involved Individuals and the Consumer Financial "
               "Marketplace, January 2022",
        url="https://www.consumerfinance.gov/data-research/research-reports/"
            "justice-involved-individuals-consumer-financial-marketplace/",
        checked_on=CHECKED,
    ),
    "mailed_dispute_identity": Fact(
        key="mailed_dispute_identity",
        statement=(
            "A mailed dispute is expected to carry full name with any generational "
            "suffix, date of birth, Social Security number, and every address from "
            "the past two years. Experian additionally asks for a copy of a "
            "government-issued ID and a proof of current address."
        ),
        source="Experian, How to Dispute Credit Report Errors by Mail",
        url="https://www.experian.com/blogs/ask-experian/credit-education/faqs/"
            "instructions-for-disputing-by-mail/",
        checked_on=CHECKED,
    ),
}


def fact(key: str) -> Fact:
    return FACTS[key]


def cite(key: str) -> str:
    return FACTS[key].cite()


# Still unverified. Anything that would need one of these renders as an open
# question in the UI rather than as a sentence.
# Practitioner testimony rather than law. Kept separate from FACTS on purpose:
# one interview is evidence, and it is not the same kind of evidence as a
# statute. The UI labels these as an interview wherever it shows them.
INTERVIEWS: tuple[dict, str] = (
    {
        "who": "Brianne Cornish, founder, FinEquity",
        "when": "2026-09-21",
        "claims": (
            "A credit-invisible client can go from no score to 650+ in about 6 "
            "to 9 months on a builder loan. A damaged file, say around 550, "
            "takes years. Those are two different products, not two speeds of "
            "one product.",
            "Pre-release with a family member acting as proxy is the model she "
            "would run today if starting over. People inside have more "
            "willingness to learn and fewer competing stressors.",
            "Engagement is the unsolved problem, not the technology. Automated "
            "nudges arrive on the same channels scammers use, so a text about "
            "connecting a bank account reads as fraud.",
            "Low-effort credit building is the strongest entry point: Experian "
            "Boost, rent reporting, utility and phone reporting.",
        ),
    },
)


OPEN_QUESTIONS: tuple[str, ...] = (
    "What actually makes a bureau escalate past a plain signed request. The "
    "access ladder assumes rung 1 usually clears; no public source confirms how "
    "often that is true.",
    "Whether a bureau honors a mid-dispute revocation of a helper's authority.",
    "Whether criminal restitution is ever furnished to a consumer reporting "
    "agency. Civil judgments are gone from reports, but restitution is a "
    "different instrument and no primary source was found either way.",
    "Whether court fines and fees are furnished, and by whom.",
    "The 6 to 9 month horizon for a credit-invisible client. Sourced to the "
    "Cornish interview, Sep 21, and not corroborated by a second source.",
    "The 32-point credit score drop per year of confinement. Cited in the team "
    "problem statement; the 50-point gap is confirmed, this one is not.",
    "What share of this population has a report error. The general rate is one "
    "in five (FTC, 2013); nobody has measured it for people coming home, and "
    "guessing would be worse than saying so.",
)
