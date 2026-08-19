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
BG_KEYCAP = QColor(72, 72, 72)  # keycap / legend background
# A control that is ON -- toggled, engaged, holding something down -- sits on a
# LIGHTER ground than one at rest.  One rule, so an active control reads the same
# whichever app it is in; the apps had each answered it their own way, and some
# not at all.
BG_BUTTON_ACTIVE = QColor(92, 92, 92)

# ---------------------------------------------------------------------------
# Text tiers (brightest → dimmest)
# ---------------------------------------------------------------------------
TEXT_PRIMARY = QColor(240, 240, 240)  # titles, headings, button labels
TEXT_SECONDARY = QColor(230, 230, 230)  # body text, info labels
TEXT_LEGEND_LABEL = QColor(225, 225, 225)  # legend item labels
TEXT_LEGEND_JOIN = QColor(205, 205, 205)  # legend joiner text (" or ")
TEXT_MUTED = QColor(120, 120, 120)  # disabled / placeholder text

# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------
BORDER_DEFAULT = QColor(210, 210, 210)  # standard border / outline
BORDER_SUBTLE = QColor(95, 95, 95)  # disabled / de-emphasized border
BORDER_TIMELINE = QColor(220, 220, 220)  # timeline outer stroke
BORDER_TICK = QColor(210, 210, 210)  # timeline tick dots
BORDER_PANEL = QColor(112, 119, 128)  # panel outline

# ---------------------------------------------------------------------------
# Palette colors (named by hue, not purpose)
# ---------------------------------------------------------------------------
BLUE = QColor(0x30, 0x80, 0xE0)  # (48, 128, 224)
GREEN = QColor(0x30, 0xA0, 0x30)  # (48, 160, 48)
RED = QColor(255, 60, 60)  # (was BGR 60,60,255)
AMBER = QColor(255, 200, 120)  # (was BGR 120,200,255)
ORANGE = QColor(190, 105, 15)  # dark orange-amber; readable under white text
PINK = QColor(200, 80, 160)

# ---------------------------------------------------------------------------
# Toggle switch
# ---------------------------------------------------------------------------
TOGGLE_ON = BLUE
TOGGLE_OFF = QColor(0xB0, 0xB0, 0xB0)  # gray inactive
TOGGLE_KNOB = QColor(255, 255, 255)

# ---------------------------------------------------------------------------
# Status (gray variants used in run history)
# ---------------------------------------------------------------------------
STATUS_SKIP = QColor(0x80, 0x80, 0x80)
STATUS_NUMBER = QColor(0x80, 0x80, 0x80)

# ---------------------------------------------------------------------------
# Clipper timeline  (all originally BGR — converted to RGB)
# ---------------------------------------------------------------------------
# There is ONE blue in this family, and the timeline's darker range IS it -- not
# a shade near it.  A timeline needs two, so the lighter range is that same blue
# tinted toward white; nothing here invents a second hue.  Both were muted
# greenish blues before, carried over from Clipper's original OpenCV values --
# shades that lived in this palette and in no app that reads it.
TIMELINE_LOADED = BLUE                    # loaded range: the family's blue
TIMELINE_ACTIVE = QColor(140, 192, 240)   # in play: that blue, tinted lighter
TIMELINE_CURSOR = QColor(255, 255, 255)  # current cursor position
TIMELINE_LOOP = QColor(255, 50, 50)  # loop frame position  (was BGR 50,50,255)
TIMELINE_SUGGESTED_IN = QColor(255, 220, 90)  # suggested in-point  (was BGR 90,220,255)
TIMELINE_SUGGESTED_OUT = QColor(90, 210, 255)  # suggested out-point  (was BGR 255,210,90)

# ---------------------------------------------------------------------------
# Dashboard (cable visualization)
# ---------------------------------------------------------------------------
CABLE_ACTIVE = QColor(160, 168, 180)  # connected cable / connector
CABLE_INACTIVE = QColor(80, 88, 96)  # disconnected cable / connector
