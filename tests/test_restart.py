"""Starting one person over.

A demo gets walked more than once. These defend the two halves of that: the
person who was rewound is genuinely back to the start, and nobody standing
next to them moved.
"""

from conftest import PIN, sign_in_inside, sign_in_helper


def _has_pin(subject_id: str) -> bool:
    from app.store import STATE

    return any(raw.get("subject_id") == subject_id and raw.get("pin_hash")
               for raw in STATE.accounts.values())


def test_restarting_clears_the_pin_so_the_next_sign_in_enrolls_again(client):
    sign_in_inside(client)
    assert _has_pin("marcus-w")

    client.post("/demo/restart", data={"client_id": "marcus-w"})

    assert not _has_pin("marcus-w")


def test_restarting_puts_the_intake_answers_back_to_the_seeded_ones(client):
    """Back to the start, not blank. An empty intake is a different demo."""
    from app.store import STATE

    sign_in_inside(client)
    client.post("/inside/intake/4", data={"has_bank_account": "yes"})
    assert STATE.clients["marcus-w"].intake_answers["has_bank_account"] == "yes"

    client.post("/demo/restart", data={"client_id": "marcus-w"})

    assert STATE.clients["marcus-w"].intake_answers["has_bank_account"] == "no"


def test_a_restart_leaves_everybody_else_where_they_were(client):
    """Two people are usually on this URL at once. Rewinding one of them is
    not permission to take the other one with them."""
    from app.store import STATE

    sign_in_helper(client, code="BRIDGE-8802")          # Rosa, for Alvarez
    assert _has_pin("m-alvarez")
    before = dict(STATE.clients["m-alvarez"].intake_answers)

    client.post("/demo/restart", data={"client_id": "marcus-w"})

    assert _has_pin("m-alvarez")
    assert STATE.clients["m-alvarez"].intake_answers == before


def test_the_seeded_reports_come_back_rather_than_vanishing(client):
    """A restart that left Marcus with no reports would hand back a stage with
    nothing on it, which is not the start of the demo."""
    from app.store import STATE

    client.post("/demo/restart", data={"client_id": "marcus-w"})

    assert len(STATE.reports["marcus-w"]) == 3


def test_restarting_the_person_you_are_signed_in_as_signs_you_out(client):
    """Their account no longer has a PIN, so the cookie names a case that has
    forgotten them."""
    sign_in_inside(client)
    landed = client.get("/inside", follow_redirects=False)
    assert "/signin" not in landed.headers["location"]

    client.post("/demo/restart", data={"client_id": "marcus-w"})

    after = client.get("/inside", follow_redirects=False)
    assert after.headers["location"].startswith("/signin")


def test_a_restart_survives_a_restart_of_the_process(client):
    """It writes. A reset that only lived in memory would come back on the
    next request that loaded the file."""
    import json

    import app.store as store

    sign_in_inside(client)
    client.post("/demo/restart", data={"client_id": "marcus-w"})

    raw = json.loads(store.DATA_PATH.read_text())
    marcus = [a for a in raw["accounts"].values()
              if a.get("subject_id") == "marcus-w"]
    assert marcus and not any(a.get("pin_hash") for a in marcus)


def test_restarting_somebody_who_opened_their_own_case_removes_it_rather_than_crashing(client):
    """A DIN typed on the tablet is never in the seed, so there is no seeded
    day to return them to. The restart page listed them and 500ed on click."""
    from app.identifiers import parse
    from app.routes.access import _open_a_case
    from app.store import STATE

    _open_a_case(parse("28-Q-7788"))
    cid = "din-28q7788"
    assert cid in STATE.clients

    response = client.post("/demo/restart", data={"client_id": cid})

    assert response.status_code == 200
    assert cid not in STATE.clients
    assert not any(a.get("subject_id") == cid for a in STATE.accounts.values())
    assert _open_a_case(parse("28-Q-7788")) is not None


def test_an_unknown_id_is_a_404_rather_than_a_silent_nothing(client):
    assert client.post("/demo/restart",
                       data={"client_id": "nobody"}).status_code == 404


def test_the_page_says_what_a_restart_throws_away(client):
    """A destructive button with no sentence under it is a trap."""
    page = client.get("/demo/restart").text
    assert "cannot be undone" in page
    assert "Marcus W." in page


def test_restart_is_not_a_product_capability(client):
    """It is a demo control. Putting it in the capability table would claim a
    person can erase a case file that holds a coordinator's work."""
    from app.surfaces import CAPABILITIES

    every = {c.value for caps in CAPABILITIES.values() for c in caps}
    assert not any("restart" in name or "reset" in name for name in every)


def test_armando_starts_with_nothing_done_so_the_journey_can_be_walked_live(client):
    from app.store import STATE
    armando = STATE.clients["a-torres"]
    assert armando.path == "" and not armando.intake_answers
    assert not any(armando.documents.values()) and len(armando.documents) == 3
    assert all(not a.get("pin_hash") for a in STATE.accounts.values())


def test_armandos_three_reports_are_on_his_case_before_anyone_signs_in(client):
    from app.store import STATE
    reports = STATE.reports["a-torres"]
    assert sorted(r["bureau"] for r in reports) == ["Equifax", "Experian", "TransUnion"]
    assert all(r["confirmed"] for r in reports)


def test_marking_a_document_on_file_puts_a_named_event_on_his_timeline(client):
    from app.store import STATE
    client.post("/staff/a-torres/documents/birth_certificate/on-file")
    armando = STATE.clients["a-torres"]
    assert armando.documents["birth_certificate"] is True
    assert armando.documents["social_security_card"] is False
    assert armando.timeline[-1]["actor"] == "Ms. Reyes"
