from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from shared_ui import app_icon
from shared_ui.app_icon import (
    CANVAS,
    CORNER_SOFTENING_MAX,
    GRID,
    INSET,
    LETTERS,
    UNIT,
    assert_follows_the_family_spec,
)
from shared_ui.palette import MAGENTA, WHITE

_MORE_ROWS_THAN_THE_FAMILY_SOFTENS = CORNER_SOFTENING_MAX + 4


def _drawn_by_the_test(cells, *, inset=INSET, grid=GRID, ink=MAGENTA, grown=0) -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    unit = grid / 5
    for row, line in enumerate(cells):
        for column, cell in enumerate(line):
            if cell != "#":
                continue
            x0, y0 = inset + column * unit, inset + row * unit
            draw.rectangle((x0 - grown, y0 - grown, x0 + unit - 1 + grown, y0 + unit - 1 + grown),
                           fill=(*ink, 255))
    return image


def _saved_by_the_test(tmp_path: Path, image: Image.Image) -> Path:
    path = tmp_path / "icon.ico"
    image.save(path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (CANVAS, CANVAS)])
    return path


def test_the_b_has_no_right_hand_corners_so_it_reads_as_a_b_not_an_8():
    first_row, *_, last_row = LETTERS["B"]

    assert (first_row[-1], last_row[-1]) == (".", ".")


def test_the_x_inks_its_two_diagonals_and_nothing_else():
    inked = {(row, column) for row, line in enumerate(LETTERS["X"]) for column, cell in enumerate(line) if cell == "#"}

    assert inked == {(i, i) for i in range(5)} | {(i, 4 - i) for i in range(5)}


@pytest.mark.parametrize("letter", sorted(LETTERS))
def test_every_letter_drawn_to_the_grid_passes(tmp_path, letter):
    assert_follows_the_family_spec(_saved_by_the_test(tmp_path, _drawn_by_the_test(LETTERS[letter])), letter)


def test_the_wrong_letter_is_named(tmp_path):
    path = _saved_by_the_test(tmp_path, _drawn_by_the_test(LETTERS["E"]))

    with pytest.raises(AssertionError, match=r"cell \(0, 4\).*'B' has it clear"):
        assert_follows_the_family_spec(path, "B")


def test_a_letter_off_the_familys_grid_fails(tmp_path):
    shrunk = _saved_by_the_test(tmp_path, _drawn_by_the_test(LETTERS["O"], inset=INSET + 20, grid=GRID - 40))

    with pytest.raises(AssertionError, match="letter grid starts"):
        assert_follows_the_family_spec(shrunk, "O")


def test_a_bar_wider_than_a_cell_fails(tmp_path):
    image = _drawn_by_the_test(LETTERS["O"])
    ImageDraw.Draw(image).rectangle(
        (INSET + UNIT, INSET + UNIT, INSET + 4 * UNIT, INSET + 1.5 * UNIT), fill=(*MAGENTA, 255))

    with pytest.raises(AssertionError, match=r"cell \(1, 1\) is inked"):
        assert_follows_the_family_spec(_saved_by_the_test(tmp_path, image), "O")


def test_ink_of_another_color_fails(tmp_path):
    white = _saved_by_the_test(tmp_path, _drawn_by_the_test(LETTERS["S"], ink=WHITE))

    with pytest.raises(AssertionError, match="not MAGENTA"):
        assert_follows_the_family_spec(white, "S")


def test_a_heavily_rounded_corner_fails(tmp_path):
    image = _drawn_by_the_test(LETTERS["O"])
    draw = ImageDraw.Draw(image)
    carved = _MORE_ROWS_THAN_THE_FAMILY_SOFTENS
    draw.polygon([(INSET, INSET), (INSET + carved, INSET), (INSET, INSET + carved)], fill=(0, 0, 0, 0))

    with pytest.raises(AssertionError, match="rounds over"):
        assert_follows_the_family_spec(_saved_by_the_test(tmp_path, image), "O")


def test_the_grid_is_five_cells_of_one_bar():
    assert UNIT * 5 == GRID
    assert INSET * 2 + GRID == CANVAS
    for letter, cells in LETTERS.items():
        assert len(cells) == 5, letter
        assert all(len(line) == 5 for line in cells), letter
        assert set("".join(cells)) <= {"#", "."}, letter
    assert app_icon.CORNER_SOFTENING_MAX < UNIT / 4


def test_a_hud_draws_an_app_s_letter_as_its_cells_in_magenta_leaving_the_rest_alone():
    image = Image.new("RGBA", (35, 35), (10, 20, 30, 255))

    app_icon.draw_letter(ImageDraw.Draw(image), (0, 0, 35, 35), "L")

    cell = 35 // 7
    magenta = [point for point in ((x, y) for y in range(35) for x in range(35))
               if image.getpixel(point) == (*MAGENTA, 255)]
    assert len(magenta) == sum(row.count("#") for row in LETTERS["L"]) * cell * cell
    assert image.getpixel((0, 0)) == (10, 20, 30, 255)
    left = (35 - 5 * cell) // 2
    a_blank_cell_of_the_l = (left + 2 * cell + cell // 2, left + cell // 2)
    assert image.getpixel(a_blank_cell_of_the_l) == (10, 20, 30, 255)


@pytest.mark.parametrize("letter", ["B", "F"])
def test_a_hud_with_no_icon_file_to_load_draws_the_letter_from_its_own_grid(letter):
    image = Image.new("RGBA", (18, 18), (0, 0, 0, 0))

    app_icon.draw_letter(ImageDraw.Draw(image), (0, 0, 18, 18), letter)

    painted = [[image.getpixel((x, y))[3] > 0 for x in range(18)] for y in range(18)]
    columns = [x for x in range(18) if any(row[x] for row in painted)]
    rows = [y for y in range(18) if any(painted[y])]
    cell = (columns[-1] - columns[0] + 1) / 5
    assert [
        "".join("#" if painted[int(rows[0] + (r + 0.5) * cell)][int(columns[0] + (c + 0.5) * cell)]
                else "." for c in range(5))
        for r in range(5)
    ] == list(LETTERS[letter])


def test_a_bar_a_third_off_its_cell_fails_though_the_cells_middle_is_inked(tmp_path):
    image = _drawn_by_the_test(LETTERS["E"])
    ImageDraw.Draw(image).rectangle(
        (INSET, INSET + 2 * UNIT, INSET + 5 * UNIT, INSET + 2 * UNIT + UNIT / 3),
        fill=(0, 0, 0, 0))

    with pytest.raises(AssertionError, match=r"cell \(2, \d\)"):
        assert_follows_the_family_spec(_saved_by_the_test(tmp_path, image), "E")


@pytest.mark.parametrize("grown", [2, -2], ids=["a hair wide", "a hair narrow"])
def test_a_bar_a_hair_wide_or_narrow_of_its_cell_still_passes(tmp_path, grown):
    drawn = _drawn_by_the_test(LETTERS["E"], grown=grown)

    assert_follows_the_family_spec(_saved_by_the_test(tmp_path, drawn), "E")
