from __future__ import annotations

import re

import pytest
from PyQt6.QtCore import QEvent, QPoint, QSize, Qt
from PyQt6.QtGui import QGuiApplication, QHelpEvent, QIcon, QTextDocument, QTextDocumentFragment
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QTextBrowser

from shared_ui.find_bar import FindBar
from shared_ui.reference import (
    ACTION_COLUMN_AT_LEAST_PX,
    BORDER,
    CONTROLLER_COLUMN_PX,
    CONTROLLER_HEADER,
    HOTKEY_BLOCK_PX,
    HOTKEY_HEADER,
    REFERENCE_WINDOW_TITLE,
    ROOM_FOR_THE_FRAME_PX,
    VOICE_COLUMN_PX,
    VOICE_HEADER,
    CommandRef,
    ReferenceBrowser,
    ReferenceDialog,
    ReferenceGroup,
    ReferenceSection,
    narrowest_page_px,
    reference_details,
    reference_first_size,
    render_reference_html,
)
from shared_ui.spacing import MARGIN_STANDARD

_QUIT = CommandRef("quit", ("quit",), key_columns=(("Ctrl+Alt+Q",),))
_PAUSE = CommandRef("pause / play everything", ("pause", "play"), key_columns=(("Esc",),),
                    detail="stops and starts the sound and the moving thumbnails")
_LISTEN = CommandRef("stop listening", ("stop listening",))
_NEXT = CommandRef("next item", ("next",), key_columns=(("Right",), ("D",), ()),
                   controller=("A / X",))
_FAVORITE = CommandRef("favorite", ("star",))

_GENERAL = ReferenceSection("General", (
    ReferenceGroup("", (_QUIT, _PAUSE)),
    ReferenceGroup("Voice control", (_LISTEN,)),
))
_SLIDES = ReferenceSection(
    "Slides", (ReferenceGroup("Navigation", (_NEXT,)), ReferenceGroup("Other", (_FAVORITE,))),
    key_headers=("Left", "Right", "Both"),
    note="Add “left” or “right” to aim a phrase, for example “left next”.")
_WITH_A_HEADSET = (_GENERAL, _SLIDES)
_NO_HEADSET = (_GENERAL,)


class _Kept:
    def __init__(self):
        self.made = []

    def keep(self, widget):
        self.made.append(widget)


@pytest.fixture
def widgets():
    kept = _Kept()
    yield kept
    for widget in kept.made:
        widget.close()
        widget.deleteLater()
    QApplication.processEvents()


def _bold_labels(html: str) -> list[str]:
    return re.findall(r"<b[^>]*>([^<]+)</b>", html)


def _tables(html: str) -> list[str]:
    return re.findall(r"<table[^>]*>.*?</table>", html, re.DOTALL)


def _rows_of(table: str) -> list[str]:
    return re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL)


def _cells_across(row: str) -> list[tuple[str, int, int, int]]:
    x, cells = 0, []
    for cell in re.findall(r"<td[^>]*>.*?</td>", row, re.DOTALL):
        width = int(re.search(r'width="(\d+)"', cell).group(1))
        span = re.search(r'colspan="(\d+)"', cell)
        cells.append((re.sub(r"<[^>]+>", "", cell), x, width, int(span.group(1)) if span else 1))
        x += width
    return cells


def _grid_at(width: int, *, controller: int = CONTROLLER_COLUMN_PX) -> dict[str, int]:
    action = width - HOTKEY_BLOCK_PX - controller - VOICE_COLUMN_PX
    return {"Action": 0, HOTKEY_HEADER: action, CONTROLLER_HEADER: action + HOTKEY_BLOCK_PX,
            VOICE_HEADER: action + HOTKEY_BLOCK_PX + controller}


