from __future__ import annotations

from PyQt6.QtCore import QCoreApplication, QEvent, QObject, QRect
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QAbstractButton, QToolTip

from shared_ui.icon_geometry import tooltip_for

__all__ = ["remember_the_stand_in_on"]

_icon_each_stand_in_replaces: dict[int, str] = {}


def remember_the_stand_in_on(pixmap: QPixmap, icon: str) -> None:
    _icon_each_stand_in_replaces[pixmap.cacheKey()] = icon
    app = QCoreApplication.instance()
    if app.findChild(_SayWhyOnHover) is None:
        app.installEventFilter(_SayWhyOnHover(app))


def _icon_missing_from(button: QAbstractButton) -> str | None:
    worn = button.icon()
    for size in worn.availableSizes():
        icon = _icon_each_stand_in_replaces.get(worn.pixmap(size, 1.0).cacheKey())
        if icon is not None:
            return icon
    return None


class _SayWhyOnHover(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.ToolTip or not isinstance(watched, QAbstractButton):
            return False
        icon = _icon_missing_from(watched)
        if icon is None:
            return False
        QToolTip.showText(event.globalPos(), tooltip_for(icon, watched.toolTip()), watched,
                          QRect(), watched.toolTipDuration())
        return True
