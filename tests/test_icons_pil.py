"""The Pillow renderer: that it draws, and that it draws what Qt draws.

The players paint their HUDs into the video frame with Pillow, and there is no Qt
in a player process, so a HUD mark could never be the same object as a toolbar
mark.  It can be the same *geometry*, which is what this checks: both renderers
walk :mod:`shared_ui.icon_geometry`, and the two renderings have to land on top
of each other.  Not pixel for pixel -- Pillow has no antialiasing of its own and
no round caps, and this module works around both -- but close enough that nobody
looking at the two screens sees two different marks.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

from shared_ui import icon_geometry, icons, icons_pil

_REPO_ROOT = Path(__file__).resolve().parent.parent
from shared_ui.colors import GREEN, RED, TEXT_PRIMARY

_SIZE = 48
_INK = (240, 240, 240)  # TEXT_PRIMARY, as the HUDs' palette spells it


def _pil_ink(image: Image.Image) -> tuple[int, int, int, int, int]:
    """``(left, top, right, bottom, count)`` of what was drawn."""
    alpha = image.split()[3].load()
    xs, ys, count = [], [], 0
    for y in range(image.height):
        for x in range(image.width):
            if alpha[x, y] > 32:
                xs.append(x)
                ys.append(y)
                count += 1
    assert xs, "nothing was drawn"
    return min(xs), min(ys), max(xs), max(ys), count


def _qt_ink(name: str, size: int) -> tuple[int, int, int, int, int]:
    image = icons.glyph_pixmap(name, size, TEXT_PRIMARY).toImage()
    xs, ys, count = [], [], 0
    for y in range(size):
        for x in range(size):
            if image.pixelColor(x, y).alpha() > 32:
                xs.append(x)
                ys.append(y)
                count += 1
    assert xs, "nothing was drawn"
    return min(xs), min(ys), max(xs), max(ys), count


def test_every_glyph_draws_through_pillow_too():
    # A mark the Qt side can draw and the Pillow side cannot is a mark that goes
    # missing on a HUD -- an empty button, with nothing raised.
    for name in icons_pil.glyph_names():
        image = icons_pil.glyph_image(name, _SIZE, _INK)
        assert image.size == (_SIZE, _SIZE), name
        assert _pil_ink(image)[4] > 0, name


def test_the_two_renderers_put_the_mark_in_the_same_place():
    # The whole point. A HUD's trash can and a toolbar's are one drawing now, so
    # their ink has to occupy the same box -- within a pixel, which is what is
    # left after Pillow's inside-the-box outlines are corrected for.
    for name in icons_pil.glyph_names():
        pillow = _pil_ink(icons_pil.glyph_image(name, _SIZE, _INK))
        qt = _qt_ink(name, _SIZE)
        for edge in range(4):
            assert abs(pillow[edge] - qt[edge]) <= 1, f"{name} edge {edge}"


def test_the_two_renderers_lay_down_a_like_amount_of_ink():
    # Same box could still mean a hairline against a slab, so the weight has to
    # agree too. Pillow's arcs have no round caps and its resampling is not Qt's,
    # so this is a band rather than an equality.
    for name in icons_pil.glyph_names():
        pillow = _pil_ink(icons_pil.glyph_image(name, _SIZE, _INK))[4]
        qt = _qt_ink(name, _SIZE)[4]
        assert abs(pillow - qt) / qt < 0.15, name


def test_a_glyph_is_drawn_in_the_color_it_is_asked_for():
    # The HUDs tint marks the way the chrome does -- a muted control, a green
    # favorite -- so the ink is whatever tuple was handed in.
    for color in ((*RED.getRgb()[:3],), (*GREEN.getRgb()[:3],)):
        image = icons_pil.glyph_image("star", _SIZE, color)
        assert image.getpixel((24, 25))[:3] == color


def test_a_pasted_mark_sits_on_what_the_hud_already_drew():
    # A HUD button paints its fill and then asks for the mark. The mark has to
    # composite onto that fill, not stamp a transparent square over it.
    panel = Image.new("RGBA", (40, 24), (0, 80, 0, 255))
    icons_pil.paste_glyph(panel, "trash", (12, 2, 20, 20), _INK)
    pixels = [panel.getpixel((x, y)) for y in range(24) for x in range(40)]

    assert panel.getpixel((2, 12)) == (0, 80, 0, 255)   # the fill, clear of the mark
    assert all(pixel[3] == 255 for pixel in pixels)     # nothing was punched out
    # The mark is laid over the fill, so its ink blends toward white where the
    # fill has no red at all.
    assert any(pixel[0] > 200 for pixel in pixels), "the mark did not land"


def test_a_pasted_mark_is_centered_in_the_box_it_was_given():
    # HUD buttons are square-ish but not square, and a mark hugging one edge
    # reads as misaligned with the buttons beside it.
    #
    # The panel is TRANSPARENT so that the ink scan sees the mark and only the
    # mark: drawn on an opaque one it measured the panel's own every pixel, so
    # the centre came out the panel's centre whatever paste_glyph did with it.
    panel = Image.new("RGBA", (48, 24), (0, 0, 0, 0))
    icons_pil.paste_glyph(panel, "plus", (0, 0, 48, 24), _INK)
    left, top, right, bottom, _count = _pil_ink(panel)
    assert abs((left + right) / 2 - 24) <= 1
    assert abs((top + bottom) / 2 - 12) <= 1


def test_a_pasted_mark_is_centered_in_a_box_that_is_not_at_the_origin():
    # The box a HUD hands over is wherever its button is, so the centring is of
    # the box rather than of the panel -- a mark centred on the panel instead
    # would land right for the one button that happens to sit in the middle.
    panel = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
    icons_pil.paste_glyph(panel, "plus", (36, 8, 24, 28), _INK)
    left, top, right, bottom, _count = _pil_ink(panel)
    assert abs((left + right) / 2 - 48) <= 1
    assert abs((top + bottom) / 2 - 22) <= 1


def test_the_geometry_and_both_renderers_offer_the_same_marks():
    # One registry. A glyph added for the toolbar and not reachable from a HUD is
    # how the two sides drifted apart in the first place.
    assert icons_pil.glyph_names() == icons.glyph_names()
    assert icons_pil.glyph_names() == icon_geometry.glyph_names()


def test_drawing_a_hud_mark_never_drags_qt_into_a_player():
    # The players are mpv and Pillow and nothing else; PyQt6 in that process
    # would be a GUI toolkit loaded into a video pipeline for the sake of a
    # dozen-pixel icon. The geometry module is what makes that avoidable, so
    # neither it nor the Pillow renderer may reach for Qt.
    #
    # The probe says which tree it read before it says what it loaded: `python -c`
    # puts the process cwd first on sys.path and nothing else, so run from
    # anywhere but this checkout it imported the editable-installed copy in the
    # primary one -- and every branch is worked on in a worktree, so a branch that
    # dragged Qt in here passed this guard.
    probe = (
        "import sys; import shared_ui.icons_pil, shared_ui.icon_geometry; "
        "print(shared_ui.__file__); "
        "print(any(m == 'PyQt6' or m.startswith('PyQt6.') for m in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], cwd=_REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)},
        capture_output=True, text=True, check=True,
    )
    read_from, qt_was_loaded = result.stdout.splitlines()

    assert Path(read_from).resolve().is_relative_to(_REPO_ROOT), (
        f"the probe read {read_from}, not the tree under test at {_REPO_ROOT}"
    )
    assert qt_was_loaded == "False", result.stdout


def test_a_mark_is_never_brighter_than_the_ink_it_was_drawn_in():
    # Lanczos overshoots at a hard edge. Drawn in color and then resampled, a
    # mark came out with pixels brighter than its own ink around every stroke --
    # a faint halo, and enough near-white to trip a HUD's own checks for it.
    # Drawing a coverage mask and coloring afterwards keeps the ink exact.
    for name in icons_pil.glyph_names():
        image = icons_pil.glyph_image(name, 24, _INK)
        for y in range(24):
            for x in range(24):
                red, green, blue, _alpha = image.getpixel((x, y))
                assert (red, green, blue) == _INK, f"{name} at {x},{y}"
