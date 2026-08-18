"""The family's icon glyphs -- one drawing of each mark, for every app.

Every app here used to paint its own glyphs, and they drifted: Fun Time's
microphone and Origenerator's ended up different shapes, which is plain to see
because the two sit on one screen at once -- the same control reading as two
different controls.  This module owns the geometry instead.  One drawing per
mark, and each app asks for it in the size and the color its own chrome wants.

Every glyph is drawn to a :data:`CANVAS`-square box and scaled from there, so a
mark keeps its proportions and its stroke weight whether it lands on a 16px tree
row or a 96px panel.  Callers take one of three routes:

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
business and it stays there.  This module ends at the geometry.
"""

from __future__ import annotations

import math

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from shared_ui.colors import TEXT_MUTED, TEXT_PRIMARY

# Every glyph is drawn to fill this box, inset a little from its edge so a round
# cap or a fat arrowhead still has room.  A mark that uses only the middle third
# of its canvas is a mark the eye can't find on a button: the glyph is scaled
# down to whatever the caller asked for, and the empty margin scales with it.
CANVAS = 48.0

# The default stroke, in canvas units.  Scaling the painter rather than the
# coordinates is what keeps this honest: the pen is not cosmetic, so a glyph
# drawn at 16px carries a third of this width and reads as the same mark rather
# than as a heavier one shrunk.
STROKE = 5.0


# ---------------------------------------------------------------------------
# Painting
# ---------------------------------------------------------------------------
def glyph_names() -> tuple[str, ...]:
    """Every mark this module can draw, sorted."""
    return tuple(sorted(_GLYPHS))


def draw_glyph(painter: QPainter, name: str, color, *,
               size: float = CANVAS, x: float = 0.0, y: float = 0.0) -> None:
    """Paint *name* through *painter*, in a *size*-square box at ``(x, y)``.

    The painter's own pen, brush, transform and hints are left as they were --
    a caller part-way through drawing a chip must not find its brush swapped
    out from under it.
    """
    draw = _GLYPHS[name]
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.translate(x, y)
    painter.scale(size / CANVAS, size / CANVAS)
    ink = QColor(color)
    pen = QPen(ink)
    pen.setWidthF(STROKE)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    draw(painter, ink)
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


def glyph_icon(name: str, *, color=None, disabled_color=None,
               size: int = int(CANVAS)) -> QIcon:
    """*name* as an icon carrying its normal and its disabled rendering.

    *color* tints the normal one -- a button that says what it does before its
    tooltip does -- and the disabled one stays the muted gray whatever that
    color is, so a button with nothing to act on reads as dead rather than as a
    dimmer shade of red.

    Drawn at *size* and left for Qt to scale down onto the button, so the edges
    stay crisp at whatever size the chrome ends up asking for.
    """
    icon = QIcon()
    icon.addPixmap(
        glyph_pixmap(name, size, TEXT_PRIMARY if color is None else color),
        QIcon.Mode.Normal,
    )
    icon.addPixmap(
        glyph_pixmap(name, size, TEXT_MUTED if disabled_color is None else disabled_color),
        QIcon.Mode.Disabled,
    )
    return icon


# ---------------------------------------------------------------------------
# The marks
# ---------------------------------------------------------------------------
def _chevron(painter: QPainter, _ink, *, pointing_left: bool) -> None:
    """A left or right chevron, drawn corner to corner of the canvas."""
    near, far, top, bottom = 15, 31, 9, 39
    if pointing_left:
        painter.drawPolyline(QPointF(far, top), QPointF(near, 24), QPointF(far, bottom))
    else:
        painter.drawPolyline(QPointF(near, top), QPointF(far, 24), QPointF(near, bottom))


# The undo/redo arc: a ring broken across one upper quadrant, the arrowhead
# filling that break.  The two are one drawing mirrored about the canvas's
# vertical center line -- hence the coordinate pairs below summing to 48 -- so
# side by side they read as a direction each, not as two rings.
_HISTORY_RING = QRectF(11, 13, 26, 26)  # center (24, 26), radius 13


def _history_arrow(painter: QPainter, ink, *, forward: bool) -> None:
    """A circular arrow curling back (undo) or on (redo).

    The head is deliberately huge -- as tall as the ring's radius and a third of
    the canvas wide -- and the arc stops short of it, so it stands in open space
    instead of merging into the stroke it caps.  A small triangle sitting on the
    ring as a nub leaves the two directions telling apart only by which end of a
    circle a few pixels are on, which at button size is no difference at all.
    """
    if forward:
        painter.drawArc(_HISTORY_RING, 80 * 16, 285 * 16)   # break at the upper right
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ink)
        painter.drawPolygon(QPointF(39, 14), QPointF(24, 5), QPointF(24, 23))
    else:
        painter.drawArc(_HISTORY_RING, 175 * 16, 285 * 16)  # break at the upper left
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ink)
        painter.drawPolygon(QPointF(9, 14), QPointF(24, 5), QPointF(24, 23))


