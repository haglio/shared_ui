from __future__ import annotations

from shared_ui.palette import BG_PRIMARY, BORDER_PANEL, TEXT_PRIMARY, as_hex, as_rgba
from shared_ui.spacing import BUTTON_RADIUS, GAP_SMALL
from shared_ui.type_scale import FONT_UI, SIZE_TINY, in_pixels

__all__ = ["GROUND", "GROUND_ALPHA", "INK", "LETTERING", "LETTERING_SIZE", "OUTLINE", "PAD", "RADIUS",
           "qt_box", "qt_lettering", "web_box"]

GROUND = BG_PRIMARY
GROUND_ALPHA = 240
OUTLINE = BORDER_PANEL
INK = TEXT_PRIMARY
RADIUS = BUTTON_RADIUS
PAD = GAP_SMALL
LETTERING = FONT_UI
LETTERING_SIZE = SIZE_TINY


def qt_box() -> str:
    red, green, blue = GROUND
    return (f"background-color: rgba({red}, {green}, {blue}, {GROUND_ALPHA}); "
            f"border: 1px solid {as_hex(OUTLINE)}; border-radius: {RADIUS}px;")


def qt_lettering() -> str:
    return f'color: {as_hex(INK)}; font: bold {LETTERING_SIZE}pt "{LETTERING}";'


def web_box() -> str:
    return (f"background:{as_rgba(GROUND, round(GROUND_ALPHA / 255, 3))}; color:{as_hex(INK)}; "
            f"border:1px solid {as_hex(OUTLINE)}; border-radius:{RADIUS}px; padding:{PAD}px; "
            f"font:bold {in_pixels(LETTERING_SIZE)}px '{LETTERING}'; text-align:center")
