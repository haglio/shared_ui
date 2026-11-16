"""Python's cycle collector runs on whichever thread happens to allocate past its threshold, and
the Qt binding destroys a widget on the thread that frees it, so a collection on a worker
thread destroys widgets there and corrupts Qt's state for the GUI thread: an access violation
later, in some unrelated event. So the automatic collector is turned off and the same young
collection, with its increment of the old objects, is run from a timer on the GUI thread."""

from __future__ import annotations

import gc

from PySide6.QtCore import QCoreApplication, QObject, QThread, QTimer

CHECK_EVERY_MS = 50


class GuiThreadCollection(QObject):
    def __init__(self, parent: QObject):
        super().__init__(parent)
        self._was_enabled = gc.isenabled()
        gc.disable()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.collect_what_is_due)
        self._timer.start(CHECK_EVERY_MS)

    def collect_what_is_due(self) -> None:
        if gc.get_count()[0] > gc.get_threshold()[0]:
            gc.collect(1)

    def stop(self) -> None:
        self._timer.stop()
        if self._was_enabled:
            gc.enable()


def collect_cycles_on_the_gui_thread(app: QObject) -> GuiThreadCollection:
    return GuiThreadCollection(app)


def the_application[App: QCoreApplication](kind: type[App], argv: list[str]) -> App:
    app = kind.instance() or kind(argv)
    on_its_gui_thread = QThread.currentThread() == app.thread()
    if on_its_gui_thread and app.findChild(GuiThreadCollection) is None:
        collect_cycles_on_the_gui_thread(app)
    return app
