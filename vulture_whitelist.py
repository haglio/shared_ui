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

# --- colors: read by the apps named ---
TEXT_LEGEND_LABEL  # clipper
TEXT_LEGEND_JOIN  # clipper
BORDER_TIMELINE  # clipper
BORDER_TICK  # clipper
TIMELINE_LOADED  # clipper
TIMELINE_ACTIVE  # clipper, origenerator
TIMELINE_CURSOR  # clipper
TIMELINE_LOOP  # clipper
TIMELINE_SUGGESTED_IN  # clipper
TIMELINE_SUGGESTED_OUT  # clipper

# --- fonts ---
SIZE_SMALL  # clipper, fun_time, scripture
SIZE_TINY  # clipper

# --- spacing ---
GAP_SMALL  # promptcrafter
BUTTON_SIZE_HUD  # origenerator, player_core
BUTTON_ICON  # clipper, evolver, fun_time, origenerator, scripture
BUTTON_ROW_GAP  # origenerator
BUTTON_PAD_H_TIGHT  # fun_time
