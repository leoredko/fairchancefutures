"""Screen text for the rest of the tablet, keyed for translation.

The first pass of Spanish covered the door, the course and the intake. These
are the screens after them: the report and its walk, the scores page, the
request, the authorization, when you go home, and the landing page, plus the
text that is case data (timeline sentences, bureau statuses) and the text kept
in other modules (the walk, the scores, the centers), read from where it lives
so the English has one home.

The dispute and request letters are not here. They go to a bureau, which reads
English, and a translation of a legal letter a person signs is a different
kind of risk than a translation of a screen.
"""

from __future__ import annotations

STATIC: dict[str, str] = {
    'index.title': 'Bridge',
    'index.hero': 'Start the credit work before the gate opens.',
    'index.signin': 'Sign in',
    'index.colophon': 'Bridge is an independent tool built for reentry programs in New York State. It is not affiliated with, endorsed by, or operated by the New York State Department of Corrections and Community Supervision or any correctional facility.',
    'denied.title': 'Not possible from this surface',
    'after.title': 'When you go home',
    'after.heading': 'Somebody to keep working with.',
    'after.lede': 'A dispute can still be running when you walk out, and by then your coordinator is no longer holding it. Some cities have a free financial counselor who does credit reports, debt and disputes. Not a loan, not a grant, no charge, ever.',
    'after.free.title': 'Nobody here can charge you to fix your credit.',
    'after.free.body': 'A company that asks for money before the work is done is breaking the law. That is in the course, and it is the single most useful thing to remember in your first month out.',
    'after.where.label': 'Where are you going home to?',
    'after.where.hint': 'County. If you are not sure yet, you can come back to this screen any time.',
    'after.choose': 'Choose a county',
    'after.show': 'Show me',
    'after.open': 'Open now',
    'after.book': 'How to get an appointment',
    'after.write_down': 'Write the number down before you go. You will not have this tablet on the outside.',
    'after.cite': '{source} · checked {date}',
    'after.coming': 'Not open yet',
    'after.unchecked.tag': 'We have not checked this one',
    'after.unchecked.body': 'There may be a center serving {county}, but nobody on this team has read the page it comes from, so we are not going to put an address in front of you that we have not opened ourselves. Ask your coordinator to look it up with you.',
    'after.unchecked.note': 'An address that has moved sends somebody who has just come home on a bus ride to a locked door. That is why this screen would rather say nothing.',
    'after.none.tag': 'No center there',
    'after.none.body': 'There is no free city-run financial counselor in {county}. Most of New York State has none: it is a city program, and it covers a handful of places. We are not going to send you to the nearest one, because two hours on a bus to a desk that will turn you away is worse than knowing now.',
    'after.none.h': 'What to do instead',
    'after.none.do': 'Finish the course. It covers the two rules that matter most out there: nobody may charge you before the work is done, and you are owed a free report from all three bureaus every year, plus another one every time you are turned down for something.',
    'after.none.cta': 'Back to the course',
    'after.colophon': 'This list is kept by hand and checked on {checked_on}. Only places somebody on this team has read about are on it.',
    'borough.Bronx': 'the Bronx',
    'borough.Kings': 'Brooklyn',
    'borough.New York': 'Manhattan',
    'borough.Queens': 'Queens',
    'borough.Richmond': 'Staten Island',
    'auth.title': 'Who is helping you',
    'auth.since': '{name}, since {signed}',
    'auth.expires': 'Expires {expires}. Acting under a {standing}.',
    'auth.enough.title': 'Nobody gets more than they need',
    'auth.enough.body': 'Whoever helps you cannot open an account in your name, take out credit, move money, or change your address. If a bureau ever needs you to sign something extra, you see exactly what it says first.',
    'auth.cancel': 'Cancel this authorization',
    'auth.cancel_note': 'You can cancel from this screen without telling {name} first. Ms. Reyes is told the same day.',
    'auth.none.title': 'Nobody outside right now',
    'auth.none.body': 'Ms. Reyes handles it through the program instead, using the same form you already signed with her. A few steps run slower. Nothing stops.',
    'auth.name_label': 'Name someone you trust',
    'auth.name_placeholder': 'First name',
    'auth.invite': 'Send them the invitation',
    'standing.signed_form': 'Signed form',
    'standing.notarized_poa': 'Limited power of attorney',
    'scope.receive_mail': 'Receive the report at their own address',
    'scope.submit_report_images': 'Add photos of the reports',
    'scope.mail_dispute_letter': 'Mail a letter we print',
    'scope.be_contacted_by_staff': 'Be contacted by the counselor',
    'scope.open_account': 'Open an account',
    'scope.apply_for_credit': 'Apply for credit',
    'scope.move_money': 'Move money',
    'scope.change_address': 'Change the address on file',
    'scope.view_ssn': 'See the Social Security number',
    'scope.view_full_account_numbers': 'See full account numbers',
    'request.title': 'Ask for your report',
    'request.suffix': 'Your report',
    'request.asked.tag': 'Asked for',
    'request.asked.h': 'It is on its way.',
    'request.asked.lede': 'Your coordinator has the request. It goes out on paper, and the bureaus have 15 days from getting it to send your file back here.',
    'request.h': 'You can do this on your own.',
    'request.lede': 'You do not need anybody on the outside to get your credit report. Not a family member, not a friend, not a lawyer. One form, one address, all three bureaus.',
    'request.notest.title': 'There is no test to pass.',
    'request.notest.body': 'Online, a bureau asks you questions about old addresses and car loans before it will show you anything. That is a web page, and you cannot reach it. This route is paper, so there is nothing to fail.',
    'request.how': 'How it works',
    'request.step1': 'You ask. Your coordinator prints the letter below and you sign it.',
    'request.step2': 'If anything needs to be sworn, the law library has a notary. They have to get you one within 72 hours of asking.',
    'request.step3': 'It goes to one address in Atlanta and covers Equifax, Experian and TransUnion together.',
    'request.step4': 'Your file comes back here as mail, in your name. You carry it to your coordinator and you read it on this screen.',
    'request.ask': 'Ask for my report',
    'request.ask_note': 'This tells your coordinator. Nothing is sent anywhere until you have signed it yourself.',
    'request.waiting.title': 'Nothing is waiting on you right now.',
    'request.waiting.body': 'Your coordinator prints it and brings it to you to sign. While you wait, the course is the useful thing to do: the lesson on reading a report is the one that pays off the day yours arrives.',
    'request.waiting.cta': 'Go to the course',
    'request.letter.h': 'The letter',
    'request.letter.lede': 'This is what goes out, in your name, to your address here. It stays in English because the bureaus read it in English.',
    'request.letter.note': 'The Social Security number and date of birth lines are blank on purpose. They go on the paper by hand and are never typed into this app.',
    'request.cite': '{source} · checked {date}',
    'scores.title': 'Why there is no single score',
    'scores.suffix': 'Credit scores',
    'scores.h': 'There is no such thing as your credit score.',
    'scores.lede': 'There are dozens of them, and they disagree on purpose.',
    'scores.three': 'Three things multiply together',
    'scores.bureau.h': 'Which bureau',
    'scores.bureau.b': 'Equifax, Experian and TransUnion hold different files. Not every lender reports to all three, so an account on one report can be missing from another.',
    'scores.model.h': 'Which model',
    'scores.model.b': 'FICO and VantageScore are different companies. FICO alone has versions 2 through 10T still in use, and they do not agree with each other.',
    'scores.industry.h': 'Which industry',
    'scores.industry.b': 'A car lender and a card issuer use scores tuned to their own risk, on a different scale entirely.',
    'scores.pulled': 'What gets pulled, and when',
    'scores.questions': 'The questions people actually ask',
    'scores.nonumber.h': 'Which is why this app does not show you a number',
    'scores.nonumber.b': 'A number with no model, no bureau and no date attached is not information. It is a guess that feels precise. What it shows you instead is what is actually on your file, and what moves it.',
    'scores.summary': 'About {n} different scores can describe one person on one day: {models} widely used models against 3 bureau files. Base scores run {b1} to {b2}; auto and card scores run {i1} to {i2}.',
    'scores.range': '{low} to {high}',
    'report.title': 'Your credit report',
    'report.suffix': 'Your reports',
    'report.waiting.one': '1 report is here. Your counselor is checking it.',
    'report.waiting.many': '{n} reports are here. Your counselor is checking them.',
    'report.waiting.line': '{bureau} · {source}, {scanned}',
    'report.waiting.why': 'They read it against the paper before it goes on this screen, because what is written here becomes a letter to a credit bureau. Nothing is wrong. It is the checking step.',
    'report.not_yet': 'Not on this screen yet.',
    'report.nothing': 'Nothing here yet.',
    'report.arrive': 'Your reports come back on paper. When they arrive, bring them to your coordinator and they will scan them into your record. Then you can read them here.',
    'report.ask.title': 'You can ask for them yourself.',
    'report.ask.body': 'You do not need anybody on the outside to do this. One form covers all three bureaus, it goes out in your name, and it comes back here.',
    'report.ask.cta': 'Ask for my report',
    'report.nophoto.h': 'You do not photograph anything',
    'report.nophoto.b': 'There is no camera in this app and there does not need to be. The paper goes to your coordinator, the coordinator scans it, and it shows up here.',
    'report.back_case': 'Back to my case',
    'report.scores.h': 'Your scores',
    'report.scores.sub': 'Same person. Same week. Three different numbers.',
    'report.pulled_card': 'Pulled {date}',
    'report.apart': '{n} points apart, and nothing is broken.',
    'report.apart.body': 'Each bureau keeps its own file on you and yours do not match.',
    'report.apart.counts': '{most} is reporting {most_n} accounts and {fewest} only {fewest_n}, so one of them is carrying something the other has never heard of.',
    'report.apart.tail': 'Whichever one a landlord or a lender pulls is the one that decides about you, which is why the work is on the file rather than on chasing a number.',
    'report.why_no_score': 'Why there is no single score',
    'report.read_with_me': 'Read it with me',
    'report.arrival.body': 'Your {bureau} report is here and nobody has read it with you yet. It takes about five minutes and it explains itself as you go.',
    'report.h': 'Your credit reports.',
    'report.ssn.h': 'Your Social Security number is blacked out',
    'report.ssn.b': 'Only the last four digits appear, on every page. The request asked them to leave the first five out, which the law lets you require, and this screen covers them again regardless.',
    'report.read_on': 'You read this on {date}',
    'report.again': 'Go through it again',
    'report.pulled_line': 'Pulled {pulled} · scanned in {scanned} by {by}',
    'report.about': 'About you, as they have it',
    'report.score': 'Score',
    'report.accounts': 'Accounts',
    'report.opened': 'opened {date}',
    'report.disputed': 'Disputed',
    'report.none': 'No accounts on file with this bureau. That is not the same as bad credit, and it moves faster than damaged does.',
    'report.public': 'Public records',
    'report.pdf': 'Save as PDF',
    'report.why_no_score_q': 'Why is there no score?',
    'report.born': 'Born {year}',
    'report.not_shown': 'Not shown',
    'report.ending': 'ending {last4}',
    'report.withheld': 'number withheld',
    'report.no_score': 'No score on this report. A file disclosure does not have to include one, and most mailed reports do not.',
    'report.sum.none': 'No accounts on file with this bureau.',
    'report.sum.accounts.one': '{n} account',
    'report.sum.accounts.many': '{n} accounts',
    'report.sum.disputed': '{n} disputed',
    'report.sum.records.one': '{n} public record',
    'report.sum.records.many': '{n} public records',
    'readdone.title': 'You have read your {bureau} report',
    'readdone.body': 'You have now read your own {bureau} credit report, start to finish. Whatever happens next on this case, that part is done and it was the hard part.',
    'readdone.pulled': 'Pulled {pulled} · {source}, {scanned} by {by}',
    'readdone.said': 'What you said, and what happens now',
    'readdone.flagged.one': 'You flagged 1 item:',
    'readdone.flagged.many': 'You flagged {n} items:',
    'readdone.check': 'Your coordinator checks these against the paper before anything is sent. That is the step that stops a letter going out about the wrong account.',
    'readdone.another.h': 'You have another report to read',
    'readdone.another.b': 'Each bureau keeps its own file, and they do not match. An item on this one may be missing from the next.',
    'readdone.another.cta': 'Read the next one',
    'readdone.again.h': 'Any of this can be read again',
    'readdone.again.b': 'Your report stays on this screen, with your Social Security number blacked out, for as long as your case is open.',
    'readdone.my_reports': 'My reports',
    'readdone.my_case': 'My case',
    'walk.title': 'Reading your {bureau} report',
    'walk.suffix': 'Reading it together',
    'walk.progress': '{n} of {total}',
    'walk.saved': 'Saved as you go. You can stop and come back to this.',
    'walk.only_you': 'You are the only person who knows this. Nobody else can tell whether you opened an account in 2016.',
    'walk.tick.h': 'If something is not yours, tick it',
    'walk.tick.b': 'Only if you are telling us something is wrong. Leave them all unticked if you recognize everything.',
    'walk.nosend': 'Saying this does not send anything yet. Your coordinator checks what you flag against the paper first, because a letter about the wrong account number is worse than no letter.',
    'walk.answer': "That's my answer",
    'walk.no_address': 'No address history on this copy.',
    'walk.flagged': 'Already flagged',
    'walk.missing': 'Nothing on this report says anything about rent you paid, a phone bill you kept up, or the lights staying on.',
    'walk.means': 'What this part means',
    'walk.full_lesson': 'Full lesson: {lesson}',
    'walk.last': 'Last part, then one question',
    'walk.next': 'Next part',
    'walk.stop': 'Stop for now',
    'timeline.mailed': 'Denise mailed the request for your report',
    'timeline.came_back': 'It came back. Two things look wrong.',
    'timeline.approved': 'Ms. Reyes approved your dispute letter',
    'timeline.waiting': 'Waiting on their answer, due {when}',
    'timeline.opened': 'Ms. Reyes opened your case',
    'timeline.agreed': '{name} agreed to help',
    'timeline.request_mailed': 'Request mailed to the bureaus',
    'timeline.dispute_handed': 'Your dispute letter to {bureau} was handed in to the coordinator',
    'timeline.dispute_mailed': 'Your dispute letter to {bureau} was mailed',
    'timeline.dispute_certified': 'Your dispute letter to {bureau} was mailed, certified, tracking number {number}',
    'timeline.request_certified': 'Request mailed to the bureaus, certified, tracking number {number}',
    'timeline.checked': 'Your {bureau} report was checked and added to your record',
    'timeline.scanned': 'Your {bureau} report was scanned into your record',
    'timeline.document': 'Your {document} is on file',
    'timeline.lesson': 'You finished the lesson on {lesson}',
    'timeline.asked': 'You asked for your credit report from all three bureaus',
    'timeline.read': 'You read your {bureau} report and said what you did and did not recognize',
    'timeline.cancelled': 'You cancelled the authorization',
    'timeline.pdf': 'The report came in as a PDF',
    'timeline.typed': 'They typed your report in by hand',
    'timeline.photo': 'They photographed your report and sent it in',
    'data.you': 'You',
    'data.counselor': 'Your counselor',
    'data.sister': 'Your sister',
    'data.denise_added': 'Denise added it',
    'data.slow': 'This part is slow. Nothing is wrong.',
    'data.outside': 'Your person outside',
    'data.status.closed_paid_agreed': 'Closed, paid as agreed',
    'data.status.closed_paid_full': 'Closed, paid in full',
    'data.status.closed_paid': 'Closed, paid',
    'data.status.open_late': 'Open, 120+ days past due',
    'data.status.collection': 'Collection, open',
    'data.status.open': 'Open',
    'data.note.comenity': 'Original creditor listed as Comenity Bank',
    'data.note.never_opened': 'never opened this account',
    'data.note.paid_open': 'paid in full, still showing open',
    'data.note.not_mine': 'not mine, wrong middle initial',
    'data.whole': 'Whole report',
    'data.ms': 'Ms. {name}',
}



