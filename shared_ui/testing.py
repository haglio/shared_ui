from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QCursor, QImage, QMouseEvent, QRegion
from PySide6.QtWidgets import QApplication, QWidget

from shared_ui import icons
from shared_ui.colors import BG_PRIMARY


def alert_shown(**how: Any):
    return patch("shared_ui.alert.show_alert", **how)


def loading_process_opened(**how: Any):
    return patch("shared_ui.loading_process.LoadingProcess.open", **how)


def loading_at_the_click(loading: Any):
    return patch("shared_ui.loading_window.Loading.at_the_click", return_value=loading)


def taking_over_stand_in():
    return patch("shared_ui.loading_handover.TakingOver")


def application_stand_in(application: Any):
    return patch("shared_ui.application.application", application)


def brought_to_front(**how: Any):
    return patch("shared_ui.foreground.bring_to_front", **how)


@contextmanager
def icons_lacking(*names: str) -> Iterator[None]:
    with patch.dict("shared_ui.icon_geometry.ICONS") as icons:
        for name in names:
            del icons[name]
        yield


@contextmanager
def icons_drawn() -> Iterator[list[str]]:
    drawn: list[str] = []
    shapes_of = icons.shapes_of

    def recording(name: str):
        drawn.append(name)
        return shapes_of(name)

    with patch("shared_ui.icons.shapes_of", recording):
        yield drawn


def appending_to(found: list) -> Callable[[Any], None]:
    def append(value: Any) -> None:
        found.append(value)

    return append


def rendered_on_the_dark_ground(widget: QWidget) -> QImage:
    """A bare ``grab()`` paints every uncovered pixel with the palette's Window color, which is
    light under Qt's offscreen backend, a ground no app ever shows beneath these widgets."""
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(BG_PRIMARY)
    widget.render(image, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
    return image


_THIS_TREE = Path(__file__).resolve().parent.parent


def toolkits_loaded_by_importing(*modules: str) -> set[str]:
    # `python -c` puts the process cwd first on sys.path and nothing else, so the probe says
    # which tree it read: from elsewhere it would import the primary checkout's copy, and a
    # branch that dragged Qt or Pillow in would pass.
    probe = (
        f"import json, sys; import {', '.join(modules)}; "
        "print(shared_ui.__file__); "
        "print(json.dumps(sorted({m.split('.')[0] for m in sys.modules if m.split('.')[0] in ('PySide6', 'PIL')})))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], cwd=_THIS_TREE,
        env={**os.environ, "PYTHONPATH": str(_THIS_TREE)},
        capture_output=True, text=True, check=True,
    )
    read_from, toolkits = result.stdout.splitlines()

    assert Path(read_from).resolve().is_relative_to(_THIS_TREE), (
        f"the probe read {read_from}, not the tree under test at {_THIS_TREE}"
    )
    return set(json.loads(toolkits))


def ground(widget: QWidget) -> str:
    drawn = widget.grab().toImage()
    return drawn.pixelColor(3, drawn.height() // 2).name()


class Pointer:
    """Offscreen, Qt hands a point to the window shown there first, so a window an earlier test
    left up takes the pointer from one shown under it; and a press nobody let go of keeps the
    pointer's own moves from reaching any widget, while a push button lights only on a move."""

    def __init__(self) -> None:
        self._resting = QCursor.pos()

    def off(self, widget: QWidget) -> None:
        window = widget.window()
        _move_clear_of_every_other_window(window)
        corner = QApplication.primaryScreen().geometry().topLeft()
        spot = window.frameGeometry()
        past_it = spot.topLeft() + QPoint(spot.width(), spot.height())
        _put_the_pointer_at(past_it if spot.contains(corner) else corner)

    def on(self, widget: QWidget, at: QPoint | None = None) -> None:
        at = at if at is not None else widget.rect().center()
        _put_the_pointer_at(widget.mapToGlobal(at))
        under = widget.childAt(at) or widget
        QApplication.sendEvent(under, QMouseEvent(
            QEvent.Type.MouseMove, QPointF(under.mapFrom(widget, at)), QPointF(widget.mapToGlobal(at)),
            Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()

    def put_back(self) -> None:
        _put_the_pointer_at(self._resting)


@pytest.fixture
def pointer() -> Iterator[Pointer]:
    pointer = Pointer()
    yield pointer
    pointer.put_back()


def _put_the_pointer_at(point: QPoint) -> None:
    QCursor.setPos(point)
    QApplication.processEvents()


def _move_clear_of_every_other_window(window: QWidget) -> None:
    screen = QApplication.primaryScreen().geometry()
    taken = [other.frameGeometry() for other in QApplication.topLevelWidgets()
             if other.isVisible() and other is not window]
    size = window.frameGeometry().size()
    for y in range(screen.y(), screen.y() + screen.height() - size.height(), 10):
        for x in range(screen.x(), screen.x() + screen.width() - size.width(), 10):
            if not any(QRect(QPoint(x, y), size).intersects(other) for other in taken):
                window.move(x, y)
                QApplication.processEvents()
                return
    raise AssertionError("windows earlier tests left up cover every spot on the screen")
