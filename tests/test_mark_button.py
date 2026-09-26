"""shared_ui.mark_button: a button that carries a mark and no word, one square
for the whole family, read back off the button as the family sheet paints it."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QPoint, QRect, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton, QToolButton, QWidget

from shared_ui.chrome import family_stylesheet
from shared_ui.icons import glyph_icon
from shared_ui.mark_button import fill_square_with_mark
from shared_ui.spacing import BUTTON_SIZE

_AN_APP_THAT_PADS_ITS_BUTTONS = (
    "QToolButton, QPushButton { border: 1px solid gray; padding: 2px 10px; }")


@pytest.fixture(params=[
    (QToolButton, ""), (QPushButton, ""),
    (QToolButton, _AN_APP_THAT_PADS_ITS_BUTTONS), (QPushButton, _AN_APP_THAT_PADS_ITS_BUTTONS),
], ids=["tool", "push", "padded-tool", "padded-push"])
def button(request):
    kind, app_rules = request.param
    host = QWidget()
    host.setStyleSheet(family_stylesheet() + app_rules)
    made = fill_square_with_mark(kind(host))
    made.setIcon(glyph_icon("speaker"))
    host.show()
    yield made
    host.close()
    host.deleteLater()


def test_a_mark_button_is_the_ordinary_square(button):
    assert button.size() == QSize(BUTTON_SIZE, BUTTON_SIZE)


def _where_the_mark_lands(button) -> QRect:
    worn = button.grab().toImage()
    icon = button.icon()
    button.setIcon(QIcon())
    bare = button.grab().toImage()
    button.setIcon(icon)
    inked = [(x, y) for y in range(worn.height()) for x in range(worn.width())
             if worn.pixel(x, y) != bare.pixel(x, y)]
    assert inked, "no mark was drawn on the button"
    xs, ys = [x for x, _ in inked], [y for _, y in inked]
    return QRect(QPoint(min(xs), min(ys)), QPoint(max(xs), max(ys)))


def test_its_mark_spans_more_than_half_the_square(button):
    mark = _where_the_mark_lands(button)

    assert max(mark.width(), mark.height()) > BUTTON_SIZE / 2


def test_the_widest_mark_keeps_two_pixels_clear_of_a_one_pixel_border(button):
    border, clear = 1, 2
    room = button.rect().adjusted(border + clear, border + clear,
                                  -(border + clear), -(border + clear))

    assert room.contains(_where_the_mark_lands(button))
