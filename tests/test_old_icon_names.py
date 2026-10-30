from __future__ import annotations

from shared_ui import (
    alert,
    icon_button,
    icon_geometry,
    icons,
    icons_pil,
    icons_svg,
    mark_button,
    spacing,
)
from shared_ui.folder_path import FolderPath


def test_each_name_from_before_icon_was_the_word_still_answers_for_a_branch_not_yet_rebased():
    assert icons.draw_glyph is icons.draw_icon
    assert icons.draw_glyph_filling is icons.draw_icon_filling
    assert icons.glyph_icon is icons.qt_icon
    assert icons.glyph_pixmap is icons.icon_pixmap
    assert icons.inline_mark is icons.inline_icon
    assert icons.marked_text is icons.icon_then_text
    assert icons_pil.glyph_image is icons_pil.pil_icon
    assert icons_pil.paste_glyph is icons_pil.paste_icon
    assert icons_svg.svg_mark is icons_svg.svg_icon
    assert icon_geometry.GLYPHS is icon_geometry.ICONS
    assert icon_geometry.glyph_names is icon_geometry.icon_names
    assert spacing.BUTTON_MARK_INSET == spacing.BUTTON_ICON_INSET
    assert spacing.BUTTON_MARK == spacing.BUTTON_FILLING_ICON
    assert mark_button.fill_square_with_mark is icon_button.fill_square_with_icon
    assert alert.mark_pixmap is alert.icon_pixmap_for


def test_a_folder_path_still_takes_its_icons_by_their_old_keyword():
    by_their_word, by_the_old_one = FolderPath("  ›  "), FolderPath("  ›  ")

    by_their_word.set_path(["All", "Favorites"], icons={1: "star"})
    by_the_old_one.set_path(["All", "Favorites"], marks={1: "star"})

    assert by_the_old_one.text() == by_their_word.text()
