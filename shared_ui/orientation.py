from __future__ import annotations

PORTRAIT = "portrait"
LANDSCAPE = "landscape"
ORIENTATIONS = (PORTRAIT, LANDSCAPE)


def orientation_of_size(width: int, height: int) -> str:
    return PORTRAIT if height > width else LANDSCAPE
