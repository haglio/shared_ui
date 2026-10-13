"""shared_ui.dropdown_pil: a dropdown's field and the list it opens, drawn with Pillow."""

from __future__ import annotations

from PIL import Image

from shared_ui.dropdown_pil import ARROW_PX, arrow_down, paint_field, paint_list
from shared_ui.lettering import load_font
from shared_ui.palette import BG_BUTTON, BG_PRIMARY, BG_TERTIARY, BLUE, TEXT_PRIMARY, hovered
from shared_ui.spacing import BUTTON_GAP

FONT = load_font(11)
FIELD = (10, 80, 92, 18)
ROWS = [((10, 26, 92, 18), "Alpha", False), ((10, 44, 92, 18), "Beta", True),
        ((10, 62, 92, 18), "Gamma", False)]


def _image() -> Image.Image:
    return Image.new("RGBA", (120, 110), (*BG_PRIMARY, 255))


def _field(text: str = "Alpha", *, lit: bool = False) -> Image.Image:
    image = _image()
    paint_field(image, FIELD, text, FONT, lit=lit)
    return image


def _list(rows=ROWS) -> Image.Image:
    image = _image()
    paint_list(image, rows, FONT)
    return image


def _color(image: Image.Image, x: int, y: int) -> tuple[int, ...]:
    return image.getpixel((x, y))[:3]


def _near(color: tuple[int, ...], ink) -> bool:
    return sum(abs(channel - wanted) for channel, wanted in zip(color, ink)) < 90


class TestTheField:
    def test_wears_the_arrow_at_its_right_end(self):
        x, y, width, height = FIELD
        drawn = _field()
        arrow = [_color(drawn, px, py) for px in range(x + width - ARROW_PX - BUTTON_GAP, x + width - 3)
                 for py in range(y + 2, y + height - 2)]

        assert any(color != BG_BUTTON for color in arrow)

    def test_its_words_start_at_its_left_and_end_short_of_the_arrow(self):
        x, y, width, height = FIELD
        arrow_starts = width - ARROW_PX - BUTTON_GAP
        drawn = _field("Gamma")
        inked = [column for column in range(arrow_starts)
                 if any(_near(_color(drawn, x + column, py), TEXT_PRIMARY)
                        for py in range(y, y + height))]

        assert min(inked) < width // 4
        assert max(inked) < arrow_starts - 1

    def test_says_what_it_is_handed(self):
        assert _field("Alpha").tobytes() != _field("Gamma").tobytes()

    def test_lit_it_lightens_as_a_button_does(self):
        x, y, width, height = FIELD

        assert _color(_field(lit=True), x + width // 2, y + height - 3) == hovered(BG_BUTTON)


class TestTheArrow:
    def test_points_down(self):
        arrow = arrow_down(24)
        rows = [(row, sum(arrow.getpixel((column, row))[3] > 40 for column in range(arrow.width)))
                for row in range(arrow.height)]
        drawn = [(row, count) for row, count in rows if count]
        apex = min(drawn, key=lambda row: row[1])[0]
        open_end = max(drawn, key=lambda row: row[1])[0]

        assert apex > open_end


class TestTheOpenList:
    def _band(self, drawn: Image.Image, rect) -> list[tuple[int, ...]]:
        x, y, width, height = rect
        return [_color(drawn, px, y + height // 2) for px in range(x + 2, x + width - 2)]

    def test_marks_the_chosen_row_in_blue(self):
        assert BLUE in self._band(_list(), ROWS[1][0])

    def test_leaves_the_rows_not_chosen_on_its_ground(self):
        drawn = _list()

        for rect, _name, _chosen in (ROWS[0], ROWS[2]):
            band = self._band(drawn, rect)
            assert BLUE not in band
            assert BG_TERTIARY in band

    def test_writes_each_row_its_own_name(self):
        renamed = [(rect, "Delta", chosen) for rect, _name, chosen in ROWS]

        assert _list().tobytes() != _list(renamed).tobytes()

    def test_is_one_frame_from_its_first_row_to_its_last(self):
        drawn = _list()
        x, top = ROWS[0][0][0], ROWS[0][0][1]
        ends_at = ROWS[-1][0][1] + ROWS[-1][0][3]

        assert _color(drawn, x + 20, top - 1) == BG_PRIMARY
        assert _color(drawn, x + 20, ends_at) == BG_PRIMARY
        assert _color(drawn, x, (top + ends_at) // 2) != BG_PRIMARY
