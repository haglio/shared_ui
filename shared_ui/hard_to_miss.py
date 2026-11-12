from __future__ import annotations

import winsound
from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtCore import QPropertyAnimation, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QMessageBox, QWidget

from shared_ui.palette import BLACK

_FADE_MS = 200
_BLUR_DIVISOR = 16
_DIM = 0.55


def blurred_and_dimmed(pixmap: QPixmap, size: QSize) -> QPixmap:
    small = pixmap.scaled(max(1, size.width() // _BLUR_DIVISOR),
                          max(1, size.height() // _BLUR_DIVISOR),
                          Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    blurred = small.scaled(size, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
    painter = QPainter(blurred)
    painter.fillRect(blurred.rect(), QColor(*BLACK, int(255 * _DIM)))
    painter.end()
    return blurred


class FadedBackground(QWidget):
    def __init__(self, window: QWidget):
        super().__init__(window, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        area = window.geometry()
        self._grab = blurred_and_dimmed(_what_the_screen_shows(window, area), area.size())
        self.setGeometry(area)
        self.setWindowOpacity(0.0)
        self._fade_in = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setDuration(_FADE_MS)

    def showEvent(self, event):
        super().showEvent(event)
        self._fade_in.start()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._grab)


def _what_the_screen_shows(window: QWidget, area: QRect) -> QPixmap:
    screen = window.screen()
    origin = screen.geometry().topLeft()
    return screen.grabWindow(0, area.x() - origin.x(), area.y() - origin.y(),
                             area.width(), area.height())


@contextmanager
def hard_to_miss(window: QWidget) -> Iterator[None]:
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    if window.isMinimized():
        yield
        return
    faded = FadedBackground(window)
    faded.show()
    try:
        yield
    finally:
        faded.close()


def sure(window: QWidget, title: str, question: str) -> bool:
    with hard_to_miss(window):
        return QMessageBox.question(
            window, title, question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes
