"""Color tokens shared across all projects, as QColors.

The values are :mod:`shared_ui.palette`'s, one QColor per name; nothing here
has a number of its own.  A Qt app reads these, and anything that draws
without Qt reads the palette.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor

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
TOGGLE_KNOB = QColor(*palette.TOGGLE_KNOB)

# ---------------------------------------------------------------------------
# Clipper's timeline and legend -- leaving for clipper, which is the one app
# that draws them.  Every one is a hue or a tier under a purpose name.
# ---------------------------------------------------------------------------
TEXT_LEGEND_LABEL = TEXT_SECONDARY
TEXT_LEGEND_JOIN = TEXT_MUTED
BORDER_TIMELINE = BORDER_DEFAULT
BORDER_TICK = BORDER_DEFAULT
TIMELINE_LOADED = BLUE
TIMELINE_ACTIVE = BLUE_LIGHT
TIMELINE_CURSOR = WHITE
TIMELINE_LOOP = RED
TIMELINE_SUGGESTED_IN = AMBER
TIMELINE_SUGGESTED_OUT = BLUE_LIGHT
