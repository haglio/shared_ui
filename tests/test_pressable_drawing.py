"""shared_ui.PressableDrawing: a drawing painted elsewhere, shown, and the pointer handed back."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from shared_ui.pressable_drawing import PressableDrawing


class _Pointer:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def press(self, x: int, y: int) -> None:
        self.calls.append(("press", x, y))

    def move(self, x: int, y: int) -> None:
        self.calls.append(("move", x, y))

    def release(self) -> None:
        self.calls.append(("release",))

    def leave(self) -> None:
        self.calls.append(("leave",))


RED = (200, 30, 30, 255)


def _move(widget, x: int, y: int) -> None:
    at = QPointF(x, y)
    QApplication.sendEvent(widget, QMouseEvent(
        QEvent.Type.MouseMove, at, widget.mapToGlobal(at), Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))


class _Drawing(PressableDrawing):
    size_painted = (20, 10)

    def drawing(self) -> tuple[bytes, tuple[int, int]]:
        width, height = self.size_painted
        return bytes(RED) * (width * height), (width, height)


def test_a_press_is_handed_on_where_it_landed():
    pointer = _Pointer()
    widget = _Drawing(pointer)
    widget.resize(40, 30)

    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=QPoint(5, 7))

    assert pointer.calls == [("press", 5, 7)]


def test_the_pointer_moving_is_handed_on_where_it_is():
    pointer = _Pointer()
    widget = _Drawing(pointer)
    widget.resize(40, 30)

    _move(widget, 12, 3)

    assert pointer.calls == [("move", 12, 3)]


def test_the_button_coming_up_is_handed_on():
    pointer = _Pointer()
    widget = _Drawing(pointer)
    widget.resize(40, 30)

    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=QPoint(5, 7))

    assert pointer.calls[-1] == ("release",)


def test_the_pointer_leaving_is_handed_on():
    pointer = _Pointer()
    widget = _Drawing(pointer)

    QApplication.sendEvent(widget, QEvent(QEvent.Type.Leave))

    assert pointer.calls == [("leave",)]


def test_it_shows_the_drawing_it_is_painted():
    widget = _Drawing(_Pointer())
    widget.resize(20, 10)

    shown = widget.grab().toImage()

    assert shown.pixelColor(3, 4).getRgb() == RED


def test_it_grows_to_hold_a_drawing_bigger_than_itself_and_never_shrinks():
    widget = _Drawing(_Pointer())
    widget.setFixedSize(5, 30)

    widget.grab()

    assert (widget.width(), widget.height()) == (20, 30)


class _Counted(_Drawing):
    def __init__(self, pointer) -> None:
        super().__init__(pointer)
        self.updates = 0

    def update(self) -> None:
        self.updates += 1
        super().update()


def test_it_repaints_after_a_press_a_move_and_a_leave_since_each_can_change_the_drawing():
    widget = _Counted(_Pointer())
    widget.resize(40, 30)

    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=QPoint(5, 7))
    _move(widget, 12, 3)
    QApplication.sendEvent(widget, QEvent(QEvent.Type.Leave))

    assert widget.updates == 3
