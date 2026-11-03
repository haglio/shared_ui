from __future__ import annotations

FONT_UI = "Segoe UI"

SIZE_TINY = 8
SIZE_SMALL = 9
SIZE_BODY = 11
SIZE_HEADING = 14
SIZES = (SIZE_HEADING, SIZE_BODY, SIZE_SMALL, SIZE_TINY)


def in_pixels(points: float) -> int:
    return round(points * 96 / 72)
