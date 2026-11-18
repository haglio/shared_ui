from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QWidget

from shared_ui.colors import BG_SECONDARY
from shared_ui.fonts import FONT_UI, make_font
from shared_ui.icons import icon_then_text
from shared_ui.message_shape import (
    INFO,
    MESSAGE_INK,
    MESSAGE_PAD_H,
    MESSAGE_PAD_V,
    MESSAGE_RADIUS,
    MESSAGE_TYPE_SIZE,
)


def set_marked_text(label: QLabel, text: str, *, mark: str, color: QColor) -> None:
    if not mark:
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setText(text)
        return
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setText(icon_then_text(mark, text, color=color, size=label.fontMetrics().height()))


class MessageLabel(QLabel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFont(make_font(FONT_UI, MESSAGE_TYPE_SIZE, bold=True))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._said = ("", "", QColor(*MESSAGE_INK[INFO]))

    def say(self, text: str, *, kind: str = INFO, mark: str = "") -> None:
        ink = QColor(*MESSAGE_INK[kind])
        self.setStyleSheet(
            f"background-color: {BG_SECONDARY.name()};"
            f" color: {ink.name()}; border: 1px solid {ink.name()};"
            f" padding: {MESSAGE_PAD_V}px {MESSAGE_PAD_H}px; border-radius: {MESSAGE_RADIUS}px;"
        )
        self._said = (text, mark, ink)
        self._draw(text)

    def fit_into(self, room: int) -> None:
        text = self._said[0]
        self._draw(text)
        overhang = self.sizeHint().width() - room
        if overhang <= 0:
            return
        metrics = self.fontMetrics()
        self._draw(metrics.elidedText(text, Qt.TextElideMode.ElideRight,
                                      max(0, metrics.horizontalAdvance(text) - overhang - 1)))

    def _draw(self, text: str) -> None:
        _said, mark, ink = self._said
        set_marked_text(self, text, mark=mark, color=ink)
        self.ensurePolished()
        self.resize(self.sizeHint())
