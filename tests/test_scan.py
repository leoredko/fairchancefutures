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


def test_no_other_surface_can_put_a_report_in(client):
    """The helper used to photograph it. That flow is gone on purpose."""
    from app.routes.family import router as family
    from app.routes.inside import router as inside

    for router in (family, inside):
        for route in router.routes:
            if "POST" in getattr(route, "methods", set()):
                assert "report" not in route.path, route.path

    sign_in_helper(client, code="BRIDGE-4417")
    assert client.get("/family/report").status_code == 404

    # And the tablet never had the capability in the first place.
    assert not can(Surface.INSIDE, Capability.UPLOAD_FILE)
