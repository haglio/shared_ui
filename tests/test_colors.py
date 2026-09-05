"""Tests for shared_ui.colors -- verify every token is a valid QColor
and core palette hues."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from shared_ui import check_box, colors


def _all_qcolors(module=colors):
    """Yield (name, value) for every QColor constant in the module."""
    for name in dir(module):
        if name.startswith("__"):
            continue
        val = getattr(module, name)
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


    def test_border_panel(self):
        # A neutral gray. It carried a blue cast before -- a fourth near-gray no
        # app in the family used anywhere else.
        c = colors.BORDER_PANEL
        assert (c.red(), c.green(), c.blue()) == (120, 120, 120)


def test_an_active_control_sits_on_a_lighter_ground_than_a_resting_one():
    """One rule for "this control is on", so it reads the same in every app.

    Each app had answered it its own way and some had not answered it at all,
    which is why a toggled button looked like a different kind of thing
    depending on which window it was in.
    """
    from shared_ui.colors import BG_BUTTON, BG_BUTTON_ACTIVE

    def lightness(color):
        return 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()

    assert lightness(BG_BUTTON_ACTIVE) > lightness(BG_BUTTON)


def test_the_light_blue_is_the_familys_blue_tinted_lighter():
    """There is one blue.  Where an app needs a lighter one beside it -- a range
    in play against a range loaded, a progress band -- it is that blue toward
    white, not a hue of its own."""
    from shared_ui.colors import BLUE, BLUE_LIGHT

    assert BLUE_LIGHT.blue() > BLUE_LIGHT.green() > BLUE_LIGHT.red()
    # Within a hair of BLUE's own hue, so the two read as one color dark and
    # light rather than as two colors.
    assert abs(BLUE_LIGHT.hue() - BLUE.hue()) <= 12
    assert BLUE_LIGHT.lightness() > BLUE.lightness()


def _grays(module):
    return {
        name: color for name, color in _all_qcolors(module)
        if name.isupper() and color.saturation() <= 40
    }


def test_the_palette_holds_as_few_grays_as_it_can():
    """Every app was reaching for its own dark and medium grays, and the palette
    itself carried near-duplicates that made that easy to excuse -- three border
    shades within ten points of each other, two legend tiers within twenty, a
    status gray eight off the muted one.  A name may still say what it is FOR;
    what it must not do is introduce a shade the eye cannot tell from another."""
    values = {color.name() for color in _grays(colors).values()}

    # The ladder: three backgrounds under a button, the button and its on-state,
    # the keycap between them, the muted gray, the standard outline, the two
    # text tiers, and white.
    assert len(values) <= 11, sorted(values)


def test_no_two_grays_sit_within_a_hair_of_each_other():
    """Which is the rule behind the count: two shades nobody can tell apart are
    one shade with two names, and they drift into different apps."""
    distinct = sorted({color.lightness() for color in _grays(colors).values()})
    for first, second in zip(distinct, distinct[1:]):
        assert second - first >= 10, f"{first} and {second} are the same gray twice"


def test_the_librarys_own_widget_paints_only_palette_colors():
    """The checkbox used to keep two grays of its own, one of them exactly the
    hair from two palette tiers that the rule above forbids -- and slipped under
    that rule because it only ever looked at `colors`."""
    palette_values = {color.name() for _, color in _all_qcolors(colors)}

    strays = sorted(name for name, color in _all_qcolors(check_box)
                    if color.name() not in palette_values)

    assert not strays, strays
