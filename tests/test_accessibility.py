"""Whether the tablet can be read, by somebody who does not read it the way the
designer did.

The claims defended here are the ones a test can actually check: that every
colour pair a person has to read clears WCAG 2.2 AA in every theme, that the
display settings are remembered and reach the page, and that the markup carries
the structure a screen reader needs. What a test cannot check is whether it is
pleasant with a screen reader running. That needs a person with one, and
`docs/ACCESSIBILITY.md` says so rather than claiming it.

The colours are read out of `app/static/bridge.css` rather than repeated here,
so the test cannot drift from what ships.
"""

import re
from pathlib import Path

import pytest

from tests.conftest import sign_in_inside

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "app" / "static" / "bridge.css").read_text()

THEMES = ("dark", "light", "contrast")


# --------------------------------------------------------------------------
# reading the tokens
# --------------------------------------------------------------------------

def _block(selector: str) -> dict[str, str]:
    """The custom properties declared in one rule, by name."""
    found = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", CSS, re.S)
    assert found, f"no rule for {selector}"
    body = re.sub(r"/\*.*?\*/", "", found.group(1), flags=re.S)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", body))


def tokens(theme: str) -> dict[str, str]:
    """Every token as the theme sees it, references resolved to a hex colour."""
    raw = _block(":root")
    if theme != "dark":
        raw = {**raw, **_block(f'html[data-theme="{theme}"]')}

    def resolve(value: str, depth: int = 0) -> str:
        value = value.strip()
        ref = re.fullmatch(r"var\((--[\w-]+)\)", value)
        if ref and depth < 8:
            return resolve(raw[ref.group(1)], depth + 1)
        return value

    return {name: resolve(value) for name, value in raw.items()}


