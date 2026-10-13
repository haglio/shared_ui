"""shared_ui.toggle_geometry: the family's on/off switch as sizes and places, for every toolkit that draws it."""

from __future__ import annotations

import pytest

from shared_ui.spacing import BUTTON_SIZE_HUD
from shared_ui.toggle_geometry import HANDLE_INSET, TRACK, TRACK_HUD, handle

_TRACK_AT = (10, 20, *TRACK)


def test_the_handle_rests_against_the_left_end_while_off():
    x, y, diameter = handle(_TRACK_AT, on=False, inset=HANDLE_INSET)

    assert x == 10 + HANDLE_INSET
    assert y == 20 + HANDLE_INSET
    assert diameter == TRACK[1] - 2 * HANDLE_INSET


def test_the_handle_rests_against_the_right_end_while_on():
    x, _y, diameter = handle(_TRACK_AT, on=True, inset=HANDLE_INSET)

    assert x + diameter == 10 + TRACK[0] - HANDLE_INSET


def test_a_hud_switch_fits_a_hud_buttons_row_in_the_desktop_switchs_proportions():
    width, height = TRACK_HUD

    assert height < BUTTON_SIZE_HUD
    assert width / height == pytest.approx(TRACK[0] / TRACK[1], rel=0.1)
