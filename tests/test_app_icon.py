"""The family's icon spec, against icons drawn to it and icons drawn off it.

Every fixture icon here is drawn by the test; no app's own file is read."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from shared_ui import app_icon
from shared_ui.app_icon import BOX, CANVAS, INSET, LETTERS, UNIT, assert_follows_the_family_spec
from shared_ui.palette import PINK, WHITE


def _draw(cells, *, inset=INSET, box=BOX, ink=PINK) -> Image.Image:
    """A letter on the grid, as plain rectangles -- corners square, edges hard."""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    unit = box / 5
    for row, line in enumerate(cells):
        for column, cell in enumerate(line):
            if cell != "#":
                continue
            x0, y0 = inset + column * unit, inset + row * unit
            draw.rectangle((x0, y0, x0 + unit - 1, y0 + unit - 1), fill=(*ink, 255))
    return image


def _ico(tmp_path: Path, image: Image.Image) -> Path:
    path = tmp_path / "icon.ico"
    image.save(path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (CANVAS, CANVAS)])
    return path


@pytest.mark.parametrize("letter", sorted(LETTERS))
def test_every_letter_drawn_to_the_grid_passes(tmp_path, letter):
    assert_follows_the_family_spec(_ico(tmp_path, _draw(LETTERS[letter])), letter)


def test_the_wrong_letter_is_named(tmp_path):
    path = _ico(tmp_path, _draw(LETTERS["E"]))

    with pytest.raises(AssertionError, match=r"cell \(1, 4\).*'B' has it inked"):
        assert_follows_the_family_spec(path, "B")


def test_a_letter_off_the_familys_grid_fails(tmp_path):
    shrunk = _ico(tmp_path, _draw(LETTERS["O"], inset=INSET + 20, box=BOX - 40))

    with pytest.raises(AssertionError, match="glyph box starts"):
        assert_follows_the_family_spec(shrunk, "O")


def test_a_stroke_wider_than_a_cell_fails(tmp_path):
    image = _draw(LETTERS["O"])
    # Thicken the ring's top inward by half a cell: the box is still the box.
    ImageDraw.Draw(image).rectangle(
        (INSET + UNIT, INSET + UNIT, INSET + 4 * UNIT, INSET + 1.5 * UNIT), fill=(*PINK, 255))

    with pytest.raises(AssertionError, match=r"cell \(1, 1\) is inked"):
        assert_follows_the_family_spec(_ico(tmp_path, image), "O")


def test_ink_of_another_color_fails(tmp_path):
    white = _ico(tmp_path, _draw(LETTERS["S"], ink=WHITE))

    with pytest.raises(AssertionError, match="not PINK"):
        assert_follows_the_family_spec(white, "S")


def test_a_heavily_rounded_corner_fails(tmp_path):
    image = _draw(LETTERS["O"])
    draw = ImageDraw.Draw(image)
    # Carve the top-left corner away over more rows than the family softens.
    draw.polygon([(INSET, INSET), (INSET + 12, INSET), (INSET, INSET + 12)], fill=(0, 0, 0, 0))

    with pytest.raises(AssertionError, match="rounds over"):
        assert_follows_the_family_spec(_ico(tmp_path, image), "O")


def test_the_grid_is_five_cells_of_one_stroke():
    assert UNIT * 5 == BOX
    assert INSET * 2 + BOX == CANVAS
    for letter, cells in LETTERS.items():
        assert len(cells) == 5 and all(len(line) == 5 for line in cells), letter
        assert set("".join(cells)) <= {"#", "."}, letter
    assert app_icon.CORNER_SOFTENING_MAX < UNIT / 4
