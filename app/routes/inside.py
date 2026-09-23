"""The facility tablet.

Two gates on every handler. require_role says who is asking, from the signed
cookie; surfaces.require says what this surface can do, from the capability
table. The URL carries no identity, so there is nothing in it to guess at.

There is no route here for uploading a file or verifying an identity, and if
someone adds one later the capability check refuses it before it does anything.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import FORBIDDEN_SCOPES, STANDING_DETAIL
from app import labels
from app.deps import templates
from app import doccs
from app import lessons
from app import report as report_module
from app import walkthrough
from app.questions import INSIDE_QUESTIONS, inside_question, teaching_for
from app.session import require_role
from app.store import (
    STATE,
    get_authorization,
    mutate,
    put_authorization,
    pending_reports,
    stored_reports,
)
from app.surfaces import Capability, Surface, require

router = APIRouter(prefix="/inside")

POSITION = {
    "not_yet_triaged": 1,
    "credit_invisible": 1,
    "damaged_file": 1,
    "thin_file": 2,
    "errors_present": 2,
}


@router.get("", response_class=HTMLResponse)
def home(request: Request):
    """Straight to the case if intake is done, otherwise pick up where they left off."""
    caller = require_role(request, "inside")
    answered = caller.client.intake_answers
    if len(answered) >= len(INSIDE_QUESTIONS):
        return RedirectResponse("/inside/case", status_code=303)
    for question in INSIDE_QUESTIONS:
        if question.field not in answered:
            return RedirectResponse(f"/inside/intake/{question.index}", status_code=303)
    return RedirectResponse("/inside/case", status_code=303)


@router.get("/intake/{index}", response_class=HTMLResponse)
def intake(request: Request, index: int):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.ANSWER_INTAKE)
    question = inside_question(index)
    return templates.TemplateResponse(
        request, "inside/intake.html",
        {"client": caller.client, "q": question, "total": len(INSIDE_QUESTIONS),
         "saved": caller.client.intake_answers.get(question.field)},
    )


@router.post("/intake/{index}")
async def answer(request: Request, index: int):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.ANSWER_INTAKE)
    client = caller.client
    question = inside_question(index)
    form = await request.form()

    with mutate():
        if question.multi:
            picked = [v for v in form.getlist(question.field) if v != "none"]
            client.intake_answers[question.field] = picked or ["none"]
        else:
            client.intake_answers[question.field] = form.get(question.field)
        # The receipt for what question one promises: the answer is saved as
        # it is given. /api/saves reads this back.
        STATE.write_log.append({
            "client_id": client.id, "field": question.field,
            "value": client.intake_answers[question.field],
            "at": date.today().isoformat(),
        })

    if index >= len(INSIDE_QUESTIONS):
        return RedirectResponse("/inside/where-you-stand", status_code=303)
    # The two knowledge questions come first, and what follows them is an
    # explanation rather than another question.
    if index == 2:
        return RedirectResponse("/inside/how-this-works", status_code=303)
    return RedirectResponse(f"/inside/intake/{index + 1}", status_code=303)


@router.get("/how-this-works", response_class=HTMLResponse)
def how_this_works(request: Request):
    """The teaching screen, sized to the answer given two questions ago."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    return templates.TemplateResponse(
        request, "inside/how_this_works.html",
        {"client": caller.client,
         "teaching": teaching_for(caller.client.intake_answers.get("knows_how"))},
    )


@router.get("/learn", response_class=HTMLResponse)
def learn(request: Request):
    """The course index. Reachable from every screen, at any point in a case.

    Deliberately not gated on intake. Somebody who signs in, reads two lessons
    and answers no questions has still got something out of this, and making
    the course wait behind a form would lose exactly the people it is for.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    client = caller.client
    return templates.TemplateResponse(
        request, "inside/learn.html",
        {"client": client,
         "rows": lessons.index_rows(client),
         "standing": lessons.standing(client),
         "next_up": lessons.next_up(client),
         # Somebody who stepped out of intake to read something gets sent back
         # to the question they were on, not to a case screen that has nothing
         # on it yet. /inside works out which that is.
         "intake_done": len(client.intake_answers) >= len(INSIDE_QUESTIONS),
         "total_minutes": lessons.TOTAL_MINUTES},
    )


@router.get("/learn/lesson/{slug}", response_class=HTMLResponse)
def lesson_resume(request: Request, slug: str):
    """Open a lesson where it was left, not at the beginning.

    The whole reason progress is stored per card. Somebody who read four
    screens yesterday and lost the tablet should not have to read them again.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    try:
        found = lessons.lesson(slug)
    except KeyError:
        return RedirectResponse("/inside/learn", status_code=303)
    at = lessons.progress(caller.client, slug)["card"]
    return RedirectResponse(
        f"/inside/learn/lesson/{found.slug}/{min(at, len(found.cards))}",
        status_code=303,
    )


