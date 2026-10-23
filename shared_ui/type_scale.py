"""The family's lettering as plain numbers -- no toolkit.

One face and four sizes, in points as a window sets them. ``in_pixels`` is the
same size for whatever letters in pixels: a Funestra's HUD and a loading screen
drawn with Pillow, a page's CSS, a panel in the headset.
"""

from __future__ import annotations

FONT_UI = "Segoe UI"

SIZE_TINY = 8
SIZE_SMALL = 9
SIZE_BODY = 11
SIZE_HEADING = 14


def in_pixels(points: float) -> int:
    return round(points * 96 / 72)
