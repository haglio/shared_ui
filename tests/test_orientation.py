from __future__ import annotations

from shared_ui.orientation import LANDSCAPE, ORIENTATIONS, PORTRAIT, orientation_of_size


def test_a_picture_taller_than_it_is_wide_is_portrait():
    assert orientation_of_size(1080, 1920) == PORTRAIT


def test_a_picture_wider_than_it_is_tall_is_landscape():
    assert orientation_of_size(1920, 1080) == LANDSCAPE


def test_a_square_is_landscape_as_the_family_has_always_filed_one():
    assert orientation_of_size(1024, 1024) == LANDSCAPE


def test_the_words_are_the_ones_the_family_has_already_stored():
    assert (PORTRAIT, LANDSCAPE) == ("portrait", "landscape")


def test_the_orientations_are_portrait_then_landscape():
    assert ORIENTATIONS == (PORTRAIT, LANDSCAPE)