@router.get("/learn/lesson/{slug}/{index:int}", response_class=HTMLResponse)
def lesson_card(request: Request, slug: str, index: int):
    """One card, or the check question when index is past the last card."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    try:
        found = lessons.lesson(slug)
    except KeyError:
        return RedirectResponse("/inside/learn", status_code=303)

    index = max(0, min(index, len(found.cards)))
    with mutate():
        lessons.record_card(caller.client, slug, index)

    row = lessons.progress(caller.client, slug)
    return templates.TemplateResponse(
        request, "inside/lesson.html",
        {"client": caller.client, "lesson": found, "index": index,
         "card": found.cards[index] if index < len(found.cards) else None,
         "is_check": index == len(found.cards),
         "answered": row["answered"],
         "done": row["done"],
         "standing": lessons.standing(caller.client)},
    )


@router.post("/learn/lesson/{slug}/check", response_class=HTMLResponse)
async def lesson_check(request: Request, slug: str):
    """Answer the check. Any answer finishes the lesson.

    The explanation is the teaching; the question only exists to make somebody
    commit before they read it. Marking them wrong in a dayroom, in front of
    whoever is waiting for the tablet, would teach them to stop answering.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    try:
        found = lessons.lesson(slug)
    except KeyError:
        return RedirectResponse("/inside/learn", status_code=303)

    form = await request.form()
    choice = (form.get("choice") or "").strip()
    already = lessons.is_complete(caller.client, slug)

    with mutate():
        lessons.record_answer(caller.client, slug, choice)
        # A finished lesson is a real thing a named person did on a real date,
        # which is what this timeline is for. Recorded once, not on every
        # re-read.
        if not already:
            caller.client.timeline.append({
                "text": f"You finished the lesson on {found.title.lower()}",
                "actor": "You",
                "on": date.today().strftime("%B %-d"),
                "done": True,
            })

    return RedirectResponse(f"/inside/learn/lesson/{slug}/done", status_code=303)


@router.get("/learn/lesson/{slug}/done", response_class=HTMLResponse)
def lesson_done(request: Request, slug: str):
    """The explanation, then what is next. Shown after the check is answered."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    try:
        found = lessons.lesson(slug)
    except KeyError:
        return RedirectResponse("/inside/learn", status_code=303)

    client = caller.client
    row = lessons.progress(client, slug)
    standing = lessons.standing(client)
    # Finishing the last one is the only moment in this app worth a noise, so
    # the whole-course screen takes over rather than sitting under a lesson.
    if standing["finished"]:
        return RedirectResponse("/inside/learn/finished", status_code=303)

    return templates.TemplateResponse(
        request, "inside/lesson_done.html",
        {"client": client, "lesson": found, "answered": row["answered"],
         "chosen": next((c for c in found.check.choices
                         if c.value == row["answered"]), None),
         "was_the_defensible_one": row["answered"] == found.check.answer,
         "standing": standing,
         "next_up": lessons.next_up(client)},
    )


@router.get("/learn/finished", response_class=HTMLResponse)
def learn_finished(request: Request):
    """Every lesson done. The one screen in Bridge that celebrates.

    Earned rather than given: it cannot be reached without an answer recorded
    on all of them. Somebody who has not finished gets sent back to the course.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    client = caller.client
    if not lessons.finished_course(client):
        return RedirectResponse("/inside/learn", status_code=303)
    return templates.TemplateResponse(
        request, "inside/learn_finished.html",
        {"client": client, "standing": lessons.standing(client),
         "curriculum": lessons.CURRICULUM,
         "minutes": lessons.TOTAL_MINUTES},
    )


@router.get("/learn/scores", response_class=HTMLResponse)
def learn_scores(request: Request):
    """Why the number a landlord sees is not the number a free app showed."""
    from app import scores

    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_LESSON)
    by_use = [
        (scores.USE_LABEL[use], scores.models_for(use))
        for use in scores.Use
        if scores.models_for(use)
    ]
    done_intake = len(caller.client.intake_answers) >= 6
    return templates.TemplateResponse(
        request, "inside/scores.html",
        {"client": caller.client,
         "summary": scores.summary_line(),
         "by_use": by_use,
         "explainers": scores.EXPLAINERS,
         "back": "/inside/case" if done_intake else "/inside/how-this-works"},
    )


