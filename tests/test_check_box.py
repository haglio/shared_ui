"""shared_ui.CheckBox paints a real ticked box.

The native Windows dark indicator -- once a Qt stylesheet touches the
checkbox -- collapses to a bare chevron that reads as a down-caret.  This
widget draws its own indicator instead.  The tests render it and sample
pixels in the indicator region: checked = a light tick on an accent-filled
box; unchecked = an empty dark box with no tick.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QWidget

from shared_ui.check_box import _BOX, CheckBox
from shared_ui.colors import BG_PRIMARY, BLUE


def _rendered(cb):
    """The widget on the dark canvas these checkboxes always sit on, with the
    window background suppressed (``DrawChildren`` only).  A bare ``grab()``
    instead paints every uncovered pixel with the palette's Window colour, which
    is dark on native Windows but light under Qt's offscreen backend; that light
    backing read as hundreds of phantom "tick" pixels, so a count depended on
    the platform rather than on the widget."""
    pix = QPixmap(cb.size())
    pix.fill(BG_PRIMARY)
    cb.render(pix, flags=QWidget.RenderFlag.DrawChildren)
    return pix.toImage()


def _classify(cb):
    """Tally indicator-region pixels by kind (accent fill / light tick / dark box)."""
    img = _rendered(cb)
    blue = white = dark = 0
    for x in range(_BOX + 3):
        for y in range(cb.height()):
            c = QColor(img.pixel(x, y))
            r, g, b = c.red(), c.green(), c.blue()
            if abs(r - BLUE.red()) < 50 and abs(g - BLUE.green()) < 50 and abs(b - BLUE.blue()) < 50:
                blue += 1
            elif r > 200 and g > 200 and b > 200:
                white += 1
            elif r < 80 and g < 80 and b < 80:
                dark += 1
    return blue, white, dark


def _brightest_label_pixel(cb) -> int:
    """The brightest channel value anywhere right of the box: the label's ink."""
    img = _rendered(cb)
    return max(QColor(img.pixel(x, y)).red()
               for x in range(_BOX + 8, cb.width()) for y in range(cb.height()))


def test_checked_draws_light_tick_on_filled_box():
    cb = CheckBox("Random")
    cb.setChecked(True)
    cb.resize(140, 24)
    blue, white, _ = _classify(cb)
    assert blue > 30      # a solid accent fill...
    assert white > 4      # ...with a light check mark stroked over it


def test_unchecked_draws_empty_box_no_tick():
    cb = CheckBox("Random")
    cb.setChecked(False)
    cb.resize(140, 24)
    blue, white, dark = _classify(cb)
    assert blue == 0      # no accent fill
    assert white == 0     # no tick
    assert dark > 30      # an empty dark box


def test_a_box_that_is_on_but_cannot_be_changed_still_shows_its_tick():
    # Off the accent -- nothing here can be clicked -- and onto the ground a
    # control that is on sits on, with the tick still on it.
    cb = CheckBox("Random")
    cb.setChecked(True)
    cb.setEnabled(False)
    cb.resize(140, 24)
    blue, white, _ = _classify(cb)
    assert blue == 0
    assert white > 4


def test_a_box_that_cannot_be_changed_mutes_its_label():
    # The label is the body text tier while the box can be changed and the
    # muted tier while it cannot -- beside the tick, the one thing that says so.
    live = CheckBox("Random")
    live.resize(140, 24)
    dim = CheckBox("Random")
    dim.resize(140, 24)
    dim.setEnabled(False)

    assert _brightest_label_pixel(dim) < _brightest_label_pixel(live)


def test_the_hint_makes_room_for_the_box_and_the_label():
    cb = CheckBox("Random")

    hint = cb.sizeHint()

    assert hint.width() >= _BOX + cb.fontMetrics().horizontalAdvance("Random")
    assert hint.height() >= _BOX + 4
    assert cb.minimumSizeHint() == hint
