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


def test_the_timeline_ranges_are_the_familys_blue():
    """They were a pair of muted greenish blues, carried over from Clipper's
    original OpenCV values -- shades that lived in this palette and in no app
    that reads it, so the timeline read as another program's chrome."""
    from shared_ui.colors import BLUE, TIMELINE_ACTIVE, TIMELINE_LOADED

    for color in (TIMELINE_LOADED, TIMELINE_ACTIVE):
        assert color.blue() > color.green() > color.red(), color.name()
        # Within a hair of BLUE's own hue, so the two ranges read as that color
        # dark and that color light rather than as a colour of their own.
        assert abs(color.hue() - BLUE.hue()) <= 12, color.name()
    assert TIMELINE_ACTIVE.lightness() > TIMELINE_LOADED.lightness()


def test_the_palette_holds_as_few_grays_as_it_can():
    """Every app was reaching for its own dark and medium grays, and the palette
    itself carried near-duplicates that made that easy to excuse -- three border
    shades within ten points of each other, two legend tiers within twenty, a
    status gray eight off the muted one.  A name may still say what it is FOR;
    what it must not do is introduce a shade the eye cannot tell from another."""
    values = set()
    for name in dir(colors):
        if not name.isupper():
            continue
        color = getattr(colors, name)
        if hasattr(color, "saturation") and color.saturation() <= 40:
            values.add(color.name())

    # The ladder: three backgrounds under a button, the button and its on-state,
    # the muted gray, the standard outline, and white.
    assert len(values) <= 11, sorted(values)


def test_no_two_grays_sit_within_a_hair_of_each_other():
    """Which is the rule behind the count: two shades nobody can tell apart are
    one shade with two names, and they drift into different apps."""
    lightnesses = sorted(
        getattr(colors, name).lightness()
        for name in dir(colors)
        if name.isupper()
        and hasattr(getattr(colors, name), "saturation")
        and getattr(colors, name).saturation() <= 40
    )
    distinct = sorted(set(lightnesses))
    for first, second in zip(distinct, distinct[1:]):
        assert second - first >= 10, f"{first} and {second} are the same gray twice"
