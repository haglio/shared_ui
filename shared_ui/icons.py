from __future__ import annotations

import html
from dataclasses import dataclass
from functools import cache

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

from shared_ui.colors import TEXT_MUTED, TEXT_PRIMARY
from shared_ui.icon_geometry import (
    CANVAS,
    PEN_WIDTH,
    STAND_IN,
    Arc,
    Ellipse,
    Line,
    Path,
    Polygon,
    Polyline,
    RoundedRect,
    shapes_of,
)
from shared_ui.stand_in_tooltips import remember_the_stand_in_on

__all__ = [
    "CANVAS",
    "PEN_WIDTH",
    "draw_icon",
    "icon_pixmap",
    "qt_icon",
]


@dataclass(frozen=True)
class _Frame:
    size: float = CANVAS
    x: float = 0.0
    y: float = 0.0


def draw_icon(painter: QPainter, name: str, color, **frame) -> None:
    ink = QColor(color)
    placed = _Frame(**frame)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.translate(placed.x, placed.y)
    painter.scale(placed.size / CANVAS, placed.size / CANVAS)
    shapes = shapes_of(name)
    for shape in shapes:
        _draw(painter, shape, ink)
    painter.restore()
    if shapes is STAND_IN and isinstance(painter.device(), QPixmap):
        remember_the_stand_in_on(painter.device(), name)


_INK_PROBE = 2 * int(CANVAS)
_VISIBLE_ALPHA = 32


@cache
def _ink_box(name: str) -> QRectF:
    image = icon_pixmap(name, _INK_PROBE, TEXT_PRIMARY).toImage()
    inked = [(x, y) for y in range(image.height()) for x in range(image.width())
             if image.pixelColor(x, y).alpha() >= _VISIBLE_ALPHA]
    xs, ys = [x for x, _y in inked], [y for _x, y in inked]
    unit = CANVAS / _INK_PROBE
    return QRectF(min(xs) * unit, min(ys) * unit,
                  (max(xs) + 1 - min(xs)) * unit, (max(ys) + 1 - min(ys)) * unit)


def draw_icon_filling(painter: QPainter, name: str, color, box: QRectF) -> None:
    ink = _ink_box(name)
    scale = min(box.width() / ink.width(), box.height() / ink.height())
    draw_icon(painter, name, color, size=CANVAS * scale,
              x=box.center().x() - ink.center().x() * scale,
              y=box.center().y() - ink.center().y() * scale)


def icon_pixmap(name: str, size: int, color) -> QPixmap:
    edge = max(1, int(size))
    pixmap = QPixmap(edge, edge)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    draw_icon(painter, name, color, size=edge)
    painter.end()
    return pixmap


def qt_icon(name: str, *, color=None, size: int = int(CANVAS)) -> QIcon:
    # Qt puts a QIcon's disabled pixmap on a button the moment the button goes dead.
    icon = QIcon()
    icon.addPixmap(
        icon_pixmap(name, size, TEXT_PRIMARY if color is None else color),
        QIcon.Mode.Normal,
    )
    icon.addPixmap(icon_pixmap(name, size, TEXT_MUTED), QIcon.Mode.Disabled)
    return icon


def inline_icon(name: str, *, color, size: int) -> str:
    png = QByteArray()
    buffer = QBuffer(png)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    icon_pixmap(name, 2 * size, color).save(buffer, "PNG")
    source = "data:image/png;base64," + bytes(png.toBase64()).decode("ascii")
    return f'<img src="{source}" width="{size}" height="{size}" style="vertical-align: middle">'


def icon_then_text(name: str, text: str, *, color, size: int) -> str:
    return f"{inline_icon(name, color=color, size=size)}&nbsp;{html.escape(text, quote=False)}"


def _set_pen(painter: QPainter, ink: QColor, width: float) -> None:
    pen = QPen(ink)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)


def _solid(painter: QPainter, ink: QColor) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)


def _solid_or_outlined(painter: QPainter, shape, ink: QColor) -> None:
    if shape.fill:
        _solid(painter, ink)
    else:
        _set_pen(painter, ink, shape.width)


def _line(painter: QPainter, shape: Line, ink: QColor) -> None:
    _set_pen(painter, ink, shape.width)
    painter.drawLine(QPointF(shape.x1, shape.y1), QPointF(shape.x2, shape.y2))


def _polyline(painter: QPainter, shape: Polyline, ink: QColor) -> None:
    _set_pen(painter, ink, shape.width)
    painter.drawPolyline(QPolygonF([QPointF(px, py) for px, py in shape.points]))


def _polygon(painter: QPainter, shape: Polygon, ink: QColor) -> None:
    if shape.fill and shape.round_radius:
        _set_pen(painter, ink, shape.round_radius * 2)
        painter.setBrush(ink)
    else:
        _solid_or_outlined(painter, shape, ink)
    painter.drawPolygon(QPolygonF([QPointF(px, py) for px, py in shape.points]))


def _rounded_rect(painter: QPainter, shape: RoundedRect, ink: QColor) -> None:
    _solid_or_outlined(painter, shape, ink)
    painter.drawRoundedRect(QRectF(shape.x, shape.y, shape.w, shape.h),
                            shape.radius, shape.radius)


def _ellipse(painter: QPainter, shape: Ellipse, ink: QColor) -> None:
    _solid_or_outlined(painter, shape, ink)
    painter.drawEllipse(QPointF(shape.cx, shape.cy), shape.rx, shape.ry)


def _arc(painter: QPainter, shape: Arc, ink: QColor) -> None:
    _set_pen(painter, ink, shape.width)
    # QPainter takes sixteenths of a degree, counter-clockwise from 3 o'clock.
    painter.drawArc(QRectF(shape.x, shape.y, shape.w, shape.h),
                    round(shape.start * 16), round(shape.span * 16))


def _path(painter: QPainter, shape: Path, ink: QColor) -> None:
    painter.save()
    painter.scale(CANVAS / shape.frame, CANVAS / shape.frame)
    _solid(painter, ink)
    painter.drawPath(_painter_path(shape))
    painter.restore()


_DRAWN_BY = {
    Line: _line, Polyline: _polyline, Polygon: _polygon, RoundedRect: _rounded_rect,
    Ellipse: _ellipse, Arc: _arc, Path: _path,
}


def _draw(painter: QPainter, shape, ink: QColor) -> None:
    _DRAWN_BY[type(shape)](painter, shape, ink)


def _painter_path(shape: Path) -> QPainterPath:
    path = QPainterPath()
    for command, *numbers in shape.commands:
        if command == "M":
            path.moveTo(*numbers)
        elif command == "L":
            path.lineTo(*numbers)
        elif command == "Q":
            path.quadTo(*numbers)
        elif command == "C":
            path.cubicTo(*numbers)
        elif command == "Z":
            path.closeSubpath()
        elif command == "R":
            x, y, w, h, radius = numbers
            path.addRoundedRect(QRectF(x, y, w, h), radius, radius)
    return path
