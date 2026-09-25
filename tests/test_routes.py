"""End to end, through the HTTP layer.

The point of these is that the constraints hold against a URL, not just against
a function call. Hiding a button is not a control.
"""

from dataclasses import asdict

from app.redaction import NEVER_RENDERED, for_surface
from app.surfaces import Surface

from tests.conftest import (PIN, clear_reports, sign_in_helper, sign_in_inside,
                            sign_in_staff)


def test_the_front_page_needs_no_session(client):
    assert client.get("/").status_code == 200
    for url in ["/metrics", "/citations", "/signin", "/helper"]:
        assert client.get(url).status_code == 200, url


def test_each_surface_loads_once_signed_in(client):
    sign_in_inside(client)
    for url in ["/inside/intake/1", "/inside/case", "/inside/where-you-stand",
                "/inside/authorization"]:
        assert client.get(url).status_code == 200, url

    # The coordinator surface needs no sign-in; the vendor system did it.
    for url in ["/staff", "/staff/new", "/staff/m-alvarez",
                "/staff/j-whitfield/triage"]:
        assert client.get(url).status_code == 200, url


def test_queue_is_sorted_by_clock_not_by_name(staff):
    html = staff.get("/staff").text
    # R. Osei is 4 days overdue, so he is above everyone despite the alphabet.
    assert html.index("R. Osei") < html.index("M. Alvarez")
    assert html.index("M. Alvarez") < html.index("T. Brennan")


def test_the_tablet_can_read_a_report_and_answer_about_it_but_never_send_one():
    """Reading your own report is the point, and saying which items you do not
    recognize is the point of reading it.

    Sending a report is still impossible: there is no camera in this app and no
    route that would take a file. The guard is on the words that mean a
    document moving, not on the word report, because answering a question about
    a report is exactly what this surface is for.
    """
    from app.routes.inside import router

    reads = [r for r in router.routes if "GET" in getattr(r, "methods", set())]
    writes = [r for r in router.routes if "POST" in getattr(r, "methods", set())]
    assert any(r.path.endswith("/report") for r in reads)
    assert any("/read" in r.path for r in reads)

    for route in writes:
        for word in ("upload", "photo", "scan", "file", "send"):
            assert word not in route.path, route.path

    # And nothing on this surface takes a file, whatever the path is called.
    for route in writes:
        annotations = getattr(route.endpoint, "__annotations__", {})
        assert "UploadFile" not in str(annotations.values()), route.path


def test_the_tablet_still_cannot_upload_or_verify_identity():
    from app.surfaces import Capability, Surface, can

    assert not can(Surface.INSIDE, Capability.UPLOAD_FILE)
    assert not can(Surface.INSIDE, Capability.VERIFY_IDENTITY)


def test_helper_with_no_signed_form_gets_the_invitation_only(client):
    # J. Whitfield has a helper code but no authorization on file.
    sign_in_helper(client, code="BRIDGE-2231")
    landing = client.get("/family")
    assert landing.status_code == 200
    assert "asked you to help" in landing.text

    # The task surface bounces back to the invitation rather than opening.
    assert "asked you to help" in client.get("/family/task").text

    # And the scoped endpoints refuse outright.
    refused = client.get("/family/packet")
    assert refused.status_code == 403
    assert "No signed authorization" in refused.text


def test_signing_the_form_is_what_creates_standing(client):
    sign_in_helper(client, code="BRIDGE-2231")
    client.post("/family/accept", data={"helper_name": "Andre"})
    assert client.get("/family/packet").status_code == 200


def test_client_revokes_from_the_tablet_and_the_helper_loses_access(client):
    helper = sign_in_helper(client, code="BRIDGE-4417")
    assert helper.get("/family/packet").status_code == 200

    # Same browser, different door: the client signs in and cancels.
    sign_in_inside(client, identifier="28A1187")
    client.post("/inside/authorization/revoke")

    sign_in_helper(client, code="BRIDGE-4417", pin=PIN)
    refused = client.get("/family/packet")
    assert refused.status_code == 403
    assert "revoked" in refused.text


