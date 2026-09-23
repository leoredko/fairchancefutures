"""End to end, through the HTTP layer.

The point of these is that the constraints hold against a URL, not just against
a function call. Hiding a button is not a control.
"""

from dataclasses import asdict

from app.redaction import NEVER_RENDERED, for_surface
from app.surfaces import Surface


def test_the_three_surfaces_load(client):
    for url in ["/", "/roles", "/metrics", "/staff",
                "/inside/marcus-w/intake/1", "/inside/marcus-w/case",
                "/family/marcus-w", "/staff/m-alvarez",
                "/staff/j-whitfield/triage"]:
        assert client.get(url).status_code == 200, url


def test_queue_is_sorted_by_clock_not_by_name(client):
    html = client.get("/staff").text
    # R. Osei is 4 days overdue, so he is above everyone despite the alphabet.
    assert html.index("R. Osei") < html.index("M. Alvarez")
    assert html.index("M. Alvarez") < html.index("T. Brennan")


def test_tablet_has_no_upload_route(client):
    """There is no URL on the inside surface that accepts a file. Not disabled,
    absent."""
    from app.routes.inside import router

    routes = [r.path for r in router.routes]
    assert routes
    assert not any("report" in r or "upload" in r for r in routes)


def test_helper_with_no_signed_form_gets_the_invitation_only(client):
    # J. Whitfield has no helper and no authorization.
    landing = client.get("/family/j-whitfield")
    assert landing.status_code == 200
    assert "asked you to help" in landing.text

    # The task surface bounces back to the invitation rather than opening.
    task = client.get("/family/j-whitfield/task")
    assert "asked you to help" in task.text

    # And the upload endpoint refuses outright.
    refused = client.get("/family/j-whitfield/report")
    assert refused.status_code == 403
    assert "No signed authorization" in refused.text


def test_signing_the_form_is_what_creates_standing(client):
    client.post("/family/j-whitfield/accept", data={"helper_name": "Andre"})
    assert client.get("/family/j-whitfield/report").status_code == 200


def test_client_revokes_from_the_tablet_and_the_helper_loses_access(client):
    assert client.get("/family/marcus-w/report").status_code == 200
    client.post("/inside/marcus-w/authorization/revoke")
    refused = client.get("/family/marcus-w/report")
    assert refused.status_code == 403
    assert "revoked" in refused.text


def test_naming_a_helper_from_the_tablet_grants_nothing_by_itself(client):
    client.post("/inside/j-whitfield/authorization/name",
                data={"helper_name": "Andre"}, follow_redirects=False)
    # The invitation is prefilled, but no grant exists until the helper accepts.
    import app.store as store
    assert store.get_authorization("j-whitfield") is None
    assert client.get("/family/j-whitfield/report").status_code == 403


def test_intake_answers_persist_and_prefill_the_staff_form(client):
    client.post("/inside/j-whitfield/intake/2", data={"ever_had_account": "unsure"})
    import app.store as store
    assert store.STATE.clients["j-whitfield"].intake_answers["ever_had_account"] == "unsure"
    html = client.get("/staff/j-whitfield/triage").text
    checked = html.split('value="unsure"')[1].split(">")[0]
    assert "checked" in checked


def test_triage_classifies_and_reorders_the_queue(client):
    client.post("/staff/j-whitfield/triage", data={
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


def test_staff_never_receive_the_sensitive_fields(client):
    import app.store as store

    record = store.STATE.clients["m-alvarez"]
    record.ssn = "078-05-1120"
    record.full_account_number = "4147202398761111"

    html = client.get("/staff/m-alvarez").text
    # The values are absent from the rendered page, not merely styled away.
    assert record.ssn not in html
    assert record.full_account_number not in html

    # And the filter drops them before a template ever sees them.
    view = for_surface(asdict(record), Surface.STAFF, {"report_sharing"})
    for field in NEVER_RENDERED:
        assert field not in view.fields
    assert "ssn" in view.withheld


def test_consent_off_hides_the_report_from_staff(client):
    import app.store as store
    store.STATE.clients["m-alvarez"].consent_scopes = []
    html = client.get("/staff/m-alvarez").text
    assert "Report sharing is off" in html


def test_letter_approval_records_whether_it_was_edited(client):
    client.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    import app.store as store
    draft = store.drafts_for("m-alvarez")[0]

    client.post(f"/staff/m-alvarez/letters/{draft['id']}/approve",
                data={"body": draft["body"] + "\nOne more line."})
    assert store.STATE.review_log == {"reviewed": 1, "edited": 1}
    assert "1 of 1" in client.get("/metrics").text


def test_letter_leaves_the_ssn_blank_for_a_pen(client):
    client.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    import app.store as store
    body = store.drafts_for("m-alvarez")[0]["body"]
    assert "[client writes by hand on the printed copy]" in body
    assert "Midland Funding" in body


def test_ladder_escalates_one_rung_on_a_kickback(client):
    import app.store as store
    assert store.STATE.clients["m-alvarez"].ladder_rung == 1
    client.post("/staff/m-alvarez/ladder/escalate")
    assert store.STATE.clients["m-alvarez"].ladder_rung == 2
    assert store.STATE.clients["m-alvarez"].ladder_status["1"] == "Kicked back"


def test_roles_page_is_generated_from_the_capability_table(client):
    """The scope slide cannot drift from the code, because it is the code."""
    html = client.get("/roles").text
    assert "verify identity" in html
    assert "upload file" in html


def test_offline_writes_land_in_the_sync_queue(client):
    client.post("/inside/marcus-w/intake/1", data={"has_bank_account": "no"})
    payload = client.get("/api/sync").json()
    assert payload["synced"] >= 1


def test_none_is_exclusive_server_side(client):
    """A checkbox group is not a control. The rule holds without the JS."""
    client.post("/staff/j-whitfield/triage", data={
        "ever_had_account": "no",
        "report_result": "no_file_found",
        "collections": "none_found",
        "has_bank_account": "no",
        "obligations": ["none", "restitution"],
        "recognizes_everything": "not_reviewed_yet",
    })
    import app.store as store
    assert store.STATE.clients["j-whitfield"].intake_answers["obligations"] == ["restitution"]


def test_drafting_produces_a_letter_for_every_bureau(client):
    from app.bureaus import BUREAUS
    import app.store as store

    client.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    drafts = store.drafts_for("m-alvarez")
    assert {d["bureau"] for d in drafts} == {b.name for b in BUREAUS}


def test_the_en_es_pill_is_gone(client):
    """There is no Spanish and lang is hardcoded en. A toggle that does not
    toggle is worse than no toggle."""
    for url in ["/inside/marcus-w/intake/1", "/family/marcus-w",
                "/inside/marcus-w/authorization"]:
        assert "EN / ES" not in client.get(url).text


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
    payload = client.get("/healthz").json()
    assert payload["ok"] is True


def test_plan_progress_reflects_the_drafts_actually_on_screen(client):
    """A seeded 'not drafted yet' while three drafts sit there is a small lie
    that costs trust in the rest of the page."""
    before = client.get("/staff/m-alvarez").text
    assert "not drafted yet" in before

    client.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    after = client.get("/staff/m-alvarez").text
    assert "not drafted yet" not in after
    assert "0 of 3 letters approved" in after
