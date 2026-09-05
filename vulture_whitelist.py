"""Vulture whitelist -- false positives that are not dead code.

This is a library: its tokens are read by the apps, not by anything here, so
vulture over this tree alone reports every one no module or test of its own
touches. Each is listed with the repos that import it, in place of the blanket
all-caps exemption that used to hide a token nobody imports. vulture matches by
bare name, so tests/test_dead_code.py asserts every entry here still answers a
report, and an entry may only be added with the reason it answers one.
"""

# ruff: noqa: F821, B018 -- a whitelist is names, not statements
# --- Qt method overrides, called by the event loop, not by us ---
_.paintEvent  # check_box, toggle_switch

# --- colors: none.  Every QColor in colors.py reads its palette twin by name, so
#     vulture sees each token used; a palette token nobody reads shows up in
#     colors.py's own tests instead. ---

# --- fonts ---
SIZE_SMALL  # clipper, fun_time, scripture
SIZE_TINY  # clipper

# --- spacing ---
GAP_SMALL  # promptcrafter
BUTTON_SIZE_HUD  # origenerator, player_core
BUTTON_ICON  # clipper, evolver, fun_time, origenerator, scripture
BUTTON_ROW_GAP  # origenerator
BUTTON_PAD_H_TIGHT  # fun_time
