from __future__ import annotations

import html

import pytest
from shared_ui.qt.QtCore import QEvent, QObject, QPoint
from shared_ui.qt.QtGui import QHelpEvent
from shared_ui.qt.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
)

from shared_ui.colors import WHITE, dress_application
from shared_ui.tooltip_shape import shape_long_tooltips, shaped

LONG = ("How strictly the model obeys the prompt. Too low drifts off it; too high burns "
        "contrast & flattens <detail>.")


@pytest.fixture
def undone(qapp):
    sheet, look = qapp.styleSheet(), qapp.palette()
    yield qapp
    qapp.setStyleSheet(sheet)
    qapp.setPalette(look)
    for shaper in qapp.findChildren(QObject):
        if type(shaper).__name__ == "_ShapeLongTooltips":
            qapp.removeEventFilter(shaper)
            shaper.setParent(None)


def _hover(widget, at: QPoint) -> None:
    QApplication.sendEvent(widget, QHelpEvent(QEvent.Type.ToolTip, at, widget.mapToGlobal(at)))


def test_a_short_tooltip_stays_one_line():
    assert shaped("The output width in pixels.") == "The output width in pixels."


def test_a_long_tooltip_is_shown_as_a_block_of_lines():
    assert shaped(LONG) == ('<p style="white-space:pre">How strictly the model obeys the prompt. '
                            "Too low drifts off it; too high burns\ncontrast &amp; flattens "
                            "&lt;detail&gt;.</p>")


def test_every_line_of_a_long_tooltip_is_at_most_eighty_characters():
    words = " ".join(f"word{n}" for n in range(60))

    lines = html.unescape(shaped(words).removeprefix('<p style="white-space:pre">')
                          .removesuffix("</p>")).split("\n")

    assert max(len(line) for line in lines) <= 80
    assert " ".join(lines) == words


def test_a_tooltip_already_written_as_rich_text_is_left_as_written():
    rich = "<b>Bold</b> " + "x" * 80
    assert shaped(rich) == rich


def test_a_tooltip_can_open_with_a_bold_white_lead():
    assert shaped("Euler a on model pages.", lead="Recommended.") == (
        f'<p style="white-space:pre"><b style="color:{WHITE.name()}">Recommended.</b> '
        "Euler a on model pages.</p>")


def test_the_dressed_app_shows_a_long_tooltip_as_a_block(undone):
    dress_application(undone)
    label = QLabel("hover me")
    label.setToolTip(LONG)
    label.show()

    _hover(label, QPoint(2, 2))

    assert QToolTip.text() == shaped(LONG)
    label.close()


def test_the_dressed_app_shows_a_long_choice_tooltip_as_a_block(undone):
    dress_application(undone)
    choices = QListWidget()
    item = QListWidgetItem("euler")
    item.setToolTip(LONG)
    choices.addItem(item)
    choices.show()

    _hover(choices.viewport(), choices.visualItemRect(item).center())

    assert QToolTip.text() == shaped(LONG)
    choices.close()


def test_an_app_that_keeps_its_own_style_sheet_can_still_shape_a_table_cells_tooltip(undone):
    shape_long_tooltips(undone)
    table = QTableWidget(1, 1)
    cell = QTableWidgetItem("stage")
    cell.setToolTip(LONG)
    table.setItem(0, 0, cell)
    table.show()

    _hover(table.viewport(), table.visualItemRect(cell).center())

    assert QToolTip.text() == shaped(LONG)
    table.close()
