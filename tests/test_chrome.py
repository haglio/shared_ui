"""shared_ui.chrome: the family's style-sheet rules, read back off the sheet and
off what Qt draws with it."""

from __future__ import annotations

import re

import pytest
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QAction, QColor, QCursor, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QPushButton,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from shared_ui import chrome, colors, palette, spacing

_HEX = re.compile(r"#[0-9a-fA-F]{3,6}\b")
_RULE = re.compile(r"(?P<selector>[^{}]+?)\s*\{(?P<body>[^{}]*)\}")
_BACKGROUND = re.compile(r"background(?:-color)?\s*:\s*(?P<value>[^;]+);")


def _rules(sheet: str) -> dict[str, str]:
    """Each selector's body, out of a sheet."""
    return {m.group("selector").strip(): m.group("body") for m in _RULE.finditer(sheet)}


def _background(body: str) -> str:
    match = _BACKGROUND.search(body)
    assert match, body
    return match.group("value").strip()


def test_every_color_on_the_sheet_is_a_palette_color_or_one_a_hover_lifted():
    sheet = chrome.family_stylesheet() + chrome.toolbar_rules() + chrome.tool_button_rules()
    grounds = {value for name in dir(palette) if name.isupper()
               for value in [getattr(palette, name)] if isinstance(value, tuple)}
    allowed = {palette.as_hex(color) for ground in grounds
               for color in (ground, palette.hovered(ground))}

    strays = sorted({hex_ for hex_ in _HEX.findall(sheet) if hex_.lower() not in allowed})

    assert not strays, f"colors spelled in place instead of taken from the palette: {strays}"
    assert sheet.count("{") == sheet.count("}")


def test_the_family_sheet_is_every_fragment():
    sheet = chrome.family_stylesheet()

    for fragment in (chrome.ground_rules(), chrome.tooltip_rules(),
                     chrome.menu_rules(), chrome.button_rules(),
                     chrome.mark_button_rules(), chrome.item_view_rules()):
        assert fragment in sheet


def test_a_button_that_is_on_sits_on_a_lighter_ground_than_one_at_rest():
    """One rule across the family, so a toggled button reads the same whichever
    app it is in.  Compared rather than name-matched, so it survives a palette
    change and still fails an inversion."""
    rules = _rules(chrome.button_rules())

    at_rest = QColor(_background(rules["QPushButton"]))
    on = QColor(_background(rules["QPushButton:checked"]))

    assert on.lightness() > at_rest.lightness()


@pytest.fixture
def put_the_pointer_on():
    resting = QCursor.pos()

    def put_it_on(widget: QWidget) -> None:
        QCursor.setPos(widget.mapToGlobal(widget.rect().center()))
        QApplication.processEvents()

    yield put_it_on
    QCursor.setPos(resting)
    QApplication.processEvents()


def _shown_button(sheet: str, *, lit: bool = False) -> QPushButton:
    button = QPushButton("Edit")
    button.setCheckable(lit)
    button.setChecked(lit)
    button.setStyleSheet(sheet)
    _shown_away_from_the_pointer(button)
    return button