def test_every_table_lays_its_columns_on_one_grid_so_the_heads_line_up_down_the_page():
    for width in (1000, 1400):
        grid = _grid_at(width)
        heads: dict[str, set[int]] = {}
        for table in _tables(render_reference_html(_WITH_A_HEADSET, width)):
            rows = _rows_of(table)
            for text, x, _width, _span in _cells_across(rows[0]):
                heads.setdefault(text, set()).add(x)
            for row in rows:
                cells = _cells_across(row)
                if cells[0][0] == "Left":
                    continue
                assert sum(cell[2] for cell in cells) == width
                assert cells[-1][1:3] == (grid[VOICE_HEADER], VOICE_COLUMN_PX)
        assert {head: xs for head, xs in heads.items() if head in grid} == {
            head: {x} for head, x in grid.items()}


def test_a_page_where_no_row_has_a_controller_input_gives_that_column_no_room():
    html = render_reference_html(_NO_HEADSET, 1000)
    grid = _grid_at(1000, controller=0)

    assert CONTROLLER_HEADER not in html
    for table in _tables(html):
        for row in _rows_of(table):
            cells = _cells_across(row)
            assert sum(cell[2] for cell in cells) == 1000
            assert cells[-1][1:3] == (grid[VOICE_HEADER], VOICE_COLUMN_PX)
    assert narrowest_page_px(_NO_HEADSET) == (HOTKEY_BLOCK_PX + VOICE_COLUMN_PX
                                              + ACTION_COLUMN_AT_LEAST_PX)
    assert narrowest_page_px(_WITH_A_HEADSET) == narrowest_page_px(_NO_HEADSET) + CONTROLLER_COLUMN_PX


def test_a_forked_hotkey_head_spans_its_columns_centered_and_underlined():
    [navigation, _other] = _tables(render_reference_html(_WITH_A_HEADSET, 1000))[2:]
    head, forks, body = _rows_of(navigation)

    assert re.search(r'<td(?=[^>]*colspan="3")(?=[^>]*align="center")[^>]*>\s*<b[^>]*>Hotkey</b>', head)
    assert f"border-bottom:1px solid {BORDER}" in head
    assert "rowspan" in head
    assert [cell[:3] for cell in _cells_across(forks)] == [
        ("Left", 0, 100), ("Right", 100, 100), ("Both", 200, 100)]
    assert [cell[0] for cell in _cells_across(body)][1:5] == ["Right", "d", "—", "A / X"]


def test_a_group_whose_rows_hold_no_key_keeps_its_actions_out_of_the_empty_hotkey_column():
    other = _tables(render_reference_html(_WITH_A_HEADSET, 1000))[3]
    grid = _grid_at(1000)

    assert _bold_labels(other) == ["Action", VOICE_HEADER]
    head, body = _rows_of(other)
    assert [cell[1:] for cell in _cells_across(head)] == [cell[1:] for cell in _cells_across(body)] == [
        (0, grid[HOTKEY_HEADER], 1),
        (grid[HOTKEY_HEADER], HOTKEY_BLOCK_PX, 1),
        (grid[CONTROLLER_HEADER], CONTROLLER_COLUMN_PX, 1),
        (grid[VOICE_HEADER], VOICE_COLUMN_PX, 1),
    ]
    assert [cell[0] for cell in _cells_across(body)] == ["favorite", "", "", "“star”"]


def test_every_head_action_included_sits_in_the_middle_of_its_cell():
    html = render_reference_html(_WITH_A_HEADSET, 1000)
    heads = re.findall(r"<td[^>]*>\s*<b[^>]*>[^<]+</b></td>", html)

    assert any(">Action<" in head for head in heads)
    for head in heads:
        assert 'valign="middle"' in head
        assert 'align="center"' in head


def _hotkey_cells(table: str) -> list[str]:
    return [cell for row in _rows_of(table) for cell in re.findall(r"<td[^>]*>.*?</td>", row)
            if "<span style=\"background:" in cell]


def test_a_letter_key_is_shown_in_lower_case_so_a_capital_i_is_never_taken_for_an_l():
    general, _voice, navigation, _other = _tables(render_reference_html(_WITH_A_HEADSET, 1000))
    keys = [re.sub(r"<[^>]+>", "", cell) for cell in _hotkey_cells(general) + _hotkey_cells(navigation)]

    assert keys == ["Ctrl+Alt+q", "Esc", "Right", "d"]


