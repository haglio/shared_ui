"""Tests for shared_ui.colors — verify every token is a valid QColor
and that BGR→RGB conversions from Clipper's original values are correct."""

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


class TestBGRConversions:
    """Clipper stored colors in BGR.  Verify the RGB values are correct."""

    def test_timeline_loaded(self):
        # Original BGR: (82, 64, 46) → RGB (46, 64, 82)
        c = colors.TIMELINE_LOADED
        assert (c.red(), c.green(), c.blue()) == (46, 64, 82)

    def test_timeline_active(self):
        # Original BGR: (176, 155, 116) → RGB (116, 155, 176)
        c = colors.TIMELINE_ACTIVE
        assert (c.red(), c.green(), c.blue()) == (116, 155, 176)

    def test_timeline_suggested_in(self):
        # Original BGR: (90, 220, 255) → RGB (255, 220, 90)
        c = colors.TIMELINE_SUGGESTED_IN
        assert (c.red(), c.green(), c.blue()) == (255, 220, 90)

    def test_timeline_suggested_out(self):
        # Original BGR: (255, 210, 90) → RGB (90, 210, 255)
        c = colors.TIMELINE_SUGGESTED_OUT
        assert (c.red(), c.green(), c.blue()) == (90, 210, 255)

    def test_timeline_loop(self):
        # Original BGR: (50, 50, 255) → RGB (255, 50, 50)
        c = colors.TIMELINE_LOOP
        assert (c.red(), c.green(), c.blue()) == (255, 50, 50)

    def test_bg_button_active(self):
        # Original BGR: (80, 90, 130) → RGB (130, 90, 80)
        c = colors.BG_BUTTON_ACTIVE
        assert (c.red(), c.green(), c.blue()) == (130, 90, 80)

    def test_border_focus(self):
        # Original BGR: (110, 220, 255) → RGB (255, 220, 110)
        c = colors.BORDER_FOCUS
        assert (c.red(), c.green(), c.blue()) == (255, 220, 110)

    def test_accent_error(self):
        # Original BGR: (60, 60, 255) → RGB (255, 60, 60)
        c = colors.ACCENT_ERROR
        assert (c.red(), c.green(), c.blue()) == (255, 60, 60)

    def test_accent_warning(self):
        # Original BGR: (120, 200, 255) → RGB (255, 200, 120)
        c = colors.ACCENT_WARNING
        assert (c.red(), c.green(), c.blue()) == (255, 200, 120)


class TestGrayValuesUnchanged:
    """Grays have identical B, G, R — verify they survived conversion."""

    def test_bg_primary(self):
        c = colors.BG_PRIMARY
        assert c.red() == c.green() == c.blue() == 24

    def test_text_primary(self):
        c = colors.TEXT_PRIMARY
        assert c.red() == c.green() == c.blue() == 240

    def test_text_secondary(self):
        c = colors.TEXT_SECONDARY
        assert c.red() == c.green() == c.blue() == 230


class TestEvolverColors:
    """Verify Evolver-origin tokens match their original hex values."""

    def test_accent_primary(self):
        c = colors.ACCENT_PRIMARY
        assert (c.red(), c.green(), c.blue()) == (0x30, 0x80, 0xE0)

    def test_toggle_on_is_accent_primary(self):
        assert colors.TOGGLE_ON is colors.ACCENT_PRIMARY

    def test_status_success(self):
        c = colors.STATUS_SUCCESS
        assert (c.red(), c.green(), c.blue()) == (0x30, 0xA0, 0x30)

    def test_status_error(self):
        c = colors.STATUS_ERROR
        assert (c.red(), c.green(), c.blue()) == (0xE0, 0x30, 0x30)


class TestDashboardColors:
    """Dashboard-origin tokens added during Tkinter→PyQt6 migration."""

    def test_accent_pink(self):
        c = colors.ACCENT_PINK
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
