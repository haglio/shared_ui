from __future__ import annotations

import pytest
from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QHelpEvent, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QToolTip,
    QWidget,
)

from shared_ui.colors import TEXT_PRIMARY
from shared_ui.icon_geometry import tooltip_for
from shared_ui.icons import draw_glyph, glyph_icon, glyph_pixmap

_A_MARK_THIS_VERSION_LACKS = "a_mark_from_another_version"
_WHY = ("This button's picture is missing from this version of the app.\n"
        "Updating the app brings it back.")


def test_a_control_wearing_a_real_mark_keeps_its_own_tooltip():
    assert tooltip_for("trash", "Move it to the trash") == "Move it to the trash"


def test_a_control_wearing_the_stand_in_says_why_under_its_own_tooltip():
    assert tooltip_for(_A_MARK_THIS_VERSION_LACKS, "Generate on its own") == (
        f"Generate on its own\n{_WHY}")


def test_a_control_with_no_tooltip_of_its_own_still_says_why_it_wears_the_stand_in():
    assert tooltip_for(_A_MARK_THIS_VERSION_LACKS, "") == _WHY


@pytest.fixture
def host():
    window = QWidget()
    QHBoxLayout(window)
    window.show()
    yield window
    QToolTip.hideText()
    window.close()
    window.deleteLater()


def _placed(host: QWidget, button):
    host.layout().addWidget(button)
    button.show()
    return button


def _hover(button) -> str:
    point = QPoint(2, 2)
    QApplication.sendEvent(button, QHelpEvent(QEvent.Type.ToolTip, point,
                                              button.mapToGlobal(point)))
    return QToolTip.text()


def test_hovering_a_button_wearing_the_stand_in_says_why_under_its_own_tooltip(host):
    button = _placed(host, QToolButton())
    button.setIcon(glyph_icon(_A_MARK_THIS_VERSION_LACKS))
    button.setToolTip("Generate on its own")

    assert _hover(button) == f"Generate on its own\n{_WHY}"


def test_hovering_a_button_wearing_a_real_mark_shows_its_own_tooltip_alone(host):
    button = _placed(host, QToolButton())
    button.setIcon(glyph_icon("trash"))
    button.setToolTip("Move it to the trash")

    assert _hover(button) == "Move it to the trash"


def test_a_button_with_no_tooltip_of_its_own_still_says_why_it_wears_the_stand_in(host):
    button = _placed(host, QToolButton())
    button.setIcon(glyph_icon(_A_MARK_THIS_VERSION_LACKS))

    assert _hover(button) == _WHY


def test_a_disabled_button_wearing_the_stand_in_says_why_too(host):
    button = _placed(host, QToolButton())
    button.setIcon(glyph_icon(_A_MARK_THIS_VERSION_LACKS))
    button.setToolTip("Generate on its own")
    button.setEnabled(False)

    assert _hover(button) == f"Generate on its own\n{_WHY}"


def test_a_button_whose_icon_is_made_from_a_stand_in_pixmap_says_why_too(host):
    button = _placed(host, QPushButton(QIcon(glyph_pixmap(_A_MARK_THIS_VERSION_LACKS, 24,
                                                          TEXT_PRIMARY)), ""))
    button.setToolTip("Copy it")

    assert _hover(button) == f"Copy it\n{_WHY}"


def test_a_button_that_paints_the_stand_in_into_its_own_picture_says_why_too(host):
    picture = QPixmap(48, 48)
    picture.fill(Qt.GlobalColor.transparent)
    painter = QPainter(picture)
    draw_glyph(painter, _A_MARK_THIS_VERSION_LACKS, TEXT_PRIMARY, size=32, x=8, y=8)
    painter.end()
    button = _placed(host, QToolButton())
    button.setIcon(QIcon(picture))
    button.setToolTip("Star it")

    assert _hover(button) == f"Star it\n{_WHY}"
