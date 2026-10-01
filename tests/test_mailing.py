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
    assert any("stand-in" in s and "USPS Tracking API" in s for s in SIMPLIFICATIONS)


def test_the_two_rules_the_advice_rests_on_are_sourced_and_the_gaps_are_open():
    assert "own expense" in FACTS["certified_mail_is_at_own_expense"].statement
    assert "not approved" in FACTS["special_handling_is_not_advanced"].statement
    assert any("legal mail" in q for q in OPEN_QUESTIONS)
    assert any("Domestic Mail Manual" in q for q in OPEN_QUESTIONS)
