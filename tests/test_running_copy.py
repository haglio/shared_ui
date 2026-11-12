from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from shared_ui.running_copy import Answer, _hear, _pipe_server, ask, listen

REPO_ROOT = Path(__file__).resolve().parents[1]


def _name() -> str:
    return f"running_copy_test_{uuid.uuid4().hex}"


def _soon() -> float:
    return time.monotonic() + 10.0


def _asked_from_another_process(qapp, name: str, said: bytes, *, within_s: float = 10.0) -> Answer | None:
    asking = subprocess.Popen(
        [sys.executable, "-c", textwrap.dedent(f"""
            import json, time
            from shared_ui.running_copy import ask
            answer = ask({name!r}, {said!r}, until=time.monotonic() + {within_s})
            print(json.dumps(None if answer is None else [answer.reply.decode(), answer.pid]))
        """)], cwd=REPO_ROOT, stdout=subprocess.PIPE, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    deadline = time.monotonic() + within_s + 30.0
    while asking.poll() is None and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    assert asking.poll() is not None, "the asking never finished"
    found = json.loads(asking.stdout.read())
    return None if found is None else Answer(found[0].encode(), found[1])


def _listening_in_another_process(name: str, words: bytes) -> tuple[subprocess.Popen, int]:
    listening = subprocess.Popen(
        [sys.executable, "-c", textwrap.dedent(f"""
            import os
            from PySide6.QtCore import QCoreApplication, QTimer
            from shared_ui.running_copy import listen
            app = QCoreApplication([])

            def answer(said, reply):
                reply({words!r})
                QTimer.singleShot(0, app.quit)

            server = listen({name!r}, answer)
            QTimer.singleShot(20_000, app.quit)
            print(os.getpid(), flush=True)
            app.exec()
        """)], cwd=REPO_ROOT, stdout=subprocess.PIPE, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return listening, int(listening.stdout.readline())


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
        answer = _asked_from_another_process(qapp, name, b"open")
    finally:
        server.close()

    assert (answer.reply, answer.pid) == (b"showing", os.getpid())
    assert heard == [b"open"]


def test_the_asker_waits_for_the_running_copys_reply():
    name = _name()
    listening, its_pid = _listening_in_another_process(name, b"showing")

    answer = ask(name, b"open", until=_soon())

    assert (answer.reply, answer.pid) == (b"showing", its_pid)
    assert listening.wait(timeout=30) == 0


def test_a_caller_that_is_not_replied_to_is_let_go_rather_than_kept_waiting(qapp):
    name = _name()
    server = listen(name, lambda said, reply: None)
    try:
        started = time.monotonic()
        answer = _asked_from_another_process(qapp, name, b"open")
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
        _asked_from_another_process(qapp, name, b"open")
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
    readyRead = Signal()
    disconnected = Signal()

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
