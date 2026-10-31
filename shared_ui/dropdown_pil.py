from __future__ import annotations

from collections.abc import Sequence

from PIL import Image, ImageDraw

from shared_ui.button_pil import button, slab
from shared_ui.icons_pil import pil_icon
from shared_ui.palette import (
    BG_BUTTON,
    BG_TERTIARY,
    BLUE,
    BORDER_SUBTLE,
    CHANNEL_MAX,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from shared_ui.spacing import BUTTON_GAP, BUTTON_PAD_H_TIGHT

ARROW_PX = 10

Rect = tuple[int, int, int, int]


def arrow_down(size: int) -> Image.Image:
    return pil_icon("chevron_right", size, TEXT_MUTED).rotate(-90, expand=False)


def _written(pen: ImageDraw.ImageDraw, rect: Rect, text: str, font) -> None:
    x, y, _width, height = rect
    pen.text((x + BUTTON_PAD_H_TIGHT, y + height / 2), text, font=font, anchor="lm",
             fill=(*TEXT_PRIMARY, CHANNEL_MAX))


def paint_field(image: Image.Image, rect: Rect, text: str, font, *, lit: bool = False) -> None:
    x, y, width, height = rect
    pen = ImageDraw.Draw(image)
    button(pen, rect, BG_BUTTON, lit=lit)
    _written(pen, rect, text, font)
    image.alpha_composite(arrow_down(ARROW_PX), (x + width - ARROW_PX - BUTTON_GAP,
                                                 y + (height - ARROW_PX) // 2))


def paint_list(image: Image.Image, rows: Sequence[tuple[Rect, str, bool]], font) -> None:
    pen = ImageDraw.Draw(image)
    left, top, width, _height = rows[0][0]
    _x, last_top, _width, last_height = rows[-1][0]
    slab(pen, (left, top, width, last_top + last_height - top), BG_TERTIARY, BORDER_SUBTLE)
    for rect, text, chosen in rows:
        x, y, row_width, row_height = rect
        if chosen:
            pen.rectangle((x + 1, y, x + row_width - 2, y + row_height - 1), fill=(*BLUE, CHANNEL_MAX))
        _written(pen, rect, text, font)
