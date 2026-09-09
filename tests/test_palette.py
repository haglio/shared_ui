"""shared_ui.palette: the numbers, once, with no toolkit -- and shared_ui.colors
as the same numbers spelled for Qt."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from shared_ui import colors, palette


def _tokens(module, kind=tuple):
    """Every COLOR the module names, spelled the way that module spells one.  The
    palette also carries how far a hover lifts a color, and a distance is not a
    color, so the sweeps below ask for the shape rather than for every name."""
    return {name: value for name in dir(module) if name.isupper()
            for value in [getattr(module, name)] if isinstance(value, kind)}


def test_every_token_is_a_channel_triple():
    found = _tokens(palette)
    assert found, "no tokens in the palette"
    for name, value in found.items():
        assert isinstance(value, tuple) and len(value) == 3, name
        assert all(isinstance(c, int) and 0 <= c <= 255 for c in value), name


def test_a_hover_lifts_whatever_ground_it_lands_on():
    """One step, one direction: a control under the pointer is lighter than the
    same control at rest, and a lit one stays its own color a shade brighter."""
    assert palette.hovered(palette.BG_BUTTON) > palette.BG_BUTTON
    assert palette.hovered(palette.BLUE) > palette.BLUE
    assert palette.hovered((250, 250, 250)) == (255, 255, 255)  # clamped, never wrapped

    assert colors.hovered(colors.BG_BUTTON) == QColor(*palette.hovered(palette.BG_BUTTON))


def test_the_hex_spelling_is_the_style_sheets():
    assert palette.as_hex(palette.BLUE) == "#3080e0"
    assert palette.as_hex((0, 0, 0)) == "#000000"
    assert QColor(palette.as_hex(palette.AMBER)) == QColor(*palette.AMBER)


def test_the_qt_spelling_is_the_palette_and_nothing_more():
    """Every palette token has a QColor twin of the same name and value, and no
    QColor in `colors` carries a number the palette does not -- a Qt app and a
    Pillow HUD looking at the same state look alike because they cannot differ.
    """
    qt = _tokens(colors, QColor)
    for name, rgb in _tokens(palette).items():
        assert name in qt, f"{name} has no QColor twin"
        assert qt[name] == QColor(*rgb), name

    palette_values = {QColor(*rgb).name() for rgb in _tokens(palette).values()}
    strays = sorted(name for name, color in qt.items() if color.name() not in palette_values)
    assert not strays, f"QColors with a number of their own: {strays}"