def test_a_single_hotkey_column_centers_its_keys_and_a_forked_one_leaves_them_at_the_left():
    general, _voice, navigation, _other = _tables(render_reference_html(_WITH_A_HEADSET, 1000))

    assert len(_hotkey_cells(general)) == 2
    assert all('align="center"' in cell for cell in _hotkey_cells(general))
    assert len(_hotkey_cells(navigation)) == 2
    assert not any('align="center"' in cell for cell in _hotkey_cells(navigation))


def _line_starts_of(document: QTextDocument, text: str) -> list[float]:
    block = document.find(text).block()
    document.documentLayout().blockBoundingRect(block)
    layout = block.layout()
    return [layout.lineAt(index).x() for index in range(layout.lineCount())]


def test_an_action_that_wraps_indents_its_later_lines_so_they_read_as_the_same_command():
    long = CommandRef("seconds a made-up thing holds the screen before the show moves on to the "
                      "next one, only while nothing holds it", ("hold seconds",))
    document = QTextDocument()
    document.setHtml(render_reference_html(
        (ReferenceSection("Long", (ReferenceGroup("", (long,)),)),), 900))
    document.setTextWidth(900)

    first, *later = _line_starts_of(document, "seconds a made-up thing")
    assert later
    assert all(start > first for start in later)


def test_an_untitled_group_has_no_heading_and_a_titled_one_has_its_own():
    general = render_reference_html(_NO_HEADSET, 1000)

    assert general.index("<table") < general.index("<h4")
    assert re.findall(r"<h4[^>]*>([^<]+)</h4>", general) == ["Voice control"]


def test_a_sections_note_and_a_rows_detail_are_tooltips_on_their_titles_never_text_on_the_page():
    html = render_reference_html(_WITH_A_HEADSET, 1000)
    details = reference_details(_WITH_A_HEADSET)

    assert set(details.values()) == {_PAUSE.detail, _SLIDES.note}
    for title, text in ((_SLIDES.title, _SLIDES.note), (_PAUSE.description, _PAUSE.detail)):
        anchor = re.search(rf'<a href="(detail:\d+)"[^>]*>{re.escape(title)}</a>', html)
        assert details[anchor.group(1)] == text
    assert _PAUSE.detail not in html
    assert "<style" not in html


def test_the_reference_shows_a_detail_as_a_rich_text_tooltip_over_its_action(widgets):
    said = []

    class Tooltip:
        @staticmethod
        def showText(_at, text, _widget):
            said.append(text)

        @staticmethod
        def hideText():
            said.append(None)

    browser = ReferenceBrowser(_WITH_A_HEADSET, tooltip=Tooltip)
    widgets.keep(browser)
    browser.resize(1000, 800)
    browser.show()
    cursor = browser.document().find(_PAUSE.description)
    cursor.setPosition(cursor.selectionStart() + 1)
    at = browser.cursorRect(cursor).center()
    assert browser.detail_at(at) == _PAUSE.detail

    assert browser.event(QHelpEvent(QEvent.Type.ToolTip, at, browser.viewport().mapToGlobal(at)))
    nowhere = QPoint(0, 0)
    browser.event(QHelpEvent(QEvent.Type.ToolTip, nowhere, browser.viewport().mapToGlobal(nowhere)))

    assert Qt.mightBeRichText(said[0])
    assert QTextDocumentFragment.fromHtml(said[0]).toPlainText() == _PAUSE.detail
    assert said[1] is None
    assert not browser.openLinks()


@pytest.mark.parametrize("sections", [_WITH_A_HEADSET, _NO_HEADSET])
@pytest.mark.parametrize("extra", [0, 50, 400, 900])
def test_the_reference_needs_no_horizontal_scrollbar_at_any_width(widgets, sections, extra):
    browser = ReferenceBrowser(sections)
    widgets.keep(browser)
    browser.resize(narrowest_page_px(sections) + extra, 800)
    browser.show()
    QApplication.processEvents()

    assert browser.width() >= browser.minimumWidth()
    assert browser.minimumWidth() < narrowest_page_px(sections) + 50
    assert browser.horizontalScrollBar().maximum() == 0


