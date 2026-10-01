"""The words on the tablet screens around the course, keyed for translation.

The lessons were translated first and the screens that carry a person to them
were not, so somebody who chose Español at the door got a door in English, a
PIN screen in English and a lesson list whose titles were Spanish and whose
every button was not. That reads as a switch that does nothing. These are the
strings on the path from the door to the end of the course.

English lives here and Spanish lives in `app/translations/es.po`, under the
same rules as the lessons: a line whose English has changed since it was
translated falls back to English by itself. `{name}` marks a value the screen
fills in, and a translation that drops or renames one is ignored for the same
reason, since a sentence with a hole in it is worse than English.

Errors are here too, keyed `error.*`. They are raised in modules that do not
know what language the tablet is set to, so the screen translates the finished
sentence by matching it against these.

Nothing here states a law. Sentences that do live in `app/lessons.py` and cite
`app/sources.py`.
"""

from __future__ import annotations

UI: dict[str, str] = {
    # -- the door -----------------------------------------------------------
    "door.title": "Bridge, sign in",
    "door.region": "New York State",
    "door.heading": "DIN number or NYS ID",
    "door.either": "Either one works.",
    "door.next": "Next",
    "door.dashes": "Dashes and spaces don't matter.",
    "door.format": "A DIN is two numbers, a letter, then four numbers. A NYSID "
                   "is eight numbers, sometimes with a letter on the end.",
    "door.helper_ask": "Helping someone on the outside?",
    "door.helper_link": "Use the code from the letter",
    "door.check_placeholder": "A number, or the word",
    "door.check_why": "Asked because this is a public demonstration link. It "
                      "keeps crawlers out and nothing else.",
    "door.other": "Other",
    "language.title": "Language",
    "language.heading": "Language",
    "language.lede": "Pick the language this tablet uses. It stays until "
                     "somebody changes it.",
    "language.other_heading": "Need another language?",
    "language.other_body": "Tell us which one. We keep a list of what people ask for.",
    "language.other_label": "Language",
    "language.other_send": "Send",
    "language.thanks": "Thank you for the feedback. We will work on it the best "
                       "we can so it can be available for your use soon.",
    "door.other_note": "Other languages are coming. For now this app is in "
                       "English and Spanish.",

    # -- the PIN ------------------------------------------------------------
    "pin.title": "Enter your PIN",
    "pin.heading": "Your PIN",
    "pin.welcome": "Welcome back, {name}.",
    "pin.submit": "Sign in",
    "pin.forgot": "Forgot it? Your counselor can clear it, then you pick a new "
                  "one here. Nobody can tell you what your old one was.",
    "pin.different": "Use a different number",
    "enroll.title": "Choose a PIN",
    "enroll.heading": "Pick a PIN",
    "enroll.lede": "{n} numbers. You choose it, and nobody here can see it once "
                   "you do, not even your counselor.",
    "enroll.new": "Your new PIN",
    "enroll.again": "Type it once more",
    "enroll.submit": "Save my PIN",
    "enroll.hands": "Your paperwork is in a lot of hands.",
    "enroll.avoid": "Don't use your birthday or any part of your own number. "
                    "Anyone holding your paperwork can read those.",
    "enroll.forgot": "If you forget it, your counselor can clear it and you pick "
                     "a new one. They never get to see or choose it.",

    # -- the header, on every tablet screen ---------------------------------
    "nav.course": "The course",
    "nav.signout": "Sign out",
    "nav.change": "Change what I am doing",
    "nav.lessons": "All lessons",
    "nav.case": "My case",
    "nav.questions": "Back to my questions",
    "nav.home": "When you go home",

    # -- the first question -------------------------------------------------
    "start.title": "What do you want to do?",
    "start.heading": "What do you want to do first?",
    "start.lede": "Either one is fine, and you can change your mind whenever "
                  "you want. Nothing you pick here closes anything off.",
    "start.now": "What you are doing now",
    "start.foot": "The lessons are open to you either way. Working on your "
                  "credit does not mean waiting to learn about it.",
    "path.learn.label": "Learn how credit works",
    "path.learn.blurb": "Short lessons, one at a time. Nothing to fill in and no "
                        "forms. It saves where you stop, so you can put the "
                        "tablet down and come back to it.",
    "path.learn.cta": "Start learning",
    "path.credit.label": "Work on my credit",
    "path.credit.blurb": "Answer some questions about your money, then a "
                         "counselor picks it up and works your case with you. "
                         "You can read the lessons any time while you wait.",
    "path.credit.cta": "Start on my credit",

    # -- the course index ---------------------------------------------------
    "learn.title": "Learn about credit",
    "learn.heading": "Learn about credit.",
    "learn.lede": "{total} lessons, about {minutes} minutes in total. Take one "
                  "at a time. It saves where you stop, so you can put the "
                  "tablet down mid-sentence and pick it up tomorrow.",
    "learn.finished": "You have finished all {total}.",
    "learn.progress": "{done} of {total} done",
    "learn.nothing": "Nothing started yet",
    "learn.left": "About {minutes} minutes left in the whole course.",
    "learn.see_covered": "See what you covered",
    "learn.carry_on": "Carry on with {title}",
    "learn.start_with": "Start with {title}",
    "learn.done": "Done",
    "learn.place": "{card} of {screens}",
    "learn.for_you": "For you now",
    "learn.length": "{minutes} minutes · {screens} screens",
    "learn.facts_heading": "Where the facts come from",
    "learn.facts_body": "Every rule in this course names the law or the agency "
                        "it comes from, and the date somebody checked it. "
                        "Nothing here is somebody's opinion about how credit "
                        "works.",
    "learn.facts_link": "See the full list",

    # -- inside a lesson ----------------------------------------------------
    "lesson.place": "{n} of {total}",
    "lesson.saved": "Saved as you go. Close this and it opens here again.",
    "lesson.question": "One question before you go.",
    "lesson.unscored": "Nothing is scored and nobody sees your answer. The "
                       "explanation is the same either way.",
    "lesson.answer": "Answer",
    "lesson.source": "Where this comes from: {source}",
    "lesson.last": "Last one, then a question",
    "lesson.next": "Next",
    "lesson.back": "Back",
    "lesson.stop": "Stop for now",
    "lesson.scores": "See every score model",
    "done.title": "{title}, done",
    "done.count": "That's {done} of {total}.",
    "done.saved": "{title} is done and saved to your record.",
    "done.answered": "You answered: {answer}",
    "done.right": "That's the one.",
    "done.worth": "Here's the thing worth knowing.",
    "done.next": "Next: {title}",
    "done.minutes": "{minutes} minutes",
    "done.keep_going": "Keep going",
    "done.stop_heading": "Or stop here",
    "done.stop_body": "{minutes} minutes left in the course, whenever you want "
                      "it. It will open where you left off.",

    # -- the end of the course ----------------------------------------------
    "end.title": "You finished the course",
    "end.heading": "You finished the whole course.",
    "end.lede": "All {total} lessons. About {minutes} minutes of it. You know "
                "more about how credit actually works than most people who "
                "have never been inside.",
    "end.cert_heading": "This is not a certificate and it is worth more than one",
    "end.cert_body": "Nobody can take this back off you, it does not expire, and "
                     "it does not show up on any record. It is just yours now. "
                     "The next time somebody tries to sell you a credit repair "
                     "package, or a landlord quotes you a number, you will know "
                     "what you are looking at.",
    "end.covered": "What you covered",
    "end.reopen": "Any of them opens again. Re-reading one does not undo "
                  "anything.",
    "end.week_heading": "The one thing to do with it this week",
    "end.week_body": "Ask your coordinator where your birth certificate and "
                     "Social Security card stand. That is the first lesson, it "
                     "has a real deadline, and it is the only part of this that "
                     "somebody else has to start for you.",
    "end.back_case": "Back to my case",

    # -- how the tablet looks, reachable from every page --------------------
    "display.dock": "Accessibility",
    "language.dock": "Language",
    "display.skip": "Skip to the page",
    "display.title": "Accessibility",
    "display.heading": "How this looks",
    "display.lede": "These stay on this tablet until somebody changes them.",
    "display.done": "Done",
    "display.selected": "Selected",
    "display.theme": "Color",
    "display.theme.dark": "Dark",
    "display.theme.dark.note": "The usual look.",
    "display.theme.light": "Light",
    "display.theme.light.note": "Dark writing on a white page.",
    "display.theme.contrast": "High contrast",
    "display.theme.contrast.note": "Black and white with yellow. No tints.",
    "display.size": "Text size",
    "display.size.normal": "Normal",
    "display.size.normal.note": "The usual size.",
    "display.size.large": "Large",
    "display.size.large.note": "A bit bigger.",
    "display.size.xlarge": "Largest",
    "display.size.xlarge.note": "As big as it goes.",
    "display.motion": "Motion",
    "display.motion.full": "Normal",
    "display.motion.full.note": "Screens fade and slide a little.",
    "display.motion.reduced": "Less motion",
    "display.motion.reduced.note": "Nothing moves on its own.",

    "display.read": "Read aloud",
    "display.read.off": "Off",
    "display.read.off.note": "Nothing is read to you.",
    "display.read.on": "On",
    "display.read.on.note": "A Listen button on each screen reads it to you. Use "
                            "headphones in shared spaces.",
    "display.dictate": "Voice typing",
    "display.dictate.off": "Off",
    "display.dictate.off.note": "Nothing listens.",
    "display.dictate.on": "On",
    "display.dictate.on.note": "Adds a Dictate button to the dispute letter on the "
                               "coordinator's desk. Never on the tablet, and never "
                               "on account numbers.",
    "dictate.start": "Dictate",
    "dictate.stop": "Stop dictating",
    "dictate.listening": "Listening. The audio stays on this computer.",
    "dictate.unavailable": "Voice typing is off. This browser cannot recognize "
                           "speech on this device without sending the audio out.",
    "dictate.ready": "Voice typing is ready. It works on this device only.",
    "read.listen": "Listen",
    "read.stop": "Stop",
    "read.headphones": "Use headphones in shared spaces.",
    "read.unavailable": "This tablet has no voice that works without a network, "
                        "so read aloud is off.",
    "read.ready": "Read aloud is ready. The voice stays on this tablet.",

    # -- what goes wrong, as the person reads it ----------------------------
    "error.wrong_answer": "That was not the right answer. Here is another one.",
    "error.no_record": "No record here for {display}. Check the number, or ask "
                       "your counselor to add you.",
    "error.id_empty": "Enter your DIN or your NYSID.",
    "error.id_letter": "That looks like a DIN with the facility letter missing. "
                       "A DIN is two digits, a letter, then four digits, like "
                       "98-A-0004.",
    "error.id_short": "That is too short. A DIN looks like 98-A-0004. A NYSID is "
                      "eight digits, sometimes with a letter on the end.",
    "error.id_bad": "That is not a DIN or a NYSID. A DIN is two digits, a "
                    "letter, then four digits, like 98-A-0004. A NYSID is eight "
                    "digits, sometimes with a letter on the end.",
    "error.pin_length": "Your PIN needs to be {n} numbers.",
    "error.pin_same": "Pick something other than the same number six times.",
    "error.pin_run": "Pick something that is not just counting up or down.",
    "error.pin_own": "That is part of your own number, which anyone holding your "
                     "paperwork can read. Pick something else.",
    "error.pin_has": "This account already has a PIN.",
    "error.pin_mismatch": "Those two PINs are not the same. Try again.",
    "error.pin_none": "This account has no PIN yet.",
    "error.pin_wrong": "That PIN is not right. {left} tries left before it locks.",
    "error.locked_wait": "Too many wrong tries. Try again in about {minutes} "
                         "minutes, or ask your counselor to reset it.",
    "error.locked_now": "That PIN was wrong too many times. The account is "
                        "locked for 15 minutes. Your counselor can reset it "
                        "sooner.",
}


