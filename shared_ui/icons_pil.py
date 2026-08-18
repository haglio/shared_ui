"""The family's icon glyphs, drawn with Pillow for the players' HUDs.

Same shapes as :mod:`shared_ui.icons` paints with QPainter -- both walk the list
in :mod:`shared_ui.icon_geometry` -- so the trash can on a player's HUD is the
trash can on Origenerator's toolbar rather than a lookalike.  It could not be
before: an mpv overlay takes a bitmap, so the HUDs paint with Pillow and there is
no Qt in a player process at all, which left every HUD mark either a typed font
character or its own hand-drawn thing.

This module imports Pillow and NOT Qt, which is what lets a player process use it
without dragging PyQt6 into a video pipeline.

Two things Pillow does not do that QPainter does, and how they are handled:
antialiasing (everything is drawn at :data:`SUPERSAMPLE` scale and resampled
down) and round line caps (a filled dot is laid at each stroke's ends).  Both
matter at HUD size, where a mark is a dozen pixels across and a stair-stepped
edge or a chopped-off stroke is most of what the eye sees.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from shared_ui.icon_geometry import (
    CANVAS,
    GLYPHS,
    STROKE,
    Arc,
    Ellipse,
    Line,
    Polygon,
    Polyline,
    RoundedRect,
    glyph_names,
)

__all__ = ["CANVAS", "STROKE", "SUPERSAMPLE", "glyph_names", "glyph_image", "paste_glyph"]

# Pillow's draw calls are hard-edged, so a glyph is drawn this many times too big
# and resampled down; the resampling is where the smooth edge comes from.  Four
# is where it stopped looking jagged at HUD sizes -- a 14px button is drawn at 56
# and thrown away, which costs nothing worth measuring since the HUDs cache what
# they draw.
SUPERSAMPLE = 4


def glyph_image(name: str, size: int, color) -> Image.Image:
    """*name* as a transparent RGBA square *size* px on a side, drawn in *color*.

    *color* is an ``(r, g, b)`` or ``(r, g, b, a)`` tuple -- what the HUDs' own
    palette is in -- rather than a QColor, since nothing here knows about Qt.
    """
    side = max(1, int(size))
    big = side * SUPERSAMPLE
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = big / CANVAS
    ink = _rgba(color)
    for shape in GLYPHS[name]:
        _draw(draw, shape, ink, scale)
    return image.resize((side, side), Image.LANCZOS)


def paste_glyph(image: Image.Image, name: str, box: tuple[int, int, int, int],
                color) -> None:
    """Lay *name* over *image*, centered in ``box`` and as big as its short side.

    Composited rather than pasted flat, so the mark sits on whatever the HUD has
    already drawn there -- a button's fill, the panel, the video -- instead of
    stamping a transparent square over it.
    """
    x, y, w, h = box
    side = max(1, min(int(w), int(h)))
    glyph = glyph_image(name, side, color)
    image.alpha_composite(glyph, (int(x + (w - side) / 2), int(y + (h - side) / 2)))


def _rgba(color) -> tuple[int, int, int, int]:
    values = tuple(int(v) for v in color)
    if len(values) == 3:
        return (*values, 255)
    return values[:4]


def _draw(draw: ImageDraw.ImageDraw, shape, ink, scale: float) -> None:
    if isinstance(shape, Line):
        points = ((shape.x1, shape.y1), (shape.x2, shape.y2))
        _stroke_path(draw, points, ink, shape.width * scale, scale)
    elif isinstance(shape, Polyline):
        _stroke_path(draw, shape.points, ink, shape.width * scale, scale)
    elif isinstance(shape, Polygon):
        if shape.fill:
            draw.polygon([(px * scale, py * scale) for px, py in shape.points], fill=ink)
        else:
            # Closed as a path rather than as an outlined polygon: Pillow's
            # polygon outline is hard-cornered whatever the width, and a star's
            # points come out chipped.
            _stroke_path(draw, (*shape.points, shape.points[0]), ink,
                         shape.width * scale, scale)
    elif isinstance(shape, RoundedRect):
        box = _box(shape.x, shape.y, shape.x + shape.w, shape.y + shape.h, scale)
        if shape.fill:
            draw.rounded_rectangle(box, radius=shape.radius * scale, fill=ink)
        else:
            grown = _centered(box, shape.width * scale)
            draw.rounded_rectangle(grown, radius=shape.radius * scale + shape.width
                                   * scale / 2, outline=ink,
                                   width=max(1, round(shape.width * scale)))
    elif isinstance(shape, Ellipse):
        box = _box(shape.cx - shape.rx, shape.cy - shape.ry,
                   shape.cx + shape.rx, shape.cy + shape.ry, scale)
        if shape.fill:
            draw.ellipse(box, fill=ink)
        else:
            draw.ellipse(_centered(box, shape.width * scale), outline=ink,
                         width=max(1, round(shape.width * scale)))
    elif isinstance(shape, Arc):
        _arc(draw, shape, ink, scale)
    else:  # pragma: no cover -- a shape added to the geometry and not to a renderer
        raise TypeError(f"no Pillow rendering for {type(shape).__name__}")


def _arc(draw: ImageDraw.ImageDraw, shape: Arc, ink, scale: float) -> None:
    """One arc, converted out of the geometry's Qt angles.

    The geometry measures counter-clockwise from 3 o'clock and gives a span;
    Pillow measures clockwise and takes two absolute angles.  Negating flips the
    direction, so the Qt sweep ``[start, start + span]`` is the Pillow sweep
    ``[-(start + span), -start]`` -- same arc, drawn the other way round.
    """
    box = _centered(_box(shape.x, shape.y, shape.x + shape.w, shape.y + shape.h, scale),
                    shape.width * scale)
    width = max(1, round(shape.width * scale))
    draw.arc(box, -(shape.start + shape.span), -shape.start, fill=ink, width=width)
    for angle in (shape.start, shape.start + shape.span):
        _cap(draw, *_on_arc(shape, angle), ink, shape.width * scale, scale)


def _on_arc(shape: Arc, degrees: float) -> tuple[float, float]:
    """Where *degrees* lands on the arc's ellipse, in canvas coordinates."""
    radians = math.radians(degrees)
    return (shape.x + shape.w / 2 + shape.w / 2 * math.cos(radians),
            shape.y + shape.h / 2 - shape.h / 2 * math.sin(radians))


