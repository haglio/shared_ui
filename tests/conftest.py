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

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure a QApplication exists for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
