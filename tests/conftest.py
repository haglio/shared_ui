"""Shared fixtures for shared_ui tests."""

from __future__ import annotations

import os
import sys

import pytest

# Render Qt offscreen for the whole suite. Agents run these tests on every commit
# on the machine the family's apps are used from; without this, each test that
# builds a widget throws a real window onto that screen for a few milliseconds,
# so a run flashes a burst of them. The merge gate sets it in its own env, which
# does nothing for a run started by hand, and it has to be set before the
# QApplication below exists. setdefault lets a developer override it to watch
# something on a real display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QWidget


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure a QApplication exists for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def put_the_pointer_on():
    resting = QCursor.pos()

    def put_it_on(widget: QWidget) -> None:
        QCursor.setPos(widget.mapToGlobal(widget.rect().center()))
        QApplication.processEvents()

    yield put_it_on
    QCursor.setPos(resting)
    QApplication.processEvents()


@pytest.fixture
def ground_of():
    def ground(widget: QWidget) -> str:
        drawn = widget.grab().toImage()
        return drawn.pixelColor(3, drawn.height() // 2).name()

    return ground
