"""Qt shows a tooltip only over the active window unless that window is marked to
always show them."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QWidget

from shared_ui.tooltip_shape import shape_long_tooltips

__all__ = ["dress_tooltips"]


class _DressTooltipWindows(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not isinstance(watched, QWidget) or not watched.isWindow():
            return False
        if event.type() == QEvent.Type.Show:
            watched.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        return False


def dress_tooltips(app) -> None:
    shape_long_tooltips(app)
    if app.findChild(_DressTooltipWindows) is None:
        app.installEventFilter(_DressTooltipWindows(app))
