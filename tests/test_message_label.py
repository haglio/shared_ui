from __future__ import annotations

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from shared_ui.icons import icon_then_text
from shared_ui.message_label import MessageLabel, set_marked_text
from shared_ui.message_shape import (
    ERROR,
    FAVORITE,
    HEARD_MARK,
    INFO,
    MESSAGE_INK,
    WARNING,
    time_to_read_ms,
)
from shared_ui.palette import GREEN, RED, TEXT_PRIMARY, YELLOW

_LONG = ("an answer that runs on and on about every change it made, far longer than any "
         "Funestra is wide")


def test_each_kind_of_message_has_its_own_color():
    assert MESSAGE_INK == {INFO: TEXT_PRIMARY, WARNING: YELLOW, ERROR: RED, FAVORITE: GREEN}


def test_a_short_message_stays_up_three_seconds():
    assert time_to_read_ms("Locked") == 3000


def test_a_longer_message_stays_up_a_quarter_second_longer_for_each_word():
    words = " ".join(["word"] * 20)

    assert time_to_read_ms(words) - time_to_read_ms(words + " more") == -250


@pytest.fixture
def host() -> QWidget:
    return QWidget()


def _a_message(host) -> MessageLabel:
    return MessageLabel(host)


@pytest.mark.parametrize("kind", [INFO, WARNING, ERROR, FAVORITE])
def test_a_message_is_drawn_in_the_color_of_its_kind(host, kind):
    message = _a_message(host)

    message.say("scene one", kind=kind)

    assert f"color: {QColor(*MESSAGE_INK[kind]).name()};" in message.styleSheet()


def test_a_message_with_no_mark_is_its_plain_text(host):
    message = _a_message(host)

    message.say("Videos only")

    assert message.text() == "Videos only"


def test_a_message_that_answers_what_was_said_starts_with_the_microphone(host):
    message = _a_message(host)

    message.say("Locked", mark=HEARD_MARK)

    assert message.text() == icon_then_text(HEARD_MARK, "Locked", color=QColor(*TEXT_PRIMARY),
                                            size=message.fontMetrics().height())


@pytest.mark.parametrize("mark", ["", HEARD_MARK])
def test_a_message_too_long_for_its_room_is_elided_to_fit(host, mark):
    message = _a_message(host)
    message.say(_LONG, mark=mark)

    message.fit_into(300)

    assert (message.width() <= 300, "…" in message.text()) == (True, True)


def test_a_message_that_is_a_window_of_its_own_is_elided_to_fit_too():
    message = MessageLabel()
    message.say(_LONG * 3)

    message.fit_into(300)

    assert (message.width() <= 300, "…" in message.text()) == (True, True), (
        "Qt holds a window's own size to two thirds of its screen, so the room is measured "
        "against the whole text rather than against the width the window was given")


def test_a_message_given_room_again_is_shown_whole(host):
    message = _a_message(host)
    message.say(_LONG)
    message.fit_into(300)

    message.fit_into(10000)

    assert message.text() == _LONG


def test_marked_text_on_any_label_puts_the_drawing_before_the_words(host):
    message = _a_message(host)

    set_marked_text(message, "can't remake this", mark="warning", color=QColor(*YELLOW))

    assert message.text() == icon_then_text("warning", "can't remake this", color=QColor(*YELLOW),
                                            size=message.fontMetrics().height())
