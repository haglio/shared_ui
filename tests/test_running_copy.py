from __future__ import annotations

import os
import threading
import time
import uuid

from PyQt6.QtCore import QObject, pyqtSignal

from shared_ui.running_copy import _hear, _pipe_server, ask, listen


def _name() -> str:
    return f"running_copy_test_{uuid.uuid4().hex}"


def _soon() -> float:
    return time.monotonic() + 10.0


def _pumped_until_it_finishes(qapp, work):
    done = []
    thread = threading.Thread(target=lambda: done.append(work()), daemon=True)
    thread.start()
    deadline = time.monotonic() + 15.0
    while thread.is_alive() and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    assert done, "the asking never finished"
    return done[0]


def _pump_until(qapp, condition) -> None:
    deadline = time.monotonic() + 10.0
    while not condition() and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)


def test_nothing_listening_is_no_answer():
    assert ask(_name(), b"hello", until=_soon()) is None


def test_the_running_copy_replies_and_says_which_process_it_is(qapp):
    name = _name()
    heard = []

    def reply_showing(said, reply):
        heard.append(said)
        reply(b"showing")

    server = listen(name, reply_showing)
    try:
        answer = _pumped_until_it_finishes(qapp, lambda: ask(name, b"open", until=_soon()))
    finally:
        server.close()

    assert (answer.reply, answer.pid) == (b"showing", os.getpid())
    assert heard == [b"open"]


def test_a_caller_that_is_not_replied_to_is_let_go_rather_than_kept_waiting(qapp):
    name = _name()
    server = listen(name, lambda said, reply: None)
    try:
        started = time.monotonic()
        answer = _pumped_until_it_finishes(qapp, lambda: ask(name, b"open", until=started + 10.0))
    finally:
        server.close()

    assert answer.reply == b""
    assert time.monotonic() - started < 5.0


def test_saying_nothing_still_reaches_the_running_copy_and_waits_for_nothing(qapp):
    name = _name()
    heard = []
    server = listen(name, lambda said, reply: heard.append(said))
    try:
        started = time.monotonic()
        assert ask(name, b"", until=started + 10.0) is not None
        assert time.monotonic() - started < 5.0
        _pump_until(qapp, lambda: heard)
    finally:
        server.close()

    assert heard == [b""]


def test_a_caller_is_heard_once_however_it_goes_on_to_hang_up(qapp):
    name = _name()
    heard = []
    server = listen(name, lambda said, reply: heard.append(said))
    try:
        _pumped_until_it_finishes(qapp, lambda: ask(name, b"open", until=_soon()))
        for _ in range(20):
            qapp.processEvents()
            time.sleep(0.01)
    finally:
        server.close()

    assert heard == [b"open"]


def test_a_name_that_cannot_be_listened_on_is_for_the_server_to_say(qapp):
    server = listen("", lambda said, reply: None)

    assert not server.isListening()


def test_a_handle_that_is_no_pipe_names_no_process():
    assert _pipe_server(0) == 0


class _Caller(QObject):
    readyRead = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, waiting: bytes) -> None:
        super().__init__()
        self._waiting = waiting

    def bytesAvailable(self) -> int:
        return len(self._waiting)

    def readAll(self) -> bytes:
        return self._waiting

    def disconnectFromServer(self) -> None:
        pass


def test_what_a_caller_said_before_it_was_accepted_is_heard_at_once(qapp):
    heard = []

    _hear(_Caller(b"open"), lambda said, reply: heard.append(said))

    assert heard == [b"open"]
