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
    "Cornish interview, Sep 21, and not corroborated.",
)
