from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from shared_ui import icons, icons_pil
from shared_ui.colors import GREEN, TEXT_MUTED, TEXT_PRIMARY
from shared_ui.icon_geometry import ICONS, STAND_IN, Arc, icon_names
from shared_ui.icon_geometry import Path as Outline
from shared_ui.palette import TEXT_PRIMARY as _INK

_REPO_ROOT = Path(__file__).resolve().parent.parent

_SIZE = 48
_A_PIXEL_OF_OUTLINE_CENTERING = 1
_THE_BAND_PILLOW_S_ARCS_AND_RESAMPLING_NEED = 0.15
_AN_ICON_THIS_VERSION_LACKS = "an_icon_from_another_version"
_EVERY_ICON_AND_THE_STAND_IN = (*icon_names(), _AN_ICON_THIS_VERSION_LACKS)


def _pil_ink(image: Image.Image) -> tuple[int, int, int, int, int]:
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
    image = icons.icon_pixmap(name, size, TEXT_PRIMARY).toImage()
    xs, ys, count = [], [], 0
    for y in range(size):
        for x in range(size):
            if image.pixelColor(x, y).alpha() > 32:
                xs.append(x)
                ys.append(y)
                count += 1
    assert xs, "nothing was drawn"
    return min(xs), min(ys), max(xs), max(ys), count


def test_every_icon_inks_something_through_pillow_too_so_no_hud_button_comes_up_empty():
    for name in _EVERY_ICON_AND_THE_STAND_IN:
        image = icons_pil.pil_icon(name, _SIZE, _INK)
        assert image.size == (_SIZE, _SIZE), name
        assert _pil_ink(image)[4] > 0, name


def test_the_two_renderers_put_the_icon_in_the_same_place():
    for name in _EVERY_ICON_AND_THE_STAND_IN:
        pillow = _pil_ink(icons_pil.pil_icon(name, _SIZE, _INK))
        qt = _qt_ink(name, _SIZE)
        for edge in range(4):
            assert abs(pillow[edge] - qt[edge]) <= _A_PIXEL_OF_OUTLINE_CENTERING, f"{name} edge {edge}"


def test_the_two_renderers_lay_down_a_like_amount_of_ink():
    for name in _EVERY_ICON_AND_THE_STAND_IN:
        pillow = _pil_ink(icons_pil.pil_icon(name, _SIZE, _INK))[4]
        qt = _qt_ink(name, _SIZE)[4]
        assert abs(pillow - qt) / qt < _THE_BAND_PILLOW_S_ARCS_AND_RESAMPLING_NEED, name


def test_an_icon_this_version_does_not_have_is_drawn_as_the_stand_in(monkeypatch):
    monkeypatch.setitem(ICONS, "_the_stand_in", STAND_IN)
    stand_in = icons_pil.pil_icon("_the_stand_in", _SIZE, _INK)

    drawn = icons_pil.pil_icon(_AN_ICON_THIS_VERSION_LACKS, _SIZE, _INK)

    assert drawn.tobytes() == stand_in.tobytes()


def test_an_icon_is_drawn_in_the_color_it_is_asked_for_a_muted_control_or_a_green_favorite():
    for color in ((*TEXT_MUTED.getRgb()[:3],), (*GREEN.getRgb()[:3],)):
        image = icons_pil.pil_icon("star", _SIZE, color)
        assert image.getpixel((24, 25))[:3] == color


def test_a_pasted_icon_sits_on_what_the_hud_already_drew():
    panel = Image.new("RGBA", (40, 24), (0, 80, 0, 255))
    icons_pil.paste_icon(panel, "trash", (12, 2, 20, 20), _INK)
    pixels = [panel.getpixel((x, y)) for y in range(24) for x in range(40)]

    assert panel.getpixel((2, 12)) == (0, 80, 0, 255)
    assert all(pixel[3] == 255 for pixel in pixels)
    assert any(pixel[0] > 200 for pixel in pixels), "the icon did not land"


def _a_panel_showing_only_the_icon_s_ink(width: int, height: int) -> Image.Image:
    return Image.new("RGBA", (width, height), (0, 0, 0, 0))


def test_a_pasted_icon_is_centered_in_a_hud_button_s_frame_which_is_not_quite_square():
    panel = _a_panel_showing_only_the_icon_s_ink(48, 24)
    icons_pil.paste_icon(panel, "plus", (0, 0, 48, 24), _INK)
    left, upper, right, lower, _count = _pil_ink(panel)
    assert abs((left + right) / 2 - 24) <= 1
    assert abs((upper + lower) / 2 - 12) <= 1


