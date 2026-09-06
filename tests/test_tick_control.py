"""shared_ui.TickControl paints a real ticked indicator.

The native Windows dark indicator -- once a Qt stylesheet touches the
control -- collapses to a bare chevron that reads as a down-caret.  This
widget draws its own indicator instead.  The tests render it and sample
pixels in the indicator region: checked = a light tick on an accent-filled
indicator; unchecked = an empty dark indicator with no tick.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QWidget

from shared_ui.colors import BG_PRIMARY, BLUE
from shared_ui.tick_control import _INDICATOR, TickControl


def _rendered(control):
    """The widget on the dark canvas these controls always sit on, with the
    window background suppressed (``DrawChildren`` only).  A bare ``grab()``
    instead paints every uncovered pixel with the palette's Window color, which
    is dark on native Windows but light under Qt's offscreen backend; that light
    backing read as hundreds of phantom "tick" pixels, so a count depended on
    the platform rather than on the widget."""
    pix = QPixmap(control.size())
    pix.fill(BG_PRIMARY)
    control.render(pix, flags=QWidget.RenderFlag.DrawChildren)
    return pix.toImage()


def _classify(control):
    """Tally indicator-region pixels by kind (accent fill / light tick / dark
    indicator)."""
    img = _rendered(control)
    blue = white = dark = 0
    for x in range(_INDICATOR + 3):
        for y in range(control.height()):
            c = QColor(img.pixel(x, y))
            r, g, b = c.red(), c.green(), c.blue()
            if abs(r - BLUE.red()) < 50 and abs(g - BLUE.green()) < 50 and abs(b - BLUE.blue()) < 50:
                blue += 1
            elif r > 200 and g > 200 and b > 200:
                white += 1
            elif r < 80 and g < 80 and b < 80:
                dark += 1
    return blue, white, dark


def _brightest_label_pixel(control) -> int:
    """The brightest channel value anywhere right of the indicator: the label's ink."""
    img = _rendered(control)
    return max(QColor(img.pixel(x, y)).red()
               for x in range(_INDICATOR + 8, control.width())
               for y in range(control.height()))


def test_checked_draws_light_tick_on_filled_indicator():
    control = TickControl("Random")
    control.setChecked(True)
    control.resize(140, 24)
    blue, white, _ = _classify(control)
    assert blue > 30      # a solid accent fill...
    assert white > 4      # ...with a light check mark drawn over it


def test_unchecked_draws_empty_indicator_no_tick():
    control = TickControl("Random")
    control.setChecked(False)
    control.resize(140, 24)
    blue, white, dark = _classify(control)
    assert blue == 0      # no accent fill
    assert white == 0     # no tick
    assert dark > 30      # an empty dark indicator


def test_a_control_that_is_on_but_cannot_be_changed_still_shows_its_tick():
    # Off the accent -- nothing here can be clicked -- and onto the ground a
    # control that is on sits on, with the tick still on it.
    control = TickControl("Random")
    control.setChecked(True)
    control.setEnabled(False)
    control.resize(140, 24)
    blue, white, _ = _classify(control)
    assert blue == 0
    assert white > 4


def test_a_control_that_cannot_be_changed_mutes_its_label():
    # The label is the body text tier while the control can be changed and the
    # muted tier while it cannot -- beside the tick, the one thing that says so.
    live = TickControl("Random")
    live.resize(140, 24)
    dim = TickControl("Random")
    dim.resize(140, 24)
    dim.setEnabled(False)

    assert _brightest_label_pixel(dim) < _brightest_label_pixel(live)


def test_the_hint_makes_room_for_the_indicator_and_the_label():
    control = TickControl("Random")

    hint = control.sizeHint()

    assert hint.width() >= _INDICATOR + control.fontMetrics().horizontalAdvance("Random")
    assert hint.height() >= _INDICATOR + 4
    assert control.minimumSizeHint() == hint
