"""The only way a credit report gets into Bridge.

Nobody photographs anything. The paper arrives at the facility, the person
carries it to their coordinator, the coordinator scans it in, and from then on
the person reads it on their own tablet with the Social Security number covered.

These tests pin the two halves of that: the coordinator can do it, and neither
of the other two surfaces can.
"""

from app.report import mask_ssn, parse_accounts
from app.surfaces import Capability, Surface, can

from tests.conftest import clear_reports, sign_in_helper, sign_in_inside


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
    form = client.post("/staff/d-marsh/report/scan")
    assert form.status_code == 200
    assert "Check it before you save" in form.text

    saved = client.post("/staff/d-marsh/report", follow_redirects=False, data={
        "bureau": "TransUnion",
        "consumer_name": "D. Marsh",
        "ssn_on_document": "123-45-6789",
        "pulled_on": "2026-08-01",
        "accounts": "Midland Funding | xxxx4471 | 2019-02 | Open | $1,204 | not mine",
    })
    assert saved.status_code == 303

    # It landed on the person's own screen, without the number that would make
    # a screen other people can read dangerous.
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
    client.post("/staff/d-marsh/report", data={
        "bureau": "Equifax", "consumer_name": "D. Marsh",
        "accounts": "Cavalry SPV | xxxx8802 |  | Open |  | wrong middle initial",
    })
    from app.store import STATE

    flagged = STATE.clients["d-marsh"].flagged_items
    assert flagged == [{"creditor": "Cavalry SPV", "last_four": "8802",
                        "reason": "wrong middle initial"}]


def test_the_tablet_is_the_one_surface_that_can_never_send_a_report(client):
    """The helper is outside with a phone and a mailbox. The person inside is
    on the tablet, which has no camera and no way to attach anything, which is
    the constraint the whole three-route design exists to work around."""
    from app.routes.inside import router as inside

    for route in inside.routes:
        if "POST" in getattr(route, "methods", set()):
            # The tablet may say things about a report. It may never move one.
            for word in ("upload", "photo", "scan", "file", "send"):
                assert word not in route.path, route.path
            annotations = getattr(route.endpoint, "__annotations__", {})
            assert "UploadFile" not in str(annotations.values()), route.path
    assert not can(Surface.INSIDE, Capability.UPLOAD_FILE)


def test_the_helper_has_three_ways_in_and_the_pdf_is_offered_first(client):
    sign_in_helper(client, code="BRIDGE-4417")
    page = client.get("/family/report").text
    assert page.index("It is a PDF") < page.index("I will type it")
    assert page.index("I will type it") < page.index("take photos")


def test_a_typed_report_lands_on_the_coordinator_desk_not_the_tablet(client):
    """Accuracy check on the input side. These fields become a dispute letter,
    and a letter about the wrong account number is worse than no letter."""
    clear_reports()
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


# --------------------------------------------------------------------------
# three files back, and they disagree
# --------------------------------------------------------------------------

def test_the_seeded_case_has_all_three_bureaus_on_file():
    """Without these the product could show somebody asking for a report and
    never show one arriving, which is a demo of a waiting room."""
    from app.store import seed, stored_reports

    seed()
    reports = stored_reports("marcus-w", confirmed_only=True)
    assert {r.bureau for r in reports} == {"Equifax", "Experian", "TransUnion"}
    assert all(r.score for r in reports), "a file with no score teaches nothing"


def test_the_three_bureaus_disagree_about_the_same_person():
    """The disagreement is the content, not set dressing. It is why a dispute
    goes to all three, and it is why three scores pulled the same week are
    three different numbers."""
    from app.store import seed, stored_reports

    seed()
    reports = stored_reports("marcus-w", confirmed_only=True)
    by_bureau = {r.bureau: r for r in reports}

    # A collection he never opened, missing from one file entirely.
    def creditors(bureau):
        return {a.creditor for a in by_bureau[bureau].accounts}

    assert "Midland Funding LLC" in creditors("Equifax")
    assert "Midland Funding LLC" in creditors("Experian")
    assert "Midland Funding LLC" not in creditors("TransUnion")

    # A car loan paid in full, still reported open at two of the three.
    def auto_status(bureau):
        return next(a.status for a in by_bureau[bureau].accounts
                    if a.creditor == "Second Chance Auto Finance")

    assert "past due" in auto_status("Equifax")
    assert "past due" in auto_status("TransUnion")
    assert "paid in full" in auto_status("Experian")

    assert len({r.score for r in reports}) == 3, "three files, three numbers"


def test_the_score_panel_names_the_model_bureau_and_date_on_every_number():
    """app/scores.py exists to refuse a number with nothing attached to it. A
    score panel that broke that rule would be the one screen contradicting the
    lesson beside it."""
    from app import scores
    from app.store import seed, stored_reports

    seed()
    spread = scores.across_bureaus(stored_reports("marcus-w", confirmed_only=True))
    assert spread["spread"] > 0
    for row in spread["rows"]:
        assert row["bureau"] and row["model"] and row["pulled_on"]


def test_the_score_panel_says_nothing_when_there_is_only_one_file():
    """One number on its own is the thing this product refuses to show. The
    comparison has to have something to compare."""
    from app import scores
    from app.report import CreditReport

    one = [CreditReport(bureau="Equifax", client_id="x", pulled_on="2026-09-20",
                        scanned_on="2026-09-22", scanned_by="D. Reyes",
                        consumer_name="Marcus W.", score=600)]
    spread = scores.across_bureaus(one)
    assert spread["spread"] == 0
    assert spread["low"] is None


def test_the_tablet_never_renders_a_full_date_of_birth(inside):
    """Line of sight. The seeded reports carry a real date of birth so the
    coordinator's side has something to hold; the tablet gets the year."""
    page = inside.get("/inside/report", follow_redirects=True).text
    assert "1988-06-14" not in page
    assert "Born 1988" in page
