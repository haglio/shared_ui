"""shared_ui.lettering: Segoe UI by file for anything that letters with Pillow, and a line cut or wrapped to a width."""

from __future__ import annotations

import math

from PIL import ImageFont

from shared_ui.lettering import WORDMARK_FACE, fit_text, load_font, wrap_text


class TestALineCutToFit:
    def test_a_line_that_fits_is_left_alone(self):
        font = ImageFont.load_default(12)

        assert fit_text(font, "play", 500) == "play"

    def test_a_line_that_does_not_is_cut_at_its_tail(self):
        """A notice leads with what it is about, so the head survives the cut."""
        font = ImageFont.load_default(12)
        cut = fit_text(font, "unrecognized voice command: " + "word " * 40, 100)

        assert cut.startswith("unrecognized")
        assert cut.endswith("…")
        assert font.getlength(cut) <= 100

    def test_a_cut_just_after_a_space_keeps_the_space_before_the_ellipsis(self):
        """As Qt's own cut does, which Origenerator's labels use."""
        font = ImageFont.load_default(12)

        assert fit_text(font, "aaaa bbbb", math.ceil(font.getlength("aaaa …"))) == "aaaa …"

    def test_a_box_narrower_than_the_ellipsis_gets_nothing(self):
        font = ImageFont.load_default(12)

        assert fit_text(font, "play", 1) == ""


class TestLinesWrappedToFit:
    def test_a_line_too_wide_for_one_goes_on_to_the_next_with_every_word_kept(self):
        font = ImageFont.load_default(12)
        said = "not sure enough of: portrait next (press Enter to accept)"

        lines = wrap_text(font, said, 150, max_lines=3)

        assert len(lines) > 1
        assert " ".join(lines) == said
        assert all(font.getlength(line) <= 150 for line in lines)

    def test_what_will_not_fit_in_the_lines_it_may_take_goes_on_the_last_whole(self):
        """Whole, so the surface that set the limit cuts it its own way."""
        font = ImageFont.load_default(12)

        lines = wrap_text(font, "word " * 60, 150, max_lines=3)

        assert len(lines) == 3
        assert " ".join(lines).split() == ["word"] * 60
        assert font.getlength(lines[-1]) > 150

    def test_a_word_wider_than_a_whole_line_keeps_a_line_of_its_own_whole(self):
        """As Qt's word wrap gives it one: what a surface then shows of a line
        still too wide for it -- cut with an ellipsis, clipped at its edge, or
        grown round -- is that surface's own, as a Qt widget's elide mode is."""
        font = ImageFont.load_default(12)

        assert wrap_text(font, "lead " + "w" * 80 + " tail", 150) == ["lead", "w" * 80, "tail"]

    def test_nothing_to_show_takes_no_lines(self):
        font = ImageFont.load_default(12)

        assert wrap_text(font, "", 150) == wrap_text(font, " \n  ", 150) == []

    def test_a_line_break_starts_a_new_line_and_a_blank_line_stays(self):
        font = ImageFont.load_default(12)

        assert wrap_text(font, "first line\n\nthird line", 500) == ["first line", "", "third line"]

    def test_the_texts_own_spaces_are_kept_but_where_a_line_breaks(self):
        """As the desktop's log and notice keep them: a run lined up on purpose,
        and the indent a line starts with, stay; the run a line breaks at goes."""
        font = ImageFont.load_default(12)
        lined_up = "12:00:00  system     made up"

        assert wrap_text(font, lined_up, 500) == [lined_up]
        assert wrap_text(font, "first\n    indented", 500) == ["first", "    indented"]
        assert wrap_text(font, "aaaa    bbbb", font.getlength("aaaa")) == ["aaaa", "bbbb"]


class TestTheFace:
    def test_a_face_this_machine_does_not_have_still_letters_the_line(self):
        font = load_font(14, face="no-such-face.ttf")

        assert font.getlength("play") > 0

    def test_a_panel_measuring_every_frame_reads_the_face_file_once(self):
        assert load_font(11) is load_font(11)
        assert load_font(11) is not load_font(11, face=WORDMARK_FACE)
