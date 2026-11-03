"""Painted rather than styled, because a Qt stylesheet cannot move a checkbox's indicator."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton

from shared_ui.colors import TEXT_SECONDARY, TOGGLE_HANDLE, TOGGLE_OFF, TOGGLE_ON
from shared_ui.spacing import GAP_MEDIUM
from shared_ui.toggle_geometry import HANDLE_INSET, TRACK, handle

_GAP = GAP_MEDIUM
_DISABLED_OPACITY = 0.4


class ToggleSwitch(QAbstractButton):

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self) -> QSize:
        width = TRACK[0]
        if self.text():
            width += _GAP + self.fontMetrics().horizontalAdvance(self.text())
        return QSize(width, max(TRACK[1], self.fontMetrics().height()))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(_DISABLED_OPACITY)
        top = (self.height() - TRACK[1]) / 2
        track = QRectF(0, top, *TRACK)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(TOGGLE_ON if self.isChecked() else TOGGLE_OFF)
        painter.drawRoundedRect(track, track.height() / 2, track.height() / 2)

        x, y, diameter = handle((track.left(), track.top(), track.width(), track.height()),
                                on=self.isChecked(), inset=HANDLE_INSET)
        painter.setBrush(TOGGLE_HANDLE)
        painter.drawEllipse(QRectF(x, y, diameter, diameter))

        if self.text():
            painter.setPen(QPen(TEXT_SECONDARY))
            painter.drawText(
                QRectF(track.right() + _GAP, 0,
                       self.width() - track.right() - _GAP, self.height()),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                self.text(),
            )
        painter.end()
