"""Font tokens shared across all projects."""

from __future__ import annotations

from functools import lru_cache

from PyQt6.QtGui import QFont

# ---------------------------------------------------------------------------
# Font families
# ---------------------------------------------------------------------------
FONT_UI = "Segoe UI"

# ---------------------------------------------------------------------------
# Size tiers (points)
# ---------------------------------------------------------------------------
SIZE_HEADING = 14
SIZE_BODY = 11
SIZE_SMALL = 9
SIZE_TINY = 8

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
