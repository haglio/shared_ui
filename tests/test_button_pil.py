"""shared_ui.button_pil: the face a control is drawn on with Pillow, at the HUD's size."""

from __future__ import annotations

from PIL import Image, ImageDraw

from shared_ui.button_pil import button, slab
from shared_ui.palette import BG_BUTTON, BG_TERTIARY, BLUE, BORDER_SUBTLE, TEXT_MUTED, hovered

RECT = (4, 6, 40, 18)
_X, _Y, _W, _H = RECT


def _drawn(paint) -> Image.Image:
    image = Image.new("RGBA", (_X + _W + 4, _Y + _H + 4), (0, 0, 0, 0))
    paint(ImageDraw.Draw(image))
    return image


def _edge(image: Image.Image) -> tuple[int, ...]:
    return image.getpixel((_X, _Y + _H // 2))[:3]


def _face(image: Image.Image) -> tuple[int, ...]:
    return image.getpixel((_X + _W // 2, _Y + _H // 2))[:3]


class TestASlab:
    def test_is_its_ground_inside_its_edge(self):
        drawn = _drawn(lambda pen: slab(pen, RECT, BG_TERTIARY, BORDER_SUBTLE))

        assert _face(drawn) == BG_TERTIARY
        assert _edge(drawn) == BORDER_SUBTLE
        assert drawn.getpixel((_X + _W - 1, _Y + _H // 2))[:3] == BORDER_SUBTLE

    def test_rounds_its_corners_rather_than_filling_them(self):
        drawn = _drawn(lambda pen: slab(pen, RECT, BG_TERTIARY, BORDER_SUBTLE))

        assert drawn.getpixel((_X, _Y))[3] == 0
        assert drawn.getpixel((_X + _W - 1, _Y + _H - 1))[3] == 0


class TestAButton:
    def test_at_rest_on_the_familys_gray_wears_the_muted_edge(self):
        drawn = _drawn(lambda pen: button(pen, RECT, BG_BUTTON, lit=False))

        assert _face(drawn) == BG_BUTTON
        assert _edge(drawn) == TEXT_MUTED

    def test_a_colored_one_is_edged_in_its_own_color(self):
        drawn = _drawn(lambda pen: button(pen, RECT, BLUE, lit=False))

        assert _face(drawn) == _edge(drawn) == BLUE

    def test_lit_lightens_its_face_and_keeps_its_edge(self):
        drawn = _drawn(lambda pen: button(pen, RECT, BG_BUTTON, lit=True))

        assert _face(drawn) == hovered(BG_BUTTON)
        assert _edge(drawn) == TEXT_MUTED
