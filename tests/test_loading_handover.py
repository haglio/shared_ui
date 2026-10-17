"""shared_ui.loading_handover: an app's loading screen taking over from the one
its launcher showed from the click."""

from __future__ import annotations

from dataclasses import replace

import pytest
from app_support import loading_screen
from PIL import Image

from shared_ui.loading_handover import TakingOver
from shared_ui.loading_panel import LoadingPanel, bar_box, render

PANEL = LoadingPanel(wordmark="Example", status="Starting...", fraction=0.0, hint="Press Esc to cancel")


@pytest.fixture
def launched(tmp_path):
    """The environment a launcher with a loading screen starts its app with."""
    return {loading_screen.FOLDER: str(tmp_path / "screen"),
            loading_screen.LINES: '["Updating Example...", "Updating Hosted..."]'}


def _place(environment) -> loading_screen.MeetingPlace:
    return loading_screen.meeting_place(environment)


class TestStartingWithoutTheLaunchersScreen:
    def test_an_app_started_any_other_way_fills_its_bar_from_empty_where_it_always_stood(self):
        taking_over = TakingOver.from_the_launcher({})

        assert (taking_over.carried(0.25), taking_over.panel_at) == (0.25, None)

    def test_nor_has_it_anywhere_to_leave_pictures(self):
        TakingOver.from_the_launcher({}).done(PANEL, covers_every_monitor=False)

    def test_a_launcher_whose_screen_is_not_up_hands_nothing_over(self, launched):
        taking_over = TakingOver.from_the_launcher(launched)

        assert (taking_over.carried(0.25), taking_over.panel_at) == (0.25, None)


class TestTakingOver:
    def test_the_bar_carries_on_from_where_the_launchers_screen_got(self, launched):
        _place(launched).stand(loading_screen.Shown(left=10, top=20, fraction=0.5))

        taking_over = TakingOver.from_the_launcher(launched)

        assert [taking_over.carried(own) for own in (0.0, 0.5, 1.0)] == [0.5, 0.75, 1.0]

    def test_the_panel_goes_where_the_launchers_screen_stood(self, launched):
        _place(launched).stand(loading_screen.Shown(left=10, top=20, fraction=0.5))

        assert TakingOver.from_the_launcher(launched).panel_at == (10, 20)

    def test_once_it_is_up_the_launchers_screen_is_told_to_go(self, launched):
        _place(launched).stand(loading_screen.Shown(left=10, top=20, fraction=0.5))

        TakingOver.from_the_launcher(launched).done(PANEL, covers_every_monitor=False)

        assert _place(launched).taken


def _picture(path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


class TestThePicturesForTheNextClick:
    @pytest.fixture
    def pictures(self, launched):
        TakingOver.from_the_launcher(launched).done(replace(PANEL, fraction=0.7), covers_every_monitor=True)
        return _place(launched).pictures()

    def test_the_next_click_opens_on_the_panel_this_screen_opened_on_with_the_bar_empty(self, pictures):
        assert _picture(pictures.opening).tobytes() == render(PANEL).tobytes()

    def test_the_next_click_fills_its_bar_with_this_panels_own_fill(self, pictures):
        assert _picture(pictures.full).tobytes() == render(replace(PANEL, fraction=1.0)).tobytes()
        assert pictures.bar == bar_box()

    def test_each_line_the_launcher_says_while_it_waits_is_this_panel_saying_it(self, pictures):
        for line in ("Updating Example...", "Updating Hosted..."):
            assert _picture(pictures.updating(line)).tobytes() == render(replace(PANEL, status=line)).tobytes()

    def test_the_next_click_stands_where_this_screen_stands(self, pictures):
        assert pictures.covers_every_monitor
