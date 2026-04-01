"""Font tokens shared across all projects."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PyQt6.QtGui import QFont

# ---------------------------------------------------------------------------
# Font families
# ---------------------------------------------------------------------------
FONT_MONO = "Cascadia Mono"
FONT_MONO_FALLBACK = "Consolas"
FONT_UI = "Segoe UI"
FONT_SYMBOL = "Segoe UI Symbol"
FONT_EMOJI = "Segoe UI Emoji"

# ---------------------------------------------------------------------------
# Size tiers (points)
# ---------------------------------------------------------------------------
SIZE_TITLE = 16
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


def mono_font(size: int = SIZE_BODY, bold: bool = False) -> QFont:
    """Monospace font with automatic fallback."""
    font = make_font(FONT_MONO, size, bold)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


# ---------------------------------------------------------------------------
# TrueType paths (for PIL/ImageFont rendering if needed)
# ---------------------------------------------------------------------------
TTF_CANDIDATES = (
    Path(r"C:\Windows\Fonts\CascadiaMono.ttf"),
    Path(r"C:\Windows\Fonts\consola.ttf"),
    Path(r"C:\Windows\Fonts\segoeui.ttf"),
)
TTF_DEFAULT = next((p for p in TTF_CANDIDATES if p.exists()), None)
