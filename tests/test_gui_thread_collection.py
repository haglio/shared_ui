from __future__ import annotations

import gc
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from PySide6.QtCore import QEventLoop, QObject

from shared_ui.gui_thread_collection import (
    GuiThreadCollection,
    collect_cycles_on_the_gui_thread,
    the_application,
)


@contextmanager
def _collections_seen() -> Iterator[list[str]]:
    started_on: list[str] = []

    def heard(phase, _info):
        if phase == "start":
            started_on.append(threading.current_thread().name)

    gc.callbacks.append(heard)
    try:
        yield started_on
    finally:
        gc.callbacks.remove(heard)


def _a_worker_that_allocates_past_the_threshold() -> list:
    kept: list = []

    def allocate():
        kept.extend([number] for number in range(4 * gc.get_threshold()[0]))

    worker = threading.Thread(target=allocate, name="allocating worker")
    worker.start()
    worker.join()
    return kept


def _events_delivered_until(condition, app, *, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while not condition() and time.monotonic() < deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)


@contextmanager
def _python_collecting_by_itself() -> Iterator[None]:
    was_enabled = gc.isenabled()
    gc.enable()
    try:
        yield
    finally:
        if not was_enabled:
            gc.disable()


@pytest.fixture
def collection(qapp):
    collecting = collect_cycles_on_the_gui_thread(qapp)
    yield collecting
    collecting.stop()


def test_python_collects_on_a_worker_thread_when_nothing_collects_on_the_gui_thread():
    with _python_collecting_by_itself(), _collections_seen() as started_on:
        kept = _a_worker_that_allocates_past_the_threshold()

    assert "allocating worker" in started_on
    assert kept


def test_what_a_worker_allocates_is_collected_on_the_gui_thread(collection, qapp):
    with _collections_seen() as started_on:
        kept = _a_worker_that_allocates_past_the_threshold()
        _events_delivered_until(lambda: bool(started_on), qapp)

    assert set(started_on) == {threading.main_thread().name}
    assert kept


def test_nothing_is_collected_before_the_young_objects_pass_pythons_threshold(collection):
    gc.collect()

    with _collections_seen() as started_on:
        collection.collect_what_is_due()

    assert started_on == []


def test_stopping_gives_python_its_own_collector_back(qapp):
    with _python_collecting_by_itself():
        collecting = collect_cycles_on_the_gui_thread(qapp)
        assert not gc.isenabled()

        collecting.stop()

        assert gc.isenabled()


def test_the_application_a_process_makes_collects_its_cycles_on_its_gui_thread(monkeypatch):
    made = []

    class MadeHere(QObject):
        @staticmethod
        def instance():
            return None

        def __init__(self, argv):
            super().__init__()
            made.append((self, argv))

    app = the_application(MadeHere, ["example"])
    try:
        assert made == [(app, ["example"])]
        assert app.findChild(GuiThreadCollection) is not None
    finally:
        app.findChild(GuiThreadCollection).stop()


def _found(app):
    class FoundElsewhere:
        @staticmethod
        def instance():
            return app

    return FoundElsewhere


def test_the_suite_collects_cycles_on_the_gui_thread_as_the_apps_do(qapp):
    assert not gc.isenabled()
    assert qapp.findChild(GuiThreadCollection) is not None


def test_an_application_found_already_collecting_is_handed_back_as_it_is(qapp):
    before = len(qapp.findChildren(GuiThreadCollection))

    assert the_application(_found(qapp), []) is qapp

    assert len(qapp.findChildren(GuiThreadCollection)) == before


def test_an_application_asked_for_off_its_gui_thread_is_left_to_the_thread_that_made_it(qapp):
    before = len(qapp.findChildren(GuiThreadCollection))
    found = []
    worker = threading.Thread(target=lambda: found.append(the_application(_found(qapp), [])))
    worker.start()
    worker.join()

    assert found == [qapp]
    assert len(qapp.findChildren(GuiThreadCollection)) == before
