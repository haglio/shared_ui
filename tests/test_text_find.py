"""shared_ui.text_find: the matches of one query across a window's text fields,
painted where they are, and walked one at a time."""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QPlainTextEdit, QTextBrowser, QVBoxLayout, QWidget

from shared_ui.colors import AMBER
from shared_ui.text_find import TextFind


@pytest.fixture
def fields():
    """Loose fields holding the texts given, in the order a form would lay them."""
    hosts = []

    def make(*texts):
        host = QWidget()
        column = QVBoxLayout(host)
        made = []
        for text in texts:
            field = QPlainTextEdit()
            field.setPlainText(text)
            column.addWidget(field)
            made.append(field)
        hosts.append(host)
        return made

    yield make
    for host in hosts:
        host.deleteLater()


def _standing_on(*fields):
    for field in fields:
        for selection in field.extraSelections():
            if selection.format.background().color() == AMBER:
                return field
    return None


def test_a_search_counts_every_match_across_the_fields(fields):
    positive, negative = fields("a cat and a cat", "no cat")
    find = TextFind()
    find.set_fields([positive, negative])

    assert find.search("cat") == 3
    assert find.position() == 1
    assert _standing_on(positive, negative) is positive


def test_matching_is_case_insensitive_and_non_overlapping(fields):
    (field,) = fields("Cat CAT cat")
    find = TextFind()
    find.set_fields([field])

    assert find.search("cat") == 3
    field.setPlainText("aaa")
    assert find.search("aa") == 1


def test_a_query_matches_its_own_characters_and_nothing_they_could_stand_for(fields):
    (field,) = fields("Shift+[ steps back, Ctrl+. does not, and neither does Shift+a")
    find = TextFind()
    find.set_fields([field])

    assert find.search("Shift+[") == 1
    assert find.search("Ctrl+.") == 1
    assert find.search("+.") == 1

def test_stepping_walks_forward_and_wraps_both_ways(fields):
    positive, negative = fields("a cat", "no cat")
    find = TextFind()
    find.set_fields([positive, negative])
    find.search("cat")

    find.step(1)
    assert (find.position(), _standing_on(positive, negative)) == (2, negative)
    find.step(1)
    assert (find.position(), _standing_on(positive, negative)) == (1, positive)
    find.step(-1)
    assert (find.position(), _standing_on(positive, negative)) == (2, negative)


def test_the_cursor_lands_on_the_current_match_without_selecting_it(fields):
    # Qt paints a real selection over an extra selection, in the palette's
    # highlight color, so a selected match would hide the amber that says which
    # match is current.
    (field,) = fields("a cat on a mat")
    find = TextFind()
    find.set_fields([field])

    find.search("mat")

    assert field.textCursor().position() == len("a cat on a ")
    assert field.textCursor().selectedText() == ""


def test_every_match_is_painted_and_the_current_one_differently(fields):
    (field,) = fields("a cat and a cat")
    find = TextFind()
    find.set_fields([field])

    find.search("cat")

    selections = field.extraSelections()
    assert len(selections) == 2
    first, second = (s.format.background().color() for s in selections)
    assert first != second


def test_the_current_highlight_moves_with_the_step(fields):
    (field,) = fields("a cat and a cat")
    find = TextFind()
    find.set_fields([field])
    find.search("cat")
    before = [s.format.background().color().name() for s in field.extraSelections()]

    find.step(1)

    after = [s.format.background().color().name() for s in field.extraSelections()]
    assert after == list(reversed(before))


def test_clearing_leaves_no_paint_behind(fields):
    (field,) = fields("a cat")
    find = TextFind()
    find.set_fields([field])
    find.search("cat")
    assert field.extraSelections()

    find.clear()

    assert not field.extraSelections()
    assert find.count() == 0
    assert find.position() == 0


def test_retargeting_drops_the_previous_fields_highlights(fields):
    old, new = fields("a cat", "another cat")
    find = TextFind()
    find.set_fields([old])
    find.search("cat")
    assert old.extraSelections()

    find.set_fields([new])

    assert not old.extraSelections()


def test_refreshing_keeps_your_place_while_the_text_is_edited(fields):
    (field,) = fields("cat cat cat")
    find = TextFind()
    find.set_fields([field])
    find.search("cat")
    find.step(1)
    assert find.position() == 2

    field.setPlainText("cat cat cat and cat")
    assert find.refresh() == 4
    assert find.position() == 2


def test_refreshing_past_the_end_clamps_rather_than_losing_the_place(fields):
    (field,) = fields("cat cat cat")
    find = TextFind()
    find.set_fields([field])
    find.search("cat")
    find.step(1)
    find.step(1)
    assert find.position() == 3

    field.setPlainText("cat")

    assert find.refresh() == 1
    assert find.position() == 1


def test_an_empty_query_matches_nothing(fields):
    (field,) = fields("a cat")
    find = TextFind()
    find.set_fields([field])

    assert find.search("") == 0
    assert not field.extraSelections()



def test_the_window_is_told_which_field_a_match_is_shown_in(fields):
    first, second = fields("a cat", "another cat")
    shown = []
    find = TextFind(reveal=shown.append)
    find.set_fields([first, second])

    find.search("cat")
    find.step(1)

    assert shown == [first, second]


def test_a_match_inside_a_table_lands_on_the_matched_words():
    browser = QTextBrowser()
    browser.setHtml(
        "<table><tr><td>Quit</td><td>Ctrl+Alt+Q</td></tr>"
        "<tr><td>Loop this one</td><td>E</td></tr></table>")
    find = TextFind()
    find.set_fields([browser])

    find.search("loop")

    cursor = browser.textCursor()
    cursor.setPosition(cursor.position() + len("loop"), cursor.MoveMode.KeepAnchor)
    assert cursor.selectedText() == "Loop"
    browser.deleteLater()