@router.get("/report", response_class=HTMLResponse)
def read_report(request: Request):
    """Read your own credit report, with the Social Security number masked.

    Safe on a shared kiosk because the disclosure is requested truncated in the
    first place, and masked again here on whatever actually arrived.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    # Confirmed only. A report a helper typed or photographed has not been
    # checked by anyone yet, and showing somebody an unverified list of
    # their own debts is worse than showing them nothing.
    reports = stored_reports(caller.client.id, confirmed_only=True)
    # But an empty screen is its own lie. Somebody told "your helper sent it
    # in" and then shown nothing has no way to tell the difference between
    # working and broken, so the waiting is named and attributed.
    waiting = pending_reports(caller.client.id)
    # A report that has landed and not been read is the most important thing on
    # this person's case. It interrupts rather than sitting in a list.
    unread = walkthrough.unread_indexes(caller.client, reports)
    return templates.TemplateResponse(
        request, "inside/report.html",
        {"client": caller.client, "reports": reports, "waiting": waiting,
         "unread": unread,
         "arrival": (
             {"index": unread[0],
              "report": reports[unread[0]],
              "credit": report_module.arrival_credit(reports[unread[0]].source)}
             if unread else None),
         "read_state": {i: walkthrough.review(caller.client, i)
                        for i, _ in enumerate(reports)}},
    )


@router.get("/report/{index:int}/read", response_class=HTMLResponse)
def read_walk_resume(request: Request, index: int):
    """Open the walk where it was left, same as a lesson."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    reports = stored_reports(caller.client.id, confirmed_only=True)
    if not 0 <= index < len(reports):
        return RedirectResponse("/inside/report", status_code=303)
    at = walkthrough.review(caller.client, index)["section"]
    sections = walkthrough.sections_for(reports[index])
    return RedirectResponse(
        f"/inside/report/{index}/read/{min(at, len(sections))}", status_code=303)


@router.get("/report/{index:int}/read/{at:int}", response_class=HTMLResponse)
def read_walk(request: Request, index: int, at: int):
    """One section of your own report, with what that section means.

    The teaching sits next to the person's own data rather than in a lesson
    somewhere else, because that is the difference between homework and the
    moment somebody actually understands what they are looking at.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = caller.client
    reports = stored_reports(client.id, confirmed_only=True)
    if not 0 <= index < len(reports):
        return RedirectResponse("/inside/report", status_code=303)

    report = reports[index]
    sections = walkthrough.sections_for(report)
    at = max(0, min(at, len(sections)))
    with mutate():
        walkthrough.record_section(client, index, at)

    row = walkthrough.review(client, index)
    return templates.TemplateResponse(
        request, "inside/report_walk.html",
        {"client": client, "report": report, "index": index, "at": at,
         "section": sections[at] if at < len(sections) else None,
         "is_final": at == len(sections),
         "total": len(sections) + 1,
         "question": walkthrough.FINAL_QUESTION,
         "choices": walkthrough.FINAL_CHOICES,
         "answered": row["answer"], "flagged": row["flagged"]},
    )


@router.post("/report/{index:int}/read/answer")
async def read_walk_answer(request: Request, index: int):
    """The person says whether they recognize their own file.

    This is `recognizes_everything`, the one field that opens a statutory
    clock, and it used to be answered on the staff form because the tablet
    could not show a report. It can now, and the person looking at the account
    is the only human alive who knows whether they opened it.

    It does not send a letter. What the person raises is a claim, and it goes
    to the coordinator to check against the paper, the same as anything else
    arriving from outside.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = caller.client
    reports = stored_reports(client.id, confirmed_only=True)
    if not 0 <= index < len(reports):
        return RedirectResponse("/inside/report", status_code=303)

    form = await request.form()
    answer = (form.get("answer") or "").strip()
    if answer not in dict(walkthrough.FINAL_CHOICES):
        return RedirectResponse(
            f"/inside/report/{index}/read", status_code=303)
    flagged = [int(v) for v in form.getlist("flagged") if str(v).isdigit()]

    first_time = not walkthrough.has_been_read(client, index)
    with mutate():
        walkthrough.record_answer(
            client, index, answer, flagged, date.today().isoformat())
        if first_time:
            client.timeline.append({
                "text": f"You read your {reports[index].bureau} report and said "
                        f"what you did and did not recognize",
                "actor": "You",
                "on": date.today().strftime("%B %-d"),
                "done": True,
            })
            if answer in ("some_not_mine", "not_sure"):
                client.needs = "Client flagged items to check"
    return RedirectResponse(f"/inside/report/{index}/read/done",
                            status_code=303)


