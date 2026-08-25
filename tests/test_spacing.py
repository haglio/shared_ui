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