def _ground(widget: QWidget) -> str:
    drawn = widget.grab().toImage()
    return drawn.pixelColor(3, drawn.height() // 2).name()


def _one_step_lighter(ground: str) -> str:
    return colors.hovered(QColor(ground)).name()


def test_a_button_under_the_pointer_sits_one_step_lighter_than_at_rest(put_the_pointer_on):
    button = _shown_button(chrome.button_rules())
    at_rest = _ground(button)
    put_the_pointer_on(button)
    under_the_pointer = _ground(button)
    button.close()

    assert under_the_pointer == _one_step_lighter(at_rest)


def test_a_lit_button_under_the_pointer_stays_its_own_color_a_shade_brighter(put_the_pointer_on):
    button = _shown_button(chrome.button_rules(), lit=True)
    lit = _ground(button)
    put_the_pointer_on(button)
    under_the_pointer = _ground(button)
    button.close()

    assert under_the_pointer == _one_step_lighter(lit)


@pytest.mark.parametrize("lit", [False, True], ids=["at rest", "lit"])
def test_a_press_flashes_the_blue_over_the_hover(put_the_pointer_on, lit):
    button = _shown_button(chrome.button_rules(), lit=lit)
    put_the_pointer_on(button)
    button.setDown(True)
    pressed = _ground(button)
    button.close()

    assert pressed == palette.as_hex(palette.BLUE)


def test_a_disabled_button_reads_as_disabled_in_text_and_ground():
    rules = _rules(chrome.button_rules())

    disabled = rules["QPushButton:disabled"]

    assert palette.as_hex(palette.TEXT_MUTED) in disabled
    assert QColor(_background(disabled)).lightness() < QColor(_background(rules["QPushButton"])).lightness()


def test_hovering_a_menu_row_that_cannot_be_clicked_promises_nothing():
    """A disabled row under the cursor keeps the menu's own ground, where an
    enabled one lights up: hovering something unclickable must not promise a
    click."""
    rules = _rules(chrome.menu_rules())

    assert _background(rules["QMenu::item:selected"]) == palette.as_hex(palette.BLUE)
    assert _background(rules["QMenu::item:disabled:selected"]) == "transparent"


def _solid_mark() -> QIcon:
    """A mark whose ink is its whole frame, so where it is drawn is where its ink is."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(*palette.TEXT_PRIMARY))
    return QIcon(pixmap)


def _menu_of_marked_rows(*labels: str) -> tuple[QMenu, list[QAction]]:
    menu = QMenu()
    menu.setStyleSheet(chrome.menu_rules())
    rows = [QAction(_solid_mark(), label, menu) for label in labels]
    menu.addActions(rows)
    menu.resize(menu.sizeHint())
    return menu, rows


def _inked_runs(image: QImage, row: QRect) -> list[tuple[int, int]]:
    """The spans of *row*'s columns with anything lighter than the row's own ground."""
    ground = image.pixelColor(row.right() - 2, row.center().y()).lightness()
    inked = [x for x in range(row.left(), row.left() + row.width())
             if any(image.pixelColor(x, y).lightness() > ground + 24
                    for y in range(row.top(), row.top() + row.height()))]
    runs: list[tuple[int, int]] = []
    for x in inked:
        if runs and x == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], x)
        else:
            runs.append((x, x))
    return runs


def test_a_menu_row_s_mark_sits_midway_between_the_menu_s_edge_and_its_words():
    """Qt puts a row's mark hard against the menu's edge and starts its words a
    whole column further in; the mark belongs in the middle of that room."""
    menu, (row,) = _menu_of_marked_rows("Heading")
    rect = menu.actionGeometry(row)

    (mark_left, mark_right), (words_left, _), *_ = _inked_runs(menu.grab().toImage(), rect)

    before_the_mark = mark_left - rect.left()
    after_the_mark = words_left - mark_right - 1
    assert abs(before_the_mark - after_the_mark) <= 2, (before_the_mark, after_the_mark)


def test_a_checked_row_s_mark_sits_on_the_lighter_ground_of_a_control_that_is_on():
    """A row that carries a mark shows its check through the mark alone, so
    without this a toggle in a menu looks the same on as off."""
    menu, (toggle,) = _menu_of_marked_rows("Heading")
    toggle.setCheckable(True)
    rect = menu.actionGeometry(toggle)
    off = menu.grab().toImage()
    (mark_left, _), *_ = _inked_runs(off, rect)
    toggle.setChecked(True)
    on = menu.grab().toImage()

    beside_the_mark = (mark_left - 2, rect.center().y())
    assert off.pixelColor(*beside_the_mark) == QColor(*palette.BG_TERTIARY)
    assert on.pixelColor(*beside_the_mark).lightness() > QColor(*palette.BG_TERTIARY).lightness()


def _shown_away_from_the_pointer(widget: QWidget) -> None:
    widget.resize(widget.sizeHint())
    widget.move(QApplication.primaryScreen().geometry().center())
    widget.show()
    QApplication.processEvents()


def _toolbar_button(padding: str = "") -> tuple[QToolBar, QToolButton]:
    toolbar = QToolBar()
    toolbar.setStyleSheet(chrome.toolbar_rules())
    toolbar.addAction(QAction("Heading", toolbar))
    [button] = [widget for widget in map(toolbar.widgetForAction, toolbar.actions())
                if isinstance(widget, QToolButton)]
    button.setStyleSheet(padding)
    _shown_away_from_the_pointer(toolbar)
    return toolbar, button


def test_a_toolbar_button_wears_the_family_button_s_border_round_its_ground():
    toolbar, button = _toolbar_button()
    drawn = button.grab().toImage()
    toolbar.close()

    middle = drawn.height() // 2
    assert drawn.pixelColor(0, middle) == QColor(*palette.BORDER_SUBTLE)
    assert drawn.pixelColor(3, middle) == QColor(*palette.BG_BUTTON)


def test_a_toolbar_s_buttons_stand_the_family_s_button_gap_apart():
    toolbar = QToolBar()
    toolbar.setStyleSheet(chrome.toolbar_rules())
    toolbar.addActions([QAction("One", toolbar), QAction("Two", toolbar)])
    _shown_away_from_the_pointer(toolbar)
    first, second = (toolbar.widgetForAction(action) for action in toolbar.actions())
    gap = second.geometry().left() - first.geometry().right() - 1
    toolbar.close()

    assert gap == spacing.BUTTON_GAP


def test_a_toolbar_button_given_more_room_on_its_right_grows_by_that_much():
    toolbar, button = _toolbar_button()
    ordinary = button.sizeHint().width()
    toolbar.close()
    toolbar, button = _toolbar_button(chrome.toolbar_padding(right=40))
    roomier = button.sizeHint().width()
    toolbar.close()

    assert roomier - ordinary == 40 - spacing.BUTTON_PAD_H_TIGHT


def test_a_tooltip_has_square_corners():
    # A rounded style-sheet tooltip on Windows paints artifact rectangles around
    # itself.
    rules = _rules(chrome.tooltip_rules())

    assert "QToolTip" in rules
    assert "border-radius" not in rules["QToolTip"]


def test_a_picked_row_the_keyboard_is_on_wears_no_focus_frame():
    # Windows 11 draws a white frame round the row the keyboard is on, and keeps
    # it there only while the list has the focus: on a picked row it is a second
    # mark beside the blue, saying nothing the blue does not.
    blue = palette.as_hex(palette.BLUE)
    view = QTreeWidget()
    view.setHeaderHidden(True)
    view.setStyleSheet(chrome.family_stylesheet()
                       + f"QTreeView::item:selected {{ background-color: {blue}; }}")
    for _ in range(2):
        view.addTopLevelItem(QTreeWidgetItem([""]))
    view.resize(200, 80)
    view.show()
    view.activateWindow()
    view.setFocus()
    view.setCurrentItem(view.topLevelItem(0))
    QApplication.processEvents()

    focused = view.hasFocus()
    image = view.viewport().grab().toImage()
    row = view.visualItemRect(view.topLevelItem(0))
    colors = {image.pixelColor(x, y).name()
              for y in range(row.top(), row.top() + row.height())
              for x in range(row.left(), row.left() + row.width())}
    view.close()

    assert focused
    assert colors == {blue}
