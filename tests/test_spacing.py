"""Tests for shared_ui.spacing — verify constants are positive ints."""

from __future__ import annotations

from shared_ui import spacing


def _all_spacing_constants():
    """Yield (name, value) for every int constant in the module."""
    for name in dir(spacing):
        if name.startswith("_"):
            continue
        val = getattr(spacing, name)
        if isinstance(val, int):
            yield name, val


class TestSpacingTokens:
    def test_all_positive(self):
        for name, val in _all_spacing_constants():
            assert val > 0, f"{name} should be positive, got {val}"



class TestButtonGrouping:
    """The two gaps a bar of grouped buttons draws with."""

    def test_a_group_boundary_is_wider_than_the_gap_inside_a_group(self):
        # If these were equal, grouping would be invisible: a bank of icons
        # would read as one undifferentiated row, which is what a rule used to
        # be drawn to fix.
        assert spacing.BUTTON_GROUP_GAP > spacing.BUTTON_GAP

    def test_the_group_gap_is_stated_as_a_ratio_of_the_gap_inside_one(self):
        # So that changing the gap inside a group carries the grouping with it,
        # rather than leaving a number behind that no longer relates to it.
        assert spacing.BUTTON_GROUP_GAP == spacing.BUTTON_GAP * 3

    def test_a_group_boundary_still_fits_inside_a_button(self):
        # A gap wider than a button reads as two separate bars rather than as
        # two groups of one.
        assert spacing.BUTTON_GROUP_GAP < spacing.BUTTON_SIZE
