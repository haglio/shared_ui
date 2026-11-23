from __future__ import annotations

from functools import lru_cache

from PySide6.QtGui import QFont

from shared_ui.type_scale import (
    FONT_UI,
    SIZE_BODY,
    SIZE_HEADING,
    SIZE_SMALL,
    SIZE_TINY,
)

__all__ = ["FONT_UI", "SIZE_BODY", "SIZE_HEADING", "SIZE_SMALL", "SIZE_TINY", "make_font", "wordmark_font"]


@lru_cache(maxsize=32)
def make_font(
    family: str = FONT_UI,
    size: int = SIZE_BODY,
    bold: bool = False,
) -> QFont:
    font = QFont(family)
    font.setPointSize(size)
    if bold:
        font.setBold(True)
    return font


def wordmark_font() -> QFont:
    font = QFont(FONT_UI, SIZE_BODY)
    font.setBold(True)
    font.setItalic(True)
    return font
