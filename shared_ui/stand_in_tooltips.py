from __future__ import annotations

from PyQt6.QtCore import QCoreApplication, QEvent, QObject, QRect
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QAbstractButton, QToolTip

from shared_ui.icon_geometry import tooltip_for

__all__ = ["remember_the_stand_in_on"]

_mark_each_stand_in_replaces: dict[int, str] = {}


def remember_the_stand_in_on(pixmap: QPixmap, mark: str) -> None:
    _mark_each_stand_in_replaces[pixmap.cacheKey()] = mark
    app = QCoreApplication.instance()
    if app.findChild(_SayWhyOnHover) is None:
        app.installEventFilter(_SayWhyOnHover(app))


def _mark_missing_from(button: QAbstractButton) -> str | None:
    icon = button.icon()
    for size in icon.availableSizes():
        mark = _mark_each_stand_in_replaces.get(icon.pixmap(size, 1.0).cacheKey())
        if mark is not None:
            return mark
    return None


class _SayWhyOnHover(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.ToolTip or not isinstance(watched, QAbstractButton):
            return False
        mark = _mark_missing_from(watched)
        if mark is None:
            return False
        QToolTip.showText(event.globalPos(), tooltip_for(mark, watched.toolTip()), watched,
                          QRect(), watched.toolTipDuration())
        return True
