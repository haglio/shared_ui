"""shared_ui.testing: putting the pointer on a widget a suite has shown."""

from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from shared_ui import chrome, colors
from shared_ui.testing import Pointer, ground


def _shown_where_a_window_was_left_up() -> tuple[QWidget, QPushButton]:
    left_up = QWidget()
    left_up.setGeometry(QApplication.primaryScreen().geometry().adjusted(0, 0, -40, -40))
    left_up.show()
    button = QPushButton("Edit")
    button.setStyleSheet(chrome.button_rules())
    button.move(left_up.geometry().center())
    button.show()
    QApplication.processEvents()
    return left_up, button


def test_a_widget_shown_under_a_window_left_up_still_gets_the_pointer():
    left_up, button = _shown_where_a_window_was_left_up()
    pointer = Pointer()
    try:
        pointer.off(button)
        at_rest = ground(button)
        pointer.on(button)
        under_the_pointer = ground(button)
    finally:
        pointer.put_back()
        button.close()
        left_up.close()

    assert under_the_pointer == colors.hovered(QColor(at_rest)).name()
