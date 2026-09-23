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
| Free weekly reports are a voluntary bureau program, online only, so they do not help a client inside | [FTC, Free Credit Reports](https://consumer.ftc.gov/articles/free-credit-reports) |
| States must periodically report child support delinquencies to the bureaus, after notice and a chance to contest. Child support arrears do reach credit reports | [42 U.S.C. 666(a)(7)](https://www.law.cornell.edu/uscode/text/42/666) |
| Civil judgments largely vanished from credit reports after July 2017 under the National Consumer Assistance Plan; tax liens fell about half | [CFPB, Quarterly Consumer Credit Trends: Public Records](https://www.consumerfinance.gov/data-research/research-reports/quarterly-consumer-credit-trends-public-records-credit-scores-and-credit-performance/) |
| A mailed dispute carries full name with suffix, DOB, SSN and two years of addresses; Experian also asks for a government ID copy and proof of address | [Experian, Disputing by Mail](https://www.experian.com/blogs/ask-experian/credit-education/faqs/instructions-for-disputing-by-mail/) |

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

- [ ] **What actually makes a bureau escalate past a plain signed request.** The
      whole access ladder assumes rung 1 usually clears. No public source
      confirms how often that is true, and if it is wrong, the ladder is wrong.
      Experian asking for an ID copy with every mailed dispute is a hint that
      rung 2 arrives more often than the ladder assumes.
- [ ] **Whether a bureau honors a mid-dispute revocation** of a helper's
      authority. The app lets a client revoke instantly from the tablet.
- [ ] **Whether criminal restitution is ever furnished to a bureau.** Civil
      judgments are gone from reports, but restitution is a different
      instrument and no primary source was found either way.
- [ ] **Whether court fines and fees are furnished, and by whom.**
- [ ] **The 6 to 9 month horizon for a credit-invisible client.** Sourced to the
      Cornish interview, Sep 21, uncorroborated, and labelled as such in the UI.

## Settled Sep 21, by the team

- Requirements vary by person. Some clear on name and SSN alone.
- POA is one accepted route, not the gate.
- A notary is available at every facility law library.
- All three bureaus accept POA plus ID verification.

## How to handle an open item on stage

Say it is open. The app already does: every unverified number renders with its
source and the word unverified next to it, and `/citations` shows the open list
alongside the checked one. A demo that admits what it has not checked survives
a hostile question. One that does not, does not.
