"""Reading your own credit report.

The report arriving is the biggest thing that happens on a case, and until now
it rendered as a table. What is defended here: it announces itself, it names
who got it here, it teaches while the person reads their own data, and it ends
by asking the person the one question that opens a legal clock.
"""

import pytest

from app import walkthrough
from app.report import ARRIVAL_CREDIT, Source
from conftest import clear_reports, sign_in_inside


@pytest.fixture()
def with_report(client, staff):
    """A confirmed report on Marcus's record, scanned at the desk.

    The seeded files are cleared first so this one is index 0 and the walk is
    over a report this test can reason about.
    """
    clear_reports()
    staff.post("/staff/marcus-w/report", data={
        "bureau": "Equifax",
        "consumer_name": "Marcus W.",
        "ssn_on_document": "123-45-6789",
        "accounts": ("Midland Funding | xxxx4471 | 2019-02 | Open | $1,204 |\n"
                     "Cap One Platinum | xxxx2210 | 2016-04 | Closed, paid | $0 |"),
    })
    return sign_in_inside(client)


# --------------------------------------------------------------------------
# the content
# --------------------------------------------------------------------------

def test_every_way_a_report_can_arrive_names_who_got_it_here():
    """Three routes in, and only one of them is the program doing it for
    somebody. Which one happened is the difference between a file appearing and
    a thing a person accomplished."""
    for source in Source:
        assert source in ARRIVAL_CREDIT, source
        assert ARRIVAL_CREDIT[source]["headline"]
        assert ARRIVAL_CREDIT[source]["body"]


def test_the_person_who_carried_the_paper_in_is_credited_for_it():
    credit = ARRIVAL_CREDIT[Source.CLIENT_DELIVERED]
    assert "You did this" in credit["headline"]


def test_an_outside_route_credits_the_person_outside_and_not_the_client():
    """Who got the report here is the difference between a file appearing and
    a thing somebody accomplished, so the two must not read the same.

    This used to assert on the word "helper", which has been taken out of the
    product: it named a person by their usefulness to somebody else. The claim
    was never about the vocabulary, so it is checked as the distinction."""
    mine = ARRIVAL_CREDIT[Source.CLIENT_DELIVERED]["headline"]
    assert "You did this" in mine
    for source in (Source.PDF, Source.TYPED, Source.PHOTO):
        headline = ARRIVAL_CREDIT[source]["headline"]
        assert headline != mine, source
        assert "helper" not in headline.lower(), source
        # Somebody else is the subject of the sentence, not the reader.
        assert not headline.lower().startswith("you "), source


def test_every_section_of_the_walk_teaches_something():
    for section in walkthrough.SECTIONS:
        assert section.teaching
        assert section.title


def test_a_section_that_points_at_a_lesson_points_at_a_real_one():
    from app.lessons import BY_SLUG

    for section in walkthrough.SECTIONS:
        if section.lesson_slug:
            assert section.lesson_slug in BY_SLUG, section.key
            assert section.lesson_label


def test_an_empty_public_records_section_is_left_out_of_the_walk():
    """An empty screen on a walk teaches nothing and makes it feel padded,
    which is how somebody decides to skip the rest."""
    from app.report import CreditReport

    bare = CreditReport(bureau="Equifax", client_id="x", pulled_on="",
                        scanned_on="", scanned_by="", consumer_name="X")
    keys = [s.key for s in walkthrough.sections_for(bare)]
    assert "public_records" not in keys

    bare.public_records = ["A judgment from 2014"]
    assert "public_records" in [s.key for s in walkthrough.sections_for(bare)]


def test_every_answer_to_the_closing_question_says_what_happens_next():
    for value, _ in walkthrough.FINAL_CHOICES:
        assert walkthrough.ANSWER_NEXT.get(value), value


def test_not_sure_is_offered_as_a_real_answer():
    """Nobody knows a 2016 account number off the top of their head. Forcing a
    yes or no produces bad data and starts the wrong clock."""
    assert "not_sure" in dict(walkthrough.FINAL_CHOICES)


# --------------------------------------------------------------------------
# the surface
# --------------------------------------------------------------------------

def test_a_landed_report_interrupts_rather_than_sitting_in_a_list(with_report):
    page = with_report.get("/inside/report").text
    assert "Read it with me" in page
    assert ARRIVAL_CREDIT[Source.SCAN]["headline"] in page


