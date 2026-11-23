from __future__ import annotations

from shared_ui.fonts import (
    FONT_UI,
    SIZE_BODY,
    SIZE_HEADING,
    make_font,
    wordmark_font,
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


class TestWordmarkFont:
    def test_the_wordmark_is_lettered_in_the_familys_body_size(self):
        f = wordmark_font()
        assert (f.family(), f.pointSize()) == (FONT_UI, SIZE_BODY)

    def test_the_wordmark_is_bold_italic(self):
        f = wordmark_font()
        assert f.bold()
        assert f.italic()

    def test_each_wordmark_font_is_its_own_so_a_change_to_one_reaches_no_other(self):
        assert wordmark_font() is not wordmark_font()
