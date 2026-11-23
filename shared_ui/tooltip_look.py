from __future__ import annotations

from shared_ui.palette import BG_TERTIARY, BORDER_SUBTLE, TEXT_PRIMARY, as_hex
from shared_ui.spacing import BUTTON_PAD_H_TIGHT, BUTTON_PAD_V

__all__ = ["GROUND", "INK", "OUTLINE", "PAD_H", "PAD_V",
           "qt_box", "qt_lettering", "web_box"]

GROUND = BG_TERTIARY
OUTLINE = BORDER_SUBTLE
INK = TEXT_PRIMARY
PAD_V = BUTTON_PAD_V
PAD_H = BUTTON_PAD_H_TIGHT


def qt_box() -> str:
    return f"background-color: {as_hex(GROUND)}; border: 1px solid {as_hex(OUTLINE)};"


def qt_lettering() -> str:
    return f"color: {as_hex(INK)};"


def web_box() -> str:
    return (f"background:{as_hex(GROUND)}; color:{as_hex(INK)}; "
            f"border:1px solid {as_hex(OUTLINE)}; padding:{PAD_V}px {PAD_H}px")