def test_the_walk_shows_the_persons_own_data_and_what_it_means(with_report):
    page = with_report.get("/inside/report/0/read/0").text
    assert "Marcus W." in page
    assert "XXX-XX-6789" in page
    assert walkthrough.BY_KEY["identity"].teaching[:40] in page


def test_the_report_never_shows_an_unmasked_social_on_the_walk(with_report):
    """The tablet is read where other people can see it. This is the one thing on it
    that must be true on every screen, not just the identity one."""
    for at in range(len(walkthrough.SECTIONS) + 1):
        page = with_report.get(f"/inside/report/0/read/{at}").text
        assert "123-45-6789" not in page, f"section {at}"
        assert "XXX-XX-6789" in page or "Social" not in page


def test_the_walk_reopens_where_it_was_left(with_report):
    with_report.get("/inside/report/0/read/2")
    landed = with_report.get("/inside/report/0/read", follow_redirects=False)
    assert landed.headers["location"] == "/inside/report/0/read/2"


def test_the_walk_ends_on_the_question_that_opens_the_clock(with_report):
    from app.report import CreditReport

    page = with_report.get("/inside/report/0/read/99").text
    assert walkthrough.FINAL_QUESTION in page
    for _, label in walkthrough.FINAL_CHOICES:
        assert label in page


def test_the_person_can_flag_an_item_as_not_theirs(with_report):
    from app.store import STATE

    with_report.post("/inside/report/0/read/answer",
                     data={"answer": "some_not_mine", "flagged": "0"})
    row = walkthrough.review(STATE.clients["marcus-w"], 0)
    assert row["done"]
    assert row["answer"] == "some_not_mine"
    assert row["flagged"] == [0]


def test_flagging_does_not_by_itself_send_a_letter(with_report):
    """The client starts the conversation. The coordinator still holds the
    deadline, because a letter about the wrong account number is worse than no
    letter at all."""
    from app.store import STATE, drafts_for

    with_report.post("/inside/report/0/read/answer",
                     data={"answer": "some_not_mine", "flagged": "0"})
    assert drafts_for("marcus-w") == []
    assert STATE.clients["marcus-w"].needs == "Client flagged items to check"


def test_reading_the_report_puts_a_named_dated_event_on_the_timeline(with_report):
    from app.store import STATE

    with_report.post("/inside/report/0/read/answer", data={"answer": "all_mine"})
    events = [e for e in STATE.clients["marcus-w"].timeline
              if "read your" in e["text"]]
    assert len(events) == 1
    assert events[0]["actor"] == "You"
    assert events[0]["on"]


def test_reading_it_again_does_not_stack_a_second_event(with_report):
    from app.store import STATE

    for _ in range(3):
        with_report.post("/inside/report/0/read/answer",
                         data={"answer": "all_mine"})
    events = [e for e in STATE.clients["marcus-w"].timeline
              if "read your" in e["text"]]
    assert len(events) == 1


def test_an_answer_that_is_not_one_of_the_choices_is_refused(with_report):
    from app.store import STATE

    with_report.post("/inside/report/0/read/answer",
                     data={"answer": "whatever"}, follow_redirects=False)
    assert not walkthrough.review(STATE.clients["marcus-w"], 0)["done"]


def test_finishing_the_walk_credits_however_the_report_actually_arrived(with_report):
    with_report.post("/inside/report/0/read/answer", data={"answer": "all_mine"})
    page = with_report.get("/inside/report/0/read/done").text
    assert ARRIVAL_CREDIT[Source.SCAN]["headline"] in page
    assert walkthrough.ANSWER_NEXT["all_mine"][:40] in page


def test_a_report_index_that_does_not_exist_goes_back_rather_than_500ing(with_report):
    landed = with_report.get("/inside/report/7/read", follow_redirects=False)
    assert landed.status_code == 303
    assert landed.headers["location"] == "/inside/report"


def test_what_the_client_flagged_reaches_the_coordinator(with_report, staff):
    """The loop closes at the desk. The client's claim is checked against the
    paper there, which is the same step everything from outside goes through."""
    with_report.post("/inside/report/0/read/answer",
                     data={"answer": "some_not_mine", "flagged": "0"})
    page = staff.get("/staff/marcus-w").text
    assert "flagged" in page.lower()
    assert "Midland Funding" in page


def test_an_unsure_client_reaches_the_coordinator_as_wanting_to_talk(with_report, staff):
    with_report.post("/inside/report/0/read/answer", data={"answer": "not_sure"})
    page = staff.get("/staff/marcus-w").text
    assert "go through it with you" in page
