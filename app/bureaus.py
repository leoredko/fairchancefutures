"""The three nationwide credit reporting agencies.

A dispute goes to all three, not to one. The previous build hardcoded Equifax
in two places, which quietly misrepresented the workflow on the exact screen
where the workflow is the point.

Addresses were read from each bureau's own page or its own mail-label document.
They move without announcement, so each one carries the URL it came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

CHECKED = date(2026, 9, 23)


@dataclass(frozen=True)
class Bureau:
    key: str
    name: str
    dispute_address: tuple[str, ...]
    source_url: str
    note: str = ""

    @property
    def address_block(self) -> str:
        return "\n".join(self.dispute_address)


BUREAUS: tuple[Bureau, ...] = (
    Bureau(
        key="equifax",
        name="Equifax",
        dispute_address=(
            "Equifax Information Services, LLC",
            "P.O. Box 740256",
            "Atlanta, GA 30374-0256",
        ),
        source_url="https://www.equifax.com/personal/help/article-list/-/h/a/"
                   "mail-in-credit-report-dispute/",
    ),
    Bureau(
        key="experian",
        name="Experian",
        dispute_address=(
            "Experian",
            "P.O. Box 4500",
            "Allen, TX 75013",
        ),
        source_url="https://www.experian.com/blogs/ask-experian/credit-education/"
                   "faqs/instructions-for-disputing-by-mail/",
        note="Experian also asks for a copy of a government-issued ID and a "
             "proof of current address with a mailed dispute. That is rung 2 of "
             "the access ladder arriving in the envelope.",
    ),
    Bureau(
        key="transunion",
        name="TransUnion",
        dispute_address=(
            "TransUnion Consumer Solutions",
            "P.O. Box 2000",
            "Chester, PA 19016-2000",
        ),
        source_url="https://www.transunion.com/credit-disputes/dispute-your-credit/"
                   "mail-or-phone",
        note="Address taken from TransUnion's own mail-label document. Their "
             "site blocks automated fetching, so re-read it by hand before a "
             "real letter goes out.",
    ),
)

BY_KEY: dict[str, Bureau] = {b.key: b for b in BUREAUS}

# The free-report request does not go to the bureaus individually. It goes to
# the centralized source, which is the only route that works without internet.
ANNUAL_REPORT_REQUEST = Bureau(
    key="annual_report_request",
    name="Annual Credit Report Request Service",
    dispute_address=(
        "Annual Credit Report Request Service",
        "P.O. Box 105281",
        "Atlanta, GA 30348-5281",
    ),
    source_url="https://consumer.ftc.gov/articles/free-credit-reports",
    note="Use the Annual Credit Report Request Form. One request covers all "
         "three bureaus.",
)


def get(key: str) -> Bureau:
    return BY_KEY[key]
