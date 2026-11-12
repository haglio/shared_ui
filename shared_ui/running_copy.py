from __future__ import annotations

import ctypes
import ctypes.wintypes
import time
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtNetwork import QLocalServer, QLocalSocket

_SEND_TIMEOUT_MS = 2000

Answering = Callable[[bytes, Callable[[bytes], None]], None]


@dataclass(frozen=True)
class Answer:
    reply: bytes
    pid: int


def listen(name: str, answer: Answering) -> QLocalServer:
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    QLocalServer.removeServer(name)
    server.listen(name)

    def accept() -> None:
        connection = server.nextPendingConnection()
        if connection is not None:
            _hear(connection, answer)

    server.newConnection.connect(accept)
    return server


def _hear(connection: QLocalSocket, answer: Answering) -> None:
    answered = []

    def once() -> None:
        if not answered:
            answered.append(True)
            _answer(connection, bytes(connection.readAll()), answer)

    connection.readyRead.connect(once)
    connection.disconnected.connect(once)
    if connection.bytesAvailable():
        once()


def _answer(connection: QLocalSocket, said: bytes, answer: Answering) -> None:
    ended = []

    def reply(words: bytes = b"") -> None:
        if ended:
            return
        ended.append(True)
        if said and words:
            connection.write(words)
            connection.waitForBytesWritten(_SEND_TIMEOUT_MS)
        connection.disconnectFromServer()
        connection.deleteLater()

    answer(said, reply)
    reply()


def ask(name: str, said: bytes, *, until: float) -> Answer | None:
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(_milliseconds_until(until)):
        return None
    pid = _pipe_server(int(socket.socketDescriptor()))
    socket.write(said)
    socket.waitForBytesWritten(_milliseconds_until(until))
    if said and not socket.bytesAvailable():
        socket.waitForReadyRead(_milliseconds_until(until))
    reply = bytes(socket.readAll())
    socket.disconnectFromServer()
    return Answer(reply, pid)


def _milliseconds_until(moment: float) -> int:
    return max(0, round((moment - time.monotonic()) * 1000))


def _pipe_server(handle: int) -> int:
    pid = ctypes.wintypes.ULONG()
    found = ctypes.windll.kernel32.GetNamedPipeServerProcessId(  # type: ignore[attr-defined]
        ctypes.c_void_p(handle), ctypes.byref(pid))
    return pid.value if found else 0
