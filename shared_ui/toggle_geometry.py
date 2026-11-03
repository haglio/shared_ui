from __future__ import annotations

from shared_ui.spacing import BUTTON_SIZE, BUTTON_SIZE_HUD

__all__ = ["HANDLE_INSET", "HANDLE_INSET_HUD", "TRACK", "TRACK_HUD", "handle"]

TRACK = (38, 20)
HANDLE_INSET = 3


def _at_hud_size(length: int) -> int:
    return round(length * BUTTON_SIZE_HUD / BUTTON_SIZE)


TRACK_HUD = (_at_hud_size(TRACK[0]), _at_hud_size(TRACK[1]))
HANDLE_INSET_HUD = _at_hud_size(HANDLE_INSET)


def handle(track: tuple[float, float, float, float], *, on: bool,
           inset: float) -> tuple[float, float, float]:
    x, y, width, height = track
    diameter = height - 2 * inset
    return (x + width - inset - diameter if on else x + inset, y + inset, diameter)
