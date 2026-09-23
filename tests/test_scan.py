"""The only way a credit report gets into Bridge.

Nobody photographs anything. The paper arrives at the facility, the person
carries it to their coordinator, the coordinator scans it in, and from then on
the person reads it on their own tablet with the Social Security number covered.

These tests pin the two halves of that: the coordinator can do it, and neither
of the other two surfaces can.
"""

from app.report import mask_ssn, parse_accounts
from app.surfaces import Capability, Surface, can

from tests.conftest import sign_in_helper, sign_in_inside


def test_masking_keeps_the_last_four_and_nothing_else():
    assert mask_ssn("123-45-6789") == "XXX-XX-6789"
    assert mask_ssn("123456789") == "XXX-XX-6789"
    assert mask_ssn("") == "XXX-XX-XXXX"
    # Already truncated on the document, because the request asked for it.
    assert mask_ssn("XXX-XX-4417") == "XXX-XX-4417"


def test_a_line_with_a_reason_becomes_a_dispute_and_one_without_does_not():
    rows = parse_accounts(
        "Midland Funding | xxxx4471 | 2019-02 | Open | $1,204 | never opened this\n"
        "\n"
        "Cap One | xxxx2210 | 2016-04 | Closed, paid | $0 |\n"
        "   \n"
    )
    assert [r["creditor"] for r in rows] == ["Midland Funding", "Cap One"]
    assert rows[0]["disputed"] and rows[0]["note"] == "never opened this"
    assert not rows[1]["disputed"]


def test_short_lines_are_forgiven():
    """A coordinator fixing a misread should not have to count pipes."""
    rows = parse_accounts("Midland Funding")
    assert rows == [{"creditor": "Midland Funding", "number": "", "opened": "",
                     "status": "", "balance": "", "disputed": False, "note": ""}]


def test_the_coordinator_scans_and_the_person_reads_it_on_the_tablet(client):
    form = client.post("/staff/j-whitfield/report/scan")
    assert form.status_code == 200
    assert "Check it before you save" in form.text

    saved = client.post("/staff/j-whitfield/report", follow_redirects=False, data={
        "bureau": "TransUnion",
        "consumer_name": "J. Whitfield",
        "ssn_on_document": "123-45-6789",
        "pulled_on": "2026-08-01",
        "accounts": "Midland Funding | xxxx4471 | 2019-02 | Open | $1,204 | not mine",
    })
    assert saved.status_code == 303

    # It landed on the person's own screen, without the number that would make
    # a shared dayroom tablet dangerous.
    sign_in_inside(client, identifier="28A0931")
    page = client.get("/inside/report").text
    assert "TransUnion" in page
    assert "Midland Funding" in page
    assert "XXX-XX-6789" in page
    assert "123-45-6789" not in page
    assert "6789" in page  # the last four are the point of keeping any of it


def test_the_full_number_is_never_written_to_storage(client):
    client.post("/staff/m-alvarez/report", data={
        "bureau": "Equifax", "consumer_name": "M. Alvarez",
        "ssn_on_document": "987-65-4321", "accounts": "Cavalry SPV",
    })
    import json

    from app.store import STATE, _serialize

    assert "987-65" not in json.dumps(_serialize())
    assert STATE.reports["m-alvarez"][0]["ssn_on_document"] == "XXX-XX-4321"


def test_a_scanned_dispute_reason_becomes_the_flagged_item(client):
    client.post("/staff/j-whitfield/report", data={
        "bureau": "Equifax", "consumer_name": "J. Whitfield",
        "accounts": "Cavalry SPV | xxxx8802 |  | Open |  | wrong middle initial",
    })
    from app.store import STATE

    flagged = STATE.clients["j-whitfield"].flagged_items
    assert flagged == [{"creditor": "Cavalry SPV", "last_four": "8802",
                        "reason": "wrong middle initial"}]


def test_the_tablet_is_the_one_surface_that_can_never_send_a_report(client):
    """The helper is outside with a phone and a mailbox. The person inside is
    on a shared kiosk with no camera and no way to attach anything, which is
    the constraint the whole three-route design exists to work around."""
    from app.routes.inside import router as inside

    for route in inside.routes:
        if "POST" in getattr(route, "methods", set()):
            assert "report" not in route.path, route.path
    assert not can(Surface.INSIDE, Capability.UPLOAD_FILE)


def test_the_helper_has_three_ways_in_and_the_pdf_is_offered_first(client):
    sign_in_helper(client, code="BRIDGE-4417")
    page = client.get("/family/report").text
    assert page.index("It is a PDF") < page.index("I will type it")
    assert page.index("I will type it") < page.index("take photos")


def test_a_typed_report_lands_on_the_coordinator_desk_not_the_tablet(client):
    """Accuracy check on the input side. These fields become a dispute letter,
    and a letter about the wrong account number is worse than no letter."""
    sign_in_helper(client, code="BRIDGE-4417")
    client.post("/family/report", data={
        "how": "typed", "bureau": "Experian",
        "accounts": "Midland Funding | xxxx4471 | 2019-02 | Open | $1,204 | not his",
    })

    from app.store import pending_reports, stored_reports

    assert len(pending_reports("marcus-w")) == 1
    assert stored_reports("marcus-w", confirmed_only=True) == []

    # The person is told it arrived and is being checked, but sees none of
    # what it says. An empty screen would be its own lie: somebody told their
    # helper sent it in cannot tell waiting apart from broken.
    sign_in_inside(client, identifier="28A1187")
    page = client.get("/inside/report").text
    assert "Your counselor is" in page
    assert "Experian" in page
    assert "Midland Funding" not in page
    assert "4471" not in page

    # The coordinator reads it against the paper and signs off.
    client.post("/staff/marcus-w/report/0/confirm", data={
        "accounts": "Midland Funding | xxxx4471 | 2019-02 | Open | $1,204 | not his",
    })
    assert pending_reports("marcus-w") == []

    sign_in_inside(client, identifier="28A1187")
    assert "Experian" in client.get("/inside/report").text


def test_the_coordinator_scanning_at_their_own_desk_needs_no_second_signoff(client):
    """They are reading the paper as they type it. A confirm step here would be
    asking the same person to check their own work twice in one sitting."""
    client.post("/staff/r-osei/report", data={
        "bureau": "Equifax", "consumer_name": "R. Osei", "accounts": "Cap One",
    })
    from app.store import pending_reports, stored_reports

    assert pending_reports("r-osei") == []
    assert len(stored_reports("r-osei", confirmed_only=True)) == 1


def test_a_photo_says_out_loud_that_it_is_the_slow_way(client):
    """Nothing here reads words out of a picture. Offering the camera without
    saying that is how somebody waits three weeks for a transcription nobody
    scheduled."""
    sign_in_helper(client, code="BRIDGE-4417")
    page = client.get("/family/report?how=photo").text
    assert "reads the words out of a picture" in page

    client.post("/family/report", data={"how": "photo"})
    from app.store import pending_reports

    waiting = pending_reports("marcus-w")
    assert len(waiting) == 1
    assert "slowest route" in waiting[0].next_step


def test_no_report_route_anywhere_stores_a_whole_social_security_number(client):
    """Every door, not just the coordinator's."""
    sign_in_helper(client, code="BRIDGE-4417")
    client.post("/family/report", data={
        "how": "typed", "bureau": "Equifax", "ssn_on_document": "123-45-6789",
        "accounts": "Cap One",
    })
    import json

    from app.store import _serialize

    assert "123-45" not in json.dumps(_serialize())
