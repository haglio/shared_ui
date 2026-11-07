from __future__ import annotations

from itertools import pairwise

from PyQt6.QtGui import QColor

from shared_ui import colors, tick_control


def _all_qcolors(module=colors):
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
    def test_blue(self):
        c = colors.BLUE
        assert (c.red(), c.green(), c.blue()) == (0x30, 0x80, 0xE0)

    def test_green(self):
        c = colors.GREEN
        assert (c.red(), c.green(), c.blue()) == (0x30, 0xA0, 0x30)

    def test_magenta(self):
        c = colors.MAGENTA
        assert (c.red(), c.green(), c.blue()) == (200, 80, 160)

    def test_border_panel(self):
        c = colors.BORDER_PANEL
        assert (c.red(), c.green(), c.blue()) == (120, 120, 120)


def test_an_active_control_sits_on_a_lighter_ground_than_a_resting_one():
    def lightness(color):
        return 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()

    assert lightness(colors.BG_BUTTON_ACTIVE) > lightness(colors.BG_BUTTON)


def test_the_light_blue_is_the_familys_blue_tinted_lighter():
    assert colors.BLUE_LIGHT.blue() > colors.BLUE_LIGHT.green() > colors.BLUE_LIGHT.red()
    assert abs(colors.BLUE_LIGHT.hue() - colors.BLUE.hue()) <= 12
    assert colors.BLUE_LIGHT.lightness() > colors.BLUE.lightness()


def _grays(module):
    return {
        name: color for name, color in _all_qcolors(module)
        if name.isupper() and color.saturation() <= 40
    }


_THE_GRAYS = (
    colors.BG_PRIMARY, colors.BG_SECONDARY, colors.BG_TERTIARY,
    colors.BG_BUTTON, colors.BG_BUTTON_ACTIVE,
    colors.BG_KEYCAP,
    colors.TEXT_MUTED,
    colors.BORDER_DEFAULT,
    colors.TEXT_PRIMARY, colors.TEXT_SECONDARY,
    colors.WHITE,
    colors.BLACK,
)

_THE_HUES = (
    colors.BLUE, colors.BLUE_LIGHT,
    colors.GREEN, colors.RED, colors.YELLOW, colors.MAGENTA,
    colors.LOADING_GROUND, colors.LOADING_ACCENT, colors.LOADING_TROUGH, colors.LOADING_HINT,
)


def test_the_palette_holds_as_few_grays_as_it_can():
    values = {color.name() for color in _grays(colors).values()}

    assert values == {gray.name() for gray in _THE_GRAYS}, sorted(values)


def test_a_new_hue_joins_the_palette_only_by_adding_it_to_this_list_on_purpose():
    hues = {color.name() for name, color in _all_qcolors(colors)
            if name.isupper() and color.saturation() > 40}

    assert hues == {hue.name() for hue in _THE_HUES}, sorted(hues)


def test_no_two_grays_sit_within_a_hair_of_each_other():
    distinct = sorted({color.lightness() for color in _grays(colors).values()})
    for first, second in pairwise(distinct):
        assert second - first >= 10, f"{first} and {second} are the same gray twice"


def test_the_librarys_own_widget_paints_only_palette_colors():
    palette_values = {color.name() for _, color in _all_qcolors(colors)}

    strays = sorted(name for name, color in _all_qcolors(tick_control)
                    if color.name() not in palette_values)

    assert not strays, strays
