"""shared_ui.loading_process: the family's loading window in a process of its own."""

from __future__ import annotations

import io
import subprocess
import sys
import time
from unittest.mock import patch

from shared_ui.loading_process import LoadingProcess, run, serve
from shared_ui.loading_window import LoadingWindow


def _window(**changes) -> LoadingWindow:
    return LoadingWindow(**{
        "caption": "Scripture Loading", "wordmark": "Scripture", "icon": None, "preview": None,
        "steps": ("Checking the tracker...", "Loading...", "Building the window..."),
        **changes,
    })


def _until(app, holds, seconds: float = 2.0) -> bool:
    deadline = time.monotonic() + seconds
    while not holds() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return holds()


class TestTheWindowsSide:
    def test_the_window_says_each_step_the_start_sends_it(self, qapp):
        window = _window()

        serve(window, io.StringIO("Loading...\n"), io.StringIO(), quit=lambda: None)

        assert _until(qapp, lambda: window.panel.status == "Loading...")

    def test_esc_on_the_window_tells_the_start_to_stop(self, qapp):
        window = _window()
        told = io.StringIO()
        serve(window, io.StringIO(), told, quit=lambda: None)

        window.reject()

        assert told.getvalue() == "cancel\n"

    def test_the_window_goes_when_the_start_stops_talking_to_it_without_canceling(self, qapp):
        window = _window()
        window.show()
        told = io.StringIO()
        quit_asked = []

        serve(window, io.StringIO(""), told, quit=lambda: quit_asked.append(window.isVisible()))

        assert _until(qapp, lambda: quit_asked == [False])
        assert told.getvalue() == ""


def _a_window_process(script: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", script], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


class TestTheStartsSide:
    def test_the_start_hears_when_the_window_is_canceled(self, qapp):
        window = LoadingProcess(_a_window_process(
            "import sys; print('cancel', flush=True); sys.stdin.read()"))
        heard = []
        window.canceled.connect(lambda: heard.append(True))

        assert _until(qapp, lambda: heard == [True])
        window.accept()

    def test_each_step_reaches_the_window_and_the_window_goes_when_the_start_is_done(
            self, qapp, tmp_path):
        said = tmp_path / "said.txt"
        process = _a_window_process(
            f"import sys; open({str(said)!r}, 'w', encoding='utf-8').write(sys.stdin.read())")
        window = LoadingProcess(process)

        window.say("Loading...")
        window.say("Building the window...")
        window.accept()

        assert process.returncode == 0
        assert said.read_text(encoding="utf-8").splitlines() == [
            "Loading...", "Building the window..."]


    def test_a_window_that_will_not_go_is_ended_rather_than_waited_on_for_good(
            self, qapp, monkeypatch):
        monkeypatch.setattr("shared_ui.loading_process.GONE_WITHIN_S", 0.2)
        process = _a_window_process("import time; time.sleep(30)")
        window = LoadingProcess(process)

        assert window.accept() is None
        assert process.wait(timeout=5) is not None


class TestTheWholeWay:
    def test_a_window_process_shows_itself_and_goes_when_the_start_is_done(self, qapp):
        window = LoadingProcess.open(
            caption="Scripture Loading", wordmark="Scripture", icon=None, preview=None,
            steps=("Checking the tracker...", "Loading..."),
            cancel_hint="Press Esc to cancel opening Scripture")
        shown = []
        window.shown.connect(shown.append)

        assert _until(qapp, lambda: bool(shown), seconds=60)
        window.say("Loading...")
        assert window.accept() == 0

    def test_a_preview_window_wears_the_apps_taskbar_identity_and_says_where_it_is(self, qapp):
        told = io.StringIO()
        with patch("app_support.win32.dress_window") as dress:
            code = run({
                "caption": "Scripture Loading", "wordmark": "Scripture", "icon": None,
                "preview": "the scene list", "is_preview": True,
                "steps": [["Checking the tracker...", 3.0], "Loading..."],
                "cancel_hint": "", "app_id": "Example.App.Preview",
            }, io.StringIO("Loading..." + chr(10)), told, qapp)

        assert code == 0
        (hwnd, app_id), _ = dress.call_args
        assert app_id == "Example.App.Preview"
        assert told.getvalue().splitlines() == [f"shown {hwnd}"]