def _box(x0: float, y0: float, x1: float, y1: float, scale: float) -> list:
    return [(x0 * scale, y0 * scale), (x1 * scale, y1 * scale)]


def _centered(box: list, width: float) -> list:
    """*box* grown by half a stroke on every side.

    Pillow draws an outline INSIDE the box it is given, where QPainter centers
    the pen on the path -- so the same numbers give Pillow a mark half a stroke
    smaller all round.  Growing the box first is what puts the two renderings on
    top of each other.
    """
    half = width / 2
    (x0, y0), (x1, y1) = box
    return [(x0 - half, y0 - half), (x1 + half, y1 + half)]


def _stroke_path(draw: ImageDraw.ImageDraw, points, ink, width: float,
                 scale: float) -> None:
    """A polyline in *ink*, with rounded joints and rounded ends."""
    scaled = [(px * scale, py * scale) for px, py in points]
    draw.line(scaled, fill=ink, width=max(1, round(width)), joint="curve")
    for px, py in (points[0], points[-1]):
        _cap(draw, px, py, ink, width, scale)


def _cap(draw: ImageDraw.ImageDraw, x: float, y: float, ink, width: float,
         scale: float) -> None:
    """The dot that stands in for a round cap on a stroke's end."""
    radius = width / 2
    cx, cy = x * scale, y * scale
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=ink)