def _lum(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _hex(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", value))


# --------------------------------------------------------------------------
# contrast, per theme
# --------------------------------------------------------------------------

GROUNDS = ("surface", "page", "surface-2")


@pytest.mark.parametrize("theme", THEMES)
def test_body_text_reads_on_every_ground_it_sits_on(theme):
    """WCAG 1.4.3: 4.5 to 1. `faint` is used as text (the small print and the
    placeholder), so it is held to the same line as everything else."""
    t = tokens(theme)
    for text in ("ink", "ink-2", "muted", "faint"):
        for ground in GROUNDS:
            got = ratio(t[f"--{text}"], t[f"--{ground}"])
            assert got >= 4.5, f"{theme}: --{text} on --{ground} is {got:.2f}"


@pytest.mark.parametrize("theme", THEMES)
def test_links_and_their_hover_read_on_every_ground(theme):
    t = tokens(theme)
    for name in ("--link", "--link-hover"):
        for ground in GROUNDS:
            got = ratio(t[name], t[f"--{ground}"])
            assert got >= 4.5, f"{theme}: {name} on --{ground} is {got:.2f}"


@pytest.mark.parametrize("theme", THEMES)
def test_the_label_on_a_brand_button_reads(theme):
    """The rule that used to turn the label white on hover measured 1.9."""
    t = tokens(theme)
    for fill in ("--teal", "--amber"):
        got = ratio(t["--on-accent"], t[fill])
        assert got >= 4.5, f"{theme}: --on-accent on {fill} is {got:.2f}"
    # The timeline dot is filled with green, which is a text colour on light.
    got = ratio(t["--on-green"], t["--green"])
    assert got >= 4.5, f"{theme}: --on-green on --green is {got:.2f}"
    assert ratio(t["--btn-hover-ink"], t["--teal"]) >= 4.5


@pytest.mark.parametrize("theme", THEMES)
def test_every_tag_and_notice_reads(theme):
    t = tokens(theme)
    for kind in ("teal", "amber", "sky", "green", "rose"):
        got = ratio(t[f"--tag-{kind}-fg"], t[f"--tag-{kind}-bg"])
        assert got >= 4.5, f"{theme}: {kind} tag is {got:.2f}"
    # Body text also sits on the tinted card backgrounds.
    for soft in ("--amber-soft", "--green-soft", "--rose-soft", "--teal-soft",
                 "--sky-soft"):
        got = ratio(t["--ink"], t[soft])
        assert got >= 4.5, f"{theme}: --ink on {soft} is {got:.2f}"
    # The error line is coloured text on its own tint.
    assert ratio(t["--rose"], t["--rose-soft"]) >= 4.5


@pytest.mark.parametrize("theme", THEMES)
def test_the_edge_of_a_field_can_be_seen(theme):
    """WCAG 1.4.11: 3 to 1 for the boundary of a control, because a box whose
    edge cannot be seen is a box nobody knows they can type in."""
    t = tokens(theme)
    for ground in GROUNDS:
        got = ratio(t["--field-bd"], t[f"--{ground}"])
        assert got >= 3.0, f"{theme}: --field-bd on --{ground} is {got:.2f}"


@pytest.mark.parametrize("theme", THEMES)
def test_the_focus_ring_can_be_seen(theme):
    """WCAG 2.4.11 and 1.4.11: somebody moving through the page with a keyboard
    or a switch has to be able to see where they are."""
    t = tokens(theme)
    for ground in GROUNDS:
        got = ratio(t["--focus"], t[f"--{ground}"])
        assert got >= 3.0, f"{theme}: --focus on --{ground} is {got:.2f}"


def test_high_contrast_clears_the_stricter_line():
    """WCAG's enhanced level, 7 to 1, is what somebody who turns high contrast
    on is asking for."""
    t = tokens("contrast")
    for text in ("ink", "ink-2", "muted", "faint", "link"):
        for ground in GROUNDS:
            got = ratio(t[f"--{text}"], t[f"--{ground}"])
            assert got >= 7.0, f"--{text} on --{ground} is {got:.2f}"


def test_every_theme_defines_every_token_it_relies_on():
    """A theme that forgot one would silently inherit the dark value, which is
    how a light page ends up with pale text on it."""
    needed = {name for name in _block(":root") if name.startswith((
        "--tag-", "--ink", "--muted", "--faint", "--surface", "--page",
        "--link", "--focus", "--field-bd", "--warn-bd", "--good-bd",
        "--denied-bd"))}
    for theme in ("light", "contrast"):
        declared = _block(f'html[data-theme="{theme}"]')
        assert needed <= set(declared), (theme, sorted(needed - set(declared)))
    for theme in THEMES:
        assert all(_hex(v) for k, v in tokens(theme).items() if k in needed), theme


# --------------------------------------------------------------------------
# the settings, and that they reach the page
# --------------------------------------------------------------------------

from html.parser import HTMLParser  # noqa: E402

from app import display  # noqa: E402
from app.ui_strings import UI  # noqa: E402


def _html_tag(page: str) -> str:
    return re.search(r"<html[^>]*>", page).group(0)


def test_a_tablet_nobody_has_touched_looks_as_it_always_did(client):
    tag = _html_tag(client.get("/signin").text)
    assert 'data-theme="dark"' in tag
    assert 'data-size="normal"' in tag
    assert 'data-motion="full"' in tag


def test_a_choice_is_remembered_and_reaches_every_page(client):
    client.post("/display", data={"theme": "light", "back": "/signin"})
    for url in ["/signin", "/helper", "/display", "/citations"]:
        assert 'data-theme="light"' in _html_tag(client.get(url).text), url


def test_the_three_settings_are_independent(client):
    client.post("/display", data={"theme": "contrast"})
    client.post("/display", data={"size": "xlarge"})
    client.post("/display", data={"motion": "reduced"})
    tag = _html_tag(client.get("/signin").text)
    assert 'data-theme="contrast"' in tag
    assert 'data-size="xlarge"' in tag
    assert 'data-motion="reduced"' in tag


def test_a_value_nobody_offers_falls_back_to_the_default(client):
    client.post("/display", data={"theme": "hotpink", "size": "<script>"})
    tag = _html_tag(client.get("/signin").text)
    assert 'data-theme="dark"' in tag and 'data-size="normal"' in tag


def test_a_hand_edited_cookie_cannot_put_anything_on_the_page(client):
    client.cookies.set("bridge_theme", '"><script>alert(1)</script>')
    page = client.get("/signin").text
    assert "<script>alert(1)" not in page
    assert 'data-theme="dark"' in _html_tag(page)


def test_the_browsers_own_controls_follow_the_theme(client):
    client.post("/display", data={"theme": "light"})
    page = client.get("/signin").text
    assert 'name="color-scheme" content="light"' in page
    assert display.THEME_COLOR["light"] in page


def test_the_settings_page_will_not_forward_you_off_this_app(client):
    for bad in ["https://example.com/x", "//example.com/x", "/\\example.com",
                "javascript:alert(1)"]:
        out = client.post("/display", data={"theme": "light", "back": bad},
                          follow_redirects=False)
        assert "example.com" not in out.headers["location"], bad
        assert "javascript" not in out.headers["location"], bad
        page = client.get("/display", params={"back": bad}).text
        assert 'href="https://example.com' not in page, bad
        assert 'href="//example.com' not in page, bad


def test_done_goes_back_to_where_the_person_was(client):
    page = client.get("/display", params={"back": "/inside/learn"}).text
    assert 'href="/inside/learn"' in page


def test_the_page_says_which_option_is_picked_in_words_and_not_only_colour(client):
    client.post("/display", data={"size": "large"})
    page = client.get("/display").text
    assert page.count("Selected") == 5      # one per group
    assert 'aria-pressed="true"' in page


def test_every_string_the_settings_page_asks_for_exists():
    for group, values in display.CHOICES.items():
        assert f"display.{group}" in UI
        for value in values:
            assert f"display.{group}.{value}" in UI, (group, value)
            assert f"display.{group}.{value}.note" in UI, (group, value)


def test_the_settings_page_is_in_spanish_when_the_tablet_is(client):
    client.post("/language", data={"lang": "es", "back": "/signin"})
    page = client.get("/display").text
    assert "Cómo se ve esto" in page
    assert "Alto contraste" in page
    assert "How this looks" not in page


def test_reduced_motion_stops_the_opening_as_well_as_the_animations(client):
    client.post("/display", data={"motion": "reduced"})
    page = client.get("/signin").text
    assert 'data-motion="reduced"' in page
    # The script that reveals the opening reads the setting.
    assert 'dataset.motion === "reduced"' in page
    assert 'html[data-motion="reduced"]' in CSS


def test_the_way_to_the_settings_is_on_every_page_except_the_settings(client):
    assert 'class="dock"' in client.get("/signin").text
    assert 'class="dock"' not in client.get("/display").text
    assert 'class="dock"' not in client.get("/language").text


def test_the_corner_links_are_called_accessibility_and_language(client):
    page = client.get("/signin").text
    assert ">Accessibility</a>" in page
    assert ">Language</a>" in page
    assert ">Display</a>" not in page


# --------------------------------------------------------------------------
# structure, for a screen reader
# --------------------------------------------------------------------------

class _Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.mains = 0
        self.ids: list[str] = []
        self.skip_target = None
        self.labels_for: set[str] = set()
        self.inputs: list[dict] = []
        self.label_depth = 0
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("role") == "main" or tag == "main":
            self.mains += 1
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and "skip" in (a.get("class") or "").split():
            self.skip_target = (a.get("href") or "").lstrip("#")
        if tag == "label":
            self.label_depth += 1
            if "for" in a:
                self.labels_for.add(a["for"])
        if tag == "h1":
            self.h1 += 1
        if tag in ("input", "select", "textarea") and a.get("type") not in (
                "hidden", "submit", "button"):
            self.inputs.append({**a, "wrapped": self.label_depth > 0})

    def handle_endtag(self, tag):
        if tag == "label":
            self.label_depth -= 1


def _scan(html: str) -> _Scan:
    scan = _Scan()
    scan.feed(html)
    return scan


def _pages(client, inside, helper, staff):
    urls = ["/signin", "/helper", "/display", "/", "/citations", "/roles",
            "/metrics", "/inside/start", "/inside/learn",
            "/inside/learn/lesson/three-papers/0", "/inside/learn/finished",
            "/inside/case", "/inside/request", "/inside/report", "/inside/after",
            "/inside/intake/1", "/family", "/family/task", "/staff", "/staff/new",
            "/staff/j-whitfield", "/staff/j-whitfield/triage"]
    return urls


def test_every_page_has_one_main_and_a_skip_link_that_lands_on_it(client):
    """Somebody moving by keyboard or switch should not tab through the header
    on every screen, and a screen reader lists landmarks to jump between."""
    from tests.conftest import sign_in_helper

    sign_in_inside(client)
    for url in ["/signin", "/helper", "/display", "/", "/citations", "/roles",
                "/metrics", "/inside/start", "/inside/learn",
                "/inside/learn/lesson/three-papers/0", "/inside/learn/finished",
                "/inside/case", "/inside/request", "/inside/report",
                "/inside/after", "/inside/intake/1", "/staff", "/staff/new",
                "/staff/j-whitfield", "/staff/j-whitfield/triage"]:
        response = client.get(url)
        if response.status_code != 200:
            continue
        scan = _scan(response.text)
        assert scan.mains == 1, (url, scan.mains)
        assert scan.skip_target == "content", url
        assert scan.ids.count("content") == 1, url
        assert scan.h1 >= 1, url


def test_the_pin_screens_name_their_fields(client):
    """The PIN screens are only reachable after a POST, so the page loop below
    cannot fetch them."""
    door = client.post("/signin", data={"identifier": "28A1187"}).text
    assert 'aria-labelledby="pin-title"' in door or 'for="pin"' in door
    for field in _scan(door).inputs:
        assert (field.get("aria-labelledby") or field.get("id")), field


def test_every_field_has_a_name_a_screen_reader_can_read(client):
    sign_in_inside(client)
    for url in ["/signin", "/helper", "/inside/intake/1", "/inside/request",
                "/staff/new", "/display"]:
        response = client.get(url)
        if response.status_code != 200:
            continue
        scan = _scan(response.text)
        for field in scan.inputs:
            named = (field.get("aria-label") or field.get("aria-labelledby")
                     or field.get("wrapped")
                     or (field.get("id") and field["id"] in scan.labels_for))
            # A field the door labels with a visible heading and a placeholder
            # is still a field with no name to a screen reader.
            assert named, (url, field)


# --------------------------------------------------------------------------
# read aloud
#
# The tablet has a speaker and a headphone jack, so this is buildable. What
# makes it safe is what it refuses to do: use a voice that sends the text to a
# service, listen to anything, or start without being asked. Those are claims
# about the script, so they are tests on the script.
# --------------------------------------------------------------------------

LISTEN = (ROOT / "app" / "static" / "listen.js").read_text()


def test_read_aloud_is_off_until_somebody_turns_it_on(client):
    page = client.get("/signin").text
    assert 'data-read="off"' in page
    assert "listen.js" not in page
    assert "listen-config" not in page


def test_turning_it_on_loads_the_script_with_the_words_it_needs(client):
    client.post("/display", data={"read": "on"})
    page = client.get("/signin").text
    assert 'data-read="on"' in page
    assert "/static/listen.js" in page
    assert 'data-listen="Listen"' in page
    assert "headphones" in page


def test_the_buttons_words_follow_the_language_of_the_tablet(client):
    client.post("/display", data={"read": "on"})
    client.post("/language", data={"lang": "es", "back": "/signin"})
    page = client.get("/signin").text
    assert 'data-listen="Escuchar"' in page
    assert 'data-stop="Parar"' in page


def test_the_script_only_ever_uses_a_voice_that_stays_on_the_tablet():
    """Many browser voices stream the text to a cloud service, and this text is
    next to a person's name and case. `localService` is the browser's own word
    for which is which."""
    assert "localService === true" in LISTEN
    # No path picks a voice without going through that filter.
    assert LISTEN.count("getVoices") == 2   # once to pick, once to see if any exist
    assert "pickVoice" in LISTEN


def test_the_script_cannot_listen_or_call_out():
    for forbidden in ("getUserMedia", "SpeechRecognition", "webkitSpeechRecognition",
                      "fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon",
                      "mediaDevices", "localStorage", "sessionStorage", "cookie"):
        assert forbidden not in LISTEN, forbidden


def test_the_script_says_nothing_until_a_button_is_pressed():
    """The only call to `speak` is inside `start`, which only the button runs."""
    assert LISTEN.count("synth.speak(") == 1
    assert LISTEN.index("synth.speak(") > LISTEN.index("function start()")
    assert 'addEventListener("click"' in LISTEN


def test_leaving_the_page_ends_the_speech():
    assert "pagehide" in LISTEN and "synth.cancel()" in LISTEN


def test_a_citation_is_not_read_aloud(client):
    """It is an English source line and a statute number, which a Spanish voice
    would mangle and which is for a law library rather than for the ear."""
    sign_in_inside(client)
    for index in range(6):
        page = client.get(f"/inside/learn/lesson/three-papers/{index}").text
        if "Where this comes from" in page or "De dónde viene" in page:
            assert "data-no-speech" in page
            return
    raise AssertionError("no card with a source was found to check")


# --------------------------------------------------------------------------
# voice typing, on the coordinator's desk only
#
# The tablet is the wrong place for it: the only typed fields there are a DIN, a
# PIN and a human check, and speaking those in a common area is a leak. The
# fields that are left are account lines, where a misheard digit becomes a
# letter about the wrong account, and the dispute letter, which is prose a
# coordinator reads before approving. So it goes on the letter and nowhere else,
# and only with recognition that runs on the computer.
# --------------------------------------------------------------------------

DICTATE = (ROOT / "app" / "static" / "dictate.js").read_text()
TEMPLATES = ROOT / "app" / "templates"


def test_voice_typing_is_off_until_somebody_turns_it_on(client):
    page = client.get("/signin").text
    assert 'data-voice="off"' in page
    assert "dictate.js" not in page and "dictate-config" not in page


def test_the_setting_flag_cannot_be_mistaken_for_a_field_to_dictate_into(client):
    """The first version put `data-dictate` on <html> as the flag, which the
    script's own selector then matched, and it crashed trying to add a button
    beside the page. Found by driving it, not by reading it."""
    client.post("/display", data={"dictate": "on"})
    page = client.get("/signin").text
    assert 'data-voice="on"' in page
    assert "data-dictate" not in _html_tag(page)
    assert 'textarea[data-dictate], input[data-dictate]' in DICTATE


def test_turning_it_on_loads_the_script_with_the_words_it_needs(client):
    client.post("/display", data={"dictate": "on"})
    page = client.get("/signin").text
    assert "/static/dictate.js" in page
    assert 'data-start="Dictate"' in page


def test_the_only_field_that_can_be_dictated_into_is_the_dispute_letter():
    marked = [path.relative_to(TEMPLATES).as_posix()
              for path in TEMPLATES.rglob("*.html")
              if re.search(r"<(?:textarea|input)[^>]*\bdata-dictate\b",
                           path.read_text())]
    assert marked == ["staff/client.html"], marked


def test_the_tablet_has_nothing_to_dictate_into():
    for path in (TEMPLATES / "inside").glob("*.html"):
        assert "data-dictate" not in path.read_text(), path.name
    for path in (TEMPLATES / "access").glob("*.html"):
        assert "data-dictate" not in path.read_text(), path.name


def test_no_number_that_becomes_a_letter_can_be_dictated():
    """The account lines and the Social Security field. A misheard digit is a
    dispute about the wrong account, which the product treats as worse than no
    dispute."""
    for name in ("staff/scan.html", "family/send_report.html"):
        assert "data-dictate" not in (TEMPLATES / name).read_text(), name


def test_the_script_only_listens_when_the_recognition_stays_on_the_computer():
    assert "processLocally: true" in DICTATE
    assert "r.processLocally = true" in DICTATE
    # A browser that ignores the property is refused, not trusted.
    assert "r.processLocally !== true" in DICTATE
    assert 'state !== "available"' in DICTATE
    # It cannot start without going through that check.
    assert DICTATE.index("SR.available") < DICTATE.index("fields.forEach(attach)")


def test_the_voice_typing_script_cannot_call_out_or_keep_anything():
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon",
                      "localStorage", "sessionStorage", "document.cookie",
                      "getUserMedia"):
        assert forbidden not in DICTATE, forbidden


def test_it_starts_only_when_the_button_is_pressed_and_stops_on_leaving():
    assert DICTATE.count("r.start()") == 1
    assert DICTATE.index("r.start()") > DICTATE.index("function begin()")
    assert 'addEventListener("click"' in DICTATE
    assert "pagehide" in DICTATE and "rec.abort()" in DICTATE


def test_words_go_where_the_cursor_was_and_not_at_the_top_of_the_letter():
    """Pressing the button moves focus to the button, so the place is kept from
    the blur. The first version dropped dictated words at the start of the
    letter."""
    assert 'addEventListener("blur"' in DICTATE
    assert "caret === null ? field.value.length" in DICTATE
