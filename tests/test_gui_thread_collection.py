from __future__ import annotations

import gc
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from shared_ui.gui_thread_collection import collect_cycles_on_the_gui_thread


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


@pytest.fixture
def collection(qapp):
    collecting = collect_cycles_on_the_gui_thread(qapp)
    yield collecting
    collecting.stop()


def test_python_collects_on_a_worker_thread_when_nothing_collects_on_the_gui_thread():
    with _collections_seen() as started_on:
        kept = _a_worker_that_allocates_past_the_threshold()

    assert "allocating worker" in started_on
    assert kept


def test_what_a_worker_allocates_is_collected_on_the_gui_thread(collection, qtbot):
    with _collections_seen() as started_on:
        kept = _a_worker_that_allocates_past_the_threshold()
        qtbot.waitUntil(lambda: bool(started_on), timeout=5000)

    assert set(started_on) == {threading.main_thread().name}
    assert kept


def test_nothing_is_collected_before_the_young_objects_pass_pythons_threshold(collection):
    gc.collect()

    with _collections_seen() as started_on:
        collection.collect_what_is_due()

    assert started_on == []


def test_stopping_gives_python_its_own_collector_back(qapp):
    collecting = collect_cycles_on_the_gui_thread(qapp)
    assert not gc.isenabled()

    collecting.stop()

    assert gc.isenabled()
