"""Shared fixtures for shared_ui tests."""

from __future__ import annotations

import os
import random
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


def pytest_collection_modifyitems(items):
    """Collect in a different order when asked, so a test that leans on the ones
    beside it fails on the commit that introduces the lean.

    ``TEST_COLLECTION_ORDER=reverse`` collects back to front;
    ``TEST_COLLECTION_ORDER=shuffle`` shuffles with ``TEST_COLLECTION_SEED`` (0
    unless given), so a red run can be repeated exactly.  Unset leaves the order
    alone; anything else is a typo, and a typo that silently ran forward would
    make the gate's second leg a green that proves nothing.
    """
    order = os.environ.get("TEST_COLLECTION_ORDER")
    if order is None:
        return
    if order == "reverse":
        items.reverse()
    elif order == "shuffle":
        random.Random(int(os.environ.get("TEST_COLLECTION_SEED", "0"))).shuffle(items)
    else:
        raise pytest.UsageError(
            f"TEST_COLLECTION_ORDER={order!r}: expected 'reverse' or 'shuffle'"
        )


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure a QApplication exists for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
