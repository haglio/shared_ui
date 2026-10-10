"""shared_ui.loading_window: the family's loading screen as a Qt window, for
the apps that boot in Qt."""

from __future__ import annotations

import logging

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

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
