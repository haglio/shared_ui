"""The shared glyphs: that each one draws, that they draw differently from each
other, and that the three routes to one produce the same mark.

That last part is the whole point of the module.  The apps reached for their
glyphs in different ways -- a toolbar wants a QIcon, a self-painted panel wants
a pixmap, a badge wants to paint into a chip it already has -- and while each
app answered that itself, the drawings drifted apart.  So the tests here lean
hardest on the routes agreeing.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from shared_ui import icons
from shared_ui.colors import GREEN, RED, TEXT_MUTED, TEXT_PRIMARY


def _blank(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap


def _ink_box(pixmap: QPixmap) -> tuple[int, int, int, int]:
    """The bounding box of what was drawn: ``(left, top, right, bottom)``."""
    image = pixmap.toImage()
    xs, ys = [], []
    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y).alpha() > 32:
                xs.append(x)
                ys.append(y)
    assert xs, "nothing was drawn"
    return min(xs), min(ys), max(xs), max(ys)


def _ink_pixels(pixmap: QPixmap) -> int:
    image = pixmap.toImage()
    return sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() > 32
    )


def test_every_registered_glyph_draws_something(qapp):
    # A name in the registry that paints nothing is worse than a missing one:
    # the caller gets a button with an empty square on it and no error.
    for name in icons.glyph_names():
        pixmap = icons.glyph_pixmap(name, 48, TEXT_PRIMARY)
        assert not pixmap.isNull(), name
        assert _ink_pixels(pixmap) > 0, name


def test_the_glyphs_are_all_different_marks(qapp):
    # Icon-only controls are only as good as the marks telling each other apart.
    drawn = {
        name: icons.glyph_pixmap(name, 48, TEXT_PRIMARY).toImage()
        for name in icons.glyph_names()
    }
    names = sorted(drawn)
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            assert drawn[first] != drawn[second], f"{first} and {second} draw alike"


# A mark whose whole identity is a single bar cannot fill a square and should not
# try: a minus stretched to be tall is a rectangle, not a minus. Named here one by
# one, so widening the exemption takes a decision rather than a shrug.
_ONE_BAR = {"minus"}


def test_every_glyph_fills_its_canvas(qapp):
    # A mark using only the middle of its box is a mark the eye can't find once
    # the box is scaled onto a 16px tree row -- the empty margin shrinks with it.
    # The long side has to carry most of the canvas; the short side is allowed to
    # be narrow, because some marks (a chevron) genuinely are.
    for name in set(icons.glyph_names()) - _ONE_BAR:
        left, top, right, bottom = _ink_box(icons.glyph_pixmap(name, 48, TEXT_PRIMARY))
        width, height = right - left, bottom - top
        assert max(width, height) >= 0.6 * 48, f"{name} is small in its box"
        assert min(width, height) >= 0.4 * 48, f"{name} is thin in its box"


def test_a_one_bar_mark_still_spans_its_canvas_the_long_way(qapp):
    # The exemption is for the SHORT side only. A minus that also stopped short
    # left to right would read as a hyphen dropped into an empty square.
    for name in _ONE_BAR:
        left, _top, right, _bottom = _ink_box(icons.glyph_pixmap(name, 48, TEXT_PRIMARY))
        assert right - left >= 0.6 * 48, f"{name} is short in its box"


def test_the_speed_pair_is_one_control_drawn_twice(qapp):
    # Minus and plus sit side by side on a speed control, so they have to be the
    # same bar at the same weight -- one of them with a second bar across it.
    from shared_ui.icon_geometry import GLYPHS

    assert set(GLYPHS["minus"]).issubset(set(GLYPHS["plus"]))


def test_every_glyph_sits_in_the_middle_of_its_canvas(qapp):
    # Marks are laid beside each other in a button bank, so one drawn off-center
    # reads as misaligned with its neighbors rather than as its own shape.
    for name in icons.glyph_names():
        left, top, right, bottom = _ink_box(icons.glyph_pixmap(name, 48, TEXT_PRIMARY))
        assert abs((left + right) / 2 - 24) <= 0.12 * 48, f"{name} sits off-center"
        assert abs((top + bottom) / 2 - 24) <= 0.12 * 48, f"{name} sits off-center"


def test_a_glyph_is_drawn_in_the_color_it_is_asked_for(qapp):
    # The apps tint marks to say what they do -- a delete in red, a star in the
    # green that means "bookmarked" across the family -- so the ink has to be
    # the color handed in rather than a fixed one.
    for color in (RED, GREEN, TEXT_PRIMARY):
        image = icons.glyph_pixmap("star", 48, color).toImage()
        assert image.pixelColor(24, 25) == color


def test_a_glyph_scales_to_the_size_it_is_asked_for(qapp):
    # Fun Time paints its bar's own panel size; Origenerator draws big and lets
    # Qt scale down.  Both get a square of exactly the side they named.
    for size in (16, 24, 48, 96):
        pixmap = icons.glyph_pixmap("mic", size, TEXT_PRIMARY)
        assert pixmap.size() == QSize(size, size)


def test_a_small_glyph_is_the_same_mark_rather_than_a_heavier_one(qapp):
    # The painter is scaled, not the coordinates, so the pen scales with the
    # drawing: the mark takes up the same share of its box at every size.  A
    # fixed stroke width instead leaves a 16px glyph a blob and a 96px one a
    # wireframe -- two marks rather than one shown large and small.
    sizes = (24, 48, 96)
    boxes = [_ink_box(icons.glyph_pixmap("mic", size, TEXT_PRIMARY)) for size in sizes]
    widths = [(right - left) / size for (left, _t, right, _b), size in zip(boxes, sizes)]
    heights = [(bottom - top) / size for (_l, top, _r, bottom), size in zip(boxes, sizes)]
    assert max(widths) - min(widths) < 0.06
    assert max(heights) - min(heights) < 0.06
    # And the ink stays a like share of the box.  Antialiasing fattens a small
    # glyph proportionally more than a large one, so this is a band, not equality.
    coverage = [
        _ink_pixels(icons.glyph_pixmap("mic", size, TEXT_PRIMARY)) / (size * size)
        for size in sizes
    ]
    assert max(coverage) < 1.3 * min(coverage)


def test_an_icon_carries_a_normal_and_a_dimmed_rendering(qapp):
    # Qt swaps to the disabled pixmap itself when a button goes dead, so both
    # have to be there and the dim one has to actually read as dim.
    icon = icons.glyph_icon("trash", color=RED)
    size = QSize(48, 48)
    normal = icon.pixmap(size, QIcon.Mode.Normal)
    disabled = icon.pixmap(size, QIcon.Mode.Disabled)
    assert _ink_pixels(normal) > 0
    assert _ink_pixels(disabled) > 0
    assert normal.toImage() != disabled.toImage()


def test_a_disabled_icon_is_the_muted_gray_whatever_its_color(qapp):
    # A colored button that dims to a paler version of its own color reads as a
    # lighter red rather than as a button with nothing to act on.
    for color in (RED, GREEN, None):
        icon = icons.glyph_icon("star", color=color)
        image = icon.pixmap(QSize(48, 48), QIcon.Mode.Disabled).toImage()
        assert image.pixelColor(24, 25) == TEXT_MUTED


def test_an_uncolored_icon_wears_the_chrome_text_color(qapp):
    icon = icons.glyph_icon("star")
    image = icon.pixmap(QSize(48, 48), QIcon.Mode.Normal).toImage()
    assert image.pixelColor(24, 25) == TEXT_PRIMARY


def test_the_pixmap_and_the_icon_draw_the_very_same_mark(qapp):
    # The mark Fun Time paints into its bar and the one Origenerator hands a
    # toolbar button are one drawing -- which is the whole reason this module
    # exists, since the two apps' microphones had drifted into different shapes.
    from_pixmap = icons.glyph_pixmap("mic", 48, TEXT_PRIMARY)
    from_icon = icons.glyph_icon("mic", size=48).pixmap(QSize(48, 48), QIcon.Mode.Normal)
    assert from_pixmap.toImage() == from_icon.toImage()


def test_painting_into_a_caller_s_painter_draws_that_same_mark_too(qapp):
    # The third route: a badge paints its chip, then asks for the mark on top.
    # It has to be the same drawing as the other two, in the place it asked for.
    direct = icons.glyph_pixmap("play", 48, TEXT_PRIMARY)
    composed = _blank(48)
    painter = QPainter(composed)
    icons.draw_glyph(painter, "play", TEXT_PRIMARY)
    painter.end()
    assert composed.toImage() == direct.toImage()


def test_a_glyph_lands_where_the_caller_placed_it(qapp):
    # A badge draws its mark inset into a chip, so the offset has to move the
    # whole drawing rather than clip it.
    canvas = _blank(48)
    painter = QPainter(canvas)
    icons.draw_glyph(painter, "star", TEXT_PRIMARY, size=24, x=12, y=12)
    painter.end()
    left, top, right, bottom = _ink_box(canvas)
    assert 12 <= left and right <= 36
    assert 12 <= top and bottom <= 36


def test_drawing_a_glyph_leaves_the_caller_s_painter_as_it_found_it(qapp):
    # A caller part-way through drawing a chip must not find its pen, brush or
    # transform swapped out underneath it -- the mark goes on top of the chip,
    # and whatever the caller draws next still comes out in its own colors.
    canvas = _blank(64)
    painter = QPainter(canvas)
    painter.translate(8, 8)
    painter.setPen(QPen(QColor(GREEN), 3))
    painter.setBrush(QColor(RED))
    icons.draw_glyph(painter, "clock", TEXT_PRIMARY, size=24)
    assert painter.pen().color() == QColor(GREEN)
    assert painter.pen().widthF() == 3
    assert painter.brush().color() == QColor(RED)
    assert painter.transform().dx() == 8 and painter.transform().dy() == 8
    painter.end()


def test_a_mark_drawn_over_a_chip_keeps_the_chip_underneath(qapp):
    # What the badge callers actually do: fill a chip, then lay the mark on it.
    # The glyph paints only its own ink, so the chip still shows around it.
    canvas = _blank(48)
    painter = QPainter(canvas)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(GREEN))
    painter.drawRoundedRect(QRectF(3, 3, 42, 42), 12, 12)
    icons.draw_glyph(painter, "play", RED, size=26, x=11, y=11)
    painter.end()
    image = canvas.toImage()
    assert image.pixelColor(6, 24) == QColor(GREEN)   # chip, clear of the mark
    assert image.pixelColor(0, 0).alpha() == 0        # outside the chip, still clear


def test_the_registry_is_what_glyph_names_reports(qapp):
    # Callers walk the names to build a bank of buttons, and the tests above walk
    # them to check every mark -- so a glyph added without a name is a glyph no
    # test ever renders.
    names = icons.glyph_names()
    assert names == tuple(sorted(names))
    assert "mic" in names
    for name in names:
        assert icons.glyph_pixmap(name, 24, TEXT_PRIMARY).size() == QSize(24, 24)


def test_the_canvas_and_stroke_are_stated_in_canvas_units(qapp):
    # Both are public: a caller composing a mark into its own drawing needs the
    # box the geometry is written against.
    assert icons.CANVAS == 48.0
    assert 0 < icons.STROKE < icons.CANVAS


def test_a_mark_never_erases_the_ground_it_is_drawn_on(qapp):
    # The copy mark holds a gap between its two sheets, and the apps each cut
    # that gap by erasing -- which works on an empty pixmap and punches a hole
    # through anything else.  Clipping is what makes the mark safe to lay over a
    # chip or a thumbnail, so the ground has to survive under every glyph.
    for name in icons.glyph_names():
        canvas = QPixmap(48, 48)
        canvas.fill(QColor(GREEN))
        painter = QPainter(canvas)
        icons.draw_glyph(painter, name, RED)
        painter.end()
        image = canvas.toImage()
        cleared = [
            (x, y)
            for y in range(48)
            for x in range(48)
            if image.pixelColor(x, y).alpha() < 255
        ]
        assert not cleared, f"{name} cleared {len(cleared)} px of what was under it"


def test_quit_and_restart_are_built_from_one_power_mark(qapp):
    from shared_ui.icon_geometry import GLYPHS, Arc, Line

    # They sit together in a menu, so they have to read as relatives rather than
    # as two unrelated drawings. Restart IS quit's ring and stroke, with the ring
    # running on into an arrowhead -- the same numbers, not merely a similar look.
    power = GLYPHS["power"]
    restart = GLYPHS["restart"]
    power_stroke = next(s for s in power if isinstance(s, Line))
    assert power_stroke in restart

    power_ring = next(s for s in power if isinstance(s, Arc))
    restart_ring = next(s for s in restart if isinstance(s, Arc))
    assert (power_ring.x, power_ring.y, power_ring.w, power_ring.h) ==         (restart_ring.x, restart_ring.y, restart_ring.w, restart_ring.h)
    assert power_ring.start == restart_ring.start
    assert restart_ring.span < power_ring.span   # it stops short, for the head


def test_the_transport_marks_have_rounded_corners(qapp):
    from shared_ui.icon_geometry import GLYPHS, Polygon

    # A play triangle with hard points reads as a sharper, lighter mark than the
    # ones beside it -- and beside an icon font's transport controls it plainly
    # was not the same drawing.
    triangle = next(s for s in GLYPHS["play"] if isinstance(s, Polygon))
    assert triangle.round_radius > 0

    # The rounding grows the mark, so it is visible in what is drawn rather than
    # only in the data.
    rounded = _ink_pixels(icons.glyph_pixmap("play", 48, TEXT_PRIMARY))
    bare = _ink_pixels(_render_shape(Polygon(triangle.points)))
    assert rounded > bare


def _render_shape(shape):
    """One geometry shape, drawn on its own -- for comparing against a glyph."""
    from shared_ui.icons import _draw

    pixmap = _blank(48)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    _draw(painter, shape, QColor(TEXT_PRIMARY))
    painter.end()
    return pixmap
