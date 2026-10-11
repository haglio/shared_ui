"""The family's loading window in a process of its own.

An app's start keeps the thread its window would draw on busy, so a loading
window in the same process stops drawing and stops answering Esc, and Windows
marks it "Not Responding" until the start lets go. In a process of its own it
answers throughout: the start sends it each step over a pipe, and it tells the
start when the user cancels.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import IO, TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal

from shared_ui.loading_window import LoadingWindow
from shared_ui.preview import Preview

if TYPE_CHECKING:
    from app_support.win32 import TaskbarApp

CANCEL = "cancel"
SHOWN = "shown"
GONE_WITHIN_S = 5.0


class LoadingProcess(QObject):
    canceled = pyqtSignal()
    shown = pyqtSignal(int)

    def __init__(self, process: subprocess.Popen) -> None:
        super().__init__()
        self._process = process
        threading.Thread(target=self._listen, name="loading-window-listen", daemon=True).start()

    @classmethod
    def open(cls, *, caption: str, wordmark: str, icon: Path | None, preview: Preview | None,
             steps: Sequence[str | tuple[str, float]], cancel_hint: str = "",
             app_id: str | None = None, taskbar: TaskbarApp | None = None) -> LoadingProcess:
        spec = {
            "caption": caption, "wordmark": wordmark,
            "icon": None if icon is None else str(icon),
            "preview": None if preview is None else preview.feature,
            "is_preview": preview is not None,
            "steps": list(steps), "cancel_hint": cancel_hint, "app_id": app_id,
            "taskbar": None if taskbar is None else {
                "name": taskbar.name, "icon": str(taskbar.icon), "relaunch": taskbar.relaunch},
        }
        return cls(subprocess.Popen(
            [sys.executable, "-m", "shared_ui.loading_process", json.dumps(spec)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))

    def say(self, step: str) -> None:
        with contextlib.suppress(OSError, ValueError):
            print(" ".join(step.splitlines()), file=self._process.stdin, flush=True)

    def accept(self) -> int | None:
        with contextlib.suppress(OSError):
            self._process.stdin.close()
        try:
            return self._process.wait(timeout=GONE_WITHIN_S)
        except subprocess.TimeoutExpired:
            self._process.kill()
            return None

    def _listen(self) -> None:
        for line in self._process.stdout:
            word, _, rest = line.strip().partition(" ")
            if word == CANCEL:
                self.canceled.emit()
            elif word == SHOWN:
                self.shown.emit(int(rest))


class _Lines(QObject):
    said = pyqtSignal(str)
    ended = pyqtSignal()

    def __init__(self, stream: IO[str]) -> None:
        super().__init__()
        self._stream = stream

    def start(self) -> None:
        threading.Thread(target=self._read, name="loading-window-lines", daemon=True).start()

    def _read(self) -> None:
        for line in self._stream:
            self.said.emit(line.rstrip("\n"))
        self.ended.emit()


def serve(window: LoadingWindow, lines_in: IO[str], lines_out: IO[str],
          quit: Callable[[], None]) -> _Lines:
    lines = _Lines(lines_in)
    lines.said.connect(window.say)
    lines.ended.connect(window.accept)
    lines.ended.connect(quit)
    window.canceled.connect(lambda: _tell(lines_out, CANCEL))
    lines.start()
    return lines


def _tell(lines_out: IO[str], line: str) -> None:
    print(line, file=lines_out, flush=True)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover -- the window's own process, which coverage does not follow
    from PyQt6.QtWidgets import QApplication  # noqa: PLC0415

    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    app = QApplication(sys.argv[:1])
    return run(json.loads((sys.argv[1:] if argv is None else argv)[0]), sys.stdin, sys.stdout, app)


def run(spec: dict, lines_in: IO[str], lines_out: IO[str], app) -> int:
    window = LoadingWindow(
        caption=spec["caption"], wordmark=spec["wordmark"],
        icon=None if spec["icon"] is None else Path(spec["icon"]),
        preview=Preview(spec["preview"]) if spec["is_preview"] else None,
        steps=[step if isinstance(step, str) else tuple(step) for step in spec["steps"]],
        cancel_hint=spec["cancel_hint"])
    if spec["app_id"]:
        from app_support.win32 import TaskbarApp, dress_window  # noqa: PLC0415

        taskbar = spec.get("taskbar")
        dress_window(int(window.winId()), spec["app_id"], None if taskbar is None else
                     TaskbarApp(taskbar["name"], Path(taskbar["icon"]), taskbar["relaunch"]))
    window.show()
    _tell(lines_out, f"{SHOWN} {int(window.winId())}")
    serve(window, lines_in, lines_out, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
