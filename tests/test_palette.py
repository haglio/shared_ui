from __future__ import annotations

from PySide6.QtGui import QColor

from shared_ui import colors, palette


def _tokens(module, kind=tuple):
    return {name: value for name in dir(module) if name.isupper()
            for value in [getattr(module, name)] if isinstance(value, kind)}


def test_every_token_is_a_channel_triple():
    found = _tokens(palette)
    assert found, "no tokens in the palette"
    for name, value in found.items():
        assert isinstance(value, tuple), name
        assert len(value) == 3, name
        assert all(isinstance(c, int) and 0 <= c <= 255 for c in value), name


def _lightness(rgb) -> int:
    return QColor(*rgb).lightness()


def test_the_grounds_run_darkest_to_lightest():
    grounds = (palette.BG_PRIMARY, palette.BG_SECONDARY, palette.BG_TERTIARY, palette.BG_BUTTON,
               palette.BG_KEYCAP, palette.BG_BUTTON_ACTIVE)

    lightness = [_lightness(ground) for ground in grounds]

    assert lightness == sorted(set(lightness))


def test_the_text_tiers_run_brightest_to_dimmest():
    tiers = (palette.TEXT_PRIMARY, palette.TEXT_SECONDARY, palette.TEXT_MUTED)

    lightness = [_lightness(tier) for tier in tiers]

    assert lightness == sorted(set(lightness), reverse=True)


def test_the_loading_screen_s_hint_is_subtler_than_its_status():
    assert _lightness(palette.LOADING_HINT) < _lightness(palette.LOADING_STATUS)


def test_a_hover_lightens_whatever_ground_it_lands_on_and_never_darkens_it():
    assert palette.hovered(palette.BG_BUTTON) > palette.BG_BUTTON
    assert palette.hovered(palette.BLUE) > palette.BLUE
    assert palette.hovered((250, 250, 250)) == (255, 255, 255)

    assert colors.hovered(colors.BG_BUTTON) == QColor(*palette.hovered(palette.BG_BUTTON))


def test_the_hex_spelling_is_the_style_sheets():
    assert palette.as_hex(palette.BLUE) == "#3080e0"
    assert palette.as_hex((0, 0, 0)) == "#000000"
    assert QColor(palette.as_hex(palette.YELLOW)) == QColor(*palette.YELLOW)


def test_the_see_through_spelling_is_the_style_sheets_rgba():
    assert palette.as_rgba(palette.BLACK, 0.55) == "rgba(0, 0, 0, 0.55)"
    assert palette.as_rgba(palette.BLUE, 1) == "rgba(48, 128, 224, 1)"


def test_the_fraction_spelling_is_what_a_headset_draws_with():
    assert palette.as_fractions(palette.WHITE, 0.5) == (1.0, 1.0, 1.0, 0.5)
    assert palette.as_fractions((51, 102, 0)) == (0.2, 0.4, 0.0, 1.0)


def test_a_color_from_outside_the_code_is_drawn_as_the_familys_nearest():
    assert palette.nearest((250, 70, 70)) == palette.RED
    assert palette.nearest((1, 2, 3)) == palette.BLACK
    assert palette.nearest(palette.GREEN) == palette.GREEN


def test_the_qt_spelling_is_the_palette_and_nothing_more():
    qt = _tokens(colors, QColor)
    for name, rgb in _tokens(palette).items():
        assert name in qt, f"{name} has no QColor twin"
        assert qt[name] == QColor(*rgb), name

    palette_values = {QColor(*rgb).name() for rgb in _tokens(palette).values()}
    strays = sorted(name for name, color in qt.items() if color.name() not in palette_values)
    assert not strays, f"QColors with a number of their own: {strays}"
