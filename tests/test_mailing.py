"""Anything Bridge asks a person to mail goes certified, with proof.

The proof is only worth having if it is recorded, so these defend the record:
what the helper typed, what the tablet shows back, and the one thing nobody
should believe, which is that the tracking status is real.
"""

from conftest import sign_in_helper, sign_in_inside
from app import mailing
from app.sources import FACTS, OPEN_QUESTIONS, SIMPLIFICATIONS

ARMANDO = "a-torres"
NUMBER = "9407 1000 0000 0000 0000 00"


def _helper_signed(client):
    sign_in_helper(client, code="BRIDGE-3306")
    client.post("/family/accept", data={"helper_name": "Rosa"})


def test_the_packet_recommends_certified_mail_and_says_who_pays(client):
    _helper_signed(client)
    page = client.get("/family/packet").text
    assert "certified, with a return receipt" in page
    assert "comes out of their own" in page and "will not advance" in page


def test_the_letter_envelope_instructions_say_to_send_it_certified():
    from app.letters import draft_report_request, draft_dispute_set

    request = draft_report_request(client_id="x", client_name="A. Test",
                                   delivery_address="somewhere")
    assert "certified, with a return receipt" in request.body
    for letter in draft_dispute_set(client_id="x", client_name="A. Test",
                                    creditor="Acme", last_four="1234",
                                    reason="not mine"):
        assert "certified, with a return receipt" in letter.body


def test_a_tracking_number_is_recorded_and_lands_on_the_timeline(client):
    from app.store import STATE

    _helper_signed(client)
    client.post("/family/mailed", data={"tracking_number": NUMBER})
    armando = STATE.clients[ARMANDO]
    assert armando.shipments[-1]["tracking_number"] == NUMBER.replace(" ", "")
    assert armando.shipments[-1]["mailed_by"] == "Rosa"
    assert "certified, tracking number" in armando.timeline[-1]["text"]
    assert armando.family_task["done"] is True


def test_a_number_that_cannot_be_one_is_not_saved_as_proof(client):
    from app.store import STATE

    _helper_signed(client)
    response = client.post("/family/mailed", data={"tracking_number": "oops!"},
                           follow_redirects=False)
    assert response.headers["location"] == "/family/mailed?bad=1"
    assert not STATE.clients[ARMANDO].shipments
    assert "does not look like a tracking" in client.get("/family/mailed?bad=1").text


def test_mailing_it_with_no_number_is_recorded_as_untracked(client):
    from app.store import STATE

    _helper_signed(client)
    client.post("/family/mailed", data={"tracking_number": ""})
    assert STATE.clients[ARMANDO].shipments[-1]["tracking_number"] == ""
    assert STATE.clients[ARMANDO].timeline[-1]["text"] == "Request mailed to the bureaus"


def test_the_tablet_shows_where_it_is_and_the_number(client, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app

    _helper_signed(client)
    client.post("/family/mailed", data={"tracking_number": NUMBER})

    tablet = TestClient(app)
    sign_in_inside(tablet, "28E3306")
    page = tablet.get("/inside/case").text
    assert "In the mail" in page and "The Post Office has it" in page
    assert NUMBER.replace(" ", "") in page and "Expected by" in page


def test_the_tablet_says_plainly_when_nothing_proves_it_was_sent(client):
    from fastapi.testclient import TestClient
    from app.main import app

    _helper_signed(client)
    client.post("/family/mailed", data={"tracking_number": ""})
    tablet = TestClient(app)
    sign_in_inside(tablet, "28E3306")
    assert "no way to prove it went" in tablet.get("/inside/case").text


def test_no_mail_card_shows_when_nothing_was_posted(client):
    sign_in_inside(client, "28E3306")
    assert "In the mail" not in client.get("/inside/case").text


def test_the_stub_walks_through_accepted_transit_and_delivered():
    from datetime import date, timedelta

    sent = date(2026, 10, 1)
    states = [mailing.lookup("9" * 20, sent.isoformat(), sent + timedelta(days=d)).state
              for d in (0, 3, 6)]
    assert states == ["accepted", "transit", "delivered"]
    assert mailing.lookup("", sent.isoformat()) is None


def test_the_stub_never_claims_to_be_real_usps_data():
    status = mailing.lookup("9" * 20, "2026-10-01")
    assert status.real is False
    assert any("stand-in" in s and "live tracking APIs" in s for s in SIMPLIFICATIONS)


def test_the_two_rules_the_advice_rests_on_are_sourced_and_the_gaps_are_open():
    assert "own expense" in FACTS["certified_mail_is_at_own_expense"].statement
    assert "not approved" in FACTS["special_handling_is_not_advanced"].statement
    assert any("legal mail" in q for q in OPEN_QUESTIONS)
    assert any("Domestic Mail Manual" in q for q in OPEN_QUESTIONS)


# --- dispute letters: handed to the coordinator, then posted ------------------

def _approved_letters(client):
    """Three drafted and approved dispute letters for Armando, one per bureau."""
    from app.letters import draft_dispute_set
    from app.store import STATE, add_draft, drafts_for, mutate

    with mutate():
        for d in draft_dispute_set(client_id=ARMANDO, client_name="A. Torres",
                                   creditor="Acme", last_four="1234",
                                   reason="not mine"):
            add_draft(d)
    for d in drafts_for(ARMANDO):
        client.post(f"/staff/{ARMANDO}/letters/{d['id']}/approve",
                    data={"body": d["body"]})
    return [d["id"] for d in drafts_for(ARMANDO)]


def test_a_letter_handed_to_the_coordinator_is_marked_and_not_yet_mailed(client):
    from app.store import STATE

    ids = _approved_letters(client)
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/handed", data={"on_date": ""})
    armando = STATE.clients[ARMANDO]
    letter = mailing.letter_shipment(armando, ids[0])
    assert letter["handed_on"] and not letter["mailed_on"]
    assert "handed in to the coordinator" in armando.timeline[-1]["text"]
    assert armando.timeline[-1]["actor"].startswith("Ms. ")


def test_the_second_step_adds_the_post_day_and_the_receipt_number(client):
    from app.store import STATE

    ids = _approved_letters(client)
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/handed", data={"on_date": ""})
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/mailed",
                data={"on_date": "", "tracking_number": NUMBER})
    letter = mailing.letter_shipment(STATE.clients[ARMANDO], ids[0])
    assert letter["handed_on"] and letter["mailed_on"]
    assert letter["tracking_number"] == NUMBER.replace(" ", "")
    assert "mailed, certified, tracking number" in STATE.clients[ARMANDO].timeline[-1]["text"]


