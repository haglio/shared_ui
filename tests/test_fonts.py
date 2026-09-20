"""The family's one font, and what asking for a variation of it gets you."""

from __future__ import annotations

from shared_ui.fonts import (
    FONT_UI,
    SIZE_BODY,
    SIZE_HEADING,
    make_font,
)


class TestMakeFont:
    def test_a_font_asked_for_with_no_family_comes_back_in_the_familys(self):
        f = make_font()
        assert f.family() == FONT_UI

    def test_the_size_asked_for_is_the_size_set(self):
        f = make_font(size=SIZE_HEADING)
        assert f.pointSize() == SIZE_HEADING

    def test_asking_for_bold_sets_bold(self):
        f = make_font(bold=True)
        assert f.bold()

    def test_a_font_is_not_bold_unless_it_was_asked_to_be(self):
        f = make_font()
        assert not f.bold()

    def test_the_same_request_twice_hands_back_one_font(self):
        a = make_font(FONT_UI, SIZE_BODY, False)
        b = make_font(FONT_UI, SIZE_BODY, False)
        assert a is b
