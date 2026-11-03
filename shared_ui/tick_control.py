"""Once a Qt stylesheet touches a QCheckBox, the native Windows dark indicator collapses
to a bare chevron, so this control paints its own."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QCheckBox

from shared_ui.colors import (
    BG_BUTTON_ACTIVE,
    BG_SECONDARY,
    BLUE,
    BORDER_SUBTLE,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WHITE,
)
from shared_ui.spacing import BUTTON_RADIUS_HUD, GAP_MEDIUM

_INDICATOR = 16
_GAP = GAP_MEDIUM
_RADIUS = BUTTON_RADIUS_HUD

_TICK_POINTS = ((0.24, 0.52), (0.42, 0.70), (0.78, 0.30))


class TickControl(QCheckBox):
    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        indicator = self._indicator_rect()
        enabled = self.isEnabled()

        if self.isChecked():
            fill = BLUE if enabled else BG_BUTTON_ACTIVE
            painter.setPen(QPen(fill, 1))
            painter.setBrush(fill)
            painter.drawRoundedRect(indicator, _RADIUS, _RADIUS)
            self._draw_tick(painter, indicator, enabled)
        else:
            painter.setPen(QPen(BORDER_SUBTLE, 1.4))
            painter.setBrush(BG_SECONDARY)
            painter.drawRoundedRect(
                indicator.adjusted(0.7, 0.7, -0.7, -0.7), _RADIUS, _RADIUS)

        text = self.text()
        if text:
            painter.setPen(TEXT_SECONDARY if enabled else TEXT_MUTED)
            left = indicator.right() + _GAP
            painter.drawText(
                QRectF(left, 0, self.width() - left, self.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                text,
            )
        painter.end()

    def _indicator_rect(self) -> QRectF:
        top = (self.height() - _INDICATOR) / 2.0
        return QRectF(1.0, top, float(_INDICATOR), float(_INDICATOR))

    def _draw_tick(self, painter: QPainter, indicator: QRectF, enabled: bool):
        edge = indicator.width()
        points = QPolygonF([
            QPointF(indicator.left() + fx * edge, indicator.top() + fy * edge)
            for fx, fy in _TICK_POINTS
        ])
        pen = QPen(WHITE if enabled else TEXT_SECONDARY)
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(points)

    def sizeHint(self) -> QSize:
        width = _INDICATOR + _GAP + self.fontMetrics().horizontalAdvance(self.text())
        height = max(_INDICATOR + 4, self.fontMetrics().height() + 4)
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()
