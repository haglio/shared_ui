from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from shared_ui.gui_thread_guard import assert_every_application_collects_on_its_gui_thread


def _a_checkout(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    return tmp_path


def test_an_application_made_by_hand_is_named_with_where_it_is_made(tmp_path):
    root = _a_checkout(tmp_path, {"app/main.py": "import sys\n\napp = QApplication(sys.argv)\n"})

    with pytest.raises(AssertionError, match=re.escape("app/main.py:3")):
        assert_every_application_collects_on_its_gui_thread(root)


def test_each_kind_of_application_is_named_however_it_is_reached(tmp_path):
    root = _a_checkout(tmp_path, {"tool.py": (
        "from PySide6 import QtCore, QtGui\n"
        "QtGui.QGuiApplication([])\n"
        "QtCore.QCoreApplication([])\n")})

    with pytest.raises(AssertionError, match=re.escape("tool.py:2\n  tool.py:3")):
        assert_every_application_collects_on_its_gui_thread(root)


def test_an_application_found_asked_for_or_only_written_about_is_not_one_made_by_hand(tmp_path):
    root = _a_checkout(tmp_path, {"app.py": (
        "app = QApplication.instance()\n"
        "made = the_application(QApplication, [])\n"
        "CHILD = 'app = QApplication([])'\n")})

    assert_every_application_collects_on_its_gui_thread(root)


def test_every_application_this_package_makes_collects_on_its_gui_thread():
    assert_every_application_collects_on_its_gui_thread(Path(__file__).resolve().parents[1])
