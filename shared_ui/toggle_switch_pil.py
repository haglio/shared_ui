"""The family's on/off switch drawn with Pillow, at the HUD buttons' size.

The switch :mod:`shared_ui.toggle_switch` paints on the desktop, its shape read
from :mod:`shared_ui.toggle_geometry`, drawn big and resampled down for the
smooth edge Pillow does not draw, as :mod:`shared_ui.icons_pil` draws the icons.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from shared_ui.icons_pil import SUPERSAMPLE
from shared_ui.palette import CHANNEL_MAX, TOGGLE_HANDLE, TOGGLE_OFF, TOGGLE_ON
from shared_ui.palette import hovered as lighter
from shared_ui.toggle_geometry import HANDLE_INSET_HUD, TRACK_HUD, handle

__all__ = ["paste_toggle_switch"]


def paste_toggle_switch(image: Image.Image, at: tuple[int, int], *, on: bool,
                        hovered: bool = False) -> None:
    width, height = (side * SUPERSAMPLE for side in TRACK_HUD)
    big = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pen = ImageDraw.Draw(big)
    ground = TOGGLE_ON if on else TOGGLE_OFF
    pen.rounded_rectangle((0, 0, width - 1, height - 1), radius=height // 2,
                          fill=(*(lighter(ground) if hovered else ground), CHANNEL_MAX))
    x, y, diameter = handle((0, 0, width, height), on=on, inset=HANDLE_INSET_HUD * SUPERSAMPLE)
    pen.ellipse((x, y, x + diameter - 1, y + diameter - 1), fill=(*TOGGLE_HANDLE, CHANNEL_MAX))
    image.alpha_composite(big.resize(TRACK_HUD, Image.Resampling.BOX), dest=at)