def _intake() -> dict[str, str]:
    """The six tablet questions, keyed by field, with their English read out of
    `app/questions.py` rather than copied here.

    Copying would give the wording two homes, and the staff screen already reads
    the originals. The design notes and the constraint line are for the team and
    never reach a person, so they are not translated.
    """
    from app.questions import INSIDE_QUESTIONS, SAVED_AS_YOU_GO

    out = {
        "intake.progress": "{n} of {total}",
        "intake.title": "Intake questions",
        "intake.back": "Back",
        "intake.saved.title": SAVED_AS_YOU_GO["title"],
        "intake.saved.body": SAVED_AS_YOU_GO["body"],
    }
    for q in INSIDE_QUESTIONS:
        out[f"intake.{q.field}.prompt"] = q.prompt
        if q.helper:
            out[f"intake.{q.field}.helper"] = q.helper
        for opt in q.options:
            out[f"intake.{q.field}.{opt.value}"] = opt.label
    return out


UI.update(_intake())


def _teaching() -> dict[str, str]:
    """The screen after question two, read out of `teaching_for` so the English
    has one home. Both lengths are keyed: somebody who said they know how this
    works gets the short one. These sentences state what the law lets a person
    require, and each is backed by a fact in `app/sources.py`
    (`free_report_mail_route`, `ssn_truncation_right`,
    `no_score_in_the_disclosure`), so the Spanish is checked against them, not
    against the English alone."""
    from app.questions import teaching_for

    out = {}
    for size, knows in (("long", "no"), ("short", "yes")):
        data = teaching_for(knows)
        out[f"teach.{size}.headline"] = data["headline"]
        for i, point in enumerate(data["points"]):
            out[f"teach.{size}.{i}.title"] = point["title"]
            out[f"teach.{size}.{i}.body"] = point["body"]
    return out


