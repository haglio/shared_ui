from __future__ import annotations

from shared_ui.qt.QtCore import QPoint, Qt
from shared_ui.qt.QtGui import QColor
from shared_ui.qt.QtTest import QTest
from shared_ui.qt.QtWidgets import QApplication, QPushButton, QWidget

from shared_ui import (
    alert,
    application,
    chrome,
    colors,
    foreground,
    icon_geometry,
    loading_handover,
    loading_process,
    loading_window,
)
from shared_ui.testing import (
    Pointer,
    alert_shown,
    application_stand_in,
    brought_to_front,
    ground,
    icons_lacking,
    loading_at_the_click,
    loading_process_opened,
    taking_over_stand_in,
)


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


def test_no_alert_reaches_the_screen():
    with alert_shown(return_value=True) as shown:
        assert alert.show_alert("Title", "Body") is True
    shown.assert_called_once_with("Title", "Body")


def test_no_loading_process_starts():
    with loading_process_opened() as opened:
        loading_process.LoadingProcess.open(caption="Example")
    opened.assert_called_once_with(caption="Example")


def test_the_loading_at_the_click_is_the_one_the_test_names():
    with loading_at_the_click("a loading") as opened:
        assert loading_window.Loading.at_the_click(None, None, None) == "a loading"
    assert opened.call_count == 1


def test_taking_over_is_stood_in_for():
    with taking_over_stand_in() as taking_over:
        assert loading_handover.TakingOver is taking_over


def test_the_application_is_the_one_the_test_names():
    with application_stand_in("an application"):
        assert application.application == "an application"


def test_nothing_is_brought_to_the_front():
    with brought_to_front() as brought:
        foreground.bring_to_front("a window")
    brought.assert_called_once_with("a window")


def test_an_icon_lacking_comes_back_after():
    present = "power"
    with icons_lacking(present):
        assert present not in icon_geometry.icon_names()
    assert present in icon_geometry.icon_names()


def test_the_pointer_on_a_window_is_handed_to_the_child_under_it(pointer):
    moved = []

    class Heard(QPushButton):
        def mouseMoveEvent(self, _event):
            moved.append("the child")

    class Window(QWidget):
        def mouseMoveEvent(self, _event):
            moved.append("the window")

    window = Window()
    window.setMouseTracking(True)
    window.resize(200, 100)
    button = Heard("Edit", window)
    button.setGeometry(20, 20, 80, 40)
    button.setMouseTracking(True)
    window.show()
    QApplication.processEvents()

    pointer.on(window, QPoint(40, 40))

    assert "the child" in moved
    assert "the window" not in moved
