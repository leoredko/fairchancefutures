"""Regenerate the app icons.

Drawn in code rather than shipped as a binary nobody can edit. Run:

    python3 scripts/make_icons.py
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

INK = (31, 29, 26)
RUST = (180, 82, 42)
PAPER = (250, 248, 245)

OUT = Path(__file__).resolve().parents[1] / "app" / "static"


def draw(size: int) -> bytes:
    px = [[PAPER] * size for _ in range(size)]

    # Rounded plate in ink.
    margin = int(size * 0.08)
    radius = int(size * 0.18)
    for y in range(margin, size - margin):
        for x in range(margin, size - margin):
            dx = min(x - margin, (size - margin - 1) - x)
            dy = min(y - margin, (size - margin - 1) - y)
            if dx < radius and dy < radius:
                if (radius - dx) ** 2 + (radius - dy) ** 2 > radius * radius:
                    continue
            px[y][x] = INK

    # A bridge: deck, two piers, an arch over the top.
    deck_y = int(size * 0.56)
    thickness = max(2, int(size * 0.055))
    for y in range(deck_y, deck_y + thickness):
        for x in range(int(size * 0.22), int(size * 0.78)):
            px[y][x] = RUST
    for cx in (int(size * 0.33), int(size * 0.67)):
        for y in range(deck_y + thickness, int(size * 0.74)):
            for x in range(cx - thickness // 2, cx + thickness // 2 + 1):
                px[y][x] = RUST
    arch_r = int(size * 0.26)
    for step in range(1800):
        t = math.pi * step / 1800
        x = int(size // 2 + arch_r * math.cos(t))
        y = int(deck_y - arch_r * math.sin(t) * 0.9)
        for oy in range(thickness):
            if 0 <= y + oy < size and 0 <= x < size:
                px[y + oy][x] = RUST

    raw = b"".join(
        b"\x00" + b"".join(bytes(px[y][x]) for x in range(size))
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
