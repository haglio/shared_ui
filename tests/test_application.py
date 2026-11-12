from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import textwrap
import weakref
from pathlib import Path

from shared_ui.qt.QtCore import QObject, QThread
from shared_ui.qt.QtWidgets import QWidget

from shared_ui import application as application_module
from shared_ui.application import (
    application,
    close_the_windows_it_opened,
    delete_what_python_still_owns,
)
from shared_ui.qt import delete, is_deleted

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_a_close_leaves_the_bindings_own_cleanup_nothing_to_delete():
    child = textwrap.dedent("""
        import gc, json, sys
        from shared_ui.qt import is_deleted, owned_by_python
        from shared_ui.qt.QtCore import QCoreApplication, QObject
        from shared_ui.qt.QtWidgets import QWidget
        from shared_ui.application import application

        kept = []

        def owned():
            count = 0
            for found in gc.get_objects():
                try:
                    if isinstance(found, QObject) and not isinstance(found, QCoreApplication):
                        count += not is_deleted(found) and owned_by_python(found)
                except ReferenceError:
                    pass
            return count

        with application(sys.argv[:1]):
            kept.append(QWidget())
        print(json.dumps([owned()]), flush=True)
    """)
    ran = subprocess.run([sys.executable, "-c", child], cwd=REPO_ROOT, timeout=120,
                         env=os.environ | {"QT_QPA_PLATFORM": "offscreen"},
                         capture_output=True, encoding="utf-8", errors="replace",
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)

    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert json.loads(ran.stdout.splitlines()[-1]) == [0]


def test_an_application_made_elsewhere_is_handed_through_and_left_alone(qapp):
    window = QWidget()

    with application([]) as app:
        assert app is qapp

    assert not is_deleted(window)


def test_an_application_made_here_has_what_python_owns_deleted_as_the_block_ends(monkeypatch):
    made, deleted_for = [], []

    class _NoApplicationYet:
        @staticmethod
        def instance():
            return None

        def __init__(self, argv):
            made.append(argv)

    monkeypatch.setattr(application_module, "QApplication", _NoApplicationYet)
    monkeypatch.setattr(application_module, "delete_what_python_still_owns", deleted_for.append)
    monkeypatch.setattr(application_module, "shape_long_tooltips", lambda _app: None)

    with application(["an app"]) as app:
        assert deleted_for == []

    assert made == [["an app"]]
    assert deleted_for == [app]


def test_an_application_made_here_shows_its_long_tooltips_as_blocks_of_lines(monkeypatch):
    shaping = []

    class _NoApplicationYet:
        @staticmethod
        def instance():
            return None

        def __init__(self, argv):
            pass

    monkeypatch.setattr(application_module, "QApplication", _NoApplicationYet)
    monkeypatch.setattr(application_module, "delete_what_python_still_owns", lambda _app: None)
    monkeypatch.setattr(application_module, "shape_long_tooltips", shaping.append)

    with application(["an app"]) as app:
        assert shaping == [app]


def test_what_is_no_qt_object_is_passed_over(qapp):
    window = QWidget()

    delete_what_python_still_owns(qapp, candidates=lambda: [object(), "a word", window])

    assert is_deleted(window)


class _Gone:
    pass


def test_a_weak_proxy_whose_object_is_gone_is_passed_over(qapp):
    gone = _Gone()
    proxy = weakref.proxy(gone)
    del gone
    window = QWidget()

    delete_what_python_still_owns(qapp, candidates=lambda: [proxy, window])

    assert is_deleted(window)


class _StillRunning(QThread):
    def isRunning(self) -> bool:  # noqa: N802 - Qt's name
        return True


def test_a_thread_still_running_is_left_running(qapp):
    thread = _StillRunning()

    delete_what_python_still_owns(qapp, candidates=lambda: [thread])

    assert not is_deleted(thread)


def test_the_windows_go_before_what_they_were_using(qapp):
    used = QObject()
    window = QWidget()
    still_there = []
    window.destroyed.connect(lambda: still_there.append(not is_deleted(used)))

    delete_what_python_still_owns(qapp, candidates=lambda: [used, window])

    assert still_there == [True]


def test_what_went_with_an_earlier_deletion_is_passed_over(qapp):
    window = QWidget()
    taken_along = QObject()
    window.destroyed.connect(lambda: delete(taken_along))

    delete_what_python_still_owns(qapp, candidates=lambda: [window, taken_along])

    assert is_deleted(taken_along)


def test_what_qt_owns_is_left_to_its_parent(qapp):
    window = QWidget()
    child = QWidget(window)

    delete_what_python_still_owns(qapp, candidates=lambda: [child])

    assert not is_deleted(child)


def test_the_application_itself_is_left_alone(qapp):
    delete_what_python_still_owns(qapp, candidates=lambda: [qapp])

    assert not is_deleted(qapp)


def test_the_log_says_how_many_it_deleted(qapp, caplog):
    windows = [QWidget(), QWidget()]

    with caplog.at_level(logging.INFO, logger="shared_ui.application"):
        delete_what_python_still_owns(qapp, candidates=lambda: windows)

    assert "Deleted 2 object(s) Python still owned" in caplog.text


def test_the_windows_a_main_window_opened_close_with_it():
    main, opened = QWidget(), QWidget()
    main.show()
    opened.show()

    close_the_windows_it_opened(main)

    assert not opened.isVisible()
    assert main.isVisible()
    delete(opened)
    delete(main)
