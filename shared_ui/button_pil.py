from __future__ import annotations

from PIL import ImageDraw

from shared_ui.palette import BG_BUTTON, TEXT_MUTED, hovered
from shared_ui.spacing import BUTTON_RADIUS_HUD


def slab(pen: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], ground, edge) -> None:
    x, y, width, height = rect
    pen.rounded_rectangle((x, y, x + width - 1, y + height - 1), radius=BUTTON_RADIUS_HUD,
                          fill=(*ground, 255), outline=(*edge, 255))


def button(pen: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], fill, *,
           lit: bool) -> None:
    edge = TEXT_MUTED if fill == BG_BUTTON else fill
    slab(pen, rect, hovered(fill) if lit else fill, edge)
