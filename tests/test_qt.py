from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest

from shared_ui.qt import chosen_binding, under_pyside6_names

REPO_ROOT = Path(__file__).resolve().parents[1]


def _installed(*names: str):
    def importing(name: str) -> object:
        if name not in names:
            raise ImportError(name)
        return object()

    return importing


def test_a_binding_the_app_already_loaded_is_the_one_drawn_with():
    assert chosen_binding({"PyQt6": object()}, _installed("PySide6", "PyQt6")) == "PyQt6"


def test_with_none_loaded_pyside6_is_drawn_with_where_it_is_installed():
    assert chosen_binding({}, _installed("PySide6", "PyQt6")) == "PySide6"


def test_with_none_loaded_pyqt6_is_drawn_with_where_it_alone_is_installed():
    assert chosen_binding({}, _installed("PyQt6")) == "PyQt6"


def test_with_no_binding_installed_the_import_says_so():
    with pytest.raises(ImportError, match="PySide6, PyQt6"):
        chosen_binding({}, _installed())


def test_a_module_under_pyside6_names_keeps_its_own_and_gains_the_new():
    module = types.ModuleType("made_up")
    module.pyqtSignal = object()

    renamed = under_pyside6_names("QtCore", module, Signal=module.pyqtSignal)

    assert (renamed.__name__, renamed.Signal, renamed.pyqtSignal) == (
        "shared_ui.qt.QtCore", module.pyqtSignal, module.pyqtSignal)


def test_an_app_on_pyqt6_draws_with_pyqt6_under_pyside6_names():
    child = textwrap.dedent("""
        import json, os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        import PyQt6
        from shared_ui import qt
        from shared_ui.qt.QtCore import QObject, Signal, Slot
        from shared_ui.qt.QtGui import Qt
        from shared_ui.qt.QtWidgets import QApplication

        app = QApplication([])
        made = QObject()
        before = qt.is_deleted(made), qt.owned_by_python(made)
        qt.delete(made)
        print(json.dumps([qt.BINDING, Signal.__module__, Slot.__module__, type(made).__module__,
                          Qt.mightBeRichText("<b>bold</b>"), *before, qt.is_deleted(made)]))
    """)
    ran = subprocess.run([sys.executable, "-c", child], cwd=REPO_ROOT, timeout=120,
                         capture_output=True, encoding="utf-8", errors="replace",
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)

    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert json.loads(ran.stdout.splitlines()[-1]) == [
        "PyQt6", "PyQt6.QtCore", "PyQt6.QtCore", "PyQt6.QtCore", True, False, True, True]
