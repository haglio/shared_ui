from __future__ import annotations

from PySide6.QtGui import QTextDocument

from shared_ui.code_text import as_rich_text
from shared_ui.colors import BG_KEYCAP
from shared_ui.type_scale import FONT_CODE


def _document(text: str) -> QTextDocument:
    document = QTextDocument()
    document.setHtml(as_rich_text(text))
    return document


def _families_of(document: QTextDocument, word: str) -> set[str]:
    families = set()
    block = document.begin()
    while block.isValid():
        fragments = block.begin()
        while not fragments.atEnd():
            fragment = fragments.fragment()
            if word in fragment.text():
                families.add(fragment.charFormat().fontFamilies()[0] if fragment.charFormat().fontFamilies()
                             else "")
            fragments += 1
        block = block.next()
    return families


def test_a_name_in_backticks_is_set_in_the_code_font_without_its_backticks():
    document = _document("moved into `1_sorted` today")

    assert document.toPlainText() == "moved into 1_sorted today"
    assert _families_of(document, "1_sorted") == {FONT_CODE}
    assert FONT_CODE not in _families_of(document, "moved")


def test_text_with_no_backticks_reads_exactly_as_written_even_where_it_looks_like_markup():
    assert _document("a <b> & c").toPlainText() == "a <b> & c"


def test_each_line_stays_a_line_of_its_own():
    assert _document("one\ntwo `x`").toPlainText() == "one\ntwo x"


def test_a_name_in_backticks_sits_on_a_lighter_gray_than_the_text_around_it():
    document = _document("moved into `1_sorted` today")
    block = document.begin()
    fragments = block.begin()
    grounds = {}
    while not fragments.atEnd():
        fragment = fragments.fragment()
        grounds[fragment.text().strip()] = fragment.charFormat().background().color().name()
        fragments += 1

    assert grounds["1_sorted"] == BG_KEYCAP.name()
    assert grounds["moved into"] != BG_KEYCAP.name()
