from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from shared_ui.colors import BG_SECONDARY, BLUE
from shared_ui.testing import rendered_on_the_dark_ground
from shared_ui.tick_control import _INDICATOR, TickControl


def _classify(control):
    img = rendered_on_the_dark_ground(control)
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
    img = rendered_on_the_dark_ground(control)
    return max(QColor(img.pixel(x, y)).red()
               for x in range(_INDICATOR + 8, control.width())
               for y in range(control.height()))


def test_checked_draws_light_tick_on_filled_indicator():
    control = TickControl("Random")
    control.setChecked(True)
    control.resize(140, 24)
    blue, white, _ = _classify(control)
    assert blue > 30
    assert white > 4


def test_unchecked_draws_empty_indicator_no_tick():
    control = TickControl("Random")
    control.setChecked(False)
    control.resize(140, 24)
    blue, white, dark = _classify(control)
    assert blue == 0
    assert white == 0
    assert dark > 30


def test_a_control_that_is_on_but_cannot_be_changed_still_shows_its_tick():
    control = TickControl("Random")
    control.setChecked(True)
    control.setEnabled(False)
    control.resize(140, 24)
    blue, white, _ = _classify(control)
    assert blue == 0
    assert white > 4


def test_a_control_that_cannot_be_changed_mutes_its_label():
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


def test_an_empty_indicator_stands_on_the_raised_ground_rather_than_the_canvas():
    control = TickControl("Random")
    control.resize(140, 24)

    middle = rendered_on_the_dark_ground(control).pixelColor(_INDICATOR // 2, control.height() // 2)

    assert middle == BG_SECONDARY


def _half_checked():
    control = TickControl("Random")
    control.setCheckState(Qt.CheckState.PartiallyChecked)
    control.resize(140, 24)
    return control


def test_half_checked_fills_the_indicator_and_draws_a_level_bar_where_the_tick_goes():
    control = _half_checked()

    blue, white, _ = _classify(control)
    img = rendered_on_the_dark_ground(control)
    top = (control.height() - _INDICATOR) // 2
    bar_row = top + _INDICATOR // 2
    brightest_of = [max(QColor(img.pixel(x, y)).red() for x in range(_INDICATOR + 1))
                    for y in range(top, top + _INDICATOR)]

    assert blue > 30
    assert white > 4
    assert QColor(img.pixel(1 + _INDICATOR // 2, bar_row)).red() > 200
    assert sum(red > 200 for red in brightest_of) <= 3


def test_half_checked_that_cannot_be_changed_still_shows_its_bar():
    control = _half_checked()
    control.setEnabled(False)

    blue, white, _ = _classify(control)

    assert blue == 0
    assert white > 4


def test_a_press_on_half_checked_ticks_it():
    control = _half_checked()

    control.click()

    assert control.checkState() == Qt.CheckState.Checked


def test_presses_go_between_ticked_and_unticked_and_never_back_to_half_checked():
    control = _half_checked()
    control.click()

    control.click()
    assert control.checkState() == Qt.CheckState.Unchecked

    control.click()
    assert control.checkState() == Qt.CheckState.Checked


def test_a_press_says_which_way_it_went_as_any_tick_does():
    pressed = []
    control = _half_checked()
    control.clicked.connect(pressed.append)

    control.click()
    control.click()

    assert pressed == [True, False]
