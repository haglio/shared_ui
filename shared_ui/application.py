"""The Qt binding deletes every QObject Python still owns as the QApplication's wrapper is
freed, walking its map of wrappers, and a deletion that makes enough new wrappers has the
map rebuilt under the walk: an access violation. So they are deleted here first."""

from __future__ import annotations

import gc
import logging
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager

from shared_ui.qt import delete, is_deleted, owned_by_python
from shared_ui.qt.QtCore import QObject, QThread
from shared_ui.qt.QtWidgets import QApplication, QWidget
from shared_ui.tooltip_shape import shape_long_tooltips

_log = logging.getLogger(__name__)


@contextmanager
def application(argv: list[str]) -> Iterator[QApplication]:
    made_elsewhere = QApplication.instance()
    if made_elsewhere is not None:
        yield made_elsewhere
        return
    app = QApplication(argv)
    shape_long_tooltips(app)
    try:
        yield app
    finally:
        delete_what_python_still_owns(app)


def delete_what_python_still_owns(
        app: QApplication, *, candidates: Callable[[], Iterable[object]] = gc.get_objects) -> None:
    owned = [found for found in candidates() if _python_owns(found) and found is not app]
    deleted = 0
    for found in sorted(owned, key=_windows_first):
        if _python_owns(found):
            delete(found)
            deleted += 1
    _log.info("Deleted %d object(s) Python still owned, before the application went", deleted)


def _python_owns(found: object) -> bool:
    try:
        if not isinstance(found, QObject):
            return False
    except ReferenceError:
        return False
    return (not is_deleted(found) and owned_by_python(found)
            and not (isinstance(found, QThread) and found.isRunning()))


def _windows_first(found: QObject) -> bool:
    return not isinstance(found, QWidget)
