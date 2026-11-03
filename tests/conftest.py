from __future__ import annotations

import os
import sys

import pytest

# Qt has to get this before the QApplication below exists, or a run flashes real windows.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

pytest_plugins = ("shared_ui.testing",)


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
