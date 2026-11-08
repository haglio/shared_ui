"""PyQt deletes every QObject Python still owns as the QApplication's wrapper is freed,
walking sip's map of wrappers, and a deletion that makes enough new wrappers has sip
rebuild the map under the walk: an access violation. So they are deleted here first."""

from __future__ import annotations

import gc
import logging
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager

from PyQt6 import sip
from PyQt6.QtCore import QObject, QThread
from PyQt6.QtWidgets import QApplication, QWidget

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
            sip.delete(found)
            deleted += 1
    _log.info("Deleted %d object(s) Python still owned, before the application went", deleted)


def _python_owns(found: object) -> bool:
    try:
        if not isinstance(found, QObject):
            return False
    except ReferenceError:
        return False
    return (not sip.isdeleted(found) and sip.ispyowned(found)
            and not (isinstance(found, QThread) and found.isRunning()))


def _windows_first(found: QObject) -> bool:
    return not isinstance(found, QWidget)
