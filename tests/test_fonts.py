"""Tests for shared_ui.fonts — verify font helpers produce valid QFonts."""

from __future__ import annotations

from PyQt6.QtGui import QFont

from shared_ui.fonts import (
    FONT_EMOJI,
    FONT_SYMBOL,
    FONT_UI,
    SIZE_BODY,
    SIZE_HEADING,
    make_font,
)


class TestMakeFont:
    def test_returns_qfont(self):
        f = make_font()
        assert isinstance(f, QFont)

    def test_default_family_is_ui(self):
        f = make_font()
        assert f.family() == FONT_UI

    def test_custom_size(self):
        f = make_font(size=SIZE_HEADING)
        assert f.pointSize() == SIZE_HEADING

    def test_bold(self):
        f = make_font(bold=True)
        assert f.bold()

    def test_not_bold_by_default(self):
        f = make_font()
        assert not f.bold()

    def test_caching(self):
        a = make_font(FONT_UI, SIZE_BODY, False)
        b = make_font(FONT_UI, SIZE_BODY, False)
        assert a is b


class TestIconFontFamilies:
    """Font family constants for icon/symbol rendering."""

    def test_font_symbol_is_str(self):
        assert FONT_SYMBOL == "Segoe UI Symbol"

    def test_font_emoji_is_str(self):
        assert FONT_EMOJI == "Segoe UI Emoji"
