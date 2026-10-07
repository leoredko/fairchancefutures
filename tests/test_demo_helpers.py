"""Demo conveniences that save typing without weakening the product."""

from app.store import STATE
from tests.conftest import sign_in_inside


def test_an_identifier_in_the_signin_link_fills_the_box_and_nothing_else(client):
    page = client.get("/signin?identifier=28-E-3306").text
    assert 'value="28-E-3306"' in page
    assert "pin" not in page.lower().split('name="identifier"')[1].split(">")[0]


def test_sample_reports_give_somebody_something_to_read_and_do_not_stack(client):
    assert STATE.reports.get("d-marsh", []) == []
    for _ in range(2):
        assert client.post("/demo/sample-report", data={"client_id": "d-marsh"}).status_code == 200
    assert len(STATE.reports["d-marsh"]) == 3
    assert all(r["confirmed"] for r in STATE.reports["d-marsh"])
    assert all(r["ssn_on_document"] == "XXX-XX-0931" for r in STATE.reports["d-marsh"])


def test_starting_somebody_over_takes_loaded_sample_reports_away(client):
    client.post("/demo/sample-report", data={"client_id": "d-marsh"})
    client.post("/demo/restart", data={"client_id": "d-marsh"})
    assert STATE.reports.get("d-marsh", []) == []


def test_sample_reports_for_nobody_is_a_404(client):
    assert client.post("/demo/sample-report", data={"client_id": "nobody"}).status_code == 404


def test_the_sample_reports_open_on_the_tablet(client):
    client.post("/demo/sample-report", data={"client_id": "d-marsh"})
    sign_in_inside(client, identifier="28A0931")
    assert client.get("/inside/report").status_code == 200


def test_starting_armando_over_puts_his_reports_back_because_they_are_in_the_seed(client):
    client.post("/demo/restart", data={"client_id": "a-torres"})
    assert len(STATE.reports["a-torres"]) == 3
