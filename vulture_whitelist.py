"""Vulture whitelist -- false positives that are not dead code.

This is a library: its tokens are read by the apps, not by anything here, so
vulture over this tree alone reports every one no module or test of its own
touches. Each is listed with the repos that import it, in place of the blanket
all-caps exemption that used to hide a token nobody imports. vulture matches by
bare name, so tests/test_dead_code.py asserts every entry here still answers a
report, and an entry may only be added with the reason it answers one.
"""
from __future__ import annotations

# ruff: noqa: F821, B018 -- a whitelist is names, not statements
# --- Qt method overrides, called by the event loop, not by us ---
_.paintEvent  # tick_control, toggle_switch
_.eventFilter  # stand_in_tooltips

# --- pytest reads these off a conftest or a test module ---
pytest_plugins  # tests/conftest.py loads the pointer fixture from shared_ui.testing
pytestmark  # this repo's checks of itself, which app_support.repo_checks runs first

# --- colors: none.  Every QColor in colors.py reads its palette twin by name, so
#     vulture sees each token used; a palette token nobody reads shows up in
#     colors.py's own tests instead. ---

# --- spacing ---
BUTTON_WORD_W  # fun_time's dashboard and its headset copy
BUTTON_ROW_GAP  # origenerator

# --- type ---
SIZES  # funestra: a satellite's title steps down through them to fit

# --- the notice's shape, drawn by fun_time (desktop and headset) and origenerator ---
NOTICE_TYPE_SIZE  # fun_time, origenerator
NOTICE_PAD_V  # fun_time, origenerator
NOTICE_PAD_H  # fun_time, origenerator
NOTICE_RADIUS  # fun_time, origenerator
NOTICE_TOP_MARGIN  # fun_time, origenerator
