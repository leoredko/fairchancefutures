# Verify before demo day

Primary sources only. This is the part that can go visibly wrong on stage, and
the one thing an audience of lawyers and counselors will catch instantly.

Nothing in the codebase cites a statute. The letter templates deliberately carry
no legal citation, and `app/letters.py` records that as a citation note on every
draft, because an unchecked citation on a letter that goes to a bureau under
somebody's signature is worse than no citation at all.

## Open

- [ ] Dispute and reinvestigation window, and what starts the clock. Referenced
      in `app/triage.py` (`PATH[ERRORS_PRESENT]`) as "a statutory reinvestigation
      window" with no number attached, on purpose.
- [ ] Whether court fines, restitution and child support report to the bureaus,
      and when. Currently `app/triage.py` routes all three to the obligations
      list and says the reporting question is unverified.
- [ ] Free report entitlement and the mail-in route. Referenced in
      `app/letters.py` (`draft_report_request`).
- [ ] What actually triggers a bureau to escalate past rung 1. The whole ladder
      in `app/authorization.py` assumes the cheap rung usually works. If that is
      wrong, the ladder is wrong.
- [ ] Which ID documents each bureau accepts at rung 2.
- [ ] Revocation procedure. The app lets a client revoke instantly from the
      tablet. Whether a bureau honors that mid-dispute is unknown.
- [ ] The 6 to 9 month horizon for a credit-invisible client. Currently sourced
      to the Cornish interview, Sep 21, and labelled as such in the UI rather
      than presented as fact.

## Settled Sep 21, by the team

- Requirements vary by person. Some clear on name and SSN alone.
- POA is one accepted route, not the gate.
- A notary is available at every facility law library.
- All three bureaus accept POA plus ID verification.

## How to handle an open item on stage

Say it is open. The app already does: every unverified number renders with its
source and the word unverified next to it. A demo that admits what it has not
checked survives a hostile question. One that does not, does not.
