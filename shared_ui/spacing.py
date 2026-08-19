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
# icon button is one square or the other, hugs its mark by the same amount, and
# sits the same distance from its neighbour -- none of which was true of any two
# apps before, and it is what made one app's row of controls read as a different
# kind of thing from another's.
BUTTON_SIZE = 28
BUTTON_SIZE_HUD = 18

# How much of that square the mark fills.  The remainder is the hug, equal on
# every button, so a mark is never crowded on one app's bar and lost on another's.
BUTTON_ICON = 16
BUTTON_ICON_HUD = 12

BUTTON_RADIUS = 4
BUTTON_RADIUS_HUD = 3

# Between buttons along a row, and between rows when a row wraps.  The row gap is
# deliberately larger: at the same gap two wrapped rows read as one crowded block
# rather than as two rows.
BUTTON_GAP = 4
BUTTON_ROW_GAP = 8

# A button carrying a word rather than a mark: the room around the word.
BUTTON_PAD_H = 10
BUTTON_PAD_V = 4

# The same button where a ROW of them has to fit a strip of fixed width -- a
# toolbar's own buttons are padded about this much, and the full pad above turns
# five short words into nearly twice the room the strip has.  It is a narrower
# pad, not a different button: same height, same radius, same grounds.
BUTTON_PAD_H_TIGHT = 6