def _die(painter: QPainter, ink) -> None:
    """A five-pip die face -- roll this again, and again."""
    painter.drawRoundedRect(QRectF(8, 8, 32, 32), 7, 7)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)
    for cx, cy in ((17, 17), (31, 17), (24, 24), (17, 31), (31, 31)):
        painter.drawEllipse(QPointF(cx, cy), 3.2, 3.2)


def _slideshow(painter: QPainter, ink) -> None:
    """A play triangle in a screen frame -- play this fullscreen."""
    painter.drawRoundedRect(QRectF(8, 11, 32, 26), 4, 4)                    # the screen
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)
    painter.drawPolygon(QPointF(20, 16), QPointF(20, 32), QPointF(33, 24))  # play triangle


def _plus(painter: QPainter, ink) -> None:
    """A bold plus filling the canvas -- add to this, or make more of it."""
    pen = QPen(ink)
    pen.setWidthF(7)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(24, 9), QPointF(24, 39))
    painter.drawLine(QPointF(9, 24), QPointF(39, 24))


def _mic(painter: QPainter, ink) -> None:
    """A microphone capsule in its cradle on a stand -- speak to the app.

    The one mark this module was written for: two apps drew it, the two drawings
    disagreed, and both are on screen together.  This is the shape they now
    both wear.
    """
    painter.setBrush(ink)
    painter.drawRoundedRect(QRectF(18, 6, 12, 21), 6, 6)          # the mic body
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(11, 11, 26, 26), 200 * 16, 140 * 16)   # the cradle
    painter.drawLine(QPointF(24, 37), QPointF(24, 42))            # the stand
    painter.drawLine(QPointF(17, 42), QPointF(31, 42))            # the base


def _wave(painter: QPainter, ink) -> None:
    """One cycle of a sine -- motion the app is sending somewhere."""
    pen = QPen(ink)
    pen.setWidthF(5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(6, 11, 18, 26), 0, 180 * 16)          # the crest
    painter.drawArc(QRectF(24, 11, 18, 26), 180 * 16, 180 * 16)  # the trough


def _speaker(painter: QPainter, ink) -> None:
    """A speaker cone with two waves coming off it -- sound is playing."""
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)
    painter.drawPolygon(QPointF(7, 18), QPointF(14, 18), QPointF(22, 9),
                        QPointF(22, 39), QPointF(14, 30), QPointF(7, 30))
    pen = QPen(ink)
    pen.setWidthF(4.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(23, 16, 12, 16), -70 * 16, 140 * 16)   # the near wave
    painter.drawArc(QRectF(25, 8, 18, 32), -70 * 16, 140 * 16)    # the far wave


def _trash(painter: QPainter, _ink) -> None:
    """A trash can: lid with a small handle over a lightly tapered body."""
    painter.drawLine(QPointF(9, 15), QPointF(39, 15))                     # lid
    painter.drawPolyline(QPointF(18, 15), QPointF(18, 9),
                         QPointF(30, 9), QPointF(30, 15))                 # handle
    painter.drawPolyline(QPointF(13, 15), QPointF(16, 41),
                         QPointF(32, 41), QPointF(35, 15))                # body
    painter.drawLine(QPointF(20, 21), QPointF(21, 36))                    # ridges
    painter.drawLine(QPointF(28, 21), QPointF(27, 36))


def _star(painter: QPainter, ink, *, filled: bool) -> None:
    """A five-pointed star, solid or an outline of one."""
    cx, cy, outer, inner = 24, 25, 17, 7
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        radius = outer if index % 2 == 0 else inner
        points.append(QPointF(cx + radius * math.cos(angle),
                              cy + radius * math.sin(angle)))
    if filled:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ink)
    else:
        pen = QPen(ink)
        pen.setWidthF(3)  # a thinner outline than the default stroke
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
    painter.drawPolygon(*points)


def _clock(painter: QPainter, _ink) -> None:
    """A round clock face with two hands, at 12 and 3 -- recency."""
    painter.drawEllipse(QRectF(9, 9, 30, 30))
    painter.drawLine(QPointF(24, 24), QPointF(24, 13))   # hour hand, pointing up
    painter.drawLine(QPointF(24, 24), QPointF(33, 24))   # minute hand, to the right


