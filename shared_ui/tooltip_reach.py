"""Qt shows a tooltip only over the active window unless that window is marked to
always show them, while a tooltip an app draws itself follows the pointer into any
window: marking every window makes the two behave alike."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QWidget

from shared_ui.tooltip_shape import shape_long_tooltips

__all__ = ["dress_tooltips"]


class _ShowTooltipsOverInactiveWindows(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Show and isinstance(watched, QWidget) and watched.isWindow():
            watched.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        return False


def dress_tooltips(app) -> None:
    shape_long_tooltips(app)
    if app.findChild(_ShowTooltipsOverInactiveWindows) is None:
        app.installEventFilter(_ShowTooltipsOverInactiveWindows(app))