@router.get("/report/{index:int}/read/done", response_class=HTMLResponse)
def read_walk_done(request: Request, index: int):
    """The end of the arc that started with a letter going out months ago."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = caller.client
    reports = stored_reports(client.id, confirmed_only=True)
    if not 0 <= index < len(reports):
        return RedirectResponse("/inside/report", status_code=303)

    report = reports[index]
    row = walkthrough.review(client, index)
    return templates.TemplateResponse(
        request, "inside/report_read.html",
        {"client": client, "report": report, "index": index,
         "answer": row["answer"],
         "what_next": walkthrough.ANSWER_NEXT.get(row["answer"], ""),
         "flagged": [report.accounts[i] for i in row["flagged"]
                     if 0 <= i < len(report.accounts)],
         "credit": report_module.arrival_credit(report.source),
         "unread": walkthrough.unread_indexes(
             client, reports)},
    )


@router.get("/where-you-stand", response_class=HTMLResponse)
def where_you_stand(request: Request):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = caller.client

    if client.case_state == "credit_invisible" or not client.classification:
        moves = [
            {"title": "You don't have a file yet",
             "body": "That is not the same as bad credit. Empty moves faster "
                     "than damaged does."},
            {"title": "One account, paid on time, starts the clock",
             "body": "Ms. Reyes will set this up with you before you go home."},
        ]
    else:
        moves = [
            {"title": "Your file exists and two items are disputed",
             "body": "Ms. Reyes approved the letter. The bureaus have to answer."},
            {"title": "One account, paid on time, keeps the clock running",
             "body": "Set up before release, not after."},
        ]
    if any(o != "none" for o in client.intake_answers.get("obligations", [])):
        moves.append({
            "title": "What the court ordered is tracked separately",
            "body": "It matters, and it does not sit in this list pretending to "
                    "be a credit card."})

    return templates.TemplateResponse(
        request, "inside/where_you_stand.html",
        {"client": client, "moves": moves,
         "position": POSITION.get(client.case_state, 1)},
    )


@router.get("/case", response_class=HTMLResponse)
def case(request: Request):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    auth = get_authorization(caller.client.id)
    return templates.TemplateResponse(
        request, "inside/case.html",
        {"client": caller.client, "timeline": caller.client.timeline,
         "auth": auth if auth and auth.is_live() else None,
         "course": lessons.standing(caller.client),
         "next_lesson": lessons.next_up(caller.client),
         # Their own dates, read back to them. Seeing the record come back
         # correct is how somebody knows the app has the right person before
         # they trust it with anything else. No date of birth is in here to
         # show: the lookup does not return one.
         "record": [
             {"label": labels.field(key), "value": caller.client.doccs_record[key]}
             for key in doccs.SHOWN_TO_THE_PERSON
             if caller.client.doccs_record.get(key)
         ],
         "release_source": caller.client.release_date_source,
         "synced": "just now"},
    )


@router.get("/authorization", response_class=HTMLResponse)
def authorization(request: Request):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.REVOKE_AUTHORIZATION)
    auth = get_authorization(caller.client.id)
    return templates.TemplateResponse(
        request, "inside/authorization.html",
        {"client": caller.client, "auth": auth,
         "scopes": sorted(labels.scope(s) for s in auth.scopes) if auth else [],
         "standing_label": STANDING_DETAIL[auth.standing]["label"] if auth else "",
         "forbidden": sorted(labels.scope(f) for f in FORBIDDEN_SCOPES)},
    )


@router.post("/authorization/revoke")
def revoke(request: Request):
    """The client cancels, from the tablet, without telling the helper first."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.REVOKE_AUTHORIZATION)
    auth = get_authorization(caller.client.id)
    with mutate():
        if auth is not None:
            put_authorization(auth.revoked())
        caller.client.helper_name = None
        caller.client.timeline.append({
            "text": "You cancelled the authorization",
            "actor": "You", "on": date.today().strftime("%B %-d"), "done": True,
        })
    return RedirectResponse("/inside/authorization", status_code=303)


@router.post("/authorization/name")
def name_helper(request: Request, helper_name: str = Form(...)):
    """Naming someone starts an invitation. It grants nothing.

    The grant is created on the family surface, by the helper, after they have
    been shown what they are agreeing to. A person cannot consent on someone
    else's behalf, which is the whole reason the two screens are separate.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.NAME_HELPER)
    with mutate():
        caller.client.helper_name = helper_name.strip()[:40]
    return RedirectResponse("/inside/authorization", status_code=303)
