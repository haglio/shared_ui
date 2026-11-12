from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QHBoxLayout, QWidget

from shared_ui.colors import TOGGLE_HANDLE, TOGGLE_OFF, TOGGLE_ON
from shared_ui.spacing import GAP_MEDIUM
from shared_ui.testing import appending_to, rendered_on_the_dark_ground
from shared_ui.toggle_geometry import TRACK
from shared_ui.toggle_switch import ToggleSwitch

_OFF_THE_SWITCH = 200


def _rendered(switch: ToggleSwitch) -> QImage:
    switch.resize(switch.sizeHint())
    return rendered_on_the_dark_ground(switch)


def _mean_ink(switch: ToggleSwitch) -> float:
    image = _rendered(switch)
    total = 0
    for x in range(image.width()):
        for y in range(image.height()):
            color = image.pixelColor(x, y)
            total += color.red() + color.green() + color.blue()
    return total / (image.width() * image.height())


def test_starts_unchecked_and_set_checked_round_trips():
    switch = ToggleSwitch()
    assert not switch.isChecked()
    switch.setChecked(True)
    assert switch.isChecked()
    switch.setChecked(False)
    assert not switch.isChecked()


def test_a_click_flips_the_state_and_announces_the_new_value():
    switch = ToggleSwitch()
    announced = []
    switch.clicked.connect(appending_to(announced))
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert switch.isChecked()
    assert announced == [True]
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert not switch.isChecked()
    assert announced == [True, False]


def test_only_the_left_button_flips_it():
    switch = ToggleSwitch()
    announced = []
    switch.clicked.connect(appending_to(announced))

    QTest.mouseClick(switch, Qt.MouseButton.RightButton)
    QTest.mouseClick(switch, Qt.MouseButton.MiddleButton)

    assert not switch.isChecked()
    assert announced == []


def test_a_press_dragged_off_the_switch_does_not_flip_it():
    switch = ToggleSwitch()
    switch.resize(switch.sizeHint())
    announced = []
    switch.clicked.connect(appending_to(announced))

    QTest.mousePress(switch, Qt.MouseButton.LeftButton, pos=QPoint(19, 10))
    QTest.mouseRelease(switch, Qt.MouseButton.LeftButton, pos=QPoint(_OFF_THE_SWITCH, 10))

    assert not switch.isChecked()
    assert announced == []


def test_a_labeled_switch_asks_for_room_for_its_word():
    bare = ToggleSwitch()
    labeled = ToggleSwitch("Auto-enhance new images")

    assert labeled.sizeHint().width() > bare.sizeHint().width()
    assert labeled.minimumSizeHint() == labeled.sizeHint()


def test_a_layout_takes_the_switch_at_its_own_size():
    host = QWidget()
    QHBoxLayout(host).addWidget(ToggleSwitch())
    host.resize(400, 200)
    host.layout().activate()

    switch = host.layout().itemAt(0).widget()

    assert switch.height() == switch.sizeHint().height()


def test_the_handle_and_track_show_which_state_it_is_in():
    off = _rendered(ToggleSwitch())
    assert off.pixelColor(10, 10) == TOGGLE_HANDLE
    assert off.pixelColor(28, 10) == TOGGLE_OFF

    on = ToggleSwitch()
    on.setChecked(True)
    on = _rendered(on)
    assert on.pixelColor(10, 10) == TOGGLE_ON
    assert on.pixelColor(28, 10) == TOGGLE_HANDLE


def test_a_disabled_switch_dims():
    on = ToggleSwitch()
    on.setChecked(True)
    off = ToggleSwitch()
    off.setChecked(True)
    off.setEnabled(False)

    assert _mean_ink(off) < _mean_ink(on)


def test_a_labeled_switch_asks_for_its_track_the_gap_and_its_words(qapp):
    switch = ToggleSwitch("Run")

    assert switch.sizeHint().width() == (
        TRACK[0] + GAP_MEDIUM + switch.fontMetrics().horizontalAdvance("Run"))
