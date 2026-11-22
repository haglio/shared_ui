from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QLabel, QToolTip

from shared_ui import palette, tooltip_look
from shared_ui.colors import dress_application
from shared_ui.tooltip_shape import shaped
from shared_ui.type_scale import in_pixels


@pytest.fixture
def dressed(qapp):
    sheet, look = qapp.styleSheet(), qapp.palette()
    dress_application(qapp)
    yield qapp
    QToolTip.hideText()
    qapp.setStyleSheet(sheet)
    qapp.setPalette(look)
    for dresser in qapp.findChildren(QObject):
        if type(dresser).__module__.startswith("shared_ui.tooltip"):
            qapp.removeEventFilter(dresser)
            dresser.setParent(None)


def _shown_tooltip(text: str) -> QLabel:
    owner = QLabel("owner")
    owner.show()
    QToolTip.showText(QPoint(10, 10), text, owner)
    shown = [window for window in QApplication.topLevelWidgets()
             if window.metaObject().className() == "QTipLabel" and window.text() == text]
    owner.close()
    return shown[-1]


def test_a_tooltip_is_a_rounded_box_the_screen_shows_through_at_its_corners(dressed):
    drawn = _shown_tooltip("Show this HUD again").grab().toImage()

    corner = drawn.pixelColor(0, 0)
    middle = drawn.pixelColor(drawn.width() // 2, drawn.height() - 2)

    assert corner.alpha() == 0
    assert (middle.red(), middle.green(), middle.blue()) == tooltip_look.GROUND
    assert middle.alpha() == tooltip_look.GROUND_ALPHA


def test_a_tooltip_centers_its_words_as_a_hud_tooltip_does(dressed):
    assert _shown_tooltip("Show this HUD again").alignment() & Qt.AlignmentFlag.AlignHCenter


def test_a_tooltip_is_lettered_in_the_huds_small_bold_type(dressed):
    lettering = _shown_tooltip("Show this HUD again").font()

    assert lettering.bold()
    assert lettering.pointSize() == tooltip_look.LETTERING_SIZE
    assert lettering.family() == tooltip_look.LETTERING


def test_every_line_of_a_long_tooltip_is_centered_under_the_one_above():
    words = QTextDocument()
    words.setHtml(shaped(" ".join(f"word{n}" for n in range(60))))

    assert words.firstBlock().blockFormat().alignment() & Qt.AlignmentFlag.AlignHCenter


def test_a_web_page_tooltip_draws_the_same_box_as_a_qt_one():
    rules = dict(part.split(":", 1) for part in tooltip_look.web_box().split("; "))

    assert rules["background"] == palette.as_rgba(tooltip_look.GROUND, 0.941)
    assert rules["border"] == f"1px solid {palette.as_hex(tooltip_look.OUTLINE)}"
    assert rules["border-radius"] == f"{tooltip_look.RADIUS}px"
    assert rules["padding"] == f"{tooltip_look.PAD}px"
    assert rules["text-align"] == "center"
    assert rules["font"].startswith(f"bold {in_pixels(tooltip_look.LETTERING_SIZE)}px")
