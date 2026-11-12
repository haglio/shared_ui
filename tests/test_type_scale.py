from __future__ import annotations

from shared_ui import fonts, type_scale
from shared_ui.testing import toolkits_loaded_by_importing


def test_the_family_letters_in_one_face_at_four_sizes():
    sizes = [type_scale.SIZE_TINY, type_scale.SIZE_SMALL, type_scale.SIZE_BODY, type_scale.SIZE_HEADING]

    assert sizes == sorted(set(sizes))
    assert type_scale.FONT_UI == fonts.FONT_UI


def test_a_window_and_a_drawing_letter_at_the_same_sizes():
    assert (fonts.SIZE_TINY, fonts.SIZE_SMALL, fonts.SIZE_BODY, fonts.SIZE_HEADING) == (
        type_scale.SIZE_TINY, type_scale.SIZE_SMALL, type_scale.SIZE_BODY, type_scale.SIZE_HEADING)


def test_a_size_in_pixels_is_its_height_on_a_96_dpi_screen():
    assert type_scale.in_pixels(9) == 12
    assert type_scale.in_pixels(18) == 24
    assert type_scale.in_pixels(8) == 11


def test_the_sizes_are_read_without_loading_qt():
    assert not {"PySide6"} & toolkits_loaded_by_importing("shared_ui.type_scale")
