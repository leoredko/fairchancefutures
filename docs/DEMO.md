# Driving it

Sign-ins for the seeded caseload. These are not shown in the application,
because seeded logins on a landing page make a product look like a sample.

## Any DIN starting 28 works

2028 has not happened, so a DIN in that range cannot belong to a real person in
the public DOCCS lookup. Type any one of them into the tablet app and a case
opens on the spot, with a PIN you choose.

    28-A-1187      28-Q-7788      28-K-0001      any 28-?-####

Anything outside that range is never auto-created, because it could be somebody
real. Those are added by a coordinator from **New intake**.

## The seeded caseload

| Who | Signs in with | Where |
| --- | --- | --- |
| Marcus W. | DIN `28-A-1187` or NYSID `00000011L` | tablet |
| M. Alvarez | DIN `28-B-0042` | tablet |
| J. Whitfield, not yet triaged | DIN `28-A-0931` | tablet |
| Denise, helping Marcus | code `BRIDGE-4417` | phone |
| Rosa, helping M. Alvarez | code `BRIDGE-8802` | phone |
| D. Reyes, coordinator | staff ID `REYES` | desktop |

Everyone picks their own PIN the first time. Six digits, not all the same, not
a run, and not a stretch of their own number.

## A walkthrough that shows the whole thing

1. **Coordinator** opens the staff app, signs in as `REYES`, and uses
   **New intake** to add somebody. Note the helper code it issues.
2. **That person** opens the tablet app, signs in with the DIN just entered,
   picks a PIN, and answers the six intake questions.
3. **Coordinator** opens them from the queue and runs triage. Six answers, one
   of four states, with the path attached. Errors jump the queue.
4. **Coordinator** drafts the dispute letters. One flagged item produces three
   letters, one per bureau. Edit one before approving and watch the edit rate
   on `/metrics` move.
5. **Helper** opens the phone app with the code, agrees to the scoped
   authorization, and prints the packet. The prisoner ID is on the envelope
   instructions, which is what the bureaus ask for on mail from a facility.
6. **That person** cancels the authorization from the tablet. The helper loses
   access on their next tap.

Close every tab and reopen them. Everything is still there.

## Three files, one caseload

`standalone/bridge-inside.html`, `bridge-family.html` and `bridge-staff.html`
are three separate applications, the way they would be deployed separately in
the real thing. Served from the same folder or the same host they share one
caseload, so a client the coordinator adds appears on the tablet. Each keeps
its own session, so signing in on one does not sign you out of another.

Published to three different origins they cannot see each other. For a
walkthrough that crosses roles, open all three from one folder or run the
server app.

## Starting over

Clear the site data for the page, or run `localStorage.clear()` in the browser
console. The seeded caseload comes back on the next load.
