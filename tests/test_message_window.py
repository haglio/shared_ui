from __future__ import annotations

import pytest
from PySide6.QtCore import QRect, Qt, QTimer

from shared_ui.message_shape import HEARD_MARK, MESSAGE_TOP_MARGIN
from shared_ui.message_window import FOLLOW_EVERY_MS, MessageWindow

_FUNESTRA = QRect(2560, 0, 800, 600)
_FUNESTRAS_WINDOW = 4242
_LONG = ("an answer that runs on and on about every change it made to the prompt, "
         "far longer than any Funestra is wide")


class _Stacking:
    def __init__(self) -> None:
        self.asked: list[tuple[int, int]] = []

    def __call__(self, own: int, beneath: int) -> bool:
        self.asked.append((own, beneath))
        return True


@pytest.fixture
def stacking() -> _Stacking:
    return _Stacking()


@pytest.fixture
def message(qapp, stacking):
    message = MessageWindow(stack=stacking)
    yield message
    message.close()


def _follow(message: MessageWindow) -> QTimer:
    return message.findChild(QTimer)


def test_the_message_is_a_window_of_its_own_that_windows_over_the_funestra_cover_too(message):
    assert message.isWindow()
    assert not message.windowFlags() & Qt.WindowType.WindowStaysOnTopHint


def test_the_message_takes_neither_the_keyboard_nor_a_click_from_the_funestra_beneath(message):
    assert message.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    assert message.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert message.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


def test_the_message_comes_up_across_the_top_of_the_funestra_in_the_middle(message):
    message.say_over(_FUNESTRA, "scene one")

    note = message.geometry()
    assert message.isVisible()
    assert note.top() == _FUNESTRA.top() + MESSAGE_TOP_MARGIN
    assert abs(note.center().x() - _FUNESTRA.center().x()) <= 1


@pytest.mark.parametrize("mark", ["", HEARD_MARK])
def test_a_message_too_long_for_the_funestra_is_elided_to_fit(message, mark):
    narrow = QRect(2560, 0, 400, 300)

    message.say_over(narrow, _LONG, mark=mark)

    assert (message.geometry().left() >= narrow.left() + MESSAGE_TOP_MARGIN,
            message.geometry().right() < narrow.right() - MESSAGE_TOP_MARGIN,
            "…" in message.text()) == (True, True, True)


def test_a_message_follows_its_funestra_when_the_funestra_widens(message):
    message.say_over(QRect(2560, 0, 400, 300), _LONG)

    message.reposition_over(QRect(2560, 0, 4000, 300))

    assert message.text() == _LONG


def test_a_message_that_fits_is_shown_whole(message):
    message.say_over(_FUNESTRA, "scene one")

    assert message.text() == "scene one"


def test_the_message_comes_up_stacked_directly_on_the_funestras_window(message, stacking):
    message.stay_above(_FUNESTRAS_WINDOW)

    message.say_over(_FUNESTRA, "scene one")

    assert stacking.asked == [(int(message.winId()), _FUNESTRAS_WINDOW)]


def test_the_message_follows_the_funestra_back_up_while_it_shows(message, stacking):
    message.stay_above(_FUNESTRAS_WINDOW)
    message.say_over(_FUNESTRA, "scene one")

    _follow(message).timeout.emit()

    assert (_follow(message).interval(), len(stacking.asked)) == (FOLLOW_EVERY_MS, 2)


def test_a_message_gone_from_the_screen_stops_following_the_funestra(message, stacking):
    message.stay_above(_FUNESTRAS_WINDOW)
    message.say_over(_FUNESTRA, "scene one")
    message.hide()
    stacking.asked.clear()

    _follow(message).timeout.emit()

    assert (stacking.asked, _follow(message).isActive()) == ([], False)


def test_before_the_funestra_names_its_window_the_message_is_stacked_onto_nothing(
        message, stacking):
    message.say_over(_FUNESTRA, "scene one")

    assert stacking.asked == []


def test_a_message_shut_down_is_off_the_screen(message):
    message.say_over(_FUNESTRA, "scene one")

    message.shutdown()

    assert not message.isVisible()


def test_a_message_wider_than_its_funestra_starts_at_the_funestras_left_edge(message):
    message.setMinimumWidth(400)

    message.say_over(QRect(100, 0, 120, 400), "scene one")

    assert message.x() == 100