def _flask(painter: QPainter, ink) -> None:
    """An Erlenmeyer flask with liquid in it -- an experiment."""
    painter.drawPolyline(                                # neck and cone, one outline
        QPointF(19, 8), QPointF(19, 18), QPointF(9, 38),
        QPointF(39, 38), QPointF(29, 18), QPointF(29, 8),
    )
    painter.drawLine(QPointF(16, 8), QPointF(32, 8))     # the lip
    painter.setPen(Qt.PenStyle.NoPen)                    # the liquid, a filled band
    painter.setBrush(ink)
    painter.drawPolygon(QPointF(14, 29), QPointF(34, 29),
                        QPointF(38, 36), QPointF(10, 36))


def _folder(painter: QPainter, _ink) -> None:
    """A tabbed folder outline."""
    painter.drawPolyline(
        QPointF(8, 39), QPointF(8, 12), QPointF(20, 12), QPointF(24, 18),
        QPointF(40, 18), QPointF(40, 39), QPointF(8, 39),
    )


def _play(painter: QPainter, ink) -> None:
    """A filled play triangle -- the universal "this is a video" mark.

    Its ink sits right of the box's center because a triangle's weight does: the
    centroid lands on 24, which is where the eye reads the middle.
    """
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)
    painter.drawPolygon(QPointF(15, 8), QPointF(15, 40), QPointF(39, 24))


def _photo(painter: QPainter, ink) -> None:
    """A framed photo -- a sun over a mountain -- the "this is an image" mark."""
    pen = QPen(ink)
    pen.setWidthF(3.4)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(8, 12, 32, 24), 4, 4)   # the picture frame
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)
    painter.drawEllipse(QPointF(17, 21), 3.2, 3.2)         # the sun, upper-left
    painter.drawPolygon(QPointF(11, 34), QPointF(22, 22),  # a single mountain peak
                        QPointF(37, 34))


def _copy(painter: QPainter, _ink) -> None:
    """Two overlapping sheets -- copy this to the clipboard.

    The back sheet is CLIPPED around the front one rather than erased out from
    under it.  Erasing (a Clear-mode fill, which is how the apps each did this)
    punches a hole through whatever is already painted underneath, so the mark
    could not be laid over a chip or a thumbnail; clipping only limits what this
    drawing paints, and leaves the ground alone.  The gap matters either way --
    two bare outlines at icon size read as a lattice rather than as one sheet in
    front of another.
    """
    front = QRectF(8, 16, 24, 26)
    back = QRectF(16, 6, 24, 26)
    radius = 3.5
    gap = 2.5

    everywhere = QPainterPath()
    everywhere.addRect(QRectF(-CANVAS, -CANVAS, 3 * CANVAS, 3 * CANVAS))
    around_the_front = QPainterPath()
    around_the_front.addRoundedRect(front.adjusted(-gap, -gap, gap, gap),
                                    radius + gap, radius + gap)
    painter.save()
    painter.setClipPath(everywhere.subtracted(around_the_front),
                        Qt.ClipOperation.IntersectClip)
    painter.drawRoundedRect(back, radius, radius)
    painter.restore()
    painter.drawRoundedRect(front, radius, radius)


def _check(painter: QPainter, ink) -> None:
    """A check mark -- yes, keep it."""
    painter.setPen(_line_art_pen(ink))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPolyline(QPointF(10, 25), QPointF(19, 35), QPointF(38, 13))


def _cross(painter: QPainter, ink) -> None:
    """Two crossed strokes -- no, reject it."""
    painter.setPen(_line_art_pen(ink))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(QPointF(11, 11), QPointF(37, 37))
    painter.drawLine(QPointF(37, 11), QPointF(11, 37))


def _line_art_pen(ink) -> QPen:
    """The weight the check and the cross share, so the pair reads as one set."""
    pen = QPen(ink)
    pen.setWidthF(5.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


# Every mark by name.  Directional and filled/outline pairs are separate entries
# rather than one entry with a flag: a caller naming "chevron_left" cannot ask
# for a chevron and forget to say which way, and the registry stays a flat list
# a test can walk end to end.
_GLYPHS = {
    "check": _check,
    "chevron_left": lambda p, ink: _chevron(p, ink, pointing_left=True),
    "chevron_right": lambda p, ink: _chevron(p, ink, pointing_left=False),
    "clock": _clock,
    "copy": _copy,
    "cross": _cross,
    "die": _die,
    "flask": _flask,
    "folder": _folder,
    "mic": _mic,
    "photo": _photo,
    "play": _play,
    "plus": _plus,
    "redo_arrow": lambda p, ink: _history_arrow(p, ink, forward=True),
    "slideshow": _slideshow,
    "speaker": _speaker,
    "star": lambda p, ink: _star(p, ink, filled=True),
    "star_outline": lambda p, ink: _star(p, ink, filled=False),
    "trash": _trash,
    "undo_arrow": lambda p, ink: _history_arrow(p, ink, forward=False),
    "wave": _wave,
}
