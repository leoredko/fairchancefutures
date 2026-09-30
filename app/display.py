"""How the tablet looks to the person holding it: colour, text size, motion,
and whether it can read a screen aloud.

Same shape as the language choice and for the same reasons. It is a property of
the device in front of somebody rather than a fact about them, so it lives in a
cookie on the tablet, survives the idle timeout, and the next person can change
it in one tap. It is not on the case file, so a coordinator never sees it and
nothing about how somebody reads the screen ends up in a record.

The server writes the three values onto `<html>` before the page leaves, which
is why nothing flashes to the wrong theme and why it works with scripts off. A
locked-down facility tablet is exactly where scripts may be off.

The defaults are the look the product already had, so a tablet nobody has
touched is unchanged.
"""

from __future__ import annotations

THEMES = ("dark", "light", "contrast")
SIZES = ("normal", "large", "xlarge")
MOTIONS = ("full", "reduced")
READS = ("off", "on")
DICTATES = ("off", "on")

DEFAULTS = {"theme": "dark", "size": "normal", "motion": "full", "read": "off",
            "dictate": "off"}
CHOICES = {"theme": THEMES, "size": SIZES, "motion": MOTIONS, "read": READS,
           "dictate": DICTATES}

COOKIES = {
    "theme": "bridge_theme",
    "size": "bridge_size",
    "motion": "bridge_motion",
    "read": "bridge_read",
    "dictate": "bridge_dictate",
}

# A year, as the language is. Chosen once by somebody who does not want to
# choose again every time the tablet locks.
COOKIE_MAX_AGE = 60 * 60 * 24 * 365

# What the browser paints behind its own chrome, per theme.
THEME_COLOR = {"dark": "#08120E", "light": "#E9F0EC", "contrast": "#000000"}


def normalize(setting: str, value: str | None) -> str:
    """Whatever arrived, turned into a value that setting actually has."""
    value = (value or "").strip().lower()
    return value if value in CHOICES[setting] else DEFAULTS[setting]


def from_request(request) -> dict[str, str]:
    """All the settings for this tablet, with anything unset or bad defaulted."""
    return {name: normalize(name, request.cookies.get(cookie))
            for name, cookie in COOKIES.items()}


def color_scheme(theme: str) -> str:
    """The browser's own controls follow the theme, so a light page does not
    get dark scrollbars and form widgets."""
    return "light" if theme == "light" else "dark"
