from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from shared_ui import palette
from shared_ui.chrome import family_stylesheet

BG_PRIMARY = QColor(*palette.BG_PRIMARY)
BG_SECONDARY = QColor(*palette.BG_SECONDARY)
BG_TERTIARY = QColor(*palette.BG_TERTIARY)
BG_BUTTON = QColor(*palette.BG_BUTTON)
BG_KEYCAP = QColor(*palette.BG_KEYCAP)
BG_BUTTON_ACTIVE = QColor(*palette.BG_BUTTON_ACTIVE)


def hovered(color: QColor) -> QColor:
    return QColor(*palette.hovered((color.red(), color.green(), color.blue())))

TEXT_PRIMARY = QColor(*palette.TEXT_PRIMARY)
TEXT_SECONDARY = QColor(*palette.TEXT_SECONDARY)
TEXT_MUTED = QColor(*palette.TEXT_MUTED)

BORDER_DEFAULT = QColor(*palette.BORDER_DEFAULT)
BORDER_SUBTLE = QColor(*palette.BORDER_SUBTLE)
BORDER_PANEL = QColor(*palette.BORDER_PANEL)

PICKED_TEXT = QColor(*palette.PICKED_TEXT)

BLUE = QColor(*palette.BLUE)
BLUE_LIGHT = QColor(*palette.BLUE_LIGHT)
GREEN = QColor(*palette.GREEN)
RED = QColor(*palette.RED)
YELLOW = QColor(*palette.YELLOW)
MAGENTA = QColor(*palette.MAGENTA)
WHITE = QColor(*palette.WHITE)
BLACK = QColor(*palette.BLACK)

LOADING_GROUND = QColor(*palette.LOADING_GROUND)
LOADING_ACCENT = QColor(*palette.LOADING_ACCENT)
LOADING_TROUGH = QColor(*palette.LOADING_TROUGH)
LOADING_STATUS = QColor(*palette.LOADING_STATUS)
LOADING_HINT = QColor(*palette.LOADING_HINT)

TOGGLE_ON = QColor(*palette.TOGGLE_ON)
TOGGLE_OFF = QColor(*palette.TOGGLE_OFF)
TOGGLE_HANDLE = QColor(*palette.TOGGLE_HANDLE)

PREVIEW_INK = QColor(*palette.PREVIEW_INK)


def family_palette(base: QPalette | None = None) -> QPalette:
    """A Qt style sheet leaves every role it does not name to the palette, which on Windows
    carries the user's accent color. The roles not restated here stay as Qt derived them:
    a style computes a widget's bevels and shadows from that widget's own ground."""
    result = QPalette(base if base is not None else QPalette())
    role = QPalette.ColorRole

    result.setColor(role.Highlight, BLUE)
    result.setColor(role.HighlightedText, PICKED_TEXT)

    # No Qt style sheet property reaches the link color of a rich-text label.
    result.setColor(role.Link, BLUE)
    result.setColor(role.LinkVisited, BLUE_LIGHT)

    result.setColor(role.Accent, BLUE)
    result.setColor(role.BrightText, WHITE)

    result.setColor(role.AlternateBase, BG_SECONDARY)

    return result


def dress_application(app, sheet: str | None = None) -> None:
    app.setPalette(family_palette(app.palette()))
    app.setStyleSheet(family_stylesheet() if sheet is None else sheet)
