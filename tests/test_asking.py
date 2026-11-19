from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from shared_ui.asking import asked, yes_or_no
from shared_ui.testing import questions_answered


@pytest.fixture
def box(qapp):
    shown = yes_or_no(None, "Close It", "Are you sure?")
    shown.show()
    qapp.processEvents()
    yield shown
    shown.close()
    shown.deleteLater()


def test_enter_answers_yes(box):
    QTest.keyClick(box, Qt.Key.Key_Return)

    assert box.clickedButton() is box.button(QMessageBox.StandardButton.Yes)


def test_the_yes_button_is_the_default(box):
    assert box.button(QMessageBox.StandardButton.Yes).isDefault()


def test_escape_answers_no(box):
    QTest.keyClick(box, Qt.Key.Key_Escape)

    assert box.clickedButton() is box.button(QMessageBox.StandardButton.No)


def test_the_box_asks_the_question_under_its_title(box):
    assert (box.windowTitle(), box.text()) == ("Close It", "Are you sure?")


@pytest.mark.parametrize(("answer", "is_yes"), [
    (QMessageBox.StandardButton.Yes, True),
    (QMessageBox.StandardButton.No, False),
])
def test_asked_is_whether_the_answer_was_yes(qapp, monkeypatch, answer, is_yes):
    questions_answered(monkeypatch, answer)

    assert asked(None, "Close It", "Are you sure?") is is_yes
