from __future__ import annotations

from pathlib import Path

from PIL import Image

from shared_ui.palette import CHANNEL_MAX, MAGENTA

CANVAS = 256
INSET = 31
GRID = CANVAS - 2 * INSET
UNIT = GRID / 5
CORNER_SOFTENING_MAX = 8
SOLID = 128
_GRID_START_SLACK = 2
_GRID_SIZE_SLACK = 4

LETTERS: dict[str, tuple[str, ...]] = {
    "B": ("####.", "#...#", "#####", "#...#", "####."),
    "C": ("#####", "#....", "#....", "#....", "#####"),
    "E": ("#####", "#....", "#####", "#....", "#####"),
    "F": ("#####", "#....", "#####", "#....", "#...."),
    "FT": ("#####", "#.#..", "#####", "#.#..", "#.#.."),
    "G": ("#####", "#....", "#.###", "#...#", "#####"),
    "L": ("#....", "#....", "#....", "#....", "#####"),
    "O": ("#####", "#...#", "#...#", "#...#", "#####"),
    "P": ("#####", "#...#", "#####", "#....", "#...."),
    "S": ("#####", "#....", "#####", "....#", "#####"),
    "V": ("#...#", "#...#", "##.##", ".###.", "..#.."),
    "VR": ("#####", "#...#", "#####", "####.", "#.##."),
}

_CELL_MARGIN = 8
_LATTICE = (0.0, 0.5, 1.0)


def draw_letter(draw, rect: tuple[int, int, int, int], letter: str) -> None:
    x, y, w, h = rect
    cell = max(1, min(w, h) // 7)
    left, top = x + (w - 5 * cell) / 2, y + (h - 5 * cell) / 2
    for row, line in enumerate(LETTERS[letter]):
        for column, painted in enumerate(line):
            if painted == "#":
                cx, cy = left + column * cell, top + row * cell
                draw.rectangle([cx, cy, cx + cell - 1, cy + cell - 1], fill=(*MAGENTA, CHANNEL_MAX))


def _master(path: Path) -> Image.Image:
    image = Image.open(path)
    if image.size != (CANVAS, CANVAS):
        image.size = (CANVAS, CANVAS)
    return image.convert("RGBA")


def _solid(pixels, x: int, y: int) -> bool:
    return pixels[x, y][3] > SOLID


def assert_follows_the_family_spec(path: Path | str, letter: str) -> None:
    cells = LETTERS[letter]
    image = _master(Path(path))
    assert image.size == (CANVAS, CANVAS), f"{path}: no {CANVAS}px master frame"
    pixels = image.load()

    solid = image.getchannel("A").point(lambda alpha: CHANNEL_MAX if alpha > SOLID else 0)
    left, upper, right, lower = solid.getbbox()
    starts = f"{path}: the letter grid starts at ({left}, {upper}), not ({INSET}, {INSET})"
    assert abs(left - INSET) <= _GRID_START_SLACK, starts
    assert abs(upper - INSET) <= _GRID_START_SLACK, starts
    measures = f"{path}: the letter grid is {right - left}x{lower - upper}, not {GRID}x{GRID}"
    assert abs((right - left) - GRID) <= _GRID_SIZE_SLACK, measures
    assert abs((lower - upper) - GRID) <= _GRID_SIZE_SLACK, measures

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

    a_bar = next((x, y) for row, line in enumerate(cells) for column, cell in enumerate(line)
                 if cell == "#"
                 for x, y in [(int(INSET + (column + 0.5) * UNIT), int(INSET + (row + 0.5) * UNIT))])
    assert pixels[a_bar][:3] == MAGENTA, f"{path}: the ink is {pixels[a_bar][:3]}, not MAGENTA"
    assert not _solid(pixels, 0, 0), f"{path}: the background is not transparent"
    assert not _solid(pixels, CANVAS - 1, CANVAS - 1), f"{path}: the background is not transparent"
