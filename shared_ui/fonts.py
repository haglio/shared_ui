"""Font tokens shared across all projects."""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtGui import QFont

from shared_ui.type_scale import (
    FONT_UI,
    SIZE_BODY,
    SIZE_HEADING,
    SIZE_SMALL,
    SIZE_TINY,
)

__all__ = ["FONT_UI", "SIZE_BODY", "SIZE_HEADING", "SIZE_SMALL", "SIZE_TINY", "make_font"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def make_font(
    family: str = FONT_UI,
    size: int = SIZE_BODY,
    bold: bool = False,
) -> QFont:
    """Build a QFont from tokens.  Results are cached."""
    font = QFont(family)
    font.setPointSize(size)
    if bold:
        font.setBold(True)
    return font
