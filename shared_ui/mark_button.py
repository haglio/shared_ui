from __future__ import annotations

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QAbstractButton

from shared_ui.chrome import MARK_BUTTON_PROPERTY
from shared_ui.spacing import BUTTON_MARK_INSET, BUTTON_SIZE

__all__ = ["fill_square_with_mark"]


def fill_square_with_mark(button: QAbstractButton, *, size: int = BUTTON_SIZE) -> QAbstractButton:
    button.setProperty(MARK_BUTTON_PROPERTY, True)
    button.setFixedSize(size, size)
    mark = size - 2 * BUTTON_MARK_INSET
    button.setIconSize(QSize(mark, mark))
    return button
