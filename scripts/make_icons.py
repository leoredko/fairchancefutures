"""Regenerate the app icons.

Drawn in code rather than shipped as a binary nobody can edit. Run:

    python3 scripts/make_icons.py

The same mark the app carries: a stone arch bridge, which is also a B lying on
its back, the deck being the spine and the two arches the bowls. The geometry
below is the same 48x34 drawing as the `markpath` in `app/templates/base.html`
and in the standalone shell, scaled up, so the icon on the home screen and the
mark in the bar cannot drift apart.

Full bleed rather than a plate floating on white, because Android crops these
to whatever shape the launcher wants and a plate inside a crop is a plate with
its corners cut off. The mark sits well inside the safe zone for that crop.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

# The canvas and the gradient, from :root in app/static/bridge.css.
CANVAS = (0x08, 0x12, 0x0E)
STOPS = ((0x0E, 0x9B, 0x6E), (0x2D, 0xD4, 0xA0), (0x22, 0xD3, 0xEE))

OUT = Path(__file__).resolve().parents[1] / "app" / "static"

# The drawing, in the units of the SVG it mirrors.
VIEW_W, VIEW_H = 48.0, 34.0
DECK = (2.0, 7.0, 46.0, 11.5)          # x0, y0, x1, y1
BODY = (4.5, 13.5, 43.5, 30.0)
ARCHES = ((9.5, 21.5), (25.5, 37.5))   # x span of each arch
ARCH_TOP, ARCH_BOTTOM, ARCH_R = 24.0, 30.0, 6.0

# The mark occupies this much of the icon, leaving the rest as the safe margin
# a maskable icon needs.
COVERAGE = 0.62


def _in_mark(x: float, y: float) -> bool:
    """Is this point, in view units, part of the mark?"""
    if DECK[0] <= x <= DECK[2] and DECK[1] <= y <= DECK[3]:
        return True
    if not (BODY[0] <= x <= BODY[2] and BODY[1] <= y <= BODY[3]):
        return False
    # The arches are cut out of the body, so a point inside one is not mark.
    for left, right in ARCHES:
        if left <= x <= right and ARCH_TOP <= y <= ARCH_BOTTOM:
            return False
        centre = (left + right) / 2
        if y <= ARCH_TOP and (x - centre) ** 2 + (y - ARCH_TOP) ** 2 <= ARCH_R ** 2:
            return False
    return True


def _gradient(t: float) -> tuple[int, int, int]:
    """Three stops, the same sweep as the SVG: deep emerald into cyan."""
    t = min(max(t, 0.0), 1.0)
    if t <= 0.55:
        a, b, local = STOPS[0], STOPS[1], t / 0.55
    else:
        a, b, local = STOPS[1], STOPS[2], (t - 0.55) / 0.45
    return tuple(round(a[i] + (b[i] - a[i]) * local) for i in range(3))


def draw(size: int) -> bytes:
    scale = size * COVERAGE / VIEW_W
    off_x = (size - VIEW_W * scale) / 2
    off_y = (size - VIEW_H * scale) / 2

    # Three samples per axis, because a hard edge on an arch at 192px is the
    # difference between a mark and a staircase.
    steps = (0.17, 0.5, 0.83)
    rows = []
    for py in range(size):
        row = []
        for px in range(size):
            hits = 0
            for sy in steps:
                vy = (py + sy - off_y) / scale
                for sx in steps:
                    vx = (px + sx - off_x) / scale
                    if _in_mark(vx, vy):
                        hits += 1
            if not hits:
                row.append(CANVAS)
                continue
            ink = _gradient((px + py) / (2.0 * size))
            if hits == 9:
                row.append(ink)
            else:
                a = hits / 9.0
                row.append(tuple(
                    round(CANVAS[i] + (ink[i] - CANVAS[i]) * a) for i in range(3)))
        rows.append(row)

    raw = b"".join(
        b"\x00" + b"".join(bytes(rows[y][x]) for x in range(size))
        for y in range(size)
    )

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    for size in (192, 512):
        path = OUT / f"icon-{size}.png"
        path.write_bytes(draw(size))
        print(f"wrote {path} ({path.stat().st_size} bytes)")
