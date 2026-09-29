"""Buttons are a flat colour, and their labels are readable on it.

The primary button used to be a teal-to-cyan ramp with a white label. White on
the bright end of that ramp measures 1.81 against a 4.5 minimum, so the label
was failing contrast across most of the button it sat on, and the gradient was
hiding it: the dark end looked fine and carried the eye.

Flat colour makes that measurable, which is the point. A tablet is read in a
day room under whatever light is there, by somebody who may not be able to lean
in, so this is not a theme preference.
"""

import re
from pathlib import Path

import pytest

CSS = Path(__file__).resolve().parents[1] / "app" / "static" / "bridge.css"

# Everything a person presses. Not .ghost or .quiet, which are transparent by
# design and take their contrast from the surface behind them.
FILLED = (".btn", ".btn.amber", ".langpick.on")


def stylesheet() -> str:
    """The stylesheet with comments removed.

    They have to go before anything is matched: the comment above `.btn`
    explains why it is not a gradient any more, and the first version of this
    test failed on the word inside its own explanation.
    """
    return re.sub(r"/\*.*?\*/", "", CSS.read_text(), flags=re.S)


def rules_for(selector: str) -> list[str]:
    """Every declaration block whose selector list contains exactly this one."""
    found = []
    for block in re.finditer(r"([^{}]+)\{([^}]*)\}", stylesheet()):
        selectors = [s.strip() for s in block.group(1).split(",")]
        if selector in selectors:
            found.append(block.group(2))
    return found


@pytest.mark.parametrize("selector", FILLED)
def test_a_button_is_never_filled_with_a_gradient(selector):
    for body in rules_for(selector):
        assert "gradient" not in body, f"{selector}: {body.strip()}"
        # var(--grad) is the gradient by another name, which is how it got past
        # the first read of this file.
        assert "--grad)" not in body, f"{selector}: {body.strip()}"


def test_the_gradients_that_are_not_buttons_are_left_alone():
    """The hero is a slab on purpose and the accent hairline is four colours.

    Stated so that deleting them later is a decision somebody makes rather than
    a tidy-up that happens while doing something else.
    """
    css = CSS.read_text()
    assert "--grad: linear-gradient" in css
    for keeper in (".hero {", ".card.accent::before {"):
        assert keeper in css


def contrast(a: str, b: str) -> float:
    def lum(h):
        h = h.lstrip("#")
        parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        parts = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
                 for x in parts]
        return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]

    hi, lo = max(lum(a), lum(b)), min(lum(a), lum(b))
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("label,fill,ink", [
    ("primary", "#2DD4A0", "#06140E"),
    ("amber", "#F0A93C", "#1B1206"),
])
def test_a_button_label_clears_the_contrast_floor(label, fill, ink):
    """4.5 to 1, which is AA for text at the size these labels are set."""
    assert contrast(ink, fill) >= 4.5, f"{label}: {contrast(ink, fill):.2f}"


def test_white_on_the_brand_teal_is_the_thing_that_was_wrong():
    """Kept as a number rather than a memory, so nobody re-proposes it."""
    assert contrast("#FFFFFF", "#2DD4A0") < 2
