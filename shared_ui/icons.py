"""The family's icon glyphs, drawn with QPainter for the apps' Qt chrome.

The shapes are not here -- they are in :mod:`shared_ui.icon_geometry`, which
knows nothing about any toolkit, and :mod:`shared_ui.icons_pil` renders the same
list through Pillow for the players' HUDs.  That split is the point: a mark drawn
here and the same mark on a HUD are one drawing.

Callers take one of three routes:

* :func:`glyph_pixmap` for a raw pixmap -- a panel that paints its own bitmap,
* :func:`glyph_icon` for a QIcon carrying a normal and a disabled rendering --
  a toolbar button, which Qt swaps between as it enables and disables,
* :func:`draw_glyph` to paint one through a painter the caller already holds --
  the route a badge takes, so the mark lands on the chip the caller just drew.

The marks are drawn rather than typed as font characters because a face is not
guaranteed to carry them (Windows draws a tofu box for the ones it lacks), and
because a typed glyph's weight then follows whatever face happens to be
installed rather than the weight of the marks beside it.

What is NOT here: an app's own composition -- the chip behind a badge, which
levels get a lettered mark, which button wears which glyph.  That is each app's
business and it stays there.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from shared_ui.colors import TEXT_MUTED, TEXT_PRIMARY
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
)

__all__ = [
    "CANVAS",
    "STROKE",
    "draw_glyph",
    "glyph_icon",
    "glyph_pixmap",
]


def draw_glyph(painter: QPainter, name: str, color, *,
               size: float = CANVAS, x: float = 0.0, y: float = 0.0) -> None:
    """Paint *name* through *painter*, in a *size*-square box at ``(x, y)``.

    The painter's own pen, brush, transform and hints are left as they were --
    a caller part-way through drawing a chip must not find its brush swapped
    out from under it.
    """
    ink = QColor(color)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.translate(x, y)
    painter.scale(size / CANVAS, size / CANVAS)
    for shape in GLYPHS[name]:
        _draw(painter, shape, ink)
    painter.restore()


def glyph_pixmap(name: str, size: int, color) -> QPixmap:
    """*name* as a transparent *size*-square pixmap, drawn in *color*."""
    side = max(1, int(size))
    pixmap = QPixmap(side, side)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    draw_glyph(painter, name, color, size=side)
    painter.end()
    return pixmap


def glyph_icon(name: str, *, color=None, size: int = int(CANVAS)) -> QIcon:
    """*name* as an icon carrying its normal and its disabled rendering.

    *color* tints the normal one -- a button that says what it does before its
    tooltip does -- and the disabled one stays the muted gray whatever that
    color is, so a button with nothing to act on reads as dead rather than as a
    dimmer shade of red.  There is deliberately no way to override the second:
    the override would be the thing the rule above rules out.

    Drawn at *size* and left for Qt to scale down onto the button, so the edges
    stay crisp at whatever size the chrome ends up asking for.
    """
    icon = QIcon()
    icon.addPixmap(
        glyph_pixmap(name, size, TEXT_PRIMARY if color is None else color),
        QIcon.Mode.Normal,
    )
    icon.addPixmap(glyph_pixmap(name, size, TEXT_MUTED), QIcon.Mode.Disabled)
    return icon


def _stroke(painter: QPainter, ink: QColor, width: float) -> None:
    """Set up an outline pen: round caps and joins, so a mark has no sharp ends."""
    pen = QPen(ink)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)


def _solid(painter: QPainter, ink: QColor) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)


def _draw(painter: QPainter, shape, ink: QColor) -> None:
    if isinstance(shape, Line):
        _stroke(painter, ink, shape.width)
        painter.drawLine(QPointF(shape.x1, shape.y1), QPointF(shape.x2, shape.y2))
    elif isinstance(shape, Polyline):
        _stroke(painter, ink, shape.width)
        painter.drawPolyline(*(QPointF(px, py) for px, py in shape.points))
    elif isinstance(shape, Polygon):
        if shape.fill and shape.round_radius:
            # Filled AND stroked with its own outline: the stroke's round joins
            # are what round the corners, and it grows the shape by the radius.
            _stroke(painter, ink, shape.round_radius * 2)
            painter.setBrush(ink)
        elif shape.fill:
            _solid(painter, ink)
        else:
            _stroke(painter, ink, shape.width)
        painter.drawPolygon(*(QPointF(px, py) for px, py in shape.points))
    elif isinstance(shape, RoundedRect):
        if shape.fill:
            _solid(painter, ink)
        else:
            _stroke(painter, ink, shape.width)
        painter.drawRoundedRect(QRectF(shape.x, shape.y, shape.w, shape.h),
                                shape.radius, shape.radius)
    elif isinstance(shape, Ellipse):
        if shape.fill:
            _solid(painter, ink)
        else:
            _stroke(painter, ink, shape.width)
        painter.drawEllipse(QPointF(shape.cx, shape.cy), shape.rx, shape.ry)
    elif isinstance(shape, Arc):
        _stroke(painter, ink, shape.width)
        # QPainter takes sixteenths of a degree, counter-clockwise from 3
        # o'clock -- which is the convention the geometry is written in.
        painter.drawArc(QRectF(shape.x, shape.y, shape.w, shape.h),
                        round(shape.start * 16), round(shape.span * 16))
    else:  # pragma: no cover -- a shape added to the geometry and not to a renderer
        raise TypeError(f"no Qt rendering for {type(shape).__name__}")
