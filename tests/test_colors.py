"""Tests for shared_ui.colors — verify every token is a valid QColor
and core palette hues."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from shared_ui import colors


def _all_qcolors():
    """Yield (name, value) for every QColor constant in the module."""
    for name in dir(colors):
        if name.startswith("_"):
            continue
        val = getattr(colors, name)
        if isinstance(val, QColor):
            yield name, val


class TestAllTokensValid:
    def test_every_token_is_a_valid_qcolor(self):
        found = list(_all_qcolors())
        assert len(found) > 0, "No QColor tokens found"
        for name, color in found:
            assert color.isValid(), f"{name} is not a valid QColor"


class TestPaletteColors:
    """Verify the core palette hues."""

    def test_blue(self):
        c = colors.BLUE
        assert (c.red(), c.green(), c.blue()) == (0x30, 0x80, 0xE0)

    def test_green(self):
        c = colors.GREEN
        assert (c.red(), c.green(), c.blue()) == (0x30, 0xA0, 0x30)

    def test_pink(self):
        c = colors.PINK
        assert (c.red(), c.green(), c.blue()) == (200, 80, 160)

    def test_cable_active(self):
        c = colors.CABLE_ACTIVE
        assert (c.red(), c.green(), c.blue()) == (160, 168, 180)

    def test_cable_inactive(self):
        c = colors.CABLE_INACTIVE
        assert (c.red(), c.green(), c.blue()) == (80, 88, 96)

    def test_border_panel(self):
        c = colors.BORDER_PANEL
        assert (c.red(), c.green(), c.blue()) == (112, 119, 128)
