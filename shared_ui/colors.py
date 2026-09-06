"""Color tokens shared across all projects, as QColors.

The values are :mod:`shared_ui.palette`'s, one QColor per name; nothing here
has a number of its own.  A Qt app reads these, and anything that draws
without Qt reads the palette.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from shared_ui import palette

# ---------------------------------------------------------------------------
# Background tiers (darkest -> lightest)
# ---------------------------------------------------------------------------
BG_PRIMARY = QColor(*palette.BG_PRIMARY)  # main canvas / window background
BG_SECONDARY = QColor(*palette.BG_SECONDARY)  # elevated surfaces (panes, cards)
BG_TERTIARY = QColor(*palette.BG_TERTIARY)  # overlay / dialog background
BG_BUTTON = QColor(*palette.BG_BUTTON)  # a control at rest
BG_KEYCAP = QColor(*palette.BG_KEYCAP)  # keycap / legend background
BG_BUTTON_ACTIVE = QColor(*palette.BG_BUTTON_ACTIVE)  # a control that is on

# ---------------------------------------------------------------------------
# Text tiers (brightest -> dimmest)
# ---------------------------------------------------------------------------
TEXT_PRIMARY = QColor(*palette.TEXT_PRIMARY)  # titles, headings, button labels
TEXT_SECONDARY = QColor(*palette.TEXT_SECONDARY)  # body text, info labels
TEXT_MUTED = QColor(*palette.TEXT_MUTED)  # disabled / placeholder text

# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------
BORDER_DEFAULT = QColor(*palette.BORDER_DEFAULT)  # standard border / outline
BORDER_SUBTLE = QColor(*palette.BORDER_SUBTLE)  # disabled / de-emphasized border
BORDER_PANEL = QColor(*palette.BORDER_PANEL)  # a panel's edge

# ---------------------------------------------------------------------------
# Hues (named by hue, not purpose)
# ---------------------------------------------------------------------------
BLUE = QColor(*palette.BLUE)
BLUE_LIGHT = QColor(*palette.BLUE_LIGHT)  # the one blue, tinted toward white
GREEN = QColor(*palette.GREEN)
RED = QColor(*palette.RED)
AMBER = QColor(*palette.AMBER)
PINK = QColor(*palette.PINK)
WHITE = QColor(*palette.WHITE)

# ---------------------------------------------------------------------------
# Toggle switch
# ---------------------------------------------------------------------------
TOGGLE_ON = QColor(*palette.TOGGLE_ON)
TOGGLE_OFF = QColor(*palette.TOGGLE_OFF)
TOGGLE_HANDLE = QColor(*palette.TOGGLE_HANDLE)


# ---------------------------------------------------------------------------
# The roles the desktop theme fills in
# ---------------------------------------------------------------------------
def family_palette(base: QPalette | None = None) -> QPalette:
    """*base* with the roles the desktop theme owns restated in family colors.

    A style sheet dresses what it names.  Every color it does not name is still
    the palette's, and the palette an app starts with is the desktop's -- so on
    Windows those roles carry the user's accent color.  That is how selected
    text in these dark apps came to be highlighted in an accent orange no app
    chose and the family does not own.

    Apply it to the ``QApplication``, beside the family style sheet::

        app.setPalette(family_palette(app.palette()))
        app.setStyleSheet(family_stylesheet())

    *base* defaults to the application's own palette.  Only the roles below are
    restated; the rest are left as Qt derived them, because a style computes a
    widget's bevels and shadows from that widget's own ground, and fixing those
    shades here would fix one answer across grounds that differ.
    """
    result = QPalette(base if base is not None else QPalette())
    role = QPalette.ColorRole

    # A selection: the one blue, with the text a picked menu row already wears.
    result.setColor(role.Highlight, BLUE)
    result.setColor(role.HighlightedText, TEXT_PRIMARY)

    # A hyperlink.  No style-sheet property reaches these, so a rich-text label
    # is the one place a color can only be said here -- or said inline by every
    # app that draws a link, which is the copy this module exists to end.
    result.setColor(role.Link, BLUE)
    result.setColor(role.LinkVisited, BLUE_LIGHT)  # that blue toward white, not a second hue

    # What a style reaches for when it wants "the accent" or a foreground
    # bright enough to sit on one.
    result.setColor(role.Accent, BLUE)
    result.setColor(role.BrightText, WHITE)

    # Not the accent -- white.  Nothing bands its rows today, and the day an
    # item view switches banding on, this is what stops white bars appearing
    # down a dark app.
    result.setColor(role.AlternateBase, BG_SECONDARY)

    return result
