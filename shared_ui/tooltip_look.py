from __future__ import annotations

from shared_ui.palette import BG_TERTIARY, BORDER_SUBTLE, TEXT_PRIMARY, as_hex
from shared_ui.spacing import BUTTON_PAD_H_TIGHT, BUTTON_PAD_V
from shared_ui.type_scale import FONT_UI, SIZE_SMALL

__all__ = ["GROUND", "GROUND_ALPHA", "INK", "LETTERING", "LETTERING_SIZE", "OUTLINE", "PAD", "PAD_H", "PAD_V", "RADIUS",
           "qt_box", "qt_lettering", "web_box"]

GROUND = BG_TERTIARY
OUTLINE = BORDER_SUBTLE
INK = TEXT_PRIMARY
PAD_V = BUTTON_PAD_V
PAD_H = BUTTON_PAD_H_TIGHT

PAD = PAD_V
RADIUS = 0
GROUND_ALPHA = 255
LETTERING = FONT_UI
LETTERING_SIZE = SIZE_SMALL


def qt_box() -> str:
    return f"background-color: {as_hex(GROUND)}; border: 1px solid {as_hex(OUTLINE)};"


def qt_lettering() -> str:
    return f"color: {as_hex(INK)};"


def web_box() -> str:
    return (f"background:{as_hex(GROUND)}; color:{as_hex(INK)}; "
            f"border:1px solid {as_hex(OUTLINE)}; padding:{PAD_V}px {PAD_H}px")