def test_naming_a_helper_from_the_tablet_grants_nothing_by_itself(client):
    sign_in_inside(client, identifier="28A0931")   # J. Whitfield
    client.post("/inside/authorization/name", data={"helper_name": "Andre"})

    import app.store as store
    assert store.get_authorization("j-whitfield") is None

    sign_in_helper(client, code="BRIDGE-2231")
    assert client.get("/family/packet").status_code == 403


def test_intake_answers_persist_and_prefill_the_staff_form(client):
    sign_in_inside(client, identifier="28A0931")
    # Question 3 is the first one that feeds triage; 1 and 2 ask what the
    # person knows rather than what they have.
    client.post("/inside/intake/3", data={"ever_had_account": "unsure"})

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


def test_the_tablet_and_the_helper_never_receive_the_sensitive_fields():
    """The boundary that is real is physical.

    A tablet read in a common area and a helper's phone are the two places a Social
    Security number cannot appear. This used to apply to the coordinator too,
    which was defending the wrong boundary: they hold the file already.
    """
    import app.store as store

    record = asdict(store.STATE.clients["m-alvarez"])
    record["ssn"] = "078-05-1120"

    for surface in (Surface.INSIDE, Surface.FAMILY):
        view = for_surface(record, surface, {"report_sharing"})
        for field in NEVER_RENDERED:
            assert field not in view.fields, f"{surface}: {field}"
        assert "ssn" in view.withheld


def test_the_coordinator_sees_the_file_they_already_hold(staff):
    """They request the birth certificate and hold the sentence and commitment
    paperwork. Hiding the number from them protects nobody."""
    import app.store as store

    record = store.STATE.clients["m-alvarez"]
    record.ssn = "078-05-1120"

    view = for_surface(asdict(record), Surface.STAFF, {"report_sharing"})
    assert view.get("ssn") == "078-05-1120"
    assert "ssn" not in view.withheld


def test_a_scanned_report_stays_truncated_even_for_the_coordinator(staff):
    """A separate protection from the one above, and it survives it. The
    disclosure is requested truncated, so that is what the document says."""
    import app.store as store

    staff.post("/staff/m-alvarez/report",
               data={"bureau": "Equifax", "consumer_name": "M. Alvarez",
                     "ssn_on_document": "078-05-1120", "accounts": "Cap One | 1111"})
    stored = store.STATE.reports["m-alvarez"][-1]
    assert stored["ssn_on_document"] == "XXX-XX-1120"


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


def test_the_client_page_says_what_is_blocking_the_id(staff):
    """This replaced the four-rung access ladder.

    The ladder modelled what a bureau would demand, which no public source
    establishes. What documents somebody actually has is knowable, is already
    reviewed quarterly by their coordinator, and has a real deadline attached.
    """
    html = staff.get("/staff/m-alvarez").text
    assert "What is blocking the ID" in html
    # The birth certificate is the one with no deadline of its own, which is
    # exactly why it is the one that gets left.
    assert "Birth certificate" in html
    assert "10 weeks" in html
    # And the page says which 120 days it means, because there are two and
    # mixing them up costs somebody their ID.
    assert "120 days after release" in html


def test_the_escalate_route_is_gone(staff):
    """Climbing a rung was the ladder's only verb. Nothing should answer it."""
    assert staff.post("/staff/m-alvarez/ladder/escalate").status_code == 404


def test_every_intake_answer_is_written_and_can_be_read_back(inside):
    """Question one promises the answer saves as it is given. This is the
    receipt. It used to be an /api/sync endpoint describing an offline queue
    draining, which never happened: every entry was marked synced as it was
    created, so it demonstrated a thing that did not occur."""
    inside.post("/inside/intake/1", data={"knows_score": "no"})
    payload = inside.get("/api/saves").json()
    assert payload["saved"] >= 1
    assert payload["writes"][-1]["field"] == "knows_score"
    assert payload["writes"][-1]["at"]


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


def test_the_front_page_is_not_a_demo_menu(client):
    """Seeded logins on the landing page make an application look like a
    sample. They live in docs/DEMO.md now."""
    html = client.get("/").text
    assert "Demo logins" not in html
    assert "28-A-1187" not in html
    assert "fictional" not in html.lower()
    assert "prototype" not in html.lower()


def test_no_wireframe_annotations_survive_in_the_product(client, staff):
    for url in ["/", "/citations", "/metrics"]:
        assert "Design note:" not in client.get(url).text, url
    for url in ["/staff", "/staff/m-alvarez", "/staff/j-whitfield/triage"]:
        assert "Design note:" not in staff.get(url).text, url


