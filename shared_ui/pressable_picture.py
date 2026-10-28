"""A picture painted by something other than Qt, shown in a widget, with the
pointer handed back to whatever painted it, in the picture's own pixels."""

from __future__ import annotations

from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QWidget


class PressablePicture(QWidget):
    def __init__(self, pointer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pointer = pointer
        self.setMouseTracking(True)

    def picture(self) -> tuple[bytes, tuple[int, int]]:
        raise NotImplementedError

    def paintEvent(self, event) -> None:
        raw, (width, height) = self.picture()
        if width > self.width() or height > self.height():
            self.setFixedSize(max(width, self.width()), max(height, self.height()))
        painter = QPainter(self)
        painter.drawImage(0, 0, QImage(raw, width, height, QImage.Format.Format_RGBA8888))
        painter.end()

    def mousePressEvent(self, event) -> None:
        self._pointer.press(*_at(event))
        self.update()

    def mouseMoveEvent(self, event) -> None:
        self._pointer.move(*_at(event))
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._pointer.release()

    def leaveEvent(self, event) -> None:
        self._pointer.leave()
        self.update()
        super().leaveEvent(event)


def _at(event) -> tuple[int, int]:
    return int(event.position().x()), int(event.position().y())
