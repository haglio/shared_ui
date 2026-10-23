"""shared_ui.pages: an HTML page or a style sheet names the family's look and gets it spelled."""

from __future__ import annotations

import pytest

from shared_ui import pages, palette


def test_a_page_names_its_colors_and_gets_the_palettes_spelling_of_each():
    page = "body { background: __PALETTE_BG_PRIMARY__; color: __PALETTE_TEXT_PRIMARY__; }"

    assert pages.with_family_look(page) == (
        f"body {{ background: {palette.as_hex(palette.BG_PRIMARY)}; "
        f"color: {palette.as_hex(palette.TEXT_PRIMARY)}; }}")


def test_a_page_names_its_face_sizes_and_spacing_and_gets_each_in_pixels():
    page = ("body { font-family: '__TYPE_FONT_UI__'; font-size: __TYPE_SIZE_BODY__; "
            "padding: __SPACING_GAP_SMALL__ __SPACING_MARGIN_DIALOG__; }")

    assert pages.with_family_look(page) == (
        "body { font-family: 'Segoe UI'; font-size: 15px; padding: 4px 16px; }")


@pytest.mark.parametrize("named", ["__PALETTE_TEAL__", "__TYPE_SIZE_HUGE__", "__SPACING_GAP_WIDE__"])
def test_a_page_naming_what_the_family_lacks_is_refused(named):
    with pytest.raises(KeyError):
        pages.with_family_look(f"a {{ color: {named}; }}")