def test_a_pasted_icon_is_centered_in_a_frame_that_is_not_at_the_origin():
    panel = _a_panel_showing_only_the_icon_s_ink(64, 40)
    icons_pil.paste_icon(panel, "plus", (36, 8, 24, 28), _INK)
    left, upper, right, lower, _count = _pil_ink(panel)
    assert abs((left + right) / 2 - 48) <= 1
    assert abs((upper + lower) / 2 - 22) <= 1


def test_the_geometry_is_the_one_registry_both_renderers_draw_from():
    for name in icon_names():
        assert not icons.icon_pixmap(name, _SIZE, TEXT_PRIMARY).isNull(), name
        assert _pil_ink(icons_pil.pil_icon(name, _SIZE, _INK))[4] > 0, name
    assert "icon_names" not in icons.__all__
    assert "icon_names" not in icons_pil.__all__


def test_an_ink_with_an_alpha_lands_dimmed_as_a_hud_dims_an_icon():
    image = icons_pil.pil_icon("star", _SIZE, (*_INK, 128))
    alphas = [image.getpixel((x, y))[3] for y in range(_SIZE) for x in range(_SIZE)]
    assert 100 <= max(alphas) <= 128


def test_the_pillow_star_outline_s_points_are_not_chipped():
    (star,) = ICONS["star_outline"]
    top = min(y for _x, y in star.points)
    alpha = icons_pil.pil_icon("star_outline", _SIZE, _INK).split()[3].load()

    assert alpha[24, int(top) - 1] > 200


def test_a_negative_span_draws_the_same_arc_as_its_positive_twin():
    def render(arc):
        mask = Image.new("L", (_SIZE * 4, _SIZE * 4), 0)
        icons_pil._draw(ImageDraw.Draw(mask), arc, 255, 4.0)
        return mask.tobytes()

    forward = Arc(x=8, y=8, w=32, h=32, start=0, span=90, width=5)
    backward = Arc(x=8, y=8, w=32, h=32, start=90, span=-90, width=5)
    assert render(forward) == render(backward)


def test_drawing_a_hud_icon_never_drags_qt_into_a_player():
    loaded = _toolkits_loaded_by_importing(
        "shared_ui.icons_pil", "shared_ui.icon_geometry", "shared_ui.palette", "shared_ui.chrome",
        "shared_ui.app_icon", "shared_ui.toggle_switch_pil")

    assert "PyQt6" not in loaded, loaded


def test_the_geometry_of_an_icon_or_a_switch_takes_no_toolkit_pillow_included():
    loaded = _toolkits_loaded_by_importing("shared_ui.icon_geometry", "shared_ui.toggle_geometry")

    assert loaded == set(), loaded


def _toolkits_loaded_by_importing(*modules: str) -> set[str]:
    # `python -c` puts the process cwd first on sys.path and nothing else, so the probe says
    # which tree it read: from elsewhere it would import the primary checkout's copy, and a
    # branch that dragged Qt or Pillow in would pass.
    probe = (
        f"import json, sys; import {', '.join(modules)}; "
        "print(shared_ui.__file__); "
        "print(json.dumps(sorted({m.split('.')[0] for m in sys.modules if m.split('.')[0] in ('PyQt6', 'PIL')})))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], cwd=_REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)},
        capture_output=True, text=True, check=True,
    )
    read_from, toolkits = result.stdout.splitlines()

    assert Path(read_from).resolve().is_relative_to(_REPO_ROOT), (
        f"the probe read {read_from}, not the tree under test at {_REPO_ROOT}"
    )
    return set(json.loads(toolkits))


def test_an_icon_is_never_brighter_than_the_ink_it_was_drawn_in():
    for name in _EVERY_ICON_AND_THE_STAND_IN:
        image = icons_pil.pil_icon(name, 24, _INK)
        for y in range(24):
            for x in range(24):
                red, green, blue, _alpha = image.getpixel((x, y))
                assert (red, green, blue) == _INK, f"{name} at {x},{y}"


def test_a_path_written_in_a_frame_of_its_own_fills_the_canvas_that_frame_stands_for(monkeypatch):
    square = Outline((("M", 0, 0), ("L", 24, 0), ("L", 24, 24), ("L", 0, 24), ("Z",)), frame=24.0)
    monkeypatch.setitem(ICONS, "_a_square_in_a_frame_of_24", (square,))

    drawn = icons_pil.pil_icon("_a_square_in_a_frame_of_24", _SIZE, _INK)

    assert _pil_ink(drawn)[:4] == (0, 0, _SIZE - 1, _SIZE - 1)
