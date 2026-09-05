"""The family's colors as plain RGB triples -- no toolkit.

Every color the apps share is here, once, as ``(red, green, blue)``.
:mod:`shared_ui.colors` is the same list as QColors for the Qt chrome, and
anything that draws without Qt reads this module instead: the players paint
their HUDs into the video frame with Pillow, and Fun Time's help page is HTML.
Each of those used to carry its own copy of the numbers, and a copy is a thing
that drifts -- one of the help page's seven hex values had already moved three
points off its source.  This module imports nothing, so a Pillow-only process
never pulls in Qt to learn what color a button is.
"""

from __future__ import annotations

Rgb = tuple[int, int, int]

# ---------------------------------------------------------------------------
# Background tiers (darkest -> lightest)
# ---------------------------------------------------------------------------
BG_PRIMARY: Rgb =(24, 24, 24)  # main canvas / window background
BG_SECONDARY: Rgb =(40, 40, 40)  # elevated surfaces (panes, cards)
BG_TERTIARY: Rgb =(50, 50, 50)  # overlay / dialog background
BG_BUTTON: Rgb =(62, 62, 62)  # a control at rest
BG_KEYCAP: Rgb =(72, 72, 72)  # keycap / legend background
# A control that is ON -- toggled, engaged, holding something down -- sits on a
# LIGHTER ground than one at rest.  One rule, so an active control reads the
# same whichever app it is in.
BG_BUTTON_ACTIVE: Rgb =(92, 92, 92)

# ---------------------------------------------------------------------------
# Text tiers (brightest -> dimmest)
# ---------------------------------------------------------------------------
TEXT_PRIMARY: Rgb =(240, 240, 240)  # titles, headings, button labels
TEXT_SECONDARY: Rgb =(230, 230, 230)  # body text, info labels
TEXT_MUTED: Rgb =(120, 120, 120)  # disabled / placeholder text

# ---------------------------------------------------------------------------
# Borders
# ---------------------------------------------------------------------------
BORDER_DEFAULT: Rgb =(210, 210, 210)  # standard border / outline
BORDER_SUBTLE: Rgb =BG_BUTTON_ACTIVE  # disabled / de-emphasized border
BORDER_PANEL: Rgb =TEXT_MUTED  # a panel's edge: the muted gray, not a shade of its own

# ---------------------------------------------------------------------------
# Hues (named by hue, not purpose)
# ---------------------------------------------------------------------------
# There is ONE blue in this family.  Where something needs a lighter one beside
# it -- a range in play against a range loaded, a progress band -- it is this
# blue tinted toward white, not a second hue.
BLUE: Rgb =(48, 128, 224)
BLUE_LIGHT: Rgb =(140, 192, 240)
GREEN: Rgb =(48, 160, 48)
RED: Rgb =(255, 60, 60)
AMBER: Rgb =(255, 200, 120)
PINK: Rgb =(200, 80, 160)
WHITE: Rgb =(255, 255, 255)

# ---------------------------------------------------------------------------
# Toggle switch
# ---------------------------------------------------------------------------
TOGGLE_ON: Rgb =BLUE
TOGGLE_OFF: Rgb =TEXT_MUTED  # the muted gray everything else off wears
TOGGLE_KNOB: Rgb =WHITE


def as_hex(rgb: Rgb) -> str:
    """The ``#rrggbb`` spelling a style sheet or an HTML page takes."""
    red, green, blue = rgb
    return f"#{red:02x}{green:02x}{blue:02x}"
