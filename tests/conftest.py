from __future__ import annotations

import os
import sys

import pytest

# Qt has to get this before the QApplication below exists, or a run flashes real windows.
# setdefault leaves a developer's own QT_QPA_PLATFORM standing, to watch a run on a real
# display; the merge gate sets it for its own runs only, not for a run started by hand.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

pytest_plugins = ("shared_ui.testing",)


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
