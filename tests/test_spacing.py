from __future__ import annotations

from shared_ui import spacing


def _all_spacing_constants():
    for name in dir(spacing):
        if name.startswith("_"):
            continue
        val = getattr(spacing, name)
        if isinstance(val, int):
            yield name, val


class TestSpacingTokens:
    def test_all_positive(self):
        for name, val in _all_spacing_constants():
            assert val > 0, f"{name} should be positive, got {val}"


class TestButtonGrouping:

    def test_a_group_boundary_is_wider_than_the_gap_inside_a_group(self):
        assert spacing.BUTTON_GROUP_GAP > spacing.BUTTON_GAP

    def test_the_group_gap_is_stated_as_a_ratio_of_the_gap_inside_one(self):
        assert spacing.BUTTON_GROUP_GAP == spacing.BUTTON_GAP * 3

    def test_a_group_boundary_still_fits_inside_a_button(self):
        assert spacing.BUTTON_GROUP_GAP < spacing.BUTTON_SIZE


class TestIcons:
    def test_an_icon_set_beside_a_word_is_smaller_than_an_icon_that_fills_its_square(self):
        assert spacing.BUTTON_ICON < spacing.BUTTON_FILLING_ICON


class TestTheHudSquare:
    def test_its_corner_is_the_ordinary_corner_scaled_down_to_it(self):
        scaled = round(spacing.BUTTON_RADIUS * spacing.BUTTON_SIZE_HUD / spacing.BUTTON_SIZE)

        assert scaled == spacing.BUTTON_RADIUS_HUD


class TestADialog:
    def test_its_margin_is_twice_the_ordinary_one(self):
        assert spacing.MARGIN_DIALOG == 2 * spacing.MARGIN_STANDARD

    def test_its_gap_is_twice_the_ordinary_one(self):
        assert spacing.GAP_DIALOG == 2 * spacing.GAP_MEDIUM


class TestARowOfButtons:
    def test_wrapped_rows_stand_further_apart_than_buttons_along_a_row(self):
        assert spacing.BUTTON_ROW_GAP > spacing.BUTTON_GAP

    def test_a_word_button_is_as_wide_as_two_hud_squares_and_the_gap_between_them(self):
        assert spacing.BUTTON_WORD_W == 2 * spacing.BUTTON_SIZE_HUD + spacing.BUTTON_GAP

    def test_a_row_that_has_to_fit_a_strip_pads_its_words_less(self):
        assert spacing.BUTTON_PAD_H_TIGHT < spacing.BUTTON_PAD_H

    def test_an_icon_that_fills_its_square_stays_inset_on_both_sides(self):
        assert spacing.BUTTON_FILLING_ICON == spacing.BUTTON_SIZE - 2 * spacing.BUTTON_ICON_INSET
