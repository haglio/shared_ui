"""The family's app icons: one PINK block letter each, on one grid.

Every app's icon is a single letter drawn on a 5x5 grid inset :data:`INSET`
pixels inside a :data:`CANVAS`-pixel square, every stroke exactly one grid
cell -- a fifth of the glyph box -- thick, with near-square corners.  The
grid is what makes eight icons read as one set on a taskbar; the spec was
written down in one app's test, which named the others' letters and checked
only its own.  Here it is checked for any of them: an app's suite calls
:func:`assert_follows_the_family_spec` on its own ``.ico``.

Pillow only, so a test can check an icon without a Qt application.  How an
icon was drawn is its own business -- what it must come out as is this.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from shared_ui.palette import PINK

CANVAS = 256  # the master frame
INSET = 31  # the glyph box's offset inside the canvas
BOX = CANVAS - 2 * INSET  # 194: the glyph box, five cells across
UNIT = BOX / 5  # one cell, and one stroke
CORNER_SOFTENING_MAX = 8  # rows a corner may round over; the family's round over three
SOLID = 128  # the alpha above which a pixel is ink rather than an edge

# The letters the family draws, as the cells they fill.  Fun Time's is its two
# initials sharing a stem, and the VR player's is a V.
LETTERS: dict[str, tuple[str, ...]] = {
    "B": ("#####", "#...#", "#####", "#...#", "#####"),
    "C": ("#####", "#....", "#....", "#....", "#####"),
    "E": ("#####", "#....", "#####", "#....", "#####"),
    "FT": ("#####", "#.#..", "#####", "#.#..", "#.#.."),
    "O": ("#####", "#...#", "#...#", "#...#", "#####"),
    "P": ("#####", "#...#", "#####", "#....", "#...."),
    "S": ("#####", "#....", "#####", "....#", "#####"),
    "V": ("#...#", "#...#", "##.##", ".###.", "..#.."),
}

# Where inside a cell to look: a 3x3 lattice kept clear of the cell's edges, so
# a stroke a hair wide or narrow of a cell passes and one a third off does not.
_CELL_MARGIN = 8
_LATTICE = (0.0, 0.5, 1.0)


def _master(path: Path) -> Image.Image:
    image = Image.open(path)
    if image.size != (CANVAS, CANVAS):
        image.size = (CANVAS, CANVAS)  # the ICO plugin picks a frame by size
    return image.convert("RGBA")


def _solid(pixels, x: int, y: int) -> bool:
    return pixels[x, y][3] > SOLID


def assert_follows_the_family_spec(path: Path | str, letter: str) -> None:
    """Fail unless the icon at *path* is *letter*, drawn to the family's spec."""
    cells = LETTERS[letter]
    image = _master(Path(path))
    assert image.size == (CANVAS, CANVAS), f"{path}: no {CANVAS}px master frame"
    pixels = image.load()

    solid = image.getchannel("A").point(lambda alpha: 255 if alpha > SOLID else 0)
    left, upper, right, lower = solid.getbbox()
    assert abs(left - INSET) <= 2 and abs(upper - INSET) <= 2, (
        f"{path}: the glyph box starts at ({left}, {upper}), not ({INSET}, {INSET})")
    assert abs((right - left) - BOX) <= 4 and abs((lower - upper) - BOX) <= 4, (
        f"{path}: the glyph box is {right - left}x{lower - upper}, not {BOX}x{BOX}")

    for row, line in enumerate(cells):
        for column, cell in enumerate(line):
            expected = cell == "#"
            x0 = INSET + column * UNIT + _CELL_MARGIN
            y0 = INSET + row * UNIT + _CELL_MARGIN
            span = UNIT - 2 * _CELL_MARGIN
            for fx in _LATTICE:
                for fy in _LATTICE:
                    x, y = int(x0 + fx * span), int(y0 + fy * span)
                    assert _solid(pixels, x, y) == expected, (
                        f"{path}: cell ({row}, {column}) is "
                        f"{'clear' if expected else 'inked'} at ({x}, {y}); "
                        f"the letter {letter!r} has it {'inked' if expected else 'clear'}")

    softening = next(k for k in range(CANVAS) if _solid(pixels, left, upper + k))
    assert softening <= CORNER_SOFTENING_MAX, (
        f"{path}: the top-left corner rounds over {softening} rows")

    a_stroke = next((x, y) for row, line in enumerate(cells) for column, cell in enumerate(line)
                    if cell == "#"
                    for x, y in [(int(INSET + (column + 0.5) * UNIT), int(INSET + (row + 0.5) * UNIT))])
    assert pixels[a_stroke][:3] == PINK, f"{path}: the ink is {pixels[a_stroke][:3]}, not PINK"
    assert not _solid(pixels, 0, 0) and not _solid(pixels, CANVAS - 1, CANVAS - 1), (
        f"{path}: the background is not transparent")