UI.update(_teaching())

UI.update({
    "teach.title": "How this works",
    "teach.more.title": "One more thing nobody tells you",
    "teach.more.body": "You do not have one credit score. You have dozens. A "
                       "landlord, a car dealer and a credit card company each "
                       "look at a different one, built by a different model, "
                       "from a different bureau's file.",
    "teach.more.cta": "Show me",
    "teach.continue": "Got it, keep going",

    "stand.title": "Where you stand",
    "stand.heading": "Here's where you're starting.",
    "stand.step.0": "Getting started",
    "stand.step.1": "Building",
    "stand.step.2": "Strong",
    "stand.road": "No number. No grade. A position on the road, and the things "
                  "that move you along it.",
    "stand.next": "See what's happening on my case",
    "stand.nofile.title": "You don't have a file yet",
    "stand.nofile.body": "That is not the same as bad credit. Empty moves "
                         "faster than damaged does.",
    "stand.account.title": "One account, paid on time, starts the clock",
    "stand.account.body": "Ms. Reyes will set this up with you before you go "
                          "home.",
    "stand.disputed.title": "Your file exists and two items are disputed",
    "stand.disputed.body": "Ms. Reyes approved the letter. The bureaus have to "
                           "answer.",
    "stand.running.title": "One account, paid on time, keeps the clock running",
    "stand.running.body": "Set up before release, not after.",
    "stand.court.title": "What the court ordered is tracked separately",
    "stand.court.body": "It matters, and it does not sit in this list "
                        "pretending to be a credit card.",

    "mail.title": "In the mail",
    "mail.lede": "Things sent for you, and where each one is.",
    "mail.request": "Your request for your credit reports",
    "mail.dispute": "Your dispute letter to {bureau}",
    "mail.handed": "Handed in to {who} on {when}",
    "mail.with_coordinator": "Ms. Reyes has it and will post it",
    "mail.sent": "Sent {when} by {who}",
    "mail.number": "Tracking number {number}",
    "mail.accepted": "The Post Office has it",
    "mail.transit": "On its way",
    "mail.delivered": "Delivered",
    "mail.expected": "Expected by {when}",
    "mail.untracked": "Sent without a tracking number, so there is no way to "
                      "prove it went. Ask Ms. Reyes if you want to send it "
                      "again.",

    "papers.title": "Your papers",
    "papers.lede": "The three documents your ID depends on, and where each one "
                   "stands.",
    "papers.have": "On file",
    "papers.not_yet": "Not yet",
    "papers.on_file": "Ms. Reyes has this on file.",
    "papers.ssn_ahead": "The application goes in 120 days before release. "
                        "That is {n} days from now.",
    "papers.ssn_passed": "The application goes in 120 days before release. "
                         "That day has passed, so it is the first thing to do.",
    "papers.birth": "Ms. Reyes requests this one. It takes weeks, and the ID "
                    "cannot be applied for without it.",
    "papers.id": "Applied for once the birth certificate and the Social "
                 "Security card are both on file.",
    "papers.ssn": "Social Security card",
    "papers.birth_label": "Birth certificate",
    "papers.id_label": "Non-driver ID",
    "case.heading": "People are working on this while you wait.",
    "case.title": "What's happening on my case",
    "case.suffix": "Your case",
    "case.synced": "Last synced {when}",
    "case.just_now": "just now",
    "case.course.finished": "You finished the credit course",
    "case.course.partial": "The credit course, {done} of {total} done",
    "case.course.new": "Learn how credit actually works",
    "case.course.all": "All {total} lessons. Any of them opens again whenever "
                       "you want it.",
    "case.course.look_back": "Look back over them",
    "case.course.minutes": "{n} minutes · saves where you stop",
    "case.course.carry_on": "Carry on",
    "case.course.start": "Start the course",
    "case.reports.title": "Your credit reports",
    "case.reports.body": "Read them here, with your Social Security number "
                         "blacked out. If they have not arrived yet, this "
                         "tells you that too.",
    "case.reports.open": "Open my reports",
    "case.reports.ask": "Ask for my report",
    "case.score.title": "There is no single credit score",
    "case.score.body": "A landlord, a car dealer and a card company each look "
                       "at a different one. Worth ten minutes.",
    "case.score.cta": "Learn why",
    "case.record.title": "What we already have for you",
    "case.record.body": "Off your DIN. Nothing here was typed by you, and if "
                        "any of it is wrong, tell your coordinator.",
    "case.helper.title": "Who is helping you",
    "case.helper.live": "{name} can receive your report at their address and "
                        "add it. Your own mail still comes to you. The "
                        "authorization expires {expires}.",
    "case.helper.cannot": "They cannot open an account in your name, take out "
                          "credit, move money, or change your address.",
    "case.helper.review": "Review or cancel this",
    "case.helper.none": "Nobody outside is authorized right now. Ms. Reyes "
                        "handles it through the program instead. A few steps "
                        "run slower. Nothing stops.",
})


def _screens() -> dict[str, str]:
    from app.ui_screens import STATIC, generated

    return {**STATIC, **generated()}


UI.update(_screens())
