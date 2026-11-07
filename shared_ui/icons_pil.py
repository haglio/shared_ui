"""Pillow has neither antialiasing nor round line caps, so an icon is drawn four times too
big, where its edges stop looking jagged at a HUD button's size, and resampled down, with a
filled dot laid at each line's end."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

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
from shared_ui.palette import CHANNEL_MAX, RGB_CHANNELS

__all__ = ["CANVAS", "SUPERSAMPLE", "paste_icon", "pil_icon"]

SUPERSAMPLE = 4


def pil_icon(name: str, size: int, color) -> Image.Image:
    edge = max(1, int(size))
    big = edge * SUPERSAMPLE
    # Pillow's Lanczos overshoots at a hard edge: resampled colored ink leaves a halo brighter
    # than the ink. Resampled coverage saturates harmlessly, so the color goes on afterwards.
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)
    scale = big / CANVAS
    for shape in shapes_of(name):
        _draw(draw, shape, CHANNEL_MAX, scale)
    mask = mask.resize((edge, edge), Image.LANCZOS)
    red, green, blue, alpha = _rgba(color)
    if alpha != CHANNEL_MAX:
        mask = mask.point(lambda value: value * alpha // CHANNEL_MAX)
    image = Image.new("RGBA", (edge, edge), (red, green, blue, 0))
    image.putalpha(mask)
    return image


def paste_icon(image: Image.Image, name: str, frame: tuple[int, int, int, int],
               color) -> None:
    x, y, w, h = frame
    edge = max(1, min(int(w), int(h)))
    icon = pil_icon(name, edge, color)
    image.alpha_composite(icon, (int(x + (w - edge) / 2), int(y + (h - edge) / 2)))


def _rgba(color) -> tuple[int, int, int, int]:
    values = tuple(int(v) for v in color)
    if len(values) == RGB_CHANNELS:
        return (*values, CHANNEL_MAX)
    return values[:4]


def _draw(draw: ImageDraw.ImageDraw, shape, ink, scale: float) -> None:
    _DRAWN_BY[type(shape)](draw, shape, ink, scale)


def _line(draw: ImageDraw.ImageDraw, shape: Line, ink, scale: float) -> None:
    _draw_path(draw, ((shape.x1, shape.y1), (shape.x2, shape.y2)), ink, shape.width * scale, scale)


def _polyline(draw: ImageDraw.ImageDraw, shape: Polyline, ink, scale: float) -> None:
    _draw_path(draw, shape.points, ink, shape.width * scale, scale)


def _polygon(draw: ImageDraw.ImageDraw, shape: Polygon, ink, scale: float) -> None:
    closed = (*shape.points, shape.points[0])
    if not shape.fill:
        # Pillow's polygon outline is hard-cornered whatever the width.
        _draw_path(draw, closed, ink, shape.width * scale, scale)
        return
    draw.polygon([(px * scale, py * scale) for px, py in shape.points], fill=ink)
    if shape.round_radius:
        _draw_path(draw, closed, ink, shape.round_radius * 2 * scale, scale)


def _rounded_rect(draw: ImageDraw.ImageDraw, shape: RoundedRect, ink, scale: float) -> None:
    frame = _frame(shape.x, shape.y, shape.x + shape.w, shape.y + shape.h, scale)
    if shape.fill:
        draw.rounded_rectangle(frame, radius=shape.radius * scale, fill=ink)
        return
    pen = shape.width * scale
    draw.rounded_rectangle(_centered(frame, pen), radius=shape.radius * scale + pen / 2,
                           outline=ink, width=max(1, round(pen)))


def _ellipse(draw: ImageDraw.ImageDraw, shape: Ellipse, ink, scale: float) -> None:
    frame = _frame(shape.cx - shape.rx, shape.cy - shape.ry,
                   shape.cx + shape.rx, shape.cy + shape.ry, scale)
    if shape.fill:
        draw.ellipse(frame, fill=ink)
        return
    pen = shape.width * scale
    draw.ellipse(_centered(frame, pen), outline=ink, width=max(1, round(pen)))


def _scaled_path(draw: ImageDraw.ImageDraw, shape: Path, ink, scale: float) -> None:
    _path(draw, shape, ink, scale * CANVAS / shape.frame)


_CURVE_STEPS = 8


def _path(draw: ImageDraw.ImageDraw, shape: Path, ink, scale: float) -> None:
    runs: list[list[tuple[float, float]]] = []
    for command, *numbers in shape.commands:
        if command == "M":
            runs.append([tuple(numbers)])
        elif command == "L":
            runs[-1].append(tuple(numbers))
        elif command == "Q":
            (x0, y0), (cx, cy, x1, y1) = runs[-1][-1], numbers
            runs[-1].extend(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                             (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1)
                            for t in (step / _CURVE_STEPS for step in range(1, _CURVE_STEPS + 1)))
        elif command == "C":
            (x0, y0), (x1, y1, x2, y2, x3, y3) = runs[-1][-1], numbers
            runs[-1].extend((
                (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 * x3,
                (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3 * y3)
                for t in (step / _CURVE_STEPS for step in range(1, _CURVE_STEPS + 1)))
        elif command == "R":
            x, y, w, h, radius = numbers
            draw.rounded_rectangle(_frame(x, y, x + w, y + h, scale), radius=radius * scale, fill=ink)
    for run in runs:
        draw.polygon([(px * scale, py * scale) for px, py in run], fill=ink)


def _arc(draw: ImageDraw.ImageDraw, shape: Arc, ink, scale: float) -> None:
    """Pillow measures clockwise and takes two absolute angles, so the Qt sweep
    ``[start, start + span]`` is ``[-(start + span), -start]``."""
    frame = _centered(_frame(shape.x, shape.y, shape.x + shape.w, shape.y + shape.h, scale),
                      shape.width * scale)
    width = max(1, round(shape.width * scale))
    # A negative span sweeps the same arc for Qt and the long way round for Pillow.
    start = shape.start if shape.span >= 0 else shape.start + shape.span
    span = abs(shape.span)
    draw.arc(frame, -(start + span), -start, fill=ink, width=width)
    for angle in (start, start + span):
        _cap(draw, _on_arc(shape, angle), ink, shape.width * scale, scale)


def _on_arc(shape: Arc, degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    return (shape.x + shape.w / 2 + shape.w / 2 * math.cos(radians),
            shape.y + shape.h / 2 - shape.h / 2 * math.sin(radians))


def _frame(x0: float, y0: float, x1: float, y1: float, scale: float) -> list:
    return [(x0 * scale, y0 * scale), (x1 * scale, y1 * scale)]


def _centered(frame: list, width: float) -> list:
    """Pillow draws an outline inside the frame it is given, where QPainter centers the pen
    on the path."""
    half = width / 2
    (x0, y0), (x1, y1) = frame
    return [(x0 - half, y0 - half), (x1 + half, y1 + half)]


def _draw_path(draw: ImageDraw.ImageDraw, points, ink, width: float,
               scale: float) -> None:
    scaled = [(px * scale, py * scale) for px, py in points]
    draw.line(scaled, fill=ink, width=max(1, round(width)), joint="curve")
    for point in (points[0], points[-1]):
        _cap(draw, point, ink, width, scale)


def _cap(draw: ImageDraw.ImageDraw, point: tuple[float, float], ink, width: float,
         scale: float) -> None:
    radius = width / 2
    cx, cy = point[0] * scale, point[1] * scale
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=ink)


_DRAWN_BY = {
    Line: _line, Polyline: _polyline, Polygon: _polygon, RoundedRect: _rounded_rect,
    Ellipse: _ellipse, Arc: _arc, Path: _scaled_path,
}
