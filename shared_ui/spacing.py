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

# A button carrying a word rather than a mark: the room above and below it.
BUTTON_PAD_V = 4

# The room to either side of that word where a ROW of such buttons has to fit a
# strip of fixed width -- narrow, because at a toolbar button's usual side pad
# five short words come to nearly twice the room the strip has.  A narrower pad,
# not a different button: same height, same radius, same grounds.
BUTTON_PAD_H_TIGHT = 6
