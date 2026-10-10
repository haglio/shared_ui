"""Every icon in the family, as geometry -- no toolkit, no colors, no pixels.

The apps draw with two different things.  The desktop chrome is Qt, and paints
with QPainter; the players' HUDs are painted into the video frame with Pillow,
because an mpv overlay takes a bitmap and there is no Qt in a player process at
all.  A mark drawn twice, once per side, is a mark that comes out two shapes.

So the marks live here, as a list of primitives per glyph, and each side renders
them: :mod:`shared_ui.icons` through QPainter, :mod:`shared_ui.icons_pil`
through Pillow.  Neither renderer decides anything about the shape.

Coordinates are in a :data:`CANVAS`-square frame and the renderers scale from
there, so a mark keeps its proportions and its pen weight whether it lands on
a 14px HUD button or a 96px panel.  Angles are Qt's convention -- degrees
counter-clockwise from 3 o'clock, given as a start and a span -- and the Pillow
renderer converts; one convention had to win, and the geometry was written
against this one.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

# Every glyph is drawn to fill this frame, inset a little from its edge so a round
# cap or a fat arrowhead still has room.  A mark that uses only the middle third
# of its canvas is a mark the eye can't find once the frame is scaled onto a tree
# row: the empty margin is scaled down with it.
CANVAS = 48.0

# The default pen width, in canvas units.  Renderers scale it with the drawing, so
# a glyph at 14px carries under a third of this width and reads as the same mark
# rather than as a heavier one shrunk.
PEN_WIDTH = 5.0


# ---------------------------------------------------------------------------
# The primitives.  Six shapes cover every mark here, and both renderers can draw
# all six -- which is the constraint that keeps the two in step.  A shape with
# ``fill`` set is a solid; otherwise it is outlined at ``width``.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = PEN_WIDTH


@dataclass(frozen=True)
class Polyline:
    points: tuple[tuple[float, float], ...]
    width: float = PEN_WIDTH


@dataclass(frozen=True)
class Polygon:
    """A closed shape, solid when *fill* is set and an outline otherwise.

    *round_radius* rounds a solid one's corners, by drawing its own outline at
    twice that width with round joins before filling it.  A play triangle drawn
    with hard points reads as sharper and lighter than the marks beside it, and
    a filled polygon is the one place this family's round caps and joins did not
    reach.
    """

    points: tuple[tuple[float, float], ...]
    fill: bool = True
    width: float = PEN_WIDTH
    round_radius: float = 0.0


@dataclass(frozen=True)
class RoundedRect:
    x: float
    y: float
    w: float
    h: float
    radius: float
    fill: bool = False
    width: float = PEN_WIDTH


@dataclass(frozen=True)
class Ellipse:
    cx: float
    cy: float
    rx: float
    ry: float
    fill: bool = False
    width: float = PEN_WIDTH


@dataclass(frozen=True)
class Arc:
    """An outlined arc of the ellipse inscribed in ``(x, y, w, h)``.

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
    width: float = PEN_WIDTH


# ---------------------------------------------------------------------------
# The marks
# ---------------------------------------------------------------------------
def _chevron(pointing_left: bool) -> tuple:
    """A left or right chevron, drawn corner to corner of the canvas."""
    near, far, upper, lower = 15, 31, 9, 39
    if pointing_left:
        return (Polyline(((far, upper), (near, 24), (far, lower))),)
    return (Polyline(((near, upper), (far, 24), (near, lower))),)


# The undo/redo arc: a ring broken across one upper quadrant, the arrowhead
# filling that break.  The two are one drawing mirrored about the canvas's
# vertical center line -- hence the coordinate pairs below summing to 48 -- so
# side by side they read as a direction each, not as two rings.  The head is
# deliberately huge and the arc stops short of it, so it stands in open space
# rather than merging into the arc it caps -- which is what makes the two
# tellable apart at a glance rather than by which end of a circle it sits on.
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
    # The outline is thinner than the default pen width: at the full weight the
    # points close up and the star reads as a blob with dents.
    return (Polygon(tuple(points), fill=filled, width=3),)


