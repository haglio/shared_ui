from __future__ import annotations

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QAbstractButton

from shared_ui.chrome import ICON_BUTTON_PROPERTY
from shared_ui.spacing import BUTTON_ICON_INSET, BUTTON_SIZE

__all__ = ["fill_square_with_icon"]


def fill_square_with_icon(button: QAbstractButton, *, size: int = BUTTON_SIZE) -> QAbstractButton:
    button.setProperty(ICON_BUTTON_PROPERTY, True)
    button.setFixedSize(size, size)
    edge = size - 2 * BUTTON_ICON_INSET
    button.setIconSize(QSize(edge, edge))
    return button
