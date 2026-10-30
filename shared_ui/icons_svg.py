"""The family's icons as SVG, for a page an app draws as HTML.

The same geometry :mod:`shared_ui.icons` and :mod:`shared_ui.icons_pil` render,
written out as SVG on the 48-square and inked in ``currentColor``, so the page's
own style sheet says what color an icon takes.  Every shape is laid down filled:
a pen's line is a rounded bar, which is also what gives it round ends and round
corners where two meet, and an outlined ring or frame is the space between two.
"""

from __future__ import annotations

import math
from itertools import pairwise

from shared_ui.icon_geometry import (
    CANVAS,
    Arc,
    Ellipse,
    Line,
    Path,
    Polygon,
    Polyline,
    RoundedRect,
    shapes_of,
)

_INK = "fill='currentColor'"
_BETWEEN = "fill='currentColor' fill-rule='evenodd'"


def _n(value: float) -> str:
    return f"{round(value, 3):g}"


def _bar(start: tuple[float, float], end: tuple[float, float], width: float) -> str:
    """A pen's line from *start* to *end*, its ends rounded by half its width."""
    (x1, y1), (x2, y2) = start, end
    length = math.dist(start, end) + width
    middle_x, middle_y = (x1 + x2) / 2, (y1 + y2) / 2
    turn = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return (f"<rect x='{_n(middle_x - length / 2)}' y='{_n(middle_y - width / 2)}' width='{_n(length)}' "
            f"height='{_n(width)}' rx='{_n(width / 2)}' "
            f"transform='rotate({_n(turn)} {_n(middle_x)} {_n(middle_y)})' {_INK}/>")


def _run(points, width: float) -> str:
    return "".join(_bar(a, b, width) for a, b in pairwise(points))


def _rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = max(0.0, min(r, w / 2, h / 2))
    return (f"M{_n(x + r)},{_n(y)} H{_n(x + w - r)} A{_n(r)},{_n(r)} 0 0 1 {_n(x + w)},{_n(y + r)} "
            f"V{_n(y + h - r)} A{_n(r)},{_n(r)} 0 0 1 {_n(x + w - r)},{_n(y + h)} "
            f"H{_n(x + r)} A{_n(r)},{_n(r)} 0 0 1 {_n(x)},{_n(y + h - r)} "
            f"V{_n(y + r)} A{_n(r)},{_n(r)} 0 0 1 {_n(x + r)},{_n(y)} Z")


def _ellipse_path(cx: float, cy: float, rx: float, ry: float) -> str:
    return (f"M{_n(cx - rx)},{_n(cy)} A{_n(rx)},{_n(ry)} 0 1 0 {_n(cx + rx)},{_n(cy)} "
            f"A{_n(rx)},{_n(ry)} 0 1 0 {_n(cx - rx)},{_n(cy)} Z")


def _line(shape: Line) -> str:
    return _bar((shape.x1, shape.y1), (shape.x2, shape.y2), shape.width)


def _polyline(shape: Polyline) -> str:
    return _run(shape.points, shape.width)


def _polygon(shape: Polygon) -> str:
    closed = (*shape.points, shape.points[0])
    points = " ".join(f"{_n(x)},{_n(y)}" for x, y in shape.points)
    if not shape.fill:
        return _run(closed, shape.width)
    solid = f"<polygon points='{points}' {_INK}/>"
    return solid + (_run(closed, shape.round_radius * 2) if shape.round_radius else "")


def _rounded_rect(shape: RoundedRect) -> str:
    if shape.fill:
        return f"<path d='{_rounded_rect_path(shape.x, shape.y, shape.w, shape.h, shape.radius)}' {_INK}/>"
    half = shape.width / 2
    outer = _rounded_rect_path(shape.x - half, shape.y - half, shape.w + shape.width,
                               shape.h + shape.width, shape.radius + half)
    inner = _rounded_rect_path(shape.x + half, shape.y + half, shape.w - shape.width,
                               shape.h - shape.width, shape.radius - half)
    return f"<path d='{outer} {inner}' {_BETWEEN}/>"


def _ellipse(shape: Ellipse) -> str:
    if shape.fill:
        return f"<path d='{_ellipse_path(shape.cx, shape.cy, shape.rx, shape.ry)}' {_INK}/>"
    half = shape.width / 2
    outer = _ellipse_path(shape.cx, shape.cy, shape.rx + half, shape.ry + half)
    inner = _ellipse_path(shape.cx, shape.cy, shape.rx - half, shape.ry - half)
    return f"<path d='{outer} {inner}' {_BETWEEN}/>"


def _arc(shape: Arc) -> str:
    """The band an arc's pen covers, between its two radii, with a round end."""
    cx, cy = shape.x + shape.w / 2, shape.y + shape.h / 2
    start, span = (shape.start, shape.span) if shape.span >= 0 else (shape.start + shape.span, -shape.span)
    half = shape.width / 2
    large = 1 if span > 180 else 0

    def at(degrees: float, grow: float) -> tuple[float, float]:
        radians = math.radians(degrees)
        return (cx + (shape.w / 2 + grow) * math.cos(radians), cy - (shape.h / 2 + grow) * math.sin(radians))

    (ox0, oy0), (ox1, oy1) = at(start, half), at(start + span, half)
    (ix1, iy1), (ix0, iy0) = at(start + span, -half), at(start, -half)
    outer_rx, outer_ry = shape.w / 2 + half, shape.h / 2 + half
    inner_rx, inner_ry = shape.w / 2 - half, shape.h / 2 - half
    band = (f"M{_n(ox0)},{_n(oy0)} A{_n(outer_rx)},{_n(outer_ry)} 0 {large} 0 {_n(ox1)},{_n(oy1)} "
            f"L{_n(ix1)},{_n(iy1)} A{_n(inner_rx)},{_n(inner_ry)} 0 {large} 1 {_n(ix0)},{_n(iy0)} Z")
    ends = "".join(f"<circle cx='{_n(x)}' cy='{_n(y)}' r='{_n(half)}' {_INK}/>"
                   for x, y in (at(start, 0), at(start + span, 0)))
    return f"<path d='{band}' {_INK}/>{ends}"


def _path_data(shape: Path) -> str:
    runs = []
    for command, *numbers in shape.commands:
        if command == "R":
            runs.append(_rounded_rect_path(*numbers))
        elif command == "Z":
            runs.append("Z")
        else:
            pairs = [f"{_n(a)},{_n(b)}" for a, b in zip(numbers[::2], numbers[1::2], strict=True)]
            runs.append(command + " ".join(pairs))
    return " ".join(runs)


def _path(shape: Path) -> str:
    return f"<path d='{_path_data(shape)}' transform='scale({_n(CANVAS / shape.frame)})' {_INK}/>"


_ELEMENTS = {Line: _line, Polyline: _polyline, Polygon: _polygon, RoundedRect: _rounded_rect,
             Ellipse: _ellipse, Arc: _arc, Path: _path}


def svg_icon(name: str, *, size: float) -> str:
    """*name* as an ``<svg>`` *size* across, drawn in the color around it."""
    shapes = "".join(_ELEMENTS[type(shape)](shape) for shape in shapes_of(name))
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {_n(CANVAS)} {_n(CANVAS)}' "
            f"width='{_n(size)}' height='{_n(size)}'>{shapes}</svg>")


svg_mark = svg_icon
