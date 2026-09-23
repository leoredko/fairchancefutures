"""End to end, through the HTTP layer.

The point of these is that the constraints hold against a URL, not just against
a function call. Hiding a button is not a control.
"""

from dataclasses import asdict

from app.redaction import NEVER_RENDERED, for_surface
from app.surfaces import Surface

from tests.conftest import PIN, sign_in_helper, sign_in_inside, sign_in_staff


def test_the_front_page_needs_no_session(client):
    assert client.get("/").status_code == 200
    for url in ["/roles", "/metrics", "/citations", "/signin", "/helper",
                "/staff-signin"]:
        assert client.get(url).status_code == 200, url


def test_each_surface_loads_once_signed_in(client):
    sign_in_inside(client)
    for url in ["/inside/intake/1", "/inside/case", "/inside/where-you-stand",
                "/inside/authorization"]:
        assert client.get(url).status_code == 200, url

    sign_in_staff(client)
    for url in ["/staff", "/staff/m-alvarez", "/staff/j-whitfield/triage"]:
        assert client.get(url).status_code == 200, url


def test_queue_is_sorted_by_clock_not_by_name(staff):
    html = staff.get("/staff").text
    # R. Osei is 4 days overdue, so he is above everyone despite the alphabet.
    assert html.index("R. Osei") < html.index("M. Alvarez")
    assert html.index("M. Alvarez") < html.index("T. Brennan")


def test_tablet_has_no_upload_route():
    """There is no URL on the inside surface that accepts a file. Not disabled,
    absent."""
    from app.routes.inside import router

    routes = [r.path for r in router.routes]
    assert routes
    assert not any("report" in r or "upload" in r for r in routes)


def test_helper_with_no_signed_form_gets_the_invitation_only(client):
    # J. Whitfield has a helper code but no authorization on file.
    sign_in_helper(client, code="BRIDGE-2231")
    landing = client.get("/family")
    assert landing.status_code == 200
    assert "asked you to help" in landing.text

    # The task surface bounces back to the invitation rather than opening.
    assert "asked you to help" in client.get("/family/task").text

    # And the upload endpoint refuses outright.
    refused = client.get("/family/report")
    assert refused.status_code == 403
    assert "No signed authorization" in refused.text


def test_signing_the_form_is_what_creates_standing(client):
    sign_in_helper(client, code="BRIDGE-2231")
    client.post("/family/accept", data={"helper_name": "Andre"})
    assert client.get("/family/report").status_code == 200


def test_client_revokes_from_the_tablet_and_the_helper_loses_access(client):
    helper = sign_in_helper(client, code="BRIDGE-4417")
    assert helper.get("/family/report").status_code == 200

    # Same browser, different door: the client signs in and cancels.
    sign_in_inside(client, identifier="28A1187")
    client.post("/inside/authorization/revoke")

    sign_in_helper(client, code="BRIDGE-4417", pin=PIN)
    refused = client.get("/family/report")
    assert refused.status_code == 403
    assert "revoked" in refused.text


def test_naming_a_helper_from_the_tablet_grants_nothing_by_itself(client):
    sign_in_inside(client, identifier="28A0931")   # J. Whitfield
    client.post("/inside/authorization/name", data={"helper_name": "Andre"})

    import app.store as store
    assert store.get_authorization("j-whitfield") is None

    sign_in_helper(client, code="BRIDGE-2231")
    assert client.get("/family/report").status_code == 403


def test_intake_answers_persist_and_prefill_the_staff_form(client):
    sign_in_inside(client, identifier="28A0931")
    client.post("/inside/intake/2", data={"ever_had_account": "unsure"})

    import app.store as store
    assert store.STATE.clients["j-whitfield"].intake_answers["ever_had_account"] == "unsure"

    sign_in_staff(client)
    html = client.get("/staff/j-whitfield/triage").text
    checked = html.split('value="unsure"')[1].split(">")[0]
    assert "checked" in checked


def test_triage_classifies_and_reorders_the_queue(staff):
    staff.post("/staff/j-whitfield/triage", data={
        "ever_had_account": "yes",
        "report_result": "thin_or_stale",
        "collections": "none_found",
        "has_bank_account": "yes",
        "obligations": ["none"],
        "recognizes_everything": "some_not_mine",
    })
    import app.store as store
    whitfield = store.STATE.clients["j-whitfield"]
    assert whitfield.case_state == "errors_present"
    # Errors carry a legal clock, so he jumps ahead of the release-date ordering.
    assert whitfield.clock_sort < 0


def test_staff_never_receive_the_sensitive_fields(staff):
    import app.store as store

    record = store.STATE.clients["m-alvarez"]
    record.ssn = "078-05-1120"
    record.full_account_number = "4147202398761111"

    html = staff.get("/staff/m-alvarez").text
    # The values are absent from the rendered page, not merely styled away.
    assert record.ssn not in html
    assert record.full_account_number not in html

    view = for_surface(asdict(record), Surface.STAFF, {"report_sharing"})
    for field in NEVER_RENDERED:
        assert field not in view.fields
    assert "ssn" in view.withheld


def test_consent_off_hides_the_report_from_staff(staff):
    import app.store as store
    store.STATE.clients["m-alvarez"].consent_scopes = []
    assert "Report sharing is off" in staff.get("/staff/m-alvarez").text


