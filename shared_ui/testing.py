"""What a family suite uses to put the pointer on a widget it has shown.

Offscreen, the screen hands a point to the window that was shown there first,
so a window an earlier test left up takes the pointer from one shown under it:
a widget is moved clear of every other window before the pointer goes to it.
And a press an earlier test never let go of keeps the pointer's own moves from
reaching any widget, while a push button lights only on a move: the widget
under the pointer is handed one directly.
"""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PyQt6.QtGui import QCursor, QMouseEvent
from PyQt6.QtWidgets import QApplication, QWidget


def ground(widget: QWidget) -> str:
    """The color *widget* is drawn on, just inside its left edge."""
    drawn = widget.grab().toImage()
    return drawn.pixelColor(3, drawn.height() // 2).name()


class Pointer:
    def __init__(self) -> None:
        self._resting = QCursor.pos()

    def off(self, widget: QWidget) -> None:
        window = widget.window()
        _move_clear_of_every_other_window(window)
        corner = QApplication.primaryScreen().geometry().topLeft()
        spot = window.frameGeometry()
        past_it = spot.topLeft() + QPoint(spot.width(), spot.height())
        _put_the_pointer_at(past_it if spot.contains(corner) else corner)

    def on(self, widget: QWidget, at: QPoint | None = None) -> None:
        at = at if at is not None else widget.rect().center()
        _put_the_pointer_at(widget.mapToGlobal(at))
        under = widget.childAt(at) or widget
        QApplication.sendEvent(under, QMouseEvent(
            QEvent.Type.MouseMove, QPointF(under.mapFrom(widget, at)), QPointF(widget.mapToGlobal(at)),
            Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()

    def put_back(self) -> None:
        _put_the_pointer_at(self._resting)


def _put_the_pointer_at(point: QPoint) -> None:
    QCursor.setPos(point)
    QApplication.processEvents()


def _move_clear_of_every_other_window(window: QWidget) -> None:
    screen = QApplication.primaryScreen().geometry()
    taken = [other.frameGeometry() for other in QApplication.topLevelWidgets()
             if other.isVisible() and other is not window]
    size = window.frameGeometry().size()
    for y in range(screen.y(), screen.y() + screen.height() - size.height(), 10):
        for x in range(screen.x(), screen.x() + screen.width() - size.width(), 10):
            if not any(QRect(QPoint(x, y), size).intersects(other) for other in taken):
                window.move(x, y)
                QApplication.processEvents()
                return
    raise AssertionError("windows earlier tests left up cover every spot on the screen")
