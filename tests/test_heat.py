"""shared_ui.heat: a funscript's speed as one of the family's colors."""

from __future__ import annotations

from shared_ui import heat, palette


def test_a_still_script_is_the_ground_and_the_fastest_is_red():
    assert heat.heat_at(0) == palette.BG_PRIMARY
    assert heat.heat_at(500) == palette.RED
    assert heat.heat_at(900) == palette.RED


def test_each_step_of_speed_reaches_the_next_family_color():
    assert [heat.heat_at(speed) for speed in (100, 200, 300, 400)] == [
        palette.BLUE, palette.BLUE_LIGHT, palette.GREEN, palette.AMBER]


def test_a_speed_between_two_steps_is_the_color_between_them():
    between = heat.heat_at(150)

    assert between == tuple(round((a + b) / 2) for a, b in zip(palette.BLUE, palette.BLUE_LIGHT, strict=True))