def generated() -> dict[str, str]:
    """English read out of the modules that own it, under stable keys."""
    from app import centers, scores, walkthrough
    from app.report import ARRIVAL_CREDIT, SOURCE_LABEL

    out: dict[str, str] = {}
    for section in walkthrough.SECTIONS:
        out[f"walkdata.{section.key}.title"] = section.title
        out[f"walkdata.{section.key}.teaching"] = section.teaching
    out["walkdata.question"] = walkthrough.FINAL_QUESTION
    for value, label in walkthrough.FINAL_CHOICES:
        out[f"walkdata.choice.{value}"] = label
    for value, text in walkthrough.ANSWER_NEXT.items():
        out[f"walkdata.next.{value}"] = text
    for source, text in ARRIVAL_CREDIT.items():
        out[f"arrival.{source.value}.headline"] = text["headline"]
        out[f"arrival.{source.value}.body"] = text["body"]
    for source, label in SOURCE_LABEL.items():
        out[f"source.{source.value}"] = label
    out["source.default"] = "Added to the record"
    # A sourced sentence, translated against the statute behind it. The
    # citation line under it stays in English on purpose.
    from app.sources import FACTS
    out["fact.free_report_entitlement"] = FACTS["free_report_entitlement"].statement
    for use, label in scores.USE_LABEL.items():
        out[f"scoredata.use.{use.value}"] = label
    for i, model in enumerate(scores.MODELS):
        out[f"scoredata.model.{i}.name"] = model.name
        out[f"scoredata.model.{i}.note"] = model.note
    for i, item in enumerate(scores.EXPLAINERS):
        out[f"scoredata.explain.{i}.q"] = item["question"]
        out[f"scoredata.explain.{i}.a"] = item["answer"]
    # Only entries somebody on the team has read reach a screen, so only those
    # are translated.
    for center in centers.CENTERS + centers.COMING:
        if not center.verified_by_hand:
            continue
        if center.eligibility:
            out[f"center.{center.key}.eligibility"] = center.eligibility
        for i, way in enumerate(center.booking):
            out[f"center.{center.key}.booking.{i}"] = way
        if center.note:
            out[f"center.{center.key}.note"] = center.note
    return out
