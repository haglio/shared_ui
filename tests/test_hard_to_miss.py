from __future__ import annotations

import time
import winsound

import pytest
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QMainWindow, QMessageBox, QWidget

from shared_ui.hard_to_miss import FadedBackground, hard_to_miss, sure

_BLACK_AND_WHITE_AVERAGE = 127


@pytest.fixture(autouse=True)
def alert_sounds(monkeypatch):
    sounded = []
    monkeypatch.setattr(winsound, "MessageBeep", sounded.append)
    return sounded


class _Checkerboard(QWidget):
    def paintEvent(self, _event):
        painter = QPainter(self)
        for x in range(0, self.width(), 8):
            for y in range(0, self.height(), 8):
                white = (x // 8 + y // 8) % 2
                painter.fillRect(x, y, 8, 8, QColor("white") if white else QColor("black"))


def _until(app, holds, seconds: float = 2.0) -> bool:
    deadline = time.monotonic() + seconds
    while not holds() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return holds()


@pytest.fixture
def window(qapp):
    shown = QMainWindow()
    shown.setCentralWidget(_Checkerboard())
    shown.setGeometry(100, 120, 320, 200)
    shown.show()
    _until(qapp, shown.isVisible)
    qapp.processEvents()
    yield shown
    shown.close()
    shown.deleteLater()


def faded_backgrounds(window):
    return [faded for faded in window.findChildren(FadedBackground) if faded.isVisible()]


def _lightness_across_the_middle(grab):
    image = grab.toImage()
    return [image.pixelColor(x, image.height() // 2).lightness()
            for x in range(0, image.width(), 4)]


def _lightness_across_the_faded_window(window):
    with hard_to_miss(window):
        return _lightness_across_the_middle(faded_backgrounds(window)[0].grab())


def _answering(monkeypatch, button):
    asked = []
    monkeypatch.setattr(QMessageBox, "question",
                        staticmethod(lambda *args: asked.append(args) or button))
    return asked


def test_the_window_behind_goes_dark_and_out_of_focus(window):
    levels = _lightness_across_the_faded_window(window)

    assert max(levels) < _BLACK_AND_WHITE_AVERAGE
    assert max(levels) - min(levels) < 255 // 8


def test_the_window_behind_still_shows_through_the_dark(window):
    assert min(_lightness_across_the_faded_window(window)) > 0


def test_the_window_fades_rather_than_going_dark_at_once(qapp, window):

    with hard_to_miss(window):
        faded = faded_backgrounds(window)[0]
        opacity_at_first = faded.windowOpacity()
        _until(qapp, lambda: faded.windowOpacity() == 1.0)

    assert opacity_at_first == 0.0


def test_the_window_comes_back_the_moment_the_popup_is_done(window):

    with hard_to_miss(window):
        pass

    assert faded_backgrounds(window) == []


def test_the_window_comes_back_even_when_the_popup_fails(window):

    with pytest.raises(RuntimeError), hard_to_miss(window):
        raise RuntimeError

    assert faded_backgrounds(window) == []


def test_a_minimized_window_is_left_alone_and_the_alert_still_sounds(window, alert_sounds):
    window.showMinimized()

    with hard_to_miss(window):
        faded = faded_backgrounds(window)

    assert faded == []
    assert alert_sounds == [winsound.MB_ICONEXCLAMATION]


@pytest.mark.parametrize(("answer", "is_sure"), [
    (QMessageBox.StandardButton.Yes, True),
    (QMessageBox.StandardButton.No, False),
])
def test_sure_is_the_answer_to_a_yes_or_no_question(window, monkeypatch, answer, is_sure):
    _answering(monkeypatch, answer)

    assert sure(window, "Close It", "Are you sure?") is is_sure


def test_sure_asks_with_no_as_the_default(window, monkeypatch):
    asked = _answering(monkeypatch, QMessageBox.StandardButton.No)

    sure(window, "Close It", "Are you sure?")

    parent, title, text, buttons, default = asked[0]
    assert (parent, title, text) == (window, "Close It", "Are you sure?")
    assert buttons == QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    assert default == QMessageBox.StandardButton.No


def test_sure_asks_over_the_faded_window_and_sounds_the_alert(window, monkeypatch, alert_sounds):
    faded_while_asked = []
    monkeypatch.setattr(QMessageBox, "question", staticmethod(
        lambda *_args: faded_while_asked.extend(faded_backgrounds(window))
        or QMessageBox.StandardButton.No))

    sure(window, "Close It", "Are you sure?")

    assert [faded.geometry() for faded in faded_while_asked] == [window.geometry()]
    assert alert_sounds == [winsound.MB_ICONEXCLAMATION]