def test_the_language_choice_is_at_the_door_and_nowhere_else(client, inside):
    """The EN / ES pill was removed for being decoration over an English-only
    app. The choice is back because the Spanish is real, and it lives at the
    sign-in door: somebody who reads Spanish should not have to get through an
    English screen to find out the app speaks to them. It does not follow them
    around the app afterwards, because it is made once."""
    door = client.get("/signin").text
    assert "Español" in door
    assert "EN / ES" not in door

    for url in ["/inside/intake/1", "/inside/authorization"]:
        assert "EN / ES" not in inside.get(url).text


def test_the_door_names_the_languages_it_does_not_have(client):
    """Somebody who reads neither English nor Spanish finds that out here,
    from a screen that admits it, rather than by working through a course in a
    language they cannot read."""
    door = client.get("/signin").text
    assert "Other" in door
    assert "coming" in door.lower()


def test_choosing_a_language_sets_it_and_comes_back(client):
    chosen = client.post("/language", data={"lang": "es", "back": "/signin"},
                         follow_redirects=False)
    assert chosen.status_code == 303
    assert chosen.headers["location"] == "/signin"
    assert "bridge_lang" in chosen.cookies


def test_the_door_will_not_forward_you_off_this_app(client):
    """An open redirect on a sign-in page is somebody else's phishing page
    wearing our address."""
    for bad in ["https://example.com/x", "//example.com/x"]:
        out = client.post("/language", data={"lang": "es", "back": bad},
                          follow_redirects=False)
        assert out.headers["location"] == "/signin", bad


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


def test_nothing_here_invites_a_search_engine(client):
    """There is no authentication: the URL is the identity. A crawler that
    indexes /inside/marcus-w hands that address to anybody searching."""
    for path in ("/", "/signin", "/citations", "/staff"):
        assert client.get(path).headers["x-robots-tag"] == "noindex, nofollow"


def test_robots_file_disallows_everything(client):
    """The crawlers that read robots.txt never see the header."""
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Disallow: /" in robots.text


def test_plan_progress_reflects_the_drafts_actually_on_screen(staff):
    """A seeded 'not drafted yet' while three drafts sit there is a small lie
    that costs trust in the rest of the page."""
    assert "not drafted yet" in staff.get("/staff/m-alvarez").text

    staff.post("/staff/m-alvarez/letters/draft", data={"item": "0"})
    after = staff.get("/staff/m-alvarez").text
    assert "not drafted yet" not in after
    assert "0 of 3 letters approved" in after


def test_no_database_column_names_reach_a_screen(staff):
    """`ssn` and `full_account_number` sitting next to written sentences is
    what made the page look half finished."""
    html = staff.get("/staff/m-alvarez").text
    for raw in ("full_account_number", "report_summary", "case_state",
                "clock_sort", "ladder_rung"):
        assert raw not in html, raw
    # The where-this-stops card names the fields in words, which is what proves
    # the label registry is being used rather than the column names.
    assert "Social Security number" in html
    assert "Full account numbers" in html
    assert "Date of birth" in html


def test_the_counselor_can_see_the_din_and_the_facility(staff):
    """Both are needed: the facility is the envelope return address and the
    DIN has to be on it. They were being reported as withheld, which was
    wrong and confusing."""
    html = staff.get("/staff/m-alvarez").text
    assert "Facility" not in html.split("Where this stops")[1][:400]
    assert "DIN" not in html.split("Where this stops")[1][:400]


def test_a_seeded_client_with_a_live_case_lands_on_it_not_on_question_one(client):
    """A person mid-dispute signing in and being asked "do you know what your
    credit score is?" reads as an app that has lost their file. The seeded
    caseload carries the answers those people would have given."""
    signed_in = sign_in_inside(client, identifier="28A1187")
    landed = signed_in.get("/inside", follow_redirects=False)
    assert landed.headers["location"] == "/inside/case"


def test_the_one_client_who_has_not_started_still_lands_on_intake(client):
    """J. Whitfield is the fresh case on purpose, so he keeps question one."""
    signed_in = sign_in_inside(client, identifier="28A0931")
    landed = signed_in.get("/inside", follow_redirects=False)
    assert "/inside/intake/" in landed.headers["location"]


