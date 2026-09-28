# Verify before demo day

Primary sources only. This is the part that can go visibly wrong on stage, and
the one thing an audience of lawyers and counselors will catch instantly.

The live version of this page is `/citations` in the running app, generated
from `app/sources.py`. Nothing in the app states a legal fact unless it is in
that registry with a URL and a date.

## Checked, 2026-09-23

| Claim | Source |
| --- | --- |
| A bureau has 30 days to complete a reinvestigation, counted from the day it **receives** the dispute, not from the postmark | [15 U.S.C. 1681i(a)(1)(A)](https://www.law.cornell.edu/uscode/text/15/1681i) |
| Extendable by up to 15 more days if the consumer sends relevant information during the 30 days, so sending more paperwork mid-dispute can push the deadline to 45 | [15 U.S.C. 1681i(a)(1)(B)](https://www.law.cornell.edu/uscode/text/15/1681i) |
| Written results within 5 business days of completing the reinvestigation; inaccurate, incomplete or unverifiable items must be promptly deleted or modified | [15 U.S.C. 1681i(a)(5)-(6)](https://www.law.cornell.edu/uscode/text/15/1681i) |
| One free file disclosure per 12 months per nationwide agency, through the centralized source, delivered within 15 days of the request | [15 U.S.C. 1681j(a)](https://www.law.cornell.edu/uscode/text/15/1681j) |
| The mail route is the Annual Credit Report Request Form to Annual Credit Report Request Service, P.O. Box 105281, Atlanta, GA 30348-5281 | [FTC, Free Credit Reports](https://consumer.ftc.gov/articles/free-credit-reports) |
| **A notary is available inside.** Facilities must schedule reasonable access to a Notary Public within 72 hours of the request for general population, and at least twice a week for SHU and protective custody. A document that has to be sworn can be sworn without anybody outside | [DOCCS Directive 4483](https://doccs.ny.gov/system/files/documents/2024/11/4483.pdf) |
| **New York restitution is docketed as a civil judgment**: the DA files a certified copy with the county clerk, who enters it as a judgment in a civil action, collectible as one | [N.Y. Crim. Proc. Law 420.10(6)(a)](https://www.nysenate.gov/legislation/laws/CPL/420.10) |
| The county's chief elected official, the mayor in New York City, designates who collects it, other than the DA. In practice the county probation department, whose answer to non-payment is a violation of probation rather than a tradeline | [CPL 420.10(8)](https://www.nysenate.gov/legislation/laws/CPL/420.10), [Oneida County Probation](https://oneidacountyny.gov/departments/probation/restitution/) |
| **So restitution does not by itself reach a credit report.** The judgment route closed when all civil judgments came off reports in July 2017, and the collecting agency does not furnish. The collections route stays open: a debt placed with a third-party collector can be reported like any other | [CFPB, removal of public records](https://www.consumerfinance.gov/about-us/blog/new-retrospective-on-removing-public-records/) |
| Free weekly reports are a voluntary bureau program, online only, so they do not help a client inside | [FTC, Free Credit Reports](https://consumer.ftc.gov/articles/free-credit-reports) |
| States must periodically report child support delinquencies to the bureaus, after notice and a chance to contest. Child support arrears do reach credit reports | [42 U.S.C. 666(a)(7)](https://www.law.cornell.edu/uscode/text/42/666) |
| Civil judgments largely vanished from credit reports after July 2017 under the National Consumer Assistance Plan; tax liens fell about half | [CFPB, Quarterly Consumer Credit Trends: Public Records](https://www.consumerfinance.gov/data-research/research-reports/quarterly-consumer-credit-trends-public-records-credit-scores-and-credit-performance/) |
| A mailed dispute carries full name with suffix, DOB, SSN and two years of addresses; Experian also asks for a government ID copy and proof of address | [Experian, Disputing by Mail](https://www.experian.com/blogs/ask-experian/credit-education/faqs/instructions-for-disputing-by-mail/) |

### Getting the documents, checked 2026-09-23

This is the chain that gates everything else, and it is what replaced the
access ladder. Added when the vital-documents question turned out to have a
real answer with a real deadline on it.

| Claim | Source |
| --- | --- |
| A birth certificate **and** a Social Security card must both be on file **before** the non-driver ID application can be submitted. The Offender Rehabilitation Coordinator prioritizes getting them and reviews each person's document status **quarterly** | [DOCCS and DMV Identification Card Program, Annual Legislative Report 2025](https://doccs.ny.gov/system/files/documents/2026/06/2025-doccs-dmv-identification-card-program-annual-legislative-report.pdf) |
| **At 120 days before release**, a person is encouraged to apply for a Social Security card. Anyone without a birth certificate is encouraged to apply at any point | same report |
| Scale and engagement: about 3,700 IDs since the program began in 2022; 1,061 issued May 2025 to April 2026, a 15% decline attributed to staffing; **493 people declined to engage** with the application process in that year | same report |
| **The other 120 days.** The DOCCS Released Offender Identification Card expires 120 days *after* release, which is the window to exchange it at a DMV office. Two clocks, opposite sides of the gate, and confusing them costs somebody their ID | [DOCCS, Obtaining DMV Identification](https://doccs.ny.gov/obtaining-dmv-identification) |
| No fee is charged when DOCCS requests a certified birth certificate in anticipation of release, and a certified copy of the sentence and commitment counts as the person's authorization, so no separate signature is needed | [N.Y. Public Health Law 4174](https://www.nysenate.gov/legislation/laws/PBH/4174) |
| That waiver covers **New York** records. Somebody born in another state or country is not covered by it | Same statute, which governs records registered under that chapter. Stated as a limit of the statute rather than as a claim about what other states do |

### What the DIN already answers, checked 2026-09-23

Nobody should be asked to retype their own release date from memory on a
metered tablet. `app/doccs.py` holds this; `simulated_lookup()` is the one
function a real integration replaces.

| Claim | Source |
| --- | --- |
| The lookup answers on a DIN with the housing or releasing facility, date received (original and current), earliest release date, parole eligibility date, conditional release date, maximum expiration date, and post-release supervision maximum expiration date | [DOCCS, Inmate Information Data Definitions](https://publicapps.doccs.ny.gov/ILookup/fpmsdoc.html) |
| **It does not return a date of birth.** A search can be narrowed by year of birth, but the record that comes back carries no DOB. So a date of birth in this app never came from the lookup; it comes from the coordinator's own record | same page |
| **Parole eligibility is not a release date.** It is the point at which somebody becomes eligible after serving their minimum term. The conditional release date is what a reentry plan is built around, and the Time Allowance Committee considers somebody four months before it | same page |

Two consequences the code depends on. The line-of-sight rule holds here by
construction rather than by a check, because there is no DOB on the record to
render. And Bridge plans against the conditional release date, falling back to
the earliest release date, never parole eligibility, and the screen names which
one it used.

Note on the open FPMS question below: this page's URL path contains `fpmsdoc`,
but the page itself says only that the data comes from "the Department's 'live'
computer data base" and names no system. So the question stays open rather than
being answered by a URL.

### The curriculum, checked 2026-09-23

Every lesson card that states a rule cites one of these by key, and a test
fails if a card cites a key that is not in the registry.

| Claim | Source |
| --- | --- |
| Most negative information comes off after **seven years**, counted from the original delinquency; bankruptcies run **ten**. Paying an old debt does not restart the clock | [15 U.S.C. 1681c(a)](https://www.law.cornell.edu/uscode/text/15/1681c) |
| A report may only be furnished for a listed permissible purpose | [15 U.S.C. 1681b(a)](https://www.law.cornell.edu/uscode/text/15/1681b) |
| An employer needs clear written disclosure and written permission first, and must hand over a copy of the report and a statement of rights **before** acting adversely on it | [15 U.S.C. 1681b(b)(2)-(3)](https://www.law.cornell.edu/uscode/text/15/1681b) |
| Denied credit, housing, insurance or a job because of a report? A free copy of that file, on request within **60 days** | [15 U.S.C. 1681j(b)](https://www.law.cornell.edu/uscode/text/15/1681j) |
| A further free report once a year for anyone certifying in writing that they are **unemployed and job-hunting within 60 days**, **receiving public welfare assistance**, or that their file has **fraud-related errors**. Somebody just home often qualifies under more than one | [15 U.S.C. 1681j(c)](https://www.law.cornell.edu/uscode/text/15/1681j) |
| A FICO score is about 35% payment history, 30% amounts owed, 15% length of history, 10% credit mix, 10% new credit, for the general population | [myFICO, What is in my FICO Scores](https://www.myfico.com/credit-education/whats-in-your-credit-score) |
| A credit repair organization may not take any money before the service is fully performed, may not tell a person to misstate their history, and may not advise altering identifying information to hide a record | [15 U.S.C. 1679b(a)-(b)](https://www.law.cornell.edu/uscode/text/15/1679b) |
| A security freeze is free, placed within 1 business day of an electronic or phone request and 3 of a mailed one, and lifted within 1 hour electronically | [15 U.S.C. 1681c-1](https://www.law.cornell.edu/uscode/text/15/1681c-1) |
| An initial fraud alert lasts at least 1 year with a free file copy; an extended alert lasts 7 years, with 2 free copies in the first 12 months and 5 years off unsolicited offers | [15 U.S.C. 1681c-1](https://www.law.cornell.edu/uscode/text/15/1681c-1) |
| **Corrected.** About **one in four** consumers identified at least one potential material error. **One in five** had an error *corrected after disputing*, which is not the same thing. About **one in twenty** had errors serious enough to mean less favorable loan terms | [FTC, Section 319 FACTA Fifth Interim Report, February 2013](https://www.ftc.gov/reports/section-319-fair-accurate-credit-transactions-act-2003-fifth-interim-federal-trade-commission-report) |

The team problem statement has that last one the wrong way round: it reads
"one in five consumers has an error", which is the corrected-after-dispute
figure. Worth fixing on the slide before anyone in the audience checks.

### Bureau dispute addresses, checked 2026-09-23

| Bureau | Address | Source |
| --- | --- | --- |
| Equifax | Equifax Information Services, LLC, P.O. Box 740256, Atlanta, GA 30374-0256 | [equifax.com](https://www.equifax.com/personal/help/article-list/-/h/a/mail-in-credit-report-dispute/) |
| Experian | Experian, P.O. Box 4500, Allen, TX 75013 | [experian.com](https://www.experian.com/blogs/ask-experian/credit-education/faqs/instructions-for-disputing-by-mail/) |
| TransUnion | TransUnion Consumer Solutions, P.O. Box 2000, Chester, PA 19016-2000 | [transunion.com](https://www.transunion.com/credit-disputes/dispute-your-credit/mail-or-phone) |

TransUnion's site refuses automated fetching, so their address came from the
title of their own mail-label document rather than from a page that was read
directly. Re-read it by hand before a real letter goes in an envelope. These
addresses move without announcement; re-check anything older than six months.

## Still open

The app asserts none of these. Where one would be needed, the screen says so.

- [ ] **What actually makes a bureau escalate past a plain signed request.** No
      public source says how often a plain request clears, and Experian asks
      for an ID copy with every mailed dispute regardless. This used to be
      load-bearing: a four-rung access ladder rested on the assumption that the
      cheapest route usually works. **The ladder is gone.** The product now
      turns on document readiness, which is knowable and already tracked
      quarterly, so this is a question worth answering rather than a hole
      underneath the design.
- [ ] **Whether a bureau honors a mid-dispute revocation** of a helper's
      authority. The app lets a client revoke instantly from the tablet.
- [ ] **Whether any New York county has designated a private collection
      agency**, rather than its probation department, to collect restitution.
      That is the one route by which restitution could reach a credit report,
      and the designation is made county by county. Answering it means asking
      counties, not reading a statute.
- [ ] **Whether court fines and fees are furnished, and by whom.**
- [ ] **The 6 to 9 month horizon for a credit-invisible client.** Sourced to the
      Cornish interview, Sep 21, uncorroborated, and labelled as such in the UI.
- [ ] **Whether the free non-driver ID for people on public assistance, SNAP or
      Medicaid exists as this repo used to claim**, dated October 2020. Could
      not verify it. What the primary sources describe is a different thing: a
      DOCCS and DMV program established in 2022 that produces an ID before
      release once the birth certificate and Social Security card are on file.
      The claim has been removed rather than left standing.

## Corroborated since, and worth saying out loud

The Cornish interview's strongest claim, that **engagement is the unsolved
problem rather than the technology**, now has independent support from a state
agency's own reporting: 493 people declined to engage with the pre-release ID
application in a single year, against 1,061 issued. Roughly one in three people
who could have walked out with a state ID said no. That is not a documents
problem.

## Settled Sep 21, by the team

- Requirements vary by person. Some clear on name and SSN alone.
- POA is one accepted route, not the gate.
- A notary is available at every facility law library.
- All three bureaus accept POA plus ID verification.

### Free counseling after release, checked 2026-09-24

The Financial Empowerment Center model is municipal, free, and does credit work
rather than general social services, which makes it the natural successor when
a dispute clock is still running on the day somebody walks out.

| Place | Eligibility as its operator words it | Source |
| --- | --- | --- |
| New York City | "You qualify for free counseling if you're at least age 18 and live or work in NYC." No income test, no immigration requirement. | [access.nyc.gov](https://access.nyc.gov/programs/nyc-financial-empowerment-centers/) |
| Syracuse | "free, one-on-one professional financial counseling to all City of Syracuse residents" | [syr.gov](https://www.syr.gov/Departments/NBD/Syracuse-FEC) |
| Rochester | 18 and over who live, work, worship or go to school in Monroe County | [cityofrochester.gov](https://www.cityofrochester.gov/departments/office-financial-empowerment/financial-empowerment-center) |
| Mount Vernon | Not read | [fecpublic.org](https://fecpublic.org/about/) |
| Buffalo | **Not open.** Entered the CFE Fund's FEC Academy Dec 2022, operator RFP issued 2025 | [buffalony.gov](https://www.buffalony.gov/m/newsflash/home/detail/1584) |

**Two of these have not been read first hand.** Rochester's site refuses
automated fetching, the same situation as the TransUnion address above, so its
eligibility line came from search results rather than from the page. Mount
Vernon is listed as an operating partner but its wording was never read, so the
eligibility field is blank rather than guessed. Both carry
`verified_by_hand=False` in `app/centers.py` and a test fails if either is
treated as checked. Somebody has to open them in a browser.

**Most of New York State has no municipal center.** `for_county` returns
nothing rather than the nearest big city, because sending somebody who just
came home on a long bus ride to a desk that will turn them away is worse than
saying there is nothing here.

### The NYC Open Data set is not a source, checked 2026-09-24

[NYC Open Data `dt2z-amuf`](https://data.cityofnewyork.us/d/dt2z-amuf) responds
and returns 23 rows. **Its rows have not changed since 2017-11-27**, which is
over 3,200 days. One of its five providers, The Financial Clinic, now operates
as Change Machine. The catalog's own `updatedAt` reads 2022, but that ticks
when somebody edits the description; only `rowsUpdatedAt` says when a row moved.

Meanwhile the city no longer publishes a location list on its own pages. Both
the old and current DCWP pages route a person to 311 or the booking portal. So
there is no current official list to reconcile the dataset against: it is not a
live feed running behind, it is an old snapshot with a JSON endpoint.

Bridge therefore reads it and never serves it.
`scripts/check_centers.py` fetches it, diffs it against the registry and
prints. It exits non-zero when it finds something, so a scheduled run fails
loudly. `app/centers.py` imports no HTTP library at all, and a test fails if
that changes.

## The DOCCS facility list, checked 2026-09-28

The facility is the return address on a dispute letter, so it is an address
under the same rule as the bureaus and the counseling centers rather than a
label on a record.

Read from the DOCCS facility pages, one page per facility, off
[Find a facility](https://doccs.ny.gov/find-facility). Forty-one facilities.
Each entry in `app/facilities.py` carries the DOCCS name, the security level,
the population it holds in DOCCS' own wording, and the mailing address.
`app/freshness.py` watches the check date on the six-month address window.

| Claim | Source |
| --- | --- |
| DOCCS currently operates **41** correctional facilities | [DOCCS, Find a facility](https://doccs.ny.gov/find-facility) |
| **Three of them hold women**: Albion, Bedford Hills and Taconic. Every other facility on the list is for men | each facility's own DOCCS page, which states "a *level* security level facility for males/females" |
| **Downstate Correctional Facility is not among them.** It closed in 2022 and is not on the DOCCS list | same; its absence from the list is the claim, and nothing here asserts a closure date beyond that |

What this replaced: eight facility names typed by hand next to a free-text
box that accepted anything. One of the eight had closed, the list mixed
facilities for men and for women with nothing marking which was which, and
`app/doccs.py` picked one by hashing the DIN. That put Marcus, who is a man,
in Bedford Hills. A hash is right one time in forty-one.

The lookup now returns no facility at all. Nothing in it knows who the person
is, so nothing in it names where they are held; a coordinator sets it from the
list, and until they do the tablet says so rather than showing a guess.

## How to handle an open item on stage

Say it is open. The app already does: every unverified number renders with its
source and the word unverified next to it, and `/citations` shows the open list
alongside the checked one. A demo that admits what it has not checked survives
a hostile question. One that does not, does not.
