"""Spacing tokens shared across all projects."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Margins (applied via setContentsMargins)
# ---------------------------------------------------------------------------
MARGIN_STANDARD = 8

# ---------------------------------------------------------------------------
# Gaps (applied via layout.setSpacing or explicit addSpacing)
# ---------------------------------------------------------------------------
GAP_SMALL = 4
GAP_MEDIUM = 8


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
# There are exactly TWO button sizes in this family: the ordinary one, and the
# smaller one the players' HUDs use because room over video is precious.  Every
# icon button is one square or the other and sits the same distance from its
# neighbour -- neither of which was true of any two apps before, and it is what
# made one app's row of controls read as a different kind of thing from another's.
BUTTON_SIZE = 28
BUTTON_SIZE_HUD = 18

# How much of the ordinary square the mark fills.  The remainder is the hug, so a
# mark is never crowded on one app's bar and lost on another's.  The HUDs' own
# hug is theirs: they inset their marks from a button rather than sizing them.
BUTTON_ICON = 16

BUTTON_RADIUS = 4

# Between buttons along a row, and between rows when a row wraps.  The row gap is
# deliberately larger: at the same gap two wrapped rows read as one crowded block
# rather than as two rows.
BUTTON_GAP = 4
BUTTON_ROW_GAP = 8

# Between one GROUP of buttons and the next along a row.  Three times the gap
# inside a group, which is what makes a boundary read as one without a rule
# drawn there -- stated as that ratio rather than as a number of its own, so a
# change to the gap inside a group carries the grouping with it.
#
# Imported by player_core (both HUD painters: the mode pair and the minimize
# beside it) and by origenerator (the browser's button bank, the combine
# panel).  Named here rather than in each of them because that is exactly what
# went wrong before it existed: every bar that grouped its buttons picked its
# own number -- 6, 8, 12 and 14 across three apps -- so the same two groups sat
# different distances apart depending on which app drew them.
BUTTON_GROUP_GAP = BUTTON_GAP * 3

# A button carrying a word rather than a mark: the room above and below it.
BUTTON_PAD_V = 4

# The room to either side of that word where a ROW of such buttons has to fit a
# strip of fixed width -- narrow, because at a toolbar button's usual side pad
# five short words come to nearly twice the room the strip has.  A narrower pad,
# not a different button: same height, same radius, same grounds.
BUTTON_PAD_H_TIGHT = 6
