"""Color tokens shared across all projects.

Every QColor is defined in RGB order.  Clipper's original values were in
OpenCV BGR — the conversion is documented inline for each affected constant.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor

# ---------------------------------------------------------------------------
# Background tiers (darkest → lightest)
# ---------------------------------------------------------------------------
BG_PRIMARY = QColor(24, 24, 24)  # main canvas / window background
BG_SECONDARY = QColor(40, 40, 40)  # elevated surfaces (panes, cards)
BG_TERTIARY = QColor(50, 50, 50)  # overlay / dialog background
BG_BUTTON = QColor(62, 62, 62)  # default button fill
BG_BUTTON_ACTIVE = QColor(130, 90, 80)  # pressed/active button fill  (was BGR 80,90,130)
BG_BUTTON_DISABLED = QColor(40, 40, 40)  # disabled button fill
BG_KEYCAP = QColor(72, 72, 72)  # keycap / legend background

# ---------------------------------------------------------------------------
# Text tiers (brightest → dimmest)
# ---------------------------------------------------------------------------
TEXT_PRIMARY = QColor(240, 240, 240)  # titles, headings, button labels
TEXT_SECONDARY = QColor(230, 230, 230)  # body text, info labels
TEXT_TERTIARY = QColor(215, 215, 215)  # helper / legend descriptions
TEXT_LEGEND_LABEL = QColor(225, 225, 225)  # legend item labels
TEXT_LEGEND_JOIN = QColor(205, 205, 205)  # legend joiner text (" or ")
TEXT_MUTED = QColor(120, 120, 120)  # disabled / placeholder text

# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------
BORDER_DEFAULT = QColor(210, 210, 210)  # standard border / outline
BORDER_SUBTLE = QColor(95, 95, 95)  # disabled / de-emphasized border
BORDER_OVERLAY = QColor(215, 215, 215)  # overlay dialog border
BORDER_FOCUS = QColor(255, 220, 110)  # focus ring  (was BGR 110,220,255)
BORDER_TIMELINE = QColor(220, 220, 220)  # timeline outer stroke
BORDER_WRAP = QColor(200, 200, 200)  # wrap-mode indicator lines
BORDER_TICK = QColor(210, 210, 210)  # timeline tick dots

# ---------------------------------------------------------------------------
# Accent / status colors
# ---------------------------------------------------------------------------
ACCENT_PRIMARY = QColor(0x30, 0x80, 0xE0)  # primary blue (toggle on, tray icon)
ACCENT_SUCCESS = QColor(120, 240, 120)  # success / done
ACCENT_ERROR = QColor(255, 60, 60)  # error / failure  (was BGR 60,60,255)
ACCENT_ERROR_TEXT = QColor(255, 90, 90)  # error message text  (was BGR 90,90,255)
ACCENT_WARNING = QColor(255, 200, 120)  # warning / notice  (was BGR 120,200,255)
ACCENT_INFO = QColor(235, 235, 235)  # neutral info text
ACCENT_PROGRESS = QColor(110, 210, 110)  # progress bar fill

# ---------------------------------------------------------------------------
# Toggle switch
# ---------------------------------------------------------------------------
TOGGLE_ON = ACCENT_PRIMARY
TOGGLE_OFF = QColor(0xB0, 0xB0, 0xB0)  # gray inactive
TOGGLE_KNOB = QColor(255, 255, 255)

# ---------------------------------------------------------------------------
# Evolver status (used in run history)
# ---------------------------------------------------------------------------
STATUS_SUCCESS = QColor(0x30, 0xA0, 0x30)
STATUS_ERROR = QColor(0xE0, 0x30, 0x30)
STATUS_SKIP = QColor(0x80, 0x80, 0x80)
STATUS_NUMBER = QColor(0x80, 0x80, 0x80)

# ---------------------------------------------------------------------------
# Clipper timeline  (all originally BGR — converted to RGB)
# ---------------------------------------------------------------------------
TIMELINE_LOADED = QColor(46, 64, 82)  # loaded range  (was BGR 82,64,46)
TIMELINE_ACTIVE = QColor(116, 155, 176)  # active range  (was BGR 176,155,116)
TIMELINE_CURSOR = QColor(255, 255, 255)  # current cursor position
TIMELINE_LOOP = QColor(255, 50, 50)  # loop frame position  (was BGR 50,50,255)
TIMELINE_SUGGESTED_IN = QColor(255, 220, 90)  # suggested in-point  (was BGR 90,220,255)
TIMELINE_SUGGESTED_OUT = QColor(90, 210, 255)  # suggested out-point  (was BGR 255,210,90)

# ---------------------------------------------------------------------------
# Dashboard (cable visualization, mode accents, panel outlines)
# ---------------------------------------------------------------------------
ACCENT_PINK = QColor(200, 80, 160)  # robot-hand / OSR2-auto mode accent
CABLE_ACTIVE = QColor(160, 168, 180)  # connected cable / connector
CABLE_INACTIVE = QColor(80, 88, 96)  # disconnected cable / connector
BORDER_PANEL = QColor(112, 119, 128)  # panel outline