def test_seeded_intake_answers_prefill_the_triage_form(staff):
    """The coordinator opens triage on a seeded client and the tablet answers
    are already there, which is the whole point of the two question sets."""
    html = staff.get("/staff/t-brennan/triage").text
    checked = html.split('value="many"')[1].split(">")[0]
    assert "checked" in checked


def test_every_link_on_the_coordinator_queue_resolves(client):
    """The queue linked to /roles from the first build and the route never
    existed, so the main staff screen carried a dead link that pytest could not
    see. This walks the nav rather than trusting it."""
    import re

    html = client.get("/staff").text
    for href in set(re.findall(r'href="(/[^"#]*)"', html)):
        assert client.get(href).status_code == 200, href


def test_roles_is_generated_from_the_capability_table(client):
    """Not a hand-written slide. If a capability moves in app/surfaces.py this
    page moves with it, which is the whole reason to render it."""
    import html as html_module

    from app.surfaces import CAPABILITIES, Capability, Surface
    from app import labels

    # Unescaped, because several labels carry an apostrophe and the page is
    # right to escape it. Comparing raw text to escaped HTML fails for the
    # wrong reason.
    page = html_module.unescape(client.get("/roles").text)
    for capability in CAPABILITIES[Surface.INSIDE]:
        assert labels.capability(capability) in page, capability
    # And it says what the tablet cannot do, with the reason.
    assert labels.capability(Capability.UPLOAD_FILE) in page
    assert "no camera roll" in page or "no open web" in page


def test_roles_grounds_the_boundary_in_where_the_device_is_read(client):
    # The tablet is issued to one person rather than shared between them, so
    # the reason these fields stop is line of sight and who administers the
    # device, not who used it last.
    html = client.get("/roles").text
    assert "Social Security number" in html
    assert "line of sight" in html
    assert "coordinator's desk is neither" in html


def test_no_enum_value_reaches_the_roles_page(client):
    html = client.get("/roles").text
    for raw in ("upload_file", "verify_identity", "manage_caseload",
                "open_account", "view_ssn", "full_account_number"):
        assert raw not in html, raw


# --------------------------------------------------------------------------
# the bar
# --------------------------------------------------------------------------

TABLET_SCREENS = [
    "/inside", "/inside/learn", "/inside/case", "/inside/how-this-works",
    "/inside/authorization", "/inside/where-you-stand", "/inside/learn/scores",
    "/inside/report", "/inside/learn/lesson/three-papers/0",
]


def test_the_course_is_one_tap_from_every_tablet_screen(inside):
    """The house rule, defended on the nav rather than written about. The
    course is the part of this product that keeps working after somebody goes
    home, so no screen is allowed to be a dead end for it. This test exists
    because the link moved: it used to sit between the logo and the person's
    own name, and rearranging a bar is exactly how a link quietly goes missing
    from one screen."""
    for url in TABLET_SCREENS:
        page = inside.get(url, follow_redirects=True)
        assert page.status_code == 200, url
        assert "/inside/learn" in page.text, f"no way to the course from {url}"


def test_the_wordmark_is_at_the_door_and_the_mark_carries_the_rest(client, inside):
    """A wordmark repeated on every click-through stops being a brand and
    becomes furniture. The name appears where somebody finds out what they are
    looking at, and the mark carries it everywhere after that.

    The wordmark is not text: it is drawn, because the app loads no web fonts
    and its last letter is the mark itself turned on its side. So it is asked
    for by shape, and the accessible name is what carries the word."""
    door = client.get("/signin").text
    assert 'class="wordmark"' in door
    assert 'href="#wordmark"' in door
    assert 'aria-label="Bridge"' in door, "the drawn wordmark has no readable name"

    for url in TABLET_SCREENS:
        page = inside.get(url, follow_redirects=True).text
        assert 'class="mark"' in page, f"no mark on {url}"
        assert 'class="wordmark"' not in page, f"wordmark still on {url}"


