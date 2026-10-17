"""shared_ui.loading_window: the family's loading screen as a Qt window, for
the apps that boot in Qt."""

from __future__ import annotations

import logging

import pytest
from app_support import loading_screen
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from shared_ui import loading_window
from shared_ui.loading_panel import render
from shared_ui.loading_window import Loading, LoadingCanceled, LoadingWindow


def _window(**changes) -> LoadingWindow:
    return LoadingWindow(**{
        "caption": "Scripture Loading", "wordmark": "Scripture", "icon": None, "preview": None,
        "steps": ("Checking the tracker...", "Loading...", "Building the window..."),
        **changes,
    })


class TestTheWindow:
    def test_it_is_the_panel_alone_under_the_caption_the_app_gives_it(self, qapp):
        window = _window()

        assert window.windowTitle() == "Scripture Loading"
        assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
        assert (window.width(), window.height()) == render(window.panel).size


    def test_it_comes_up_in_front_with_the_keyboard_whoever_started_its_process(
            self, qapp, monkeypatch):
        # Started from a launcher link, an app's process is one Windows will not
        # let take the foreground: the screen opened under the window the user
        # clicked in, and Esc went to that window.
        brought: list = []
        monkeypatch.setattr(loading_window, "bring_to_front", brought.append)
        window = _window()

        window.show()

        assert brought == [window]
        window.close()


class TestWhatItSays:
    def test_it_opens_on_the_first_step_with_nothing_done_yet(self, qapp):
        window = _window()

        assert (window.panel.status, window.panel.fraction) == ("Checking the tracker...", 0.0)

    def test_a_step_said_puts_its_words_up_and_the_work_before_it_on_the_bar(self, qapp):
        window = _window(steps=(("Checking the tracker...", 3.0), ("Loading...", 1.0), "Building the window..."))

        window.say("Loading...")
        assert (window.panel.status, window.panel.fraction) == ("Loading...", 0.6)

        window.say("Building the window...")
        assert (window.panel.status, window.panel.fraction) == ("Building the window...", 0.8)

    def test_words_that_are_no_step_of_the_plan_leave_the_bar_where_it_was(self, qapp):
        window = _window()
        window.say("Loading...")

        window.say("Reading twelve scripts...")

        assert window.panel.status == "Reading twelve scripts..."
        assert window.panel.fraction == 1 / 3


class TestCanceling:
    def test_esc_keeps_the_window_up_saying_it_is_canceling_and_tells_the_boot(self, qapp):
        window = _window(cancel_hint="Press Esc to cancel opening Scripture")
        told = []
        window.canceled.connect(lambda: told.append(True))
        assert window.panel.hint == "Press Esc to cancel opening Scripture"

        QTest.keyClick(window, Qt.Key.Key_Escape)

        assert told == [True]
        assert (window.panel.status, window.panel.hint) == ("Canceling...", "")
        window.say("Loading...")
        assert window.panel.status == "Canceling..."


class TestTheLoading:
    def test_without_a_window_each_step_goes_to_the_log(self, qapp, caplog):
        loading = Loading(qapp, logging.getLogger("test.boot"), None)

        with caplog.at_level(logging.INFO, logger="test.boot"):
            loading.say("Opening the image library...")

        assert "Boot: Opening the image library..." in caplog.text

    def test_a_start_from_a_launcher_with_a_loading_screen_opens_its_window(self, qapp, monkeypatch, tmp_path):
        monkeypatch.setenv(loading_screen.FOLDER, str(tmp_path / "screen"))
        monkeypatch.setenv(loading_screen.LINES, '["Updating Scripture..."]')
        window = _window()

        loading = Loading.at_the_click(qapp, logging.getLogger("test.boot"), lambda: window)
        loading.say("Loading...")

        assert window.panel.status == "Loading..."

    def test_any_other_start_opens_none_and_says_each_step_to_the_log(self, qapp, monkeypatch, caplog):
        monkeypatch.delenv(loading_screen.FOLDER, raising=False)
        opened = []

        loading = Loading.at_the_click(qapp, logging.getLogger("test.boot"), lambda: opened.append(_window()))
        with caplog.at_level(logging.INFO, logger="test.boot"):
            loading.say("Loading...")

        assert opened == []
        assert "Boot: Loading..." in caplog.text

    def test_a_cancel_stops_the_start_at_its_next_step(self, qapp):
        window = _window(cancel_hint="Press Esc to cancel opening Scripture")
        loading = Loading(qapp, logging.getLogger("test.boot"), window)
        loading.say("Loading...")

        QTest.keyClick(window, Qt.Key.Key_Escape)

        with pytest.raises(LoadingCanceled):
            loading.say("Building the window...")
        assert window.panel.status == "Canceling..."

    def test_done_takes_the_window_down(self, qapp):
        window = _window()
        window.show()
        loading = Loading(qapp, logging.getLogger("test.boot"), window)

        loading.done()

        assert not window.isVisible()
        assert window.result() == LoadingWindow.DialogCode.Accepted.value


class TestTakingOverFromTheLaunchersScreen:
    @pytest.fixture
    def place(self, tmp_path, monkeypatch, qapp):
        monkeypatch.setenv(loading_screen.FOLDER, str(tmp_path / "screen"))
        monkeypatch.setenv(loading_screen.LINES, '["Updating Scripture..."]')
        monkeypatch.setattr(loading_window, "bring_to_front", lambda window: None)
        return loading_screen.meeting_place({loading_screen.FOLDER: str(tmp_path / "screen"),
                                             loading_screen.LINES: '["Updating Scripture..."]'})

    def test_it_opens_where_the_launchers_screen_stood_with_its_bar_carried_on(self, place):
        place.stand(loading_screen.Shown(left=10, top=20, fraction=0.4))

        window = _window()
        opened_at = (window.pos().x(), window.pos().y(), window.panel.fraction)
        window.say("Loading...")

        assert opened_at == (10, 20, 0.4)
        assert window.panel.fraction == pytest.approx(0.4 + 0.6 / 3)

    def test_once_up_it_tells_the_launchers_screen_to_go_and_leaves_its_pictures(self, place):
        place.stand(loading_screen.Shown(left=10, top=20, fraction=0.4))
        window = _window()

        window.show()
        QTest.qWait(50)
        window.close()

        assert place.taken
        pictures = place.pictures()
        assert not pictures.covers_every_monitor
        assert pictures.updating("Updating Scripture...") is not None
