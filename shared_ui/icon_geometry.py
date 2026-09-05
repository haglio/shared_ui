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
# The bolt and the ring it bursts out of.  The ring is centered and broken where
# the bolt crosses it, top-right and bottom-left, so the bolt reads as passing
# THROUGH rather than as a scribble laid on top of a circle -- the gaps are what
# make the two one mark.  Kept in canvas units here so both are stated against
# one center: the ring's radius, and the angles its two arcs stop at.
_BOLT_RING = (8.5, 8.5, 31.0, 31.0)   # center (24, 24), radius 15.5
_BOLT_RING_ARC = 148.0                # each arc's span; the two gaps take the rest
_BOLT_RING_STROKE = 4.2               # thinner than the default: at the full weight
                                      # the ring closes on the bolt and the two
                                      # merge into one blob at button size


def _bolt_ring() -> tuple:
    """A lightning bolt bursting out of a broken ring -- run this by itself.

    The ring says "keeps going" and the bolt says "on its own", which together
    are what an unattended, self-restarting run is.  The bolt is a solid, and it
    is what the eye lands on: the ring alone would be another circular arrow, and
    undo and redo already wear one two buttons away.  Its points are left hard --
    a bolt is its points, and rounding them off costs the mark the very thing
    that tells it apart from the arcs beside it.
    """
    return (
        # Over the top and down the left; under the bottom and up the right.
        Arc(*_BOLT_RING, 78, _BOLT_RING_ARC, _BOLT_RING_STROKE),
        Arc(*_BOLT_RING, 258, _BOLT_RING_ARC, _BOLT_RING_STROKE),
        Polygon((
            (34, 6),                              # the top point, clear of the ring
            (28.5, 22.5), (36, 22.5),             # in to the waist, out to the ledge
            (14.5, 42),                           # the bottom point, clear of it too
            (20, 27.5), (12, 27.5),               # back up to the waist's other side
        )),
    )


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


# The two bars ``plus`` is drawn as, in one place: the outline below traces the
# very silhouette they fill, and ``minus`` is the horizontal one of them, so all
# three move together rather than being three hand-measured crosses.
_PLUS_BAR = 7.0     # how wide a bar is drawn
_PLUS_REACH = 15.0  # from the center to where a bar's stroke ends, before its cap


def _plus_outline() -> tuple:
    """The outline of the cross ``plus`` fills -- its hollow counterpart, the way
    ``star_outline`` answers ``star``.

    Twelve corners walked round the two bars' silhouette: out along an arm, back
    across its tip, and in to the notch where the next arm starts.  The tips are
    left square where the bars' own round caps are curved -- the pen's round join
    softens them, and matching those caps exactly would cost an arc per arm for a
    difference under a pixel at any size a badge is drawn at.

    Stroked thin, and thinner than the default: at the full weight the two arms
    close up and the inside of the mark reads as a heavier bar rather than as
    empty.
    """
    half, arm = _PLUS_BAR / 2, _PLUS_REACH + _PLUS_BAR / 2
    points = []
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):     # up, right, down, left
        px, py = -dy, dx                                  # that arm's own crossways
        for along, across in ((arm, -half), (arm, half), (half, half)):
            points.append((24 + dx * along + px * across,
                           24 + dy * along + py * across))
    return (Polygon(tuple(points), fill=False, width=2.4),)


def _enhance_filter() -> tuple:
    """The enhancement plus with a funnel over its corner -- show only the
    enhanced ones.

    Built the way ``reset`` is, out of the two marks it means at once: the plus
    is the very sign an enhanced picture wears in its corner across this family,
    and the funnel is what narrows a set to part of itself.  Either alone is a
    different control -- a bare plus is Enhance, which exists on the toolbar, and
    a bare funnel would not say WHAT it kept.

    The funnel sits down and right of the plus and crosses its lower arm rather
    than clearing it: two marks set apart in one box read as two controls
    crowded together, where one laid over the other reads as a single sign about
    a single thing.
    """
    plus = (16.0, 16.0)                                   # up in the box's corner
    bar, reach = 6.0, 10.0
    return (
        Line(plus[0], plus[1] - reach, plus[0], plus[1] + reach, bar),
        Line(plus[0] - reach, plus[1], plus[0] + reach, plus[1], bar),
        Polygon(((17, 26), (45, 26),                      # the funnel's mouth...
                 (33.5, 36), (33.5, 45),                  # ...down its right side
                 (28.5, 41), (28.5, 36)),                 # ...and back up its left
                fill=False, width=3.2),
    )


def _copy() -> tuple:
    """Two overlapping sheets -- copy this to the clipboard.

    The back sheet is drawn as the part of its outline the front sheet does not
    cover, rather than as a whole rectangle with a hole punched through it: a
    punched hole (a Clear-mode fill) works on an empty pixmap and erases whatever
    is underneath anywhere else, so the mark could not be laid over a chip or a
    thumbnail.  The gap matters either way -- two bare outlines at icon size read
    as a lattice rather than as one sheet in front of another.
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
        # Short and wide rather than long and narrow.  A head drawn along the
        # tangent at the stroke's own weight was barely visible at button size --
        # it read as the ring simply ending.  Widening it is what makes the mark
        # say "and back on again" instead of "off, with a nick in the circle".
        Polygon(((29.1, 9.8), (41.6, 12.3), (29.4, 22.5))),
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
    "bolt_ring": _bolt_ring(),
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
    "enhance_filter": _enhance_filter(),
    "expand_horizontal": _expand_horizontal(),
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
    # A pair: one bar and two, at one weight, so a speed-down and a speed-up
    # beside each other read as the same control twice rather than as two.
    "minus": (Line(24 - _PLUS_REACH, 24, 24 + _PLUS_REACH, 24, _PLUS_BAR),),
    "plus": (
        Line(24, 24 - _PLUS_REACH, 24, 24 + _PLUS_REACH, _PLUS_BAR),
        Line(24 - _PLUS_REACH, 24, 24 + _PLUS_REACH, 24, _PLUS_BAR),
    ),
    "plus_outline": _plus_outline(),
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
