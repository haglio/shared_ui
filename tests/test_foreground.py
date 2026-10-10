"""shared_ui.foreground: a window put in front with the keyboard when it opens."""

from __future__ import annotations

import pytest

from shared_ui import foreground
from shared_ui.foreground import bring_to_front


class _AWindow:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def raise_(self) -> None:
        self.asked.append("raise")

    def activateWindow(self) -> None:  # noqa: N802 - Qt's name
        self.asked.append("activate")

    def winId(self) -> int:  # noqa: N802 - Qt's name
        return 4321


def test_qt_asks_first_and_windows_is_then_made_to_put_the_window_in_front(monkeypatch):
    # Qt's raise and activate go down the very path Windows refuses to a process
    # the user is not looking at, so the forced call is what lands.
    forced: list[int] = []
    monkeypatch.setattr(foreground, "force_foreground_window", forced.append)
    monkeypatch.setattr(foreground, "_drawn_by_windows", lambda: True)
    window = _AWindow()

    bring_to_front(window)

    assert window.asked == ["raise", "activate"]
    assert forced == [4321]


@pytest.mark.usefixtures("qapp")
def test_a_window_windows_does_not_draw_is_never_handed_to_windows(monkeypatch):
    # Offscreen, as every suite here runs, a window's id is Qt's own counter
    # rather than a handle Windows gave out, so it names no window of this one.
    forced: list[int] = []
    monkeypatch.setattr(foreground, "force_foreground_window", forced.append)

    bring_to_front(_AWindow())

    assert forced == []
