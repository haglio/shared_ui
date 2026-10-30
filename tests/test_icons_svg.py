"""shared_ui.icons_svg: the family's icons for a page drawn as SVG."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

from shared_ui import icons, icons_svg
from shared_ui.colors import TEXT_PRIMARY
from shared_ui.icon_geometry import ICONS, Arc, Ellipse, Line, Path, icon_names


def _parsed(markup: str) -> ET.Element:
    return ET.fromstring(markup)


def test_an_icon_is_an_svg_of_the_family_canvas_sized_for_its_place():
    drawn = _parsed(icons_svg.svg_icon("check", size=26))

    assert drawn.tag.endswith("svg")
    assert drawn.get("viewBox") == "0 0 48 48"
    assert drawn.get("width") == "26" and drawn.get("height") == "26"


@pytest.mark.parametrize("name", icon_names())
def test_every_icon_is_laid_down_filled_in_the_color_around_it(name):
    drawn = list(_parsed(icons_svg.svg_icon(name, size=24)))

    assert drawn, name
    assert {element.get("fill") for element in drawn} == {"currentColor"}, name


def test_a_pen_s_line_is_a_bar_of_its_width_rounded_past_both_ends(monkeypatch):
    monkeypatch.setitem(ICONS, "_level", (Line(4, 24, 40, 24, 3),))

    (bar,) = list(_parsed(icons_svg.svg_icon("_level", size=24)))

    assert [bar.get(key) for key in ("x", "y", "width", "height", "rx")] == ["2.5", "22.5", "39", "3", "1.5"]
    assert bar.get("transform") == "rotate(0 22 24)"


def test_an_outlined_ring_is_the_band_between_two_circles(monkeypatch):
    monkeypatch.setitem(ICONS, "_ring", (Ellipse(24, 24, 10, 10, width=4),))

    (ring,) = list(_parsed(icons_svg.svg_icon("_ring", size=24)))

    assert ring.get("fill-rule") == "evenodd"
    assert ring.get("d").count("Z") == 2 and " A12,12 " in ring.get("d") and " A8,8 " in ring.get("d")


def test_an_arc_runs_counterclockwise_from_three_o_clock_and_ends_round(monkeypatch):
    monkeypatch.setitem(ICONS, "_quarter", (Arc(14, 14, 20, 20, 0, 90, 2),))

    band, start, end = list(_parsed(icons_svg.svg_icon("_quarter", size=24)))

    assert band.get("d") == "M35,24 A11,11 0 0 0 24,13 L24,15 A9,9 0 0 1 33,24 Z"
    assert [(cap.get("cx"), cap.get("cy"), cap.get("r")) for cap in (start, end)] == [
        ("34", "24", "1"), ("24", "14", "1")]


def test_a_path_is_drawn_at_its_own_frame_s_scale(monkeypatch):
    square = Path((("M", 0, 0), ("L", 24, 0), ("Q", 24, 24, 0, 24), ("Z",)), frame=24.0)
    monkeypatch.setitem(ICONS, "_framed", (square,))

    (path,) = list(_parsed(icons_svg.svg_icon("_framed", size=24)))

    assert path.get("transform") == "scale(2)"
    assert path.get("d") == "M0,0 L24,0 Q24,24 0,24 Z"


def _ink(image: QImage) -> list[tuple[int, int]]:
    return [(x, y) for y in range(image.height()) for x in range(image.width())
            if image.pixelColor(x, y).alpha() > 32]


def _box(ink) -> tuple[int, int, int, int]:
    return (min(x for x, _ in ink), min(y for _, y in ink), max(x for x, _ in ink), max(y for _, y in ink))


@pytest.mark.parametrize("name", icon_names())
def test_a_page_s_icon_is_the_icon_the_chrome_draws(name):
    page = QImage(48, 48, QImage.Format.Format_ARGB32_Premultiplied)
    page.fill(Qt.GlobalColor.transparent)
    painter = QPainter(page)
    QSvgRenderer(QByteArray(icons_svg.svg_icon(name, size=48).replace("currentColor", "#f0f0f0").encode())
                 ).render(painter)
    painter.end()
    chrome = icons.icon_pixmap(name, 48, TEXT_PRIMARY).toImage()

    drawn, expected = _ink(page), _ink(chrome)
    assert all(abs(a - b) <= 1 for a, b in zip(_box(drawn), _box(expected), strict=True)), name
    assert abs(len(drawn) - len(expected)) / len(expected) < 0.1, name
