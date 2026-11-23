from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QLabel, QToolTip

from shared_ui import palette, tooltip_look
from shared_ui.colors import dress_application
from shared_ui.tooltip_shape import shaped


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


def test_a_tooltip_is_a_square_box_filled_to_its_corners(dressed):
    drawn = _shown_tooltip("Show this HUD again").grab().toImage()

    inside = drawn.pixelColor(1, 1)
    middle = drawn.pixelColor(drawn.width() // 2, drawn.height() - 2)

    assert (inside.red(), inside.green(), inside.blue()) == tooltip_look.GROUND
    assert inside.alpha() == 255
    assert (middle.red(), middle.green(), middle.blue()) == tooltip_look.GROUND


def test_a_tooltip_starts_its_words_at_the_left(dressed):
    assert not _shown_tooltip("Show this HUD again").alignment() & Qt.AlignmentFlag.AlignHCenter


def test_a_tooltip_is_lettered_as_the_apps_own_words_are(dressed):
    lettering = _shown_tooltip("Show this HUD again").font()

    assert not lettering.bold()
    assert lettering.pointSizeF() == dressed.font().pointSizeF()
    assert lettering.family() == dressed.font().family()


def test_every_line_of_a_long_tooltip_starts_at_the_left():
    words = QTextDocument()
    words.setHtml(shaped(" ".join(f"word{n}" for n in range(60))))

    assert not words.firstBlock().blockFormat().alignment() & Qt.AlignmentFlag.AlignHCenter


def test_a_web_page_tooltip_draws_the_same_box_as_a_qt_one():
    rules = dict(part.split(":", 1) for part in tooltip_look.web_box().split("; "))

    assert rules["background"] == palette.as_hex(tooltip_look.GROUND)
    assert rules["border"] == f"1px solid {palette.as_hex(tooltip_look.OUTLINE)}"
    assert rules["padding"] == f"{tooltip_look.PAD_V}px {tooltip_look.PAD_H}px"
    assert "border-radius" not in rules
    assert "text-align" not in rules
    assert "font" not in rules
