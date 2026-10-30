"""shared_ui.application: what Python still owns is deleted before the app goes."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import textwrap
import weakref
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import QObject, QThread
from PyQt6.QtWidgets import QWidget

from shared_ui import application as application_module
from shared_ui.application import application, delete_what_python_still_owns

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_a_close_leaves_pyqts_own_cleanup_nothing_to_delete():
    # Only a process of its own can free its QApplication's wrapper, which is
    # the moment PyQt walks its map of wrappers deleting what Python owns.
    child = textwrap.dedent("""
        import gc, json, sys, weakref
        from PyQt6 import sip
        from PyQt6.QtCore import QCoreApplication, QObject
        from PyQt6.QtWidgets import QWidget
        from shared_ui.application import application

        kept, said = [], []

        def owned():
            count = 0
            for found in gc.get_objects():
                try:
                    if isinstance(found, QObject) and not isinstance(found, QCoreApplication):
                        count += not sip.isdeleted(found) and sip.ispyowned(found)
                except ReferenceError:
                    pass
            return count

        def main():
            global watching
            with application(sys.argv[:1]) as app:
                kept.append(QWidget())
                watching = weakref.ref(app, lambda _gone: said.append(owned()))

        main()
        print(json.dumps(said), flush=True)
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

    assert not sip.isdeleted(window)


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

    with application(["an app"]) as app:
        assert deleted_for == []

    assert made == [["an app"]]
    assert deleted_for == [app]


def test_what_is_no_qt_object_is_passed_over(qapp):
    window = QWidget()

    delete_what_python_still_owns(qapp, candidates=lambda: [object(), "a word", window])

    assert sip.isdeleted(window)


class _Gone:
    pass


def test_a_weak_proxy_whose_object_is_gone_is_passed_over(qapp):
    gone = _Gone()
    proxy = weakref.proxy(gone)
    del gone
    window = QWidget()

    delete_what_python_still_owns(qapp, candidates=lambda: [proxy, window])

    assert sip.isdeleted(window)


class _StillRunning(QThread):
    def isRunning(self) -> bool:  # noqa: N802 - Qt's name
        return True


def test_a_thread_still_running_is_left_running(qapp):
    thread = _StillRunning()

    delete_what_python_still_owns(qapp, candidates=lambda: [thread])

    assert not sip.isdeleted(thread)


def test_the_windows_go_before_what_they_were_using(qapp):
    used = QObject()
    window = QWidget()
    still_there = []
    window.destroyed.connect(lambda: still_there.append(not sip.isdeleted(used)))

    delete_what_python_still_owns(qapp, candidates=lambda: [used, window])

    assert still_there == [True]


def test_what_went_with_an_earlier_deletion_is_passed_over(qapp):
    window = QWidget()
    taken_along = QWidget()
    taken_along.setParent(window)
    sip.transferback(taken_along)

    delete_what_python_still_owns(qapp, candidates=lambda: [window, taken_along])

    assert sip.isdeleted(taken_along)


def test_what_qt_owns_is_left_to_its_parent(qapp):
    window = QWidget()
    child = QWidget(window)

    delete_what_python_still_owns(qapp, candidates=lambda: [child])

    assert not sip.isdeleted(child)


def test_the_application_itself_is_left_alone(qapp):
    delete_what_python_still_owns(qapp, candidates=lambda: [qapp])

    assert not sip.isdeleted(qapp)


def test_the_log_says_how_many_it_deleted(qapp, caplog):
    windows = [QWidget(), QWidget()]

    with caplog.at_level(logging.INFO, logger="shared_ui.application"):
        delete_what_python_still_owns(qapp, candidates=lambda: windows)

    assert "Deleted 2 object(s) Python still owned" in caplog.text