def test_marking_it_handed_in_twice_changes_nothing(client):
    from app.store import STATE

    ids = _approved_letters(client)
    for _ in range(2):
        client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/handed", data={"on_date": ""})
    assert len([s for s in STATE.clients[ARMANDO].shipments
                if s["draft_id"] == ids[0]]) == 1


def test_each_bureau_gets_its_own_envelope_and_its_own_number(client):
    from app.store import STATE

    ids = _approved_letters(client)
    for i, draft_id in enumerate(ids):
        client.post(f"/staff/{ARMANDO}/letters/{draft_id}/mailed",
                    data={"on_date": "", "tracking_number": f"9407{i}0000000000000"})
    numbers = {s["tracking_number"] for s in STATE.clients[ARMANDO].shipments}
    assert len(numbers) == 3


def test_a_day_that_has_not_come_yet_is_refused(client):
    from datetime import date, timedelta
    from app.store import STATE

    ids = _approved_letters(client)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/mailed",
                data={"on_date": tomorrow, "tracking_number": NUMBER})
    assert not STATE.clients[ARMANDO].shipments


def test_a_letter_nobody_approved_cannot_be_marked_mailed(client):
    from app.letters import draft_dispute_set
    from app.store import STATE, add_draft, mutate

    with mutate():
        row = add_draft(draft_dispute_set(client_id=ARMANDO, client_name="A. Torres",
                                          creditor="Acme", last_four="1234",
                                          reason="not mine")[0])
    client.post(f"/staff/{ARMANDO}/letters/{row['id']}/mailed",
                data={"on_date": "", "tracking_number": NUMBER})
    assert not STATE.clients[ARMANDO].shipments


def test_a_helper_can_mark_a_letter_mailed_without_the_coordinator_touching_it(client):
    from app.store import STATE

    ids = _approved_letters(client)
    _helper_signed(client)
    page = client.get("/family/disputes").text
    assert "I mailed it" in page and "certified" in page
    client.post(f"/family/disputes/{ids[0]}/mailed",
                data={"on_date": "", "tracking_number": NUMBER})
    letter = mailing.letter_shipment(STATE.clients[ARMANDO], ids[0])
    assert letter["mailed_by"] == "Rosa" and not letter["handed_on"]


def test_the_helper_is_told_when_the_coordinator_already_has_a_letter(client):
    ids = _approved_letters(client)
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/handed", data={"on_date": ""})
    _helper_signed(client)
    assert "will post it" in client.get("/family/disputes").text


def test_the_helpers_one_task_becomes_the_dispute_letters_once_they_are_approved(client):
    _approved_letters(client)
    _helper_signed(client)
    task = client.get("/family/task").text
    assert "dispute letters" in task and "/family/disputes" in task


def test_the_tablet_shows_each_stage_of_a_letter_in_turn(client):
    from fastapi.testclient import TestClient
    from app.main import app

    ids = _approved_letters(client)
    tablet = TestClient(app)
    sign_in_inside(tablet, "28E3306")
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/handed", data={"on_date": ""})
    page = tablet.get("/inside/case").text
    assert "Ms. Reyes has it and will post it" in page
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/mailed",
                data={"on_date": "", "tracking_number": NUMBER})
    page = tablet.get("/inside/case").text
    assert NUMBER.replace(" ", "") in page and "Your dispute letter to" in page


def test_the_coordinators_desk_shows_the_posting_card_for_approved_letters(client):
    ids = _approved_letters(client)
    page = client.get(f"/staff/{ARMANDO}").text
    assert "Posting the approved letters" in page and "Handed to me" in page
    client.post(f"/staff/{ARMANDO}/letters/{ids[0]}/mailed",
                data={"on_date": "", "tracking_number": NUMBER})
    assert NUMBER.replace(" ", "") in client.get(f"/staff/{ARMANDO}").text
