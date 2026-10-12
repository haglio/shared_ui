"""shared_ui.testing: putting the pointer on a widget a suite has shown."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from shared_ui import chrome, colors
from shared_ui.testing import Pointer, ground


def _shown_button(at: QPoint | None = None) -> QPushButton:
    button = QPushButton("Edit")
    button.setStyleSheet(chrome.button_rules())
    if at is not None:
        button.move(at)
    button.show()
    QApplication.processEvents()
    return button


def _lifts_under_the_pointer(pointer: Pointer, button: QPushButton) -> bool:
    try:
        pointer.off(button)
        at_rest = ground(button)
        pointer.on(button)
        return ground(button) == colors.hovered(QColor(at_rest)).name()
    finally:
        button.close()


def test_a_widget_shown_under_a_window_left_up_still_gets_the_pointer(pointer):
    left_up = QWidget()
    left_up.setGeometry(QApplication.primaryScreen().geometry().adjusted(0, 0, -40, -40))
    left_up.show()
    try:
        assert _lifts_under_the_pointer(pointer, _shown_button(left_up.geometry().center()))
    finally:
        left_up.close()


def test_a_widget_still_gets_the_pointer_after_a_press_nobody_let_go_of(pointer):
    pressed = QWidget()
    pressed.resize(60, 30)
    pressed.show()
    QTest.mousePress(pressed, Qt.MouseButton.LeftButton)
    pressed.close()
    try:
        assert _lifts_under_the_pointer(pointer, _shown_button())
    finally:
        QTest.mouseRelease(pressed, Qt.MouseButton.LeftButton)
