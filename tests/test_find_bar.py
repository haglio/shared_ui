"""shared_ui.find_bar: the strip Ctrl+F opens over a window's text."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shared_ui.chrome import family_stylesheet
from shared_ui.colors import BG_BUTTON, BG_SECONDARY, BLUE, TEXT_MUTED
from shared_ui.find_bar import FindBar


@pytest.fixture
def window():
    host = QWidget()
    QVBoxLayout(host)
    host.show()
    yield host
    host.close()
    host.deleteLater()


@pytest.fixture
def bar(window):
    made = FindBar("Find in prompts:", "a word you wrote…")
    window.layout().addWidget(made)
    return made


@pytest.fixture
def field(window):
    def make(text):
        made = QPlainTextEdit()
        made.setPlainText(text)
        window.layout().addWidget(made)
        return made

    return make


def _query(bar) -> QLineEdit:
    return bar.findChild(QLineEdit)


def _count(bar) -> str:
    return bar.findChild(QLabel, "findCount").text()


def _button(bar, tooltip_start: str) -> QToolButton:
    (button,) = [b for b in bar.findChildren(QToolButton) if b.toolTip().startswith(tooltip_start)]
    return button


def test_the_strip_takes_no_room_until_it_is_opened(bar):
    assert bar.isHidden()


def test_opening_shows_it_and_takes_the_keyboard(bar, field):
    bar.open_find([field("a cat")])

    assert bar.isVisible()
    assert bar.focusWidget() is _query(bar)


def test_opening_selects_the_standing_query_so_typing_replaces_it(bar, field):
    searched = field("a cat")
    bar.open_find([searched])
    _query(bar).setText("cat")

    bar.open_find([searched])

    assert _query(bar).selectedText() == "cat"
    assert _count(bar) == "1 of 1"


def test_typing_searches_what_the_strip_was_opened_over(bar, field):
    searched = field("a cat and a cat")
    bar.open_find([searched])

    _query(bar).setText("cat")

    assert _count(bar) == "1 of 2"
    assert len(searched.extraSelections()) == 2


def test_enter_steps_to_the_next_match(bar, field):
    bar.open_find([field("a cat and a cat")])
    _query(bar).setText("cat")

    QTest.keyClick(_query(bar), Qt.Key.Key_Return)

    assert _count(bar) == "2 of 2"


def test_shift_enter_steps_back(bar, field):
    bar.open_find([field("cat cat cat")])
    _query(bar).setText("cat")

    QTest.keyClick(_query(bar), Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)

    assert _count(bar) == "3 of 3"


def test_the_arrows_step_each_way(bar, field):
    bar.open_find([field("cat cat")])
    _query(bar).setText("cat")

    _button(bar, "Next match").click()
    assert _count(bar) == "2 of 2"
    _button(bar, "Previous match").click()
    assert _count(bar) == "1 of 2"


def test_the_close_button_puts_the_strip_away_and_its_marks_with_it(bar, field):
    searched = field("a cat")
    bar.open_find([searched])
    _query(bar).setText("cat")

    _button(bar, "Close the find").click()

    assert bar.isHidden()
    assert not searched.extraSelections()


def test_the_count_reads_as_a_place_in_the_results(bar, field):
    bar.open_find([field(" ".join(["cat"] * 12))])
    _query(bar).setText("cat")

    _button(bar, "Next match").click()
    _button(bar, "Next match").click()

    assert _count(bar) == "3 of 12"


def test_a_query_that_finds_nothing_says_so(bar, field):
    bar.open_find([field("a cat")])

    _query(bar).setText("wombat")

    assert _count(bar) == "No matches"


def test_nothing_typed_yet_reads_as_nothing_rather_than_zero(bar, field):
    # A count of zero before you have searched anything reads as a failed search.
    bar.open_find([field("a cat")])

    assert _count(bar) == ""


def test_the_arrows_gray_out_with_nowhere_to_step(bar, field):
    searched = field("a cat")
    bar.open_find([searched])
    _query(bar).setText("cat")

    assert not _button(bar, "Next match").isEnabled()
    assert not _button(bar, "Previous match").isEnabled()

    searched.setPlainText("a cat and a cat")
    bar.refresh()

    assert _button(bar, "Next match").isEnabled()
    assert _button(bar, "Previous match").isEnabled()


def test_refreshing_keeps_your_place_while_the_text_is_edited(bar, field):
    searched = field("cat cat cat")
    bar.open_find([searched])
    _query(bar).setText("cat")
    _button(bar, "Next match").click()

    searched.setPlainText("cat cat cat and cat")
    bar.refresh()

    assert _count(bar) == "2 of 4"


def test_retargeting_an_open_strip_searches_the_new_text_and_unpaints_the_old(bar, field):
    old, new = field("a cat"), field("a cat and a cat")
    bar.open_find([old])
    _query(bar).setText("cat")

    bar.retarget([new])

    assert _count(bar) == "1 of 2"
    assert not old.extraSelections()


def test_retargeting_an_open_strip_at_nothing_puts_it_away(bar, field):
    searched = field("a cat")
    bar.open_find([searched])
    _query(bar).setText("cat")

    bar.retarget([])

    assert bar.isHidden()
    assert not searched.extraSelections()

def test_a_closed_strip_ignores_retargeting_and_refreshing(bar, field):
    searched = field("a cat")
    bar.open_find([searched])
    _query(bar).setText("cat")
    bar.close_find()

    bar.retarget([searched])
    bar.refresh()

    assert bar.isHidden()
    assert not searched.extraSelections()


def test_opening_invites_typing(bar, field):
    invited = []
    bar.typing_invited.connect(lambda: invited.append(True))

    bar.open_find([field("a cat")])

    assert invited == [True]


def test_a_click_in_the_query_invites_typing(bar, field):
    bar.open_find([field("a cat")])
    invited = []
    bar.typing_invited.connect(lambda: invited.append(True))

    QTest.mouseClick(_query(bar), Qt.MouseButton.LeftButton)

    assert invited == [True]


def test_the_close_names_the_key_the_window_closes_it_with():
    assert _button(FindBar("Find:", "", dismiss_key="Esc"), "Close").toolTip() == "Close the find (Esc)"
    assert _button(FindBar("Find:", ""), "Close").toolTip() == "Close the find"


def test_the_strip_says_what_it_searches(bar):
    (words,) = [label.text() for label in bar.findChildren(QLabel) if label.objectName() != "findCount"]
    assert words == "Find in prompts:"
    assert _query(bar).placeholderText() == "a word you wrote…"


def test_the_strip_dresses_itself_in_a_window_with_only_the_family_sheet(bar, field, window):
    window.setStyleSheet(family_stylesheet())
    bar.open_find([field("a cat")])
    _query(bar).setText("dog")
    QApplication.processEvents()

    picture = bar.grab().toImage()
    query = _query(bar).geometry()
    close = _button(bar, "Close").geometry()
    assert picture.pixelColor(query.left(), query.center().y()) == BLUE
    assert picture.pixelColor(query.center().x(), query.y() + query.height() - 3) == BG_SECONDARY
    assert picture.pixelColor(close.left() + 2, close.top() + 2) == BG_BUTTON
    assert bar.findChild(QLabel, "findCount").palette().color(QPalette.ColorRole.WindowText) == TEXT_MUTED