def test_letter_approval_records_whether_it_was_edited(staff):
    staff.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    import app.store as store
    draft = store.drafts_for("m-alvarez")[0]

    staff.post(f"/staff/m-alvarez/letters/{draft['id']}/approve",
               data={"body": draft["body"] + "\nOne more line."})
    assert store.STATE.review_log == {"reviewed": 1, "edited": 1}
    assert "1 of 1" in staff.get("/metrics").text


def test_letter_leaves_the_ssn_blank_for_a_pen(staff):
    staff.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    import app.store as store
    body = store.drafts_for("m-alvarez")[0]["body"]
    assert "[client writes by hand on the printed copy]" in body
    assert "Midland Funding" in body


def test_ladder_escalates_one_rung_on_a_kickback(staff):
    import app.store as store
    assert store.STATE.clients["m-alvarez"].ladder_rung == 1
    staff.post("/staff/m-alvarez/ladder/escalate")
    assert store.STATE.clients["m-alvarez"].ladder_rung == 2
    assert store.STATE.clients["m-alvarez"].ladder_status["1"] == "Kicked back"


def test_roles_page_is_generated_from_the_capability_table(client):
    """The scope slide cannot drift from the code, because it is the code."""
    html = client.get("/roles").text
    # Rendered through the label registry, so the page shows sentences rather
    # than enum values.
    assert "Verify identity online" in html
    assert "Upload a file" in html
    assert "verify_identity" not in html


def test_offline_writes_land_in_the_sync_queue(inside):
    inside.post("/inside/intake/1", data={"has_bank_account": "no"})
    payload = inside.get("/api/sync").json()
    assert payload["synced"] >= 1


def test_none_is_exclusive_server_side(staff):
    """A checkbox group is not a control. The rule holds without the JS."""
    staff.post("/staff/j-whitfield/triage", data={
        "ever_had_account": "no",
        "report_result": "no_file_found",
        "collections": "none_found",
        "has_bank_account": "no",
        "obligations": ["none", "restitution"],
        "recognizes_everything": "not_reviewed_yet",
    })
    import app.store as store
    assert store.STATE.clients["j-whitfield"].intake_answers["obligations"] == ["restitution"]


def test_drafting_produces_a_letter_for_every_bureau(staff):
    from app.bureaus import BUREAUS
    import app.store as store

    staff.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    drafts = store.drafts_for("m-alvarez")
    assert {d["bureau"] for d in drafts} == {b.name for b in BUREAUS}


def test_the_en_es_pill_is_gone(inside):
    """There is no Spanish and lang is hardcoded en. A toggle that does not
    toggle is worse than no toggle."""
    for url in ["/inside/intake/1", "/inside/authorization"]:
        assert "EN / ES" not in inside.get(url).text


def test_citations_page_lists_every_fact_with_its_source(client):
    from app.sources import FACTS

    html = client.get("/citations").text
    for fact in FACTS.values():
        assert fact.source in html
        assert fact.url in html


def test_the_app_installs_as_a_tablet_app(client):
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    body = manifest.json()
    assert body["display"] == "standalone"
    assert body["start_url"] == "/"

    # The worker must be served from the root or it cannot claim the app.
    worker = client.get("/sw.js")
    assert worker.status_code == 200
    assert worker.headers["service-worker-allowed"] == "/"


def test_the_worker_makes_no_offline_promise(client):
    """Offline-first is a real feature and this worker is not it. If somebody
    adds a cache here, the tablet can serve a stale deadline."""
    worker = client.get("/sw.js").text
    assert "caches.open" not in worker
    assert "cache.match" not in worker


def test_health_check_answers(client):
    assert client.get("/healthz").json()["ok"] is True


def test_plan_progress_reflects_the_drafts_actually_on_screen(staff):
    """A seeded 'not drafted yet' while three drafts sit there is a small lie
    that costs trust in the rest of the page."""
    assert "not drafted yet" in staff.get("/staff/m-alvarez").text

    staff.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    after = staff.get("/staff/m-alvarez").text
    assert "not drafted yet" not in after
    assert "0 of 3 letters approved" in after


def test_design_notes_are_off_until_you_ask_for_them(staff):
    """Annotations inside a product are what make a product look like a
    wireframe. They are still worth having for a walkthrough, so they are a
    toggle rather than a deletion."""
    page = staff.get("/staff/m-alvarez")
    body_tag = page.text.split("<body", 1)[1][:80]
    assert "show-notes" not in body_tag
    assert "/notes/toggle" in page.text          # the way to turn them on
    assert "notes-card" in page.text             # the markup is there, just hidden

    staff.get("/notes/toggle")
    after = staff.get("/staff/m-alvarez").text.split("<body", 1)[1][:80]
    assert "show-notes" in after

    staff.get("/notes/toggle")
    off_again = staff.get("/staff/m-alvarez").text.split("<body", 1)[1][:80]
    assert "show-notes" not in off_again


def test_no_database_column_names_reach_a_screen(staff):
    """`ssn` and `full_account_number` sitting next to written sentences is
    what made the page look half finished."""
    html = staff.get("/staff/m-alvarez").text
    for raw in ("full_account_number", "report_summary", "case_state",
                "clock_sort", "ladder_rung"):
        assert raw not in html, raw
    assert "Social Security number" in html
    assert "Full account numbers" in html


def test_the_counselor_can_see_the_din_and_the_facility(staff):
    """Both are needed: the facility is the envelope return address and the
    DIN has to be on it. They were being reported as withheld, which was
    wrong and confusing."""
    html = staff.get("/staff/m-alvarez").text
    assert "Facility" not in html.split("Not shared with you")[1][:400]
    assert "DIN" not in html.split("Not shared with you")[1][:400]