# The two bars ``plus`` is drawn as, in one place: the outline below traces the
# very silhouette they fill, and ``minus`` is the horizontal one of them, so all
# three move together rather than being three hand-measured crosses.
_PLUS_BAR = 7.0     # how wide a bar is drawn
_PLUS_REACH = 15.0  # from the center to where a bar's line ends, before its cap


def _plus_outline() -> tuple:
    """The outline of the cross ``plus`` fills -- its hollow counterpart, the way
    ``star_outline`` answers ``star``.

    Twelve corners walked round the two bars' silhouette: out along an arm, back
    across its tip, and in to the notch where the next arm starts.  The tips are
    left square where the bars' own round caps are curved -- the pen's round join
    softens them, and matching those caps exactly would cost an arc per arm for a
    difference under a pixel at any size a badge is drawn at.

    Outlined thin, and thinner than the default: at the full weight the two arms
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
    than clearing it: two marks set apart in one frame read as two controls
    crowded together, where one laid over the other reads as a single sign about
    a single thing.
    """
    plus = (16.0, 16.0)                                   # up in the frame's corner
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
    cover, rather than as a whole rectangle with a cutout punched through it: a
    punched cutout (a Clear-mode fill) works on an empty pixmap and erases
    whatever is underneath anywhere else, so the mark could not be laid over a
    chip or a thumbnail.  The gap matters either way -- two bare outlines at icon
    size read as a lattice rather than as one sheet in front of another.
    """
    radius = 3.5
    return (
        Line(16, 13.5, 16, 9.5),                       # back sheet, left edge
        Arc(16, 6, 7, 7, 90, 90),                      # its top-left corner
        Line(19.5, 6, 36.5, 6),                        # its top edge
        Arc(33, 6, 7, 7, 0, 90),                       # its top-right corner
        Line(40, 9.5, 40, 28.5),                       # its right edge
        Arc(33, 25, 7, 7, 270, 90),                    # its lower-right corner
        Line(36.5, 32, 34.5, 32),                      # what is left of its lower edge
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
        Arc(9, 21, 14, 14, 180, 90),                   # around the lower-left corner
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


def _power() -> tuple:
    ring_broken_at_the_top = Arc(9.0, 12.0, 30.0, 30.0, 128, 284)
    bar_standing_in_the_break = Line(24, 6, 24, 24)
    return (ring_broken_at_the_top, bar_standing_in_the_break)


def _toward_the_middle(value: float, scale: float) -> float:
    return CANVAS / 2 + (value - CANVAS / 2) * scale


def _shrunk_toward_the_middle(shapes: tuple, scale: float) -> tuple:
    def shrunk(shape):
        if isinstance(shape, Arc):
            return Arc(_toward_the_middle(shape.x, scale), _toward_the_middle(shape.y, scale),
                       shape.w * scale, shape.h * scale, shape.start, shape.span, shape.width * scale)
        return Line(_toward_the_middle(shape.x1, scale), _toward_the_middle(shape.y1, scale),
                    _toward_the_middle(shape.x2, scale), _toward_the_middle(shape.y2, scale),
                    shape.width * scale)

    return tuple(shrunk(shape) for shape in shapes)


def _restart() -> tuple:
    quit_at_three_quarters_size = _shrunk_toward_the_middle(_power(), 0.75)
    arrow_round_it_counterclockwise = Arc(3, 3, 42, 42, 110.8, 299.2, 3.5)
    its_head_pointing_into_the_gap_over_the_bar = Polygon(((29.8, 1.5), (42.0, 2.6), (34.3, 11.7)))
    return (*quit_at_three_quarters_size, arrow_round_it_counterclockwise,
            its_head_pointing_into_the_gap_over_the_bar)


def _question(scale: float = 1.0, pen: float = PEN_WIDTH) -> tuple:
    def toward_the_middle(value: float) -> float:
        return _toward_the_middle(value, scale)

    return (
        Arc(toward_the_middle(14), toward_the_middle(6), 20 * scale, 20 * scale, -25, 215, pen),
        Line(toward_the_middle(33.1), toward_the_middle(20.2), 24, toward_the_middle(31), pen),
        Ellipse(24, toward_the_middle(40), 0.6 * pen, 0.6 * pen, fill=True),
    )


STAND_IN = (RoundedRect(4, 4, 40, 40, 9, width=3.6), *_question(scale=0.68, pen=4.0))


_PAIR_LANES = (13.0, 35.0)
_PAIR_TAIL = 5.0
_PAIR_NECK = 32.0
_PAIR_TIP = 43.0
_PAIR_HALF_HEAD = 6.5
_PAIR_PEN = 4.5              # a shade under the default: two lines at full weight
                             # closed the gap between them at button size


def _shuffle() -> tuple:
    shapes: list = []
    for start, end in zip(_PAIR_LANES, reversed(_PAIR_LANES), strict=True):
        shapes.append(Line(_PAIR_TAIL, start, _PAIR_NECK, end, _PAIR_PEN))
        shapes.append(Polygon(((_PAIR_TIP, end),
                               (_PAIR_NECK, end - _PAIR_HALF_HEAD),
                               (_PAIR_NECK, end + _PAIR_HALF_HEAD))))
    return tuple(shapes)


def _calendar() -> tuple:
    return (
        RoundedRect(6, 10, 36, 32, 4, width=3.6),
        Line(6, 19.5, 42, 19.5, 3.6),
        Line(16, 5, 16, 13, 3.6),
        Line(32, 5, 32, 13, 3.6),
        RoundedRect(26, 26, 9, 9, 1.5, fill=True),
    )


_STACK_LEFT, _STACK_RIGHT = 9.0, 39.0
_LID_MIDDLE = 11.0
_RIM_CURVE = 5.0
_CYLINDER_HEIGHT = 9.0
_CYLINDERS = 3
_STACK_PEN = 3.6


def _database() -> tuple:
    radius = (_STACK_RIGHT - _STACK_LEFT) / 2
    rim_middles = [_LID_MIDDLE + n * _CYLINDER_HEIGHT for n in range(1, _CYLINDERS + 1)]
    return (
        Ellipse(_STACK_LEFT + radius, _LID_MIDDLE, radius, _RIM_CURVE, width=_STACK_PEN),
        *(Arc(_STACK_LEFT, middle - _RIM_CURVE, 2 * radius, 2 * _RIM_CURVE, 180, 180, _STACK_PEN)
          for middle in rim_middles),
        Line(_STACK_LEFT, _LID_MIDDLE, _STACK_LEFT, rim_middles[-1], _STACK_PEN),
        Line(_STACK_RIGHT, _LID_MIDDLE, _STACK_RIGHT, rim_middles[-1], _STACK_PEN),
    )


def _upright_arrow(lane: float, *, pointing_up: bool) -> tuple:
    def along(distance: float) -> float:
        return CANVAS - distance if pointing_up else distance

    neck = along(_PAIR_NECK)
    return (
        Line(lane, along(_PAIR_TAIL), lane, neck, _PAIR_PEN),
        Polygon(((lane, along(_PAIR_TIP)),
                 (lane - _PAIR_HALF_HEAD, neck),
                 (lane + _PAIR_HALF_HEAD, neck))),
    )


def _flip_ends() -> tuple:
    up_lane, down_lane = _PAIR_LANES
    return (*_upright_arrow(up_lane, pointing_up=True),
            *_upright_arrow(down_lane, pointing_up=False))


_TIMELINE = Line(5, 37.5, 43, 37.5, 3.4)
_CLIP_TOP = 12.0
_CLIP_HEIGHT = 18.0
_CLIPS_END = 17.0


def _clip_on_the_timeline(end: float) -> tuple:
    return (_TIMELINE,
            RoundedRect(_TIMELINE.x1, _CLIP_TOP, end - _TIMELINE.x1, _CLIP_HEIGHT, 3.5, fill=True))


_JUMP_SHORT_CLIP = RoundedRect(8, 5, 8, 10, 2.5, fill=True)
_JUMP_LONG_CLIP = RoundedRect(20, 5, 20, 10, 2.5, fill=True)
_JUMP_ARROW_Y = 31.0
_JUMP_STEM = 8.0
_JUMP_HALF_HEAD = 11.0


def _clip_scene_jump(to_scene: bool) -> tuple:
    tail, neck, tip = 16.0, 25.0, 35.0
    if not to_scene:
        tail, neck, tip = (CANVAS - x for x in (tail, neck, tip))
    return (
        _JUMP_SHORT_CLIP,
        _JUMP_LONG_CLIP,
        Line(tail, _JUMP_ARROW_Y, neck, _JUMP_ARROW_Y, _JUMP_STEM),
        Polygon(((tip, _JUMP_ARROW_Y),
                 (neck, _JUMP_ARROW_Y - _JUMP_HALF_HEAD),
                 (neck, _JUMP_ARROW_Y + _JUMP_HALF_HEAD))),
    )


def _compilation() -> tuple:
    """A stack of pages -- the set a clip belongs to, played in its own order.

    Three rather than the copy mark's two, and stepped evenly along a diagonal:
    a stack says "several, in order", where two sheets say "this one and a copy
    of it".
    """
    return tuple(
        RoundedRect(16 - 4 * step, 5 + 5.5 * step, 24, 26, 3, width=3.2)
        for step in range(3)
    )


def _headset() -> tuple:
    """A headset seen head-on: a visor with two lenses and a strap either side.

    The family's VR icon is its own letters, which say the app rather than the
    act; a control that means "put this on" wants the thing itself.
    """
    return (
        RoundedRect(6, 14, 36, 20, 8, width=3.6),
        Ellipse(16, 24, 5, 5, fill=True),
        Ellipse(32, 24, 5, 5, fill=True),
        Line(1, 21, 6, 21, 3.4),
        Line(42, 21, 47, 21, 3.4),
    )


def _monitor() -> tuple:
    """A desktop monitor: a screen on a stem and a foot.

    What the control OUT of the headset goes to, rather than a headset negated.
    A ring drawn across the visor is more line than a button this size can hold
    — at eighteen pixels it read as a smudge — where two rectangles and a bar
    stay legible all the way down.
    """
    return (
        RoundedRect(5, 9, 38, 26, 3, width=3.6),
        Line(24, 35, 24, 40, 3.6),
        Line(14, 41, 34, 41, 3.6),
    )


def _vr_hemisphere() -> tuple:
    """A gridded dome -- video that wraps around you rather than sitting flat."""
    return (
        Arc(4, 6, 40, 52, 0, 180, 3.6),      # the dome, over its equator
        Arc(4, 22, 40, 20, 180, 180, 3.6),   # the rim, coming toward you
        Arc(14, 6, 20, 52, 0, 180, 2.8),     # a meridian
        Arc(9, 14, 30, 16, 180, 180, 2.8),   # and a parallel
    )


def _flat_2d() -> tuple:
    """A gridded screen seen at an angle -- video that stays a rectangle.

    Leaning, because square-on it is a plain rectangle, and a plain rectangle
    beside a dome reads as a missing icon rather than as the flat one.
    """
    lean, top, lower = 10.0, 10.0, 38.0

    def edge(y: float) -> tuple[float, float]:
        shift = lean * (y - top) / (lower - top)
        return 14.0 - shift, 44.0 - shift

    left_top, right_top = edge(top)
    left_low, right_low = edge(lower)
    lines = []
    for fraction in (1 / 3, 2 / 3):
        y = top + (lower - top) * fraction
        left, right = edge(y)
        lines.append(Line(left, y, right, y, 2.6))
        lines.append(Line(left_top + (right_top - left_top) * fraction, top,
                          left_low + (right_low - left_low) * fraction, lower, 2.6))
    return (
        Polygon(((left_top, top), (right_top, top), (right_low, lower), (left_low, lower)),
                fill=False, width=3.4),
        *lines,
    )


def _versions() -> tuple:
    """Two pages offset along a diagonal, with a double-headed arrow across them.

    The copy mark is two sheets too, and stands square; this pair leans, and the
    arrow between them is what says the act is swapping one for the other rather
    than making a second.
    """
    return (
        RoundedRect(22, 5, 21, 26, 3, width=3.4),      # the other cut
        RoundedRect(5, 17, 21, 26, 3, width=3.4),      # the one on screen
        Line(15, 33, 33, 15, 4.0),                     # the swap, along the offset
        Polygon(((36, 12), (26, 13), (35, 22))),
        Polygon(((12, 36), (22, 35), (13, 26))),
    )


def _funscript_jump() -> tuple:
    """An arrow running into an F -- skip ahead to where the scripting starts.

    The F is the letter every funscripted thing in this family is marked with,
    and the arrow says the act is going TO it rather than switching it on.
    """
    return (
        Line(4, 24, 15, 24, 4.5),
        Polygon(((25, 24), (14, 17), (14, 31))),
        Line(31, 8, 31, 40, 4.5),                      # the F's stem
        Line(31, 8, 44, 8, 4.5),                       # its top bar
        Line(31, 22, 41, 22, 4.5),                     # and its waist
    )


# The four states of OSR2 control, as one drawing read four ways: the device from
# the side -- its column on the right, the sleeve riding up and down it on the arm
# between them -- with the sleeve at whichever end the hold settles it on.  An
# arrow points AT the sleeve for the two holds, from above for the one that
# settles it home and from below for the one that sends it away, and points away
# from it both ways for the release that lets it move again.  Control-off draws
# that same free sleeve with an X where each of release's arrows was: the device
# is not being held anywhere, it is simply not being driven.
_COLUMN = RoundedRect(28, 8, 15, 32, 3, width=3.4)
_SLEEVE_X, _SLEEVE_W, _SLEEVE_H = 6.0, 15.0, 13.0
_ARROW_X = 13.5      # the arrows run up the sleeve's own center line
_ARROW_HALF = 7.0    # half an arrowhead's width
_ARROW_PEN = 4.0


def _sleeve(top: float) -> tuple:
    """The sleeve at *top*, and the arm carrying it to the column."""
    middle = top + _SLEEVE_H / 2
    return (
        RoundedRect(_SLEEVE_X, top, _SLEEVE_W, _SLEEVE_H, 4, width=3.4),
        Line(_SLEEVE_X + _SLEEVE_W, middle, 28, middle, 3.0),
    )


def _hold_arrow(tip: float, base: float) -> tuple:
    """An arrowhead at *tip* with its stem running back from *base*."""
    tail = base + (base - tip) * 0.7
    return (
        Line(_ARROW_X, tail, _ARROW_X, base, _ARROW_PEN),
        Polygon(((_ARROW_X, tip), (_ARROW_X - _ARROW_HALF, base),
                 (_ARROW_X + _ARROW_HALF, base))),
    )


def _park() -> tuple:
    return (_COLUMN, *_sleeve(27), *_hold_arrow(23, 13))


def _retract() -> tuple:
    return (_COLUMN, *_sleeve(8), *_hold_arrow(25, 35))


def _release() -> tuple:
    return (_COLUMN, *_sleeve(17.5), *_hold_arrow(3, 12), *_hold_arrow(45, 36))


_CROSS_HALF = 6.0    # an X's arm, from its middle
_CROSS_PEN = 3.6     # a shade finer than an arrow's, which has a solid head


def _hold_cross(middle: float) -> tuple:
    """An X centered at *middle* on the sleeve's own center line.

    It takes the whole band between the sleeve and the frame's edge, which is
    what keeps it legible at a HUD button's size -- and keeps it off the sleeve,
    where an X overlapping the drawing read as a bow tie rather than as a mark
    beside it.
    """
    left, right = _ARROW_X - _CROSS_HALF, _ARROW_X + _CROSS_HALF
    upper, lower = middle - _CROSS_HALF, middle + _CROSS_HALF
    return (
        Line(left, upper, right, lower, _CROSS_PEN),
        Line(left, lower, right, upper, _CROSS_PEN),
    )


def _control_off() -> tuple:
    return (_COLUMN, *_sleeve(17.5), *_hold_cross(8), *_hold_cross(40))


def _quarter_offset() -> tuple:
    """A stacked one-quarter with an arrow beside it -- nudge the motion's phase.

    Stacked rather than the typed fraction so the mark is as tall as the ones
    beside it and leaves room for the arrow, which is what says which way the
    nudge goes: the phase only ever runs forward.
    """
    return (
        Polyline(((8, 8), (13, 4), (13, 20)), 4.5),    # the one
        Line(7, 19, 19, 19, 4.5),                      # standing on its foot
        Line(4, 24, 22, 24, 4.5),                      # the vinculum
        Polyline(((16, 28), (6, 39), (21, 39)), 4.5),  # the four
        Line(16, 31, 16, 44, 4.5),
        Polygon(((44, 24), (31, 15), (31, 33))),       # and which way it turns
    )


# The letter grid every app in this family is marked on: five cells square, each
# painted cell a solid block, adjacent ones merging into a bar.  The .ico files
# are drawn on it (:mod:`shared_ui.app_icon`) and the players stamp F-mode's
# letter off it, so a toolbar's copy has to be the same letter and not a
# letter drawn some other way.
_GRID_CELLS = 5
_GRID_INSET = 5.0
_GRID_UNIT = (CANVAS - 2 * _GRID_INSET) / _GRID_CELLS


def _grid_letter(rows: tuple[str, ...]) -> tuple:
    """The cells *rows* paints, as solid blocks on the family's letter grid."""
    blocks = []
    for row, line in enumerate(rows):
        for column, painted in enumerate(line):
            if painted != "#":
                continue
            x = _GRID_INSET + column * _GRID_UNIT
            y = _GRID_INSET + row * _GRID_UNIT
            blocks.append(Polygon((
                (x, y), (x + _GRID_UNIT, y),
                (x + _GRID_UNIT, y + _GRID_UNIT), (x, y + _GRID_UNIT),
            )))
    return tuple(blocks)


