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

from shared_ui.check_box import CheckBox, _BOX
from shared_ui.colors import BLUE, BG_PRIMARY


def _classify(cb):
    """Tally indicator-region pixels by kind (accent fill / light tick / dark box).

    The widget is rendered onto a pixmap pre-filled with ``BG_PRIMARY`` -- the
    dark canvas these checkboxes always sit on -- with the window background
    suppressed (``DrawChildren`` only).  A bare ``grab()`` instead paints every
    uncovered pixel with the palette's Window colour, which is dark on native
    Windows but light under Qt's offscreen backend; that light backing read as
    hundreds of phantom "tick" pixels, so ``white`` depended on the platform
    rather than on the widget.  Rendering on a fixed dark backing keeps ``white``
    measuring only the real tick and makes the counts identical everywhere.
    """
    pix = QPixmap(cb.size())
    pix.fill(BG_PRIMARY)
    cb.render(pix, flags=QWidget.RenderFlag.DrawChildren)
    img = pix.toImage()
    blue = white = dark = 0
    for x in range(0, _BOX + 3):
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


def test_click_toggles_checked_state():
    cb = CheckBox("Random")
    assert cb.isChecked() is False
    cb.click()
    assert cb.isChecked() is True
