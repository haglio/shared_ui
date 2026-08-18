"""Every icon in the family, as geometry -- no toolkit, no colors, no pixels.

The apps draw with two different things.  The desktop chrome is Qt, and paints
with QPainter; the players' HUDs are painted into the video frame with Pillow,
because an mpv overlay takes a bitmap and there is no Qt in a player process at
all.  While each side owned its own drawing of a mark, the two drifted -- the
microphone came out a different shape in each app, and the trash can on a HUD
had nothing to do with the trash can on a toolbar.

So the marks live here, as a list of primitives per glyph, and each side renders
them: :mod:`shared_ui.icons` through QPainter, :mod:`shared_ui.icons_pil`
through Pillow.  Neither renderer decides anything about the shape.  This module
imports nothing but ``math``, so a Pillow-only process never pulls in Qt and a
Qt-only one never pulls in Pillow.

Coordinates are in a :data:`CANVAS`-square box and the renderers scale from
there, so a mark keeps its proportions and its stroke weight whether it lands on
a 14px HUD button or a 96px panel.  Angles are Qt's convention -- degrees
counter-clockwise from 3 o'clock, given as a start and a span -- and the Pillow
renderer converts; one convention had to win, and the geometry was written
against this one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Every glyph is drawn to fill this box, inset a little from its edge so a round
# cap or a fat arrowhead still has room.  A mark that uses only the middle third
# of its canvas is a mark the eye can't find once the box is scaled onto a tree
# row: the empty margin is scaled down with it.
CANVAS = 48.0

# The default stroke, in canvas units.  Renderers scale it with the drawing, so
# a glyph at 14px carries under a third of this width and reads as the same mark
# rather than as a heavier one shrunk.
STROKE = 5.0


# ---------------------------------------------------------------------------
# The primitives.  Six shapes cover every mark here, and both renderers can draw
# all six -- which is the constraint that keeps the two in step.  A shape with
# ``fill`` set is a solid; otherwise it is stroked at ``width``.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = STROKE


@dataclass(frozen=True)
class Polyline:
    points: tuple[tuple[float, float], ...]
    width: float = STROKE


@dataclass(frozen=True)
class Polygon:
    """A closed shape, solid when *fill* is set and an outline otherwise.

    *round_radius* rounds a solid one's corners, by stroking its own outline at
    twice that width with round joins before filling it.  A play triangle drawn
    with hard points reads as sharper and lighter than the marks beside it, and
    a filled polygon is the one place this family's round caps and joins did not
    reach.
    """

    points: tuple[tuple[float, float], ...]
    fill: bool = True
    width: float = STROKE
    round_radius: float = 0.0


@dataclass(frozen=True)
class RoundedRect:
    x: float
    y: float
    w: float
    h: float
    radius: float
    fill: bool = False
    width: float = STROKE


@dataclass(frozen=True)
class Ellipse:
    cx: float
    cy: float
    rx: float
    ry: float
    fill: bool = False
    width: float = STROKE


@dataclass(frozen=True)
class Arc:
    """A stroked arc of the ellipse inscribed in ``(x, y, w, h)``.

    ``start`` and ``span`` are degrees counter-clockwise from 3 o'clock, the
    convention QPainter uses (in sixteenths, which the Qt renderer multiplies
    back in).  Pillow measures clockwise and takes two absolute angles, so its
    renderer converts.  Give a positive span and let the start go negative: a
    negative span means the same arc to Qt and the long way round to Pillow.
    """

    x: float
    y: float
    w: float
    h: float
    start: float
    span: float
    width: float = STROKE


# ---------------------------------------------------------------------------
# The marks
# ---------------------------------------------------------------------------
def _chevron(pointing_left: bool) -> tuple:
    """A left or right chevron, drawn corner to corner of the canvas."""
    near, far, top, bottom = 15, 31, 9, 39
    if pointing_left:
        return (Polyline(((far, top), (near, 24), (far, bottom))),)
    return (Polyline(((near, top), (far, 24), (near, bottom))),)


# The undo/redo arc: a ring broken across one upper quadrant, the arrowhead
# filling that break.  The two are one drawing mirrored about the canvas's
# vertical center line -- hence the coordinate pairs below summing to 48 -- so
# side by side they read as a direction each, not as two rings.  The head is
# deliberately huge and the arc stops short of it, so it stands in open space
# rather than merging into the stroke it caps; the small nub this replaced left
# the two telling apart only by which end of a circle a few pixels sat on.
_HISTORY_RING = (11, 13, 26, 26)  # center (24, 26), radius 13


def _history_arrow(forward: bool) -> tuple:
    if forward:
        return (
            Arc(*_HISTORY_RING, 80, 285),                  # break at the upper right
            Polygon(((39, 14), (24, 5), (24, 23))),
        )
    return (
        Arc(*_HISTORY_RING, 175, 285),                     # break at the upper left
        Polygon(((9, 14), (24, 5), (24, 23))),
    )


def _star(filled: bool) -> tuple:
    """A five-pointed star, solid or an outline of one."""
    cx, cy, outer, inner = 24, 25, 17, 7
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        radius = outer if index % 2 == 0 else inner
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    # The outline is thinner than the default stroke: at the full weight the
    # points close up and the star reads as a blob with dents.
    return (Polygon(tuple(points), fill=filled, width=3),)


def _copy() -> tuple:
    """Two overlapping sheets -- copy this to the clipboard.

    The back sheet is drawn as the part of its outline the front sheet does not
    cover, rather than as a whole rectangle with a hole punched through it.  Both
    apps used to punch: a Clear-mode fill, which works on an empty pixmap and
    erases whatever is underneath anywhere else, so neither copy of the mark
    could be laid over a chip or a thumbnail.  The gap matters either way -- two
    bare outlines at icon size read as a lattice rather than as one sheet in
    front of another.
    """
    radius = 3.5
    return (
        Line(16, 13.5, 16, 9.5),                       # back sheet, left edge
        Arc(16, 6, 7, 7, 90, 90),                      # its top-left corner
        Line(19.5, 6, 36.5, 6),                        # its top edge
        Arc(33, 6, 7, 7, 0, 90),                       # its top-right corner
        Line(40, 9.5, 40, 28.5),                       # its right edge
        Arc(33, 25, 7, 7, 270, 90),                    # its bottom-right corner
        Line(36.5, 32, 34.5, 32),                      # what is left of its bottom
        RoundedRect(8, 16, 24, 26, radius),            # the front sheet, whole
    )


def _loop() -> tuple:
    """Two arrows chasing each other around a rounded rectangle -- repeat this.

    Two arrows rather than one ring, because a ring is what undo and the reset
    badge already are; a circuit with a head at each end says "around and around"
    where a single arc says "back one step".  Each arrow is a horizontal run into
    a corner, ending in a head pointing along the way it was going.
    """
    return (
        Line(12, 13, 32, 13),                          # the upper run, left to right
        Arc(25, 13, 14, 14, 0, 90),                    # around the top-right corner
        Polygon(((34.5, 20), (43.5, 20), (39, 29))),   # and down into its head
        Line(36, 35, 16, 35),                          # the lower run, right to left
        Arc(9, 21, 14, 14, 180, 90),                   # around the bottom-left corner
        Polygon(((13.5, 28), (4.5, 28), (9, 19))),     # and up into its head
    )


def _reset() -> tuple:
    """A gear with a circular arrow at its corner -- put the settings back.

    The gear says "this is about the settings" and the arrow says "back to how
    they started"; either alone is a different control -- a bare gear is Settings
    and a bare circular arrow is Undo, both of which exist elsewhere in this
    family.
    """
    cx, cy, root, tip = 20.0, 20.0, 10.0, 15.0
    teeth = tuple(
        Line(cx + root * math.cos(a), cy + root * math.sin(a),
             cx + tip * math.cos(a), cy + tip * math.sin(a), 4.5)
        for a in (index * math.pi / 4 for index in range(8))
    )
    return (
        Ellipse(cx, cy, root, root, width=4.5),        # the gear's rim
        *teeth,
        Ellipse(cx, cy, 3.5, 3.5, width=3),            # its bore
        Arc(28, 28, 16, 16, 35, 250, 3.6),             # the circular arrow...
        Polygon(((45.5, 33), (39, 30.5), (41, 38))),   # ...and its head
    )


# The power mark's two parts, shared by quit and restart so the pair reads as one
# family: a ring broken at the top, and the stroke standing in that break.  Quit
# is the two of them; restart is the two of them with the ring running on into an
# arrowhead.  Drawn to the weight of a toolbar icon font's power symbol, which is
# what the apps' menus sat next to.
_POWER_RING = (9.0, 12.0, 30.0, 30.0)  # center (24, 27), radius 15
_POWER_STROKE = Line(24, 6, 24, 24)


def _power() -> tuple:
    """A ring broken at the top with a stroke standing in the break -- power.

    Off, quit, shut down: the mark every one of these apps' quit controls wears,
    so the same act looks the same whichever window it is in.
    """
    return (Arc(*_POWER_RING, 128, 284), _POWER_STROKE)


def _restart() -> tuple:
    """The power mark whose ring runs on into an arrowhead -- off, then on again.

    Not the plain circular arrow: that is undo's mark, and this is the control
    that takes the whole app down and brings it back.  It is built from quit's
    own ring and stroke, so the two sit together in a menu as obvious relatives
    rather than as two unrelated drawings.
    """
    return (
        Arc(*_POWER_RING, 128, 272),                          # the ring, stopping short
        Polygon(((30.4, 11.3), (39.3, 14.2), (31.7, 20.6))),  # where it runs on
        _POWER_STROKE,
    )


def _question() -> tuple:
    """A question mark -- the help control.

    Drawn rather than typed, for the reason every mark here is: set in the body
    face it came out a text character among icons, visibly lighter and smaller
    than the marks it sat beside.
    """
    return (
        Arc(14, 6, 20, 20, -25, 215),    # the hook: up the right, over, down the left
        Line(33.1, 20.2, 24, 31),        # the tail, sweeping in under it
        Ellipse(24, 40, 3, 3, fill=True),
    )


def _expand_horizontal() -> tuple:
    """A double-headed arrow lying flat -- widen this.

    Deliberately chunky.  Typed as a character it was a hairline beside the solid
    arrowheads of the transport controls, which made one control look like a
    different class of thing from its neighbors.
    """
    return (
        Line(15, 24, 33, 24, 6),
        Polygon(((5, 24), (17, 13), (17, 35))),
        Polygon(((43, 24), (31, 13), (31, 35))),
    )


GLYPHS: dict[str, tuple] = {
    "check": (
        Polyline(((10, 25), (19, 35), (38, 13)), 5.5),
    ),
    "chevron_left": _chevron(pointing_left=True),
    "chevron_right": _chevron(pointing_left=False),
    "clock": (                                            # hands at 12 and 3
        Ellipse(24, 24, 15, 15),
        Line(24, 24, 24, 13),
        Line(24, 24, 33, 24),
    ),
    "copy": _copy(),
    "cross": (
        Line(11, 11, 37, 37, 5.5),
        Line(37, 11, 11, 37, 5.5),
    ),
    "expand_horizontal": _expand_horizontal(),
    "die": (                                              # a five-pip face
        RoundedRect(8, 8, 32, 32, 7),
        *(Ellipse(cx, cy, 3.2, 3.2, fill=True)
          for cx, cy in ((17, 17), (31, 17), (24, 24), (17, 31), (31, 31))),
    ),
    "flask": (                                            # an Erlenmeyer, with liquid
        Polyline(((19, 8), (19, 18), (9, 38), (39, 38), (29, 18), (29, 8))),
        Line(16, 8, 32, 8),                               # the lip
        Polygon(((14, 29), (34, 29), (38, 36), (10, 36))),
    ),
    "folder": (
        Polyline(((8, 39), (8, 12), (20, 12), (24, 18), (40, 18), (40, 39), (8, 39))),
    ),
    "loop": _loop(),
    "mic": (                                              # capsule, cradle, stand
        RoundedRect(18, 6, 12, 21, 6, fill=True),
        Arc(11, 11, 26, 26, 200, 140),
        Line(24, 37, 24, 42),
        Line(17, 42, 31, 42),
    ),
    "photo": (                                            # a sun over a mountain
        RoundedRect(8, 12, 32, 24, 4, width=3.4),
        Ellipse(17, 21, 3.2, 3.2, fill=True),
        Polygon(((11, 34), (22, 22), (37, 34))),
    ),
    # The play triangle's corners are rounded, like the transport marks in an icon
    # font: hard points read as a sharper, lighter mark than the ones beside it.
    # Its ink sits right of the box's center because a triangle's weight does --
    # the centroid lands on 24, which is where the eye reads middle.
    "play": (Polygon(((15, 8), (15, 40), (39, 24)), round_radius=3),),
    "pause": (                                            # two bars, rounded to match
        RoundedRect(13, 7, 8.5, 34, 3.5, fill=True),
        RoundedRect(26.5, 7, 8.5, 34, 3.5, fill=True),
    ),
    "power": _power(),
    "plus": (
        Line(24, 9, 24, 39, 7),
        Line(9, 24, 39, 24, 7),
    ),
    "question": _question(),
    "redo_arrow": _history_arrow(forward=True),
    "reset": _reset(),
    "restart": _restart(),
    "slideshow": (                                        # a play triangle in a screen
        RoundedRect(8, 11, 32, 26, 4),
        Polygon(((20, 16), (20, 32), (33, 24))),
    ),
    "speaker": (                                          # a cone and two waves
        Polygon(((7, 18), (14, 18), (22, 9), (22, 39), (14, 30), (7, 30))),
        Arc(23, 16, 12, 16, -70, 140, 4.5),
        Arc(25, 8, 18, 32, -70, 140, 4.5),
    ),
    "star": _star(filled=True),
    "star_outline": _star(filled=False),
    "trash": (                                            # lid, handle, body, ridges
        Line(9, 15, 39, 15),
        Polyline(((18, 15), (18, 9), (30, 9), (30, 15))),
        Polyline(((13, 15), (16, 41), (32, 41), (35, 15))),
        Line(20, 21, 21, 36),
        Line(28, 21, 27, 36),
    ),
    "undo_arrow": _history_arrow(forward=False),
    "wave": (                                             # one cycle of a sine
        Arc(6, 11, 18, 26, 0, 180),
        Arc(24, 11, 18, 26, 180, 180),
    ),
}


def glyph_names() -> tuple[str, ...]:
    """Every mark the family can draw, sorted."""
    return tuple(sorted(GLYPHS))
