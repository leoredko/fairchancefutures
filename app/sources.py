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
RELEASES_CHECKED = date(2026, 10, 6)

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
    "notary_in_the_law_library": Fact(
        key="notary_in_the_law_library",
        statement=(
            "Facilities must run a schedule that gives people in general "
            "population reasonable access to a Notary Public within 72 hours "
            "of asking, excluding weekends and holidays. People in SHU or "
            "protective custody get notarial services at least twice a week. "
            "So a document that has to be sworn can be sworn inside, without "
            "anybody on the outside."
        ),
        source="DOCCS Directive 4483, Law Libraries, Incarcerated Individual "
               "Legal Assistance and Notary Public Services, dated 2022-04-19",
        url="https://doccs.ny.gov/system/files/documents/2024/11/4483.pdf",
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
            "read on the tablet at all."
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
    # Added because the app had this backwards. It told an audience that a
    # person inside "does not have a street address that receives mail on
    # their behalf", which is not true: they receive their own mail, at the
    # facility, under their own name and DIN.
    "incoming_mail_is_inspected_not_absent": Fact(
        key="incoming_mail_is_inspected_not_absent",
        statement=(
            "A person inside receives their own mail, addressed to them at the "
            "facility under their commitment name and Department Identification "
            "Number. All incoming general correspondence is opened and "
            "inspected for cash, checks, money orders, printed or photocopied "
            "material and contraband, and the person's presence is not required "
            "for that inspection. It is not read unless the superintendent "
            "authorizes it in writing on specific grounds. Excluding weekends "
            "and holidays, letters should not be held more than 48 hours. Mail "
            "with no return address is treated as contraband and is not "
            "delivered."
        ),
        source="DOCCS Directive 4422, Incarcerated Individual Correspondence "
               "Program, dated 07/28/2021",
        url="https://doccs.ny.gov/Directives/4422.pdf",
        checked_on=date(2026, 9, 28),
    ),
    # The outgoing half of the mail correction. Bridge said a person inside
    # has outgoing mail handled for them by a family member, a friend or the
    # program. They send their own.
    "outgoing_mail_is_theirs_to_send": Fact(
        key="outgoing_mail_is_theirs_to_send",
        statement=(
            "An incarcerated individual may submit correspondence to be sent to "
            "any person or business. They address and send their own mail, "
            "printing their own return address on the envelope. Free postage is "
            "thin rather than absent: the allotment is five one-ounce domestic "
            "first class letters a week, at reception or classification "
            "facilities only, for no more than four weeks, and it cannot be "
            "accumulated week to week. Funds may be advanced for legal mail. So "
            "the obstacle to mailing a dispute is postage and paper, not "
            "permission."
        ),
        source="DOCCS Directive 4422, Incarcerated Individual Correspondence Program, dated 07/28/2021",
        url="https://doccs.ny.gov/Directives/4422.pdf",
        checked_on=date(2026, 9, 28),
    ),
    # Certified mail is the recommended default for everything Bridge asks a
    # person to post, so who pays and what it does inside both need a source.
    "certified_mail_is_at_own_expense": Fact(
        key="certified_mail_is_at_own_expense",
        statement=(
            "A person inside may send a certified or registered letter at "
            "their own expense, and will be given the return receipt, if "
            "requested, after delivery has been made. Certified or registered "
            "mail coming in is signed for by the person it is addressed to; "
            "if they refuse to sign, it goes back marked refused."
        ),
        source="DOCCS Directive 4422, Incarcerated Individual Correspondence "
               "Program, dated 07/28/2021, items 19 and 20 and section H",
        url="https://doccs.ny.gov/Directives/4422.pdf",
        checked_on=date(2026, 10, 1),
    ),
    "special_handling_is_not_advanced": Fact(
        key="special_handling_is_not_advanced",
        statement=(
            "DOCCS can advance first-class postage for legal mail to someone "
            "with insufficient funds, up to $20. Advances for special handling "
            "such as certified mail and return receipt are not approved unless "
            "a statute or court rule requires it. Whether a particular item "
            "counts as legal mail is a question for DOCCS's Office of Counsel."
        ),
        source="DOCCS Directive 2788, Collection and Repayment of Incarcerated "
               "Individual Advances and Obligations, dated 08/13/2026, section "
               "A.1",
        url="https://doccs.ny.gov/Directives/2788.pdf",
        checked_on=date(2026, 10, 1),
    ),
    # Why the identity route is closed, which is a real constraint the demo
    # shows rather than a simplification.
    "the_tablet_has_no_internet": Fact(
        key="the_tablet_has_no_internet",
        statement=(
            "A tablet inside runs on a private network that does not allow "
            "access to the internet. A bureau's web page cannot be opened from "
            "it, which closes every route a bureau offers a free citizen."
        ),
        source="DOCCS Directive 4425, Incarcerated Individual Tablet Program, dated 11/01/2022",
        url="https://doccs.ny.gov/Directives/4425.pdf",
        checked_on=date(2026, 9, 28),
    ),
    "fico_ranges_are_not_one_scale": Fact(
        key="fico_ranges_are_not_one_scale",
        statement=(
            "Base FICO scores run 300 to 850. The industry-specific scores a "
            "car lender or a card issuer pulls run 250 to 900. A number on one "
            "scale does not mean the same thing on the other, which is why a "
            "person can be told two different scores and neither is wrong."
        ),
        source="myFICO, FICO Score versions",
        url="https://www.myfico.com/credit-education/credit-scores/"
            "fico-score-versions",
        checked_on=date(2026, 9, 28),
    ),
    "birth_certificate_takes_ten_to_twelve_weeks": Fact(
        key="birth_certificate_takes_ten_to_twelve_weeks",
        statement=(
            "New York State Vital Records processes a regular-handling mail "
            "request for a certified birth certificate within ten to twelve "
            "weeks of receiving it. Bridge plans against the ten, which is the "
            "fast end of the state's own range rather than a safe estimate. A "
            "birth registered in New York City goes to a different office with "
            "its own times."
        ),
        source="NYS Department of Health, Ordering records by mail",
        url="https://www.health.ny.gov/vital_records/mailrequests.htm",
        checked_on=date(2026, 9, 28),
    ),
    "facility_record_rules": Fact(
        key="facility_record_rules",
        statement=(
            "Correctional facilities have different rules about retaining "
            "personal information, so how a person keeps a copy of their own "
            "credit report has to be checked facility by facility. This is a "
            "reason the report is read by the counselor and whoever is helping "
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

    # New York restitution, answered 2026-09-23. Three steps that together
    # close what had been the largest open question in this file. The answer
    # is "no, not by itself", and the reasoning matters more than the verdict,
    # because each step could change independently.
    "restitution_is_a_civil_judgment": Fact(
        key="restitution_is_a_civil_judgment",
        statement=(
            "In New York a restitution order becomes a civil judgment. The "
            "district attorney files a certified copy with the county clerk, "
            "who enters it in the same manner as a judgment in a civil action, "
            "and it may then be collected in the same manner as one."
        ),
        source="N.Y. Crim. Proc. Law 420.10(6)(a)",
        url="https://www.nysenate.gov/legislation/laws/CPL/420.10",
        checked_on=CHECKED,
    ),
    "restitution_collected_by_a_public_agency": Fact(
        key="restitution_collected_by_a_public_agency",
        statement=(
            "The county's chief elected official, and in New York City the "
            "mayor, must designate an official or organization other than the "
            "district attorney to collect and administer restitution. In "
            "practice that is the county probation department, whose lever for "
            "non-payment is a violation of probation rather than a credit "
            "tradeline."
        ),
        source="N.Y. Crim. Proc. Law 420.10(8); Oneida County Probation",
        url="https://oneidacountyny.gov/departments/probation/restitution/",
        checked_on=CHECKED,
    ),
    "restitution_does_not_reach_the_bureaus": Fact(
        key="restitution_does_not_reach_the_bureaus",
        statement=(
            "So a New York restitution order does not by itself reach a credit "
            "report. The judgment route is closed, because the public-record "
            "standards that took effect in July 2017 removed all civil "
            "judgments from credit reports, and the agency that collects "
            "restitution does not furnish to the bureaus. What remains is the "
            "collections route: a debt placed with a third-party collector can "
            "be reported as a collection account like any other."
        ),
        source="CFPB, A new retrospective on the removal of public records",
        url="https://www.consumerfinance.gov/about-us/blog/"
            "new-retrospective-on-removing-public-records/",
        checked_on=CHECKED,
    ),
    # ----------------------------------------------------------------------
    # Getting the documents, which gates everything else. Added 2026-09-23
    # after the vital-documents question turned out to have a real answer with
    # a real deadline attached.
    # ----------------------------------------------------------------------
    "documents_gate_the_id": Fact(
        key="documents_gate_the_id",
        statement=(
            "A birth certificate and a Social Security card must both be on "
            "file before the non-driver ID application can even be submitted. "
            "The Offender Rehabilitation Coordinator prioritizes getting them "
            "and reviews each person's document status quarterly."
        ),
        source="DOCCS and DMV Identification Card Program, Annual Legislative "
               "Report 2025",
        url="https://doccs.ny.gov/system/files/documents/2026/06/"
            "2025-doccs-dmv-identification-card-program-annual-legislative-report.pdf",
        checked_on=CHECKED,
    ),
    "social_security_card_at_120_days": Fact(
        key="social_security_card_at_120_days",
        statement=(
            "At 120 days before release, a person is encouraged to apply for a "
            "Social Security card. Anyone without a birth certificate is "
            "encouraged to apply for one at any point, and earlier is better "
            "because it is the slower of the two."
        ),
        source="DOCCS and DMV Identification Card Program, Annual Legislative "
               "Report 2025",
        url="https://doccs.ny.gov/system/files/documents/2026/06/"
            "2025-doccs-dmv-identification-card-program-annual-legislative-report.pdf",
        checked_on=CHECKED,
    ),
    "release_id_expires_at_120_days": Fact(
        key="release_id_expires_at_120_days",
        statement=(
            "The DOCCS Released Offender Identification Card expires 120 days "
            "after release. That is the window to take it to a DMV office and "
            "exchange it for a non-driver photo ID. Note that this is a "
            "different 120 days from the one before release, and confusing the "
            "two costs somebody their ID."
        ),
        source="DOCCS, Obtaining DMV Identification",
        url="https://doccs.ny.gov/obtaining-dmv-identification",
        checked_on=CHECKED,
    ),
    "birth_certificate_no_fee": Fact(
        key="birth_certificate_no_fee",
        statement=(
            "No fee is charged when DOCCS requests a certified birth "
            "certificate for somebody in anticipation of their release, and a "
            "certified copy of the sentence and commitment counts as that "
            "person's authorization, so no separate signature is needed. This "
            "covers New York records. Somebody born in another state or "
            "another country is not covered by it."
        ),
        source="N.Y. Public Health Law 4174",
        url="https://www.nysenate.gov/legislation/laws/PBH/4174",
        checked_on=CHECKED,
    ),

    # ----------------------------------------------------------------------
    # The rest of the curriculum. Every lesson card that states a rule cites
    # one of these by key, so a claim with no source cannot render.
    # ----------------------------------------------------------------------
    "negative_information_ages_off": Fact(
        key="negative_information_ages_off",
        statement=(
            "Most negative information has to come off a credit report after "
            "seven years: collection accounts and charge-offs seven years from "
            "when they first went delinquent, civil judgments and paid tax "
            "liens seven years, other adverse items seven years. Bankruptcies "
            "run ten years. The clock is counted from the original delinquency, "
            "so paying an old debt does not restart it."
        ),
        source="15 U.S.C. 1681c(a)",
        url="https://www.law.cornell.edu/uscode/text/15/1681c",
        checked_on=CHECKED,
    ),
    "who_may_pull_a_report": Fact(
        key="who_may_pull_a_report",
        statement=(
            "A credit report may only be given out for a purpose the law "
            "lists: a credit application, an insurance decision, employment "
            "with the person's written permission, a court order, child "
            "support enforcement, or the person's own written instructions. "
            "Curiosity is not on the list."
        ),
        source="15 U.S.C. 1681b(a)",
        url="https://www.law.cornell.edu/uscode/text/15/1681b",
        checked_on=CHECKED,
    ),
    "employer_needs_written_permission": Fact(
        key="employer_needs_written_permission",
        statement=(
            "An employer cannot pull a credit report without telling the "
            "person clearly and in writing and getting written permission "
            "first. If they then decide against hiring based on it, they have "
            "to hand over a copy of the report and a written statement of the "
            "person's rights before they act on it."
        ),
        source="15 U.S.C. 1681b(b)(2)-(3)",
        url="https://www.law.cornell.edu/uscode/text/15/1681b",
        checked_on=CHECKED,
    ),
    "free_report_after_a_denial": Fact(
        key="free_report_after_a_denial",
        statement=(
            "Turned down for credit, an apartment, insurance or a job because "
            "of a credit report? The bureau has to give a free copy of that "
            "file, on request within 60 days of being told about the decision."
        ),
        source="15 U.S.C. 1681j(b)",
        url="https://www.law.cornell.edu/uscode/text/15/1681j",
        checked_on=CHECKED,
    ),
    "free_report_unemployed_or_on_assistance": Fact(
        key="free_report_unemployed_or_on_assistance",
        statement=(
            "A free report is also owed, once every 12 months, to anybody who "
            "certifies in writing that they are unemployed and intend to look "
            "for work in the next 60 days, that they receive public welfare "
            "assistance, or that they believe their file contains errors from "
            "fraud. Somebody coming home often qualifies under more than one."
        ),
        source="15 U.S.C. 1681j(c)",
        url="https://www.law.cornell.edu/uscode/text/15/1681j",
        checked_on=CHECKED,
    ),
    "score_factor_weights": Fact(
        key="score_factor_weights",
        statement=(
            "A FICO score is built from five things: payment history about 35 "
            "percent, how much is owed against available credit about 30 "
            "percent, length of credit history about 15 percent, credit mix "
            "about 10 percent, and new credit about 10 percent. Those weights "
            "are for the general population and shift depending on what is in "
            "a particular file."
        ),
        source="myFICO, What is in my FICO Scores",
        url="https://www.myfico.com/credit-education/whats-in-your-credit-score",
        checked_on=CHECKED,
    ),
    "credit_repair_cannot_charge_up_front": Fact(
        key="credit_repair_cannot_charge_up_front",
        statement=(
            "A credit repair company may not take any money before the service "
            "it promised has been fully performed. It also may not tell a "
            "person to misstate their credit history, or advise them to alter "
            "their identifying information to hide a bad record. Both are "
            "prohibited outright."
        ),
        source="15 U.S.C. 1679b(a)-(b)",
        url="https://www.law.cornell.edu/uscode/text/15/1679b",
        checked_on=CHECKED,
    ),
    "security_freeze_is_free": Fact(
        key="security_freeze_is_free",
        statement=(
            "A security freeze stops new credit being opened in somebody's "
            "name and must be placed free of charge, within one business day "
            "of an electronic or phone request and three business days of a "
            "mailed one. Lifting it is free too, within one hour "
            "electronically."
        ),
        source="15 U.S.C. 1681c-1",
        url="https://www.law.cornell.edu/uscode/text/15/1681c-1",
        checked_on=CHECKED,
    ),
    "extended_fraud_alert": Fact(
        key="extended_fraud_alert",
        statement=(
            "An initial fraud alert lasts at least one year and comes with a "
            "free copy of the file. Somebody who files an identity theft "
            "report can get an extended alert that lasts seven years, comes "
            "with two free copies in the first 12 months, and keeps their name "
            "off unsolicited credit offers for five years."
        ),
        source="15 U.S.C. 1681c-1",
        url="https://www.law.cornell.edu/uscode/text/15/1681c-1",
        checked_on=CHECKED,
    ),
    "dispute_outcomes": Fact(
        key="dispute_outcomes",
        statement=(
            "In the FTC's 2013 study, about one in four consumers identified "
            "at least one potential material error on a credit report. One in "
            "five had an error that the agency corrected after they disputed "
            "it. About one in twenty had errors serious enough to mean less "
            "favorable terms on a loan. The one-in-five figure is the share "
            "whose error was corrected, which is not the same as the share who "
            "had one."
        ),
        source="FTC, Section 319 of the Fair and Accurate Credit Transactions "
               "Act of 2003: Fifth Interim Report to Congress, February 2013",
        url="https://www.ftc.gov/reports/section-319-fair-accurate-credit-"
            "transactions-act-2003-fifth-interim-federal-trade-commission-report",
        checked_on=CHECKED,
    ),

    "lookup_returns_the_sentence_dates": Fact(
        key="lookup_returns_the_sentence_dates",
        statement=(
            "The DOCCS incarcerated lookup answers on a DIN with the housing "
            "or releasing facility, the date received, the earliest release "
            "date, the parole eligibility date, the conditional release date, "
            "the maximum expiration date and the post-release supervision "
            "maximum expiration date. So none of those need to be typed in "
            "from memory by the person they belong to."
        ),
        source="DOCCS, Inmate Information Data Definitions",
        url="https://publicapps.doccs.ny.gov/ILookup/fpmsdoc.html",
        checked_on=CHECKED,
    ),
    "lookup_returns_no_date_of_birth": Fact(
        key="lookup_returns_no_date_of_birth",
        statement=(
            "The lookup does not return a date of birth. A search can be "
            "narrowed by year of birth, but the record that comes back does "
            "not carry a DOB. So a date of birth in this app never came from "
            "the lookup: it comes from the coordinator's own record."
        ),
        source="DOCCS, Inmate Information Data Definitions",
        url="https://publicapps.doccs.ny.gov/ILookup/fpmsdoc.html",
        checked_on=CHECKED,
    ),
    "parole_eligibility_is_not_a_release_date": Fact(
        key="parole_eligibility_is_not_a_release_date",
        statement=(
            "Parole eligibility is the point at which somebody becomes "
            "eligible after serving their minimum term, not a date they go "
            "home on. The conditional release date is the one a reentry plan "
            "is built around, and the Time Allowance Committee considers "
            "somebody four months before it."
        ),
        source="DOCCS, Inmate Information Data Definitions",
        url="https://publicapps.doccs.ny.gov/ILookup/fpmsdoc.html",
        checked_on=CHECKED,
    ),
    "doccs_releases_2025": Fact(
        key="doccs_releases_2025",
        statement=(
            "DOCCS released 10,275 incarcerated individuals from its "
            "facilities in calendar year 2025, 454 more (4.6%) than the 9,821 "
            "in 2024. Of those, 9,412 went to community supervision (3,762 on "
            "parole, 4,811 on conditional release, 839 at maximum expiration "
            "with post-release supervision) and 863 did not. Incarcerated "
            "parolee releases are counted separately, in a different table. "
            "This is a count of people leaving, and says nothing about the "
            "state of their credit."
        ),
        source="NYS DOCCS, Admissions and Releases, Calendar Year 2025, "
               "Tables 4 and 8",
        url="https://doccs.ny.gov/system/files/documents/2026/06/"
            "admissions-and-releases-report-calendar-year-2025_final.pdf",
        checked_on=RELEASES_CHECKED,
    ),
    "cany_release_file": Fact(
        key="cany_release_file",
        statement=(
            "The Correctional Association of New York publishes a "
            "de-identified, release-level file derived from DOCCS data, "
            "January 2016 to the present, with the releasing facility, "
            "release type and county of commitment. Summed by the team on "
            "2026-10-06 it counts 10,042 releases in 2025 and 9,658 in 2024. "
            "Its own data dictionary warns it does not match DOCCS's "
            "published totals exactly (3% apart in 2022), so the DOCCS "
            "report is the number to quote and this file is for breakdowns "
            "such as one facility's releases."
        ),
        source="Correctional Association of New York, Data Portal: Releases "
               "(CSV and data dictionary)",
        url="https://www.correctionalassociation.org/data-download",
        checked_on=RELEASES_CHECKED,
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
@dataclass(frozen=True)
class SurveyFinding:
    """One thing a survey supports, carrying the count it rests on.

    The count sits on the record rather than inside the sentence so a reader
    can do the division themselves, and so a test can refuse a finding that
    claims more responses than the survey collected. Thirteen people is a
    number you say out loud, not a percentage you hide behind.
    """

    statement: str
    count: int
    of: int

    def cite(self) -> str:
        return f"{self.statement} ({self.count} of {self.of})"


@dataclass(frozen=True)
class Survey:
    """Field evidence, and a third kind of it.

    A statute is a statute. The Cornish interview is one practitioner. This is
    a small number of people who have the problem, answering the same questions
    as each other, which is the only one of the three that produces counts.
    None of them substitutes for another, so each is labelled by kind wherever
    it is cited.
    """

    key: str
    title: str
    who_ran_it: str
    where: str
    fielded: str
    responses: int
    method: str
    findings: tuple[SurveyFinding, ...]
    limitations: tuple[str, ...]


# Run by a fellow of this cohort among people inside his own facility, which is
# why it exists at all: nobody on this team could have collected it. It is the
# only evidence Bridge has from people who actually have the problem, and the
# first thing it did was correct us. We had assumed people inside would not
# know a free report existed. Eleven of thirteen did. The gap is not that the
# entitlement is unknown, it is that knowing about it changes nothing from a
# tablet with no route out, and that almost nobody knows what to do with an
# error once they are looking at one.
SURVEYS: tuple[Survey, ...] = (
    Survey(
        key="maine_peer_survey",
        title="Bridge: Credit and Reentry Interest Survey",
        who_ran_it=(
            "A fellow of the 2026 Fair Chance Futures AI Lab cohort, among "
            "people incarcerated alongside him"
        ),
        where="A correctional facility in Maine, not named on this record",
        fielded="2026-09-25 to 2026-09-27",
        responses=13,
        method=(
            "A Google Form, answered directly by people inside. Peer "
            "administered rather than run by this team."
        ),
        findings=(
            SurveyFinding(
                "Named money and credit a priority before release, more than "
                "chose any other option, ahead of work, family relationships "
                "and housing.",
                9, 13,
            ),
            SurveyFinding(
                "Would not know what to do next after finding a mistake on a "
                "credit report, answering no or only somewhat.",
                8, 13,
            ),
            SurveyFinding(
                "Want to see their credit report before release. One person "
                "skipped the question, so this one is out of twelve.",
                9, 12,
            ),
            SurveyFinding(
                "Have seen their own credit report at any point while they "
                "have been inside.",
                2, 13,
            ),
            SurveyFinding(
                "Already knew a free annual copy can be requested from each of "
                "the three nationwide bureaus.",
                11, 13,
            ),
            SurveyFinding(
                "Would rather work through an application on their own than "
                "take any of the offered kinds of help, the most common answer.",
                5, 13,
            ),
            SurveyFinding(
                "Chose asking family or a friend as the help they would most "
                "want, the least common answer but one.",
                1, 13,
            ),
        ),
        limitations=(
            "Thirteen responses from one facility in Maine. Bridge is built "
            "for New York State, and nothing here establishes anything about "
            "a DOCCS population or about people coming home generally.",

            "A convenience sample. These are people one fellow could reach, "
            "who chose to answer. Nobody was sampled at random.",

            "Both free-text questions came back empty on all thirteen "
            "responses: the one asking what would make the tool hard to use, "
            "and the one asking for an estimated release date. The survey "
            "produced counts and not one quotation.",

            "Knowledge is self-reported. Eleven said they knew about the free "
            "annual copy; nobody was asked to name the route, and the mail "
            "route is the only one that works from inside.",

            "The name of the fellow who ran it is not on this record yet, and "
            "neither is how consent was taken. Both belong here before this "
            "is cited outside the team.",
        ),
    ),
)


INTERVIEWS: tuple[dict, str] = (
    {
        "who": "Briane Cornish, founder and executive director, finEQUITY",
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


# What this build assumes rather than establishes.
#
# Different from an open question. An open question is something nobody has
# answered and somebody should. A simplification is something we looked at,
# decided not to model, and chose to carry anyway, because this is a capstone
# on a deadline and not a deployment.
#
# Written down for one reason: so the next person does not spend an afternoon
# discovering the gap and thinking they found a bug, and so nobody on stage is
# caught claiming more than the build does. Each one names what is assumed and
# what is actually the case.
SIMPLIFICATIONS: tuple[str, ...] = (
    "Bridge assumes the tablet is online, so a write lands when it is made "
    "and the course keeps a place without a queue. The real device is more "
    "limited than that and everything on it is monitored. Modelling the "
    "difference means caching the app shell and replaying writes later, which "
    "is real work and is not built. The browser build behaves exactly as "
    "written; a deployment would not.",

    "Bridge assumes a person on the caseload has a tablet and can reach it. "
    "Access is not universal in practice. This build has no separate path for "
    "somebody without one.",

    "How Bridge would be provisioned onto a facility tablet is not "
    "established. The browser build is how it is developed and shown.",

    "Mail tracking is a stand-in. `app/mailing.py` returns a status and an "
    "expected date worked out from the mailing date, never from a carrier. "
    "Integration with live tracking APIs for the major carriers is pending; "
    "USPS's, for one, needs a registered application, an OAuth token and a "
    "separate access request that this build does not have. The screen is "
    "real and the status behind it is not.",
)

OPEN_QUESTIONS: tuple[str, ...] = (
    "Whether a bureau dispute is legal mail. Directive 2788 is ambiguous on "
    "it. The team's working understanding, from experience and not in "
    "writing, is that a person can mark outgoing mail as legal mail and it "
    "goes out as long as it is not addressed to a private residence, which a "
    "bureau's address is not. Nothing on a screen states it. Certified service "
    "is not advanced either way unless a statute or court rule requires it.",
    "What USPS itself says Certified Mail and a return receipt provide. The "
    "product recommends both so there is a record of sending that nobody "
    "inside the product wrote, but the Domestic Mail Manual wording has not "
    "been read from usps.com, which this build's tooling cannot reach.",
    "What actually makes a bureau escalate past a plain signed request. No "
    "public source says how often a plain request clears, and Experian asks "
    "for an ID copy with every mailed dispute regardless. This used to be "
    "load-bearing: a four-rung access ladder was built on the assumption that "
    "the cheapest route usually works. The ladder is gone and the product now "
    "turns on document readiness instead, which is knowable, so this is a "
    "question worth answering rather than a hole under the design.",
    "Whether a bureau honors a mid-dispute revocation of an outside "
    "person's authority.",
    "Whether any New York county has designated a private collection agency, "
    "rather than its probation department, to collect restitution. That is the "
    "one route by which restitution could reach a credit report, and the "
    "designation is made county by county.",
    "Whether court fines and fees are furnished, and by whom.",
    "The 6 to 9 month horizon for a credit-invisible client. Sourced to the "
    "Cornish interview, Sep 21, and not corroborated by a second source.",
    "The 32-point credit score drop per year of confinement. Cited in the team "
    "problem statement; the 50-point gap is confirmed, this one is not.",
    "What share of this population has a report error. The general rate is one "
    "in five (FTC, 2013); nobody has measured it for people coming home, and "
    "guessing would be worse than saying so.",
)