def test_the_last_letter_of_the_wordmark_is_the_mark_itself(client):
    """The whole idea. The mark is a stone arch bridge and, turned on its
    side, an E: a spine with three arms. If the wordmark ever stopped
    referencing markpath it would be spelling the name in letters that merely
    resemble the logo, which is a different and much weaker thing."""
    import re

    door = client.get("/signin").text
    block = re.search(r'<g id="wordmark".*?</g>\s*</defs>', door, re.S)
    assert block, "no wordmark definition on the page"
    assert 'href="#markpath"' in block.group(0), \
        "the wordmark no longer ends in the mark"
    assert "rotate(-90)" in block.group(0), \
        "the mark is in the wordmark but not turned on its side"


def test_no_bar_subtitle_starts_lowercase(inside):
    """Sentence case everywhere. These read as one strip beside a person's own
    name, and half of them were lowercase."""
    import re

    for url in TABLET_SCREENS:
        page = inside.get(url, follow_redirects=True).text
        for found in re.findall(r'<span class="who">([^<]*)</span>', page):
            text = found.replace("&middot;", "·").strip()
            for part in text.split("·"):
                part = part.strip()
                if part and part[0].isalpha():
                    assert part[0].isupper(), f"{url}: {part!r} starts lowercase"


# --------------------------------------------------------------------------
# asking for your own report, with nobody outside
# --------------------------------------------------------------------------

def test_a_person_with_nobody_outside_can_still_ask_for_their_report(inside):
    """The question the product could not previously answer out loud: what
    happens to somebody with no family, no friend, nobody taking their calls.
    The helper surface reads like the route when it is only the faster one."""
    page = inside.get("/inside/request", follow_redirects=True)
    assert page.status_code == 200
    assert "You can do this on your own" in page.text
    assert "Ask for my report" in page.text


def test_the_request_letter_comes_back_to_the_facility_not_to_a_helper(inside):
    """The whole point of the self-served route. A delivery address belonging
    to somebody outside is the dependency this screen exists to remove."""
    page = inside.get("/inside/request", follow_redirects=True).text
    assert "Correctional Facility" in page


def test_asking_goes_on_the_timeline_as_something_the_person_did(inside):
    """Not a status flag. An event with nobody attached reads as a scam from
    inside, per the Cornish interview, so this is recorded the same way
    finishing a lesson is: a named person, on a real date."""
    inside.post("/inside/request", follow_redirects=True)
    case = inside.get("/inside/case", follow_redirects=True).text
    assert "You asked for your credit report" in case

    after = inside.get("/inside/request", follow_redirects=True).text
    assert "It is on its way" in after


def test_asking_twice_does_not_stack_up_on_the_timeline(inside):
    """Somebody tapping a button again because nothing visibly happened should
    not end up with the same event three times on their own case."""
    for _ in range(3):
        inside.post("/inside/request", follow_redirects=True)
    case = inside.get("/inside/case", follow_redirects=True).text
    assert case.count("You asked for your credit report") == 1


def test_the_empty_report_screen_says_how_to_make_one_arrive(inside):
    """It used to say reports come back on paper and never say how to start
    that, which is a dead end dressed as an explanation."""
    clear_reports()
    page = inside.get("/inside/report", follow_redirects=True).text
    assert "/inside/request" in page


def test_the_word_helper_never_reaches_a_screen(client, inside, helper, staff):
    """It named a person by their usefulness to somebody else.

    A family member is not a "helper", they are a person who happens to be
    outside, and a product that files them under their function to the case is
    doing the thing this one is otherwise careful not to do. The word is out
    of every screen; `helper_name` and the /helper route survive as
    identifiers, which nobody reads.
    """
    pages = []
    for surface, urls in (
        (client, ["/", "/roles", "/citations"]),
        (inside, ["/inside", "/inside/case", "/inside/authorization",
                  "/inside/report", "/inside/request", "/inside/learn"]),
        (helper, ["/family"]),
        (staff, ["/staff", "/staff/marcus-w"]),
    ):
        for url in urls:
            page = surface.get(url, follow_redirects=True)
            if page.status_code == 200:
                pages.append((url, page.text))

    assert len(pages) > 8, "too few pages reached for this to prove anything"
    for url, text in pages:
        # The identifiers are allowed; the word a person would read is not.
        visible = (text.replace("helper_name", "").replace("/helper", "")
                       .replace('id="helper"', "").replace('for="helper"', ""))
        assert "helper" not in visible.lower(), f"{url} still says it"
