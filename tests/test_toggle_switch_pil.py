"""shared_ui.toggle_switch_pil: the family's on/off switch drawn with Pillow, at the HUD's size."""

from __future__ import annotations

from PIL import Image

from shared_ui.palette import BG_PRIMARY, TOGGLE_HANDLE, TOGGLE_OFF, TOGGLE_ON, hovered
from shared_ui.toggle_geometry import HANDLE_INSET_HUD, TRACK_HUD, handle
from shared_ui.toggle_switch_pil import paste_toggle_switch

_AT = (3, 2)
_W, _H = TRACK_HUD


def _drawn(*, on: bool, under_the_pointer: bool = False) -> Image.Image:
    image = Image.new("RGBA", (_AT[0] + _W + 3, _AT[1] + _H + 2), (*BG_PRIMARY, 255))
    paste_toggle_switch(image, _AT, on=on, hovered=under_the_pointer)
    return image


def _where_the_handle_sits(*, on: bool) -> tuple[int, int]:
    x, y, diameter = handle((*_AT, _W, _H), on=on, inset=HANDLE_INSET_HUD)
    return int(x + diameter / 2), int(y + diameter / 2)


def _color(image: Image.Image, at: tuple[int, int]) -> tuple[int, ...]:
    return image.getpixel(at)[:3]


def test_off_is_the_muted_track_with_the_handle_at_the_left():
    off = _drawn(on=False)

    assert _color(off, _where_the_handle_sits(on=False)) == TOGGLE_HANDLE
    assert _color(off, _where_the_handle_sits(on=True)) == TOGGLE_OFF


def test_on_is_the_blue_track_with_the_handle_at_the_right():
    on = _drawn(on=True)

    assert _color(on, _where_the_handle_sits(on=True)) == TOGGLE_HANDLE
    assert _color(on, _where_the_handle_sits(on=False)) == TOGGLE_ON


def test_under_the_pointer_its_track_is_one_step_lighter():
    lit = _drawn(on=True, under_the_pointer=True)

    assert _color(lit, _where_the_handle_sits(on=False)) == hovered(TOGGLE_ON)
    assert _color(lit, _where_the_handle_sits(on=True)) == TOGGLE_HANDLE


def test_it_paints_nothing_outside_its_rounded_track():
    drawn = _drawn(on=True)
    middle = _AT[1] + _H // 2

    assert _color(drawn, (_AT[0] - 1, middle)) == BG_PRIMARY
    assert _color(drawn, (_AT[0] + _W, middle)) == BG_PRIMARY
    assert _color(drawn, _AT) == BG_PRIMARY
