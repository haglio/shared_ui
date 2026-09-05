"""shared_ui.ToggleSwitch: what a click does, and what the user sees."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QHBoxLayout, QWidget

from shared_ui.colors import BG_PRIMARY, TOGGLE_KNOB, TOGGLE_OFF, TOGGLE_ON
from shared_ui.toggle_switch import ToggleSwitch

_OFF_THE_SWITCH = 200


def _rendered(switch: ToggleSwitch) -> QImage:
    """The switch on the dark ground it sits on in every app -- the widget's
    own window background left out, since under the offscreen backend that
    is a light gray no app ever shows behind it."""
    switch.resize(switch.sizeHint())
    image = QImage(switch.size(), QImage.Format.Format_ARGB32)
    image.fill(BG_PRIMARY)
    switch.render(image, flags=QWidget.RenderFlag.DrawChildren)
    return image


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
    switch.clicked.connect(announced.append)
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert switch.isChecked()
    assert announced == [True]
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert not switch.isChecked()
    assert announced == [True, False]


def test_only_the_left_button_flips_it():
    """Where this switch is a pipeline's pause control, a right-click on it
    used to stop the schedule -- and a right-click is what a user does looking
    for a context menu."""
    switch = ToggleSwitch()
    announced = []
    switch.clicked.connect(announced.append)

    QTest.mouseClick(switch, Qt.MouseButton.RightButton)
    QTest.mouseClick(switch, Qt.MouseButton.MiddleButton)

    assert not switch.isChecked()
    assert announced == []


def test_a_press_dragged_off_the_switch_does_not_flip_it():
    """The other half of the button protocol: a press is not a click until it
    is released on the widget, which is how a user takes back a click they did
    not mean."""
    switch = ToggleSwitch()
    switch.resize(switch.sizeHint())
    announced = []
    switch.clicked.connect(announced.append)

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


def test_the_knob_and_track_show_which_state_it_is_in():
    """The paint is the only thing that tells the user the state: on is the
    family's blue track with the knob right, off the muted track, knob left."""
    off = _rendered(ToggleSwitch())
    assert off.pixelColor(10, 10) == TOGGLE_KNOB       # knob left
    assert off.pixelColor(28, 10) == TOGGLE_OFF        # muted track

    on = ToggleSwitch()
    on.setChecked(True)
    on = _rendered(on)
    assert on.pixelColor(10, 10) == TOGGLE_ON          # blue track
    assert on.pixelColor(28, 10) == TOGGLE_KNOB        # knob right


def test_a_disabled_switch_dims():
    # It paints itself, so nothing else would have dimmed it -- and a switch
    # that still looks on inside a panel gone dark is the one thing that says
    # the panel is still live.
    on = ToggleSwitch()
    on.setChecked(True)
    off = ToggleSwitch()
    off.setChecked(True)
    off.setEnabled(False)

    assert _mean_ink(off) < _mean_ink(on)
