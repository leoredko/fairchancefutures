"""Find text that paints on top of other text, on a running Bridge.

Two visible lines of type whose rectangles intersect is a layout bug pytest
cannot see, because catching it needs a browser actually doing layout. This
script drives one, measures every text node on every screen at several frame
sizes, and prints what collides. It only ever prints.

The bug that prompted it: the tablet frame has a fixed aspect ratio, so it is
a flex column with a fixed height, and a flex column with a fixed height
shrinks its children to fit. A pane shrunk below its own content does not
clip, it paints over the pane beneath it, so on any screen short enough the
language note landed underneath the sign-in heading. Nothing in the suite
could have caught that, and a person doing a walkthrough caught it in a
minute.

Run it against a server you started yourself:

    python3 -m uvicorn app.main:app --port 8111 &
    python3 scripts/check_overlap.py http://127.0.0.1:8111

Needs playwright and the Chromium at PLAYWRIGHT_BROWSERS_PATH; it is a
development tool rather than a dependency, which is why it is not in
requirements.txt and not in CI.
"""

from __future__ import annotations

import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8111"
CHROMIUM = "/opt/pw-browsers/chromium"

# Sizes a demonstration actually lands on: a laptop, a projector, a small
# window. The short ones are where a fixed-height frame starts squeezing.
SIZES = [(1440, 900), (1366, 768), (1280, 700), (1100, 650), (1280, 640), (1920, 1080)]

OPEN_SCREENS = ["/signin", "/", "/citations", "/metrics", "/roles", "/helper",
                "/staff", "/family"]
INSIDE_SCREENS = ["/inside", "/inside/start", "/inside/learn",
                  "/inside/how-this-works", "/inside/request", "/inside/report",
                  "/inside/where-you-stand", "/inside/case",
                  "/inside/authorization", "/inside/learn/scores",
                  "/inside/intake/0", "/inside/intake/1"]

# A DIN in the 28 range opens a case on the spot, which is how anybody tries
# the app. The PIN is set on first sign-in, because a PIN is never seeded.
DIN, PIN = "28-A-1187", "419307"

MEASURE = """
() => {
  const boxes = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walk.nextNode())) {
    if (!node.textContent.trim()) continue;
    const el = node.parentElement;
    if (!el) continue;
    const style = getComputedStyle(el);
    if (style.visibility === "hidden" || style.display === "none") continue;
    if (Number(style.opacity) === 0) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const r = range.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    boxes.push({text: node.textContent.trim().slice(0, 60), el, r});
  }
  const found = [];
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      // One inside the other is nesting, not a collision.
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const across = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left) - 2;
      const down = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top) - 2;
      if (across > 0 && down > 0) {
        found.push({a: a.text, b: b.text,
                    across: Math.round(across), down: Math.round(down)});
      }
    }
  }
  return found;
}
"""


def sign_in(page) -> str:
    """Get to the tablet, whether this DIN needs a PIN set or entered."""
    page.goto(f"{BASE}/signin", wait_until="networkidle")
    page.fill("input[name=identifier]", DIN)
    page.click('form[action="/signin"] button[type=submit]')
    page.wait_for_load_state("networkidle")
    for _ in range(3):
        fields = page.eval_on_selector_all(
            "form input[type=password]", "els => els.map(e => e.name)")
        if not fields:
            break
        for name in fields:
            page.fill(f'input[name="{name}"]', PIN)
        page.click("form button[type=submit]")
        page.wait_for_load_state("networkidle")
    return page.url


def report(path: str, size: str, hits: list) -> None:
    print(f"{path}  {size}: {len(hits)} overlapping")
    for hit in hits:
        print(f'    "{hit["a"]}"')
        print(f'      on top of "{hit["b"]}"  ({hit["across"]}px by {hit["down"]}px)')


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Needs playwright: pip install playwright")
        return 2

    checked = collisions = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM)
        for width, height in SIZES:
            size = f"{width}x{height}"
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()

            for path in OPEN_SCREENS:
                page.goto(BASE + path, wait_until="networkidle")
                page.wait_for_timeout(150)
                hits = page.evaluate(MEASURE)
                checked += 1
                collisions += len(hits)
                if hits:
                    report(path, size, hits)

            landed = sign_in(page)
            if "/inside" not in landed:
                print(f"Could not sign in at {size}, stopped at {landed}")
                return 2
            for path in INSIDE_SCREENS:
                page.goto(BASE + path, wait_until="networkidle")
                page.wait_for_timeout(150)
                if "/signin" in page.url:
                    print(f"Bounced back to sign-in on {path} at {size}")
                    return 2
                hits = page.evaluate(MEASURE)
                checked += 1
                collisions += len(hits)
                if hits:
                    report(path, size, hits)

            context.close()
        browser.close()

    print(f"\n{checked} screen renders checked at {len(SIZES)} sizes.")
    print("Nothing overlaps." if not collisions
          else f"{collisions} overlapping pairs of text.")
    return 1 if collisions else 0


if __name__ == "__main__":
    raise SystemExit(main())