def _fmode() -> tuple:
    """F-mode's letter, on the grid the app icons are drawn on.

    The same cells the players stamp on their HUDs, so the one on a toolbar is
    that letter rather than one drawn some other way.
    """
    return _grid_letter(("#####", "#....", "#####", "#....", "#...."))


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
    "bolt": (
        Polygon(((34, 6), (28.5, 22.5), (36, 22.5), (14.5, 42), (20, 27.5), (12, 27.5))),
    ),
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
    "clip_to_scene": _clip_scene_jump(to_scene=True),
    "compilation": _compilation(),
    "control_off": _control_off(),
    "copy": _copy(),
    "cross": (
        Line(11, 11, 37, 37, 5.5),
        Line(37, 11, 11, 37, 5.5),
    ),
    "database": _database(),
    "enhance_filter": _enhance_filter(),
    "expand_horizontal": _expand_horizontal(),
    "flat_2d": _flat_2d(),
    "flip_ends": _flip_ends(),
    "flask": (                                            # an Erlenmeyer, with liquid
        Polyline(((19, 8), (19, 18), (9, 38), (39, 38), (29, 18), (29, 8))),
        Line(16, 8, 32, 8),                               # the lip
        Polygon(((14, 29), (34, 29), (38, 36), (10, 36))),
    ),
    "fmode": _fmode(),
    "folder": (
        Polyline(((8, 39), (8, 12), (20, 12), (24, 18), (40, 18), (40, 39), (8, 39))),
    ),
    "full": _clip_on_the_timeline(_TIMELINE.x2),
    "headset": _headset(),
    "latest": _calendar(),
    "funscript_jump": _funscript_jump(),
    "log": (
        RoundedRect(10, 5, 28, 38, 4, width=3.6),
        Line(17, 16, 31, 16, 3.6),
        Line(17, 24, 31, 24, 3.6),
        Line(17, 32, 26, 32, 3.6),
    ),
    "loop": _loop(),
    "monitor": _monitor(),
    "mic": (                                              # capsule, cradle, stand
        RoundedRect(18, 6, 12, 21, 6, fill=True),
        Arc(11, 11, 26, 26, 200, 140),
        Line(24, 37, 24, 42),
        Line(17, 42, 31, 42),
    ),
    "park": _park(),
    "photo": (                                            # a sun over a mountain
        RoundedRect(8, 12, 32, 24, 4, width=3.4),
        Ellipse(17, 21, 3.2, 3.2, fill=True),
        Polygon(((11, 34), (22, 22), (37, 34))),
    ),
    # The play triangle's corners are rounded, like the transport marks in an icon
    # font: hard points read as a sharper, lighter mark than the ones beside it.
    # Its ink sits right of the frame's center because a triangle's weight does --
    # the centroid lands on 24, which is where the eye reads middle.
    "play": (Polygon(((15, 8), (15, 40), (39, 24)), round_radius=3),),
    "pause": (                                            # two bars, rounded to match
        RoundedRect(13, 7, 8.5, 34, 3.5, fill=True),
        RoundedRect(26.5, 7, 8.5, 34, 3.5, fill=True),
    ),
    "power": _power(),
    "quarter_offset": _quarter_offset(),
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
    "release": _release(),
    "reset": _reset(),
    "restart": _restart(),
    "retract": _retract(),
    "scene_to_clip": _clip_scene_jump(to_scene=False),
    "clips": _clip_on_the_timeline(_CLIPS_END),
    "shuffle": _shuffle(),
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
    "versions": _versions(),
    "vr_hemisphere": _vr_hemisphere(),
    "wave": (                                             # one cycle of a sine
        Arc(6, 11, 18, 26, 0, 180),
        Arc(24, 11, 18, 26, 180, 180),
    ),
}

RENAMED_MARKS: dict[str, str] = {
    "clock_full": "full", "clock_short": "clips", "full_length": "full", "shorts": "clips",
}
GLYPHS.update({old: GLYPHS[new] for old, new in RENAMED_MARKS.items()})


def glyph_names() -> tuple[str, ...]:
    """Every mark the family can draw, sorted."""
    return tuple(sorted(GLYPHS))


_log = logging.getLogger(__name__)
_named_in_the_log: set[str] = set()


def shapes_of(name: str) -> tuple:
    if name in GLYPHS:
        return GLYPHS[name]
    if name not in _named_in_the_log:
        _named_in_the_log.add(name)
        _log.warning("shared_ui has no mark named %r, so its button shows the stand-in", name)
    return STAND_IN


_WHY_IT_WEARS_THE_STAND_IN = ("This button's picture is missing from this version of the app.\n"
                              "Updating the app brings it back.")


def tooltip_for(mark: str, tooltip: str) -> str:
    if mark in GLYPHS:
        return tooltip
    return "\n".join(line for line in (tooltip, _WHY_IT_WEARS_THE_STAND_IN) if line)