def test_the_reference_lays_its_tables_out_again_when_its_width_changes_and_keeps_its_place(widgets):
    def widths():
        return {frame.format().width().rawValue()
                for frame in browser.document().rootFrame().childFrames()}

    browser = ReferenceBrowser(_WITH_A_HEADSET)
    widgets.keep(browser)
    browser.resize(1000, 300)
    browser.show()
    QApplication.processEvents()
    page = browser.viewport().width() - 2 * browser.document().documentMargin()
    assert widths() == {page}
    browser.verticalScrollBar().setValue(40)

    browser.resize(1300, 300)
    QApplication.processEvents()

    assert widths() == {page + 300}
    assert browser.verticalScrollBar().value() == 40


def _dialog(widgets, sections=_WITH_A_HEADSET):
    dialog = ReferenceDialog(sections, icon=QIcon())
    widgets.keep(dialog)
    return dialog


def test_the_reference_is_titled_for_what_it_holds(widgets):
    assert _dialog(widgets).windowTitle() == REFERENCE_WINDOW_TITLE == "Hotkeys & Voice Commands Reference"


def test_ctrl_f_opens_a_find_that_survives_the_page_being_laid_out_again(widgets):
    dialog = _dialog(widgets)
    dialog.show()
    dialog.activateWindow()
    assert QTest.qWaitForWindowActive(dialog)

    QTest.keyClick(dialog, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    dialog.findChild(QLineEdit).setText("Ctrl+Alt+Q")
    assert dialog.findChild(QLabel, "findCount").text() == "1 of 1"

    dialog.resize(dialog.width() + 200, dialog.height())
    QApplication.processEvents()

    assert dialog.findChild(QLabel, "findCount").text() == "1 of 1"
    [marked] = dialog.findChild(QTextBrowser).extraSelections()
    assert marked.cursor.selectedText() == "Ctrl+Alt+q"


def test_the_reference_find_keeps_off_the_windows_edges(widgets):
    dialog = _dialog(widgets)
    dialog.resize(640, 480)
    dialog.show()
    dialog.open_find()
    QApplication.processEvents()

    strip = dialog.findChild(FindBar)
    held = strip.childrenRect().translated(strip.mapTo(dialog, QPoint(0, 0)))
    assert held.left() >= MARGIN_STANDARD
    assert dialog.width() - held.right() - 1 >= MARGIN_STANDARD
    assert dialog.height() - held.y() - held.height() >= MARGIN_STANDARD


def test_the_reference_opens_at_a_size_that_fits_its_screen_and_never_narrower_than_its_grid(widgets):
    dialog = _dialog(widgets)
    available = QGuiApplication.primaryScreen().availableGeometry()
    fits = reference_first_size(available.size(), at_least_wide=dialog.minimumWidth())

    assert (dialog.width(), dialog.height()) == (fits.width(), fits.height())
    assert narrowest_page_px(_WITH_A_HEADSET) < dialog.minimumWidth()
    dialog.resize(300, 800)
    assert dialog.width() == dialog.minimumWidth()


def test_the_first_size_is_the_smaller_of_a_thousand_by_eight_hundred_and_what_the_screen_fits():
    roomy = reference_first_size(QSize(1920, 1040), at_least_wide=820)
    short = reference_first_size(QSize(1280, 720), at_least_wide=820)
    narrow = reference_first_size(QSize(800, 800), at_least_wide=820)

    assert (roomy.width(), roomy.height()) == (1000, 800)
    assert (short.width(), short.height()) == (1000, 720 - ROOM_FOR_THE_FRAME_PX)
    assert (narrow.width(), narrow.height()) == (820, 800 - ROOM_FOR_THE_FRAME_PX)


def test_a_section_says_whether_any_row_has_a_key_or_a_controller_input():
    assert _GENERAL.has_keys
    assert not _GENERAL.has_controller
    assert _SLIDES.has_controller
    assert not ReferenceSection("Spoken", (ReferenceGroup("", (_LISTEN,)),)).has_keys
