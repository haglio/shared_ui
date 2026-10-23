from __future__ import annotations

import re

from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPixmap, QTextDocumentFragment
from PyQt6.QtWidgets import QWidget

from shared_ui.colors import BG_PRIMARY, BLUE_LIGHT
from shared_ui.folder_path import FolderPath


def _links(path: FolderPath) -> list[tuple[str, str]]:
    return re.findall(r'<a href="([^"]*)"[^>]*>([^<]*)</a>', path.text())


def test_every_step_above_the_last_is_a_link_to_it():
    path = FolderPath(" / ")

    path.set_path(["Library", "big_batch", "cuts"])

    assert _links(path) == [("0", "Library"), ("1", "big_batch")]
    assert path.plain_text() == "Library / big_batch / cuts"


def test_clicking_a_step_says_which_step_it_was():
    path = FolderPath(" / ")
    path.set_path(["Library", "big_batch", "cuts"])
    clicked = []
    path.step_clicked.connect(clicked.append)

    path.linkActivated.emit({name: href for href, name in _links(path)}["big_batch"])

    assert clicked == [1]


def test_a_click_of_the_mouse_on_a_step_reaches_it(qapp):
    path = FolderPath(" / ")
    path.set_path(["Library", "big_batch", "cuts"])
    path.resize(path.sizeHint())
    clicked = []
    path.step_clicked.connect(clicked.append)
    on_the_first_step = QPointF(3, path.height() / 2)

    for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        qapp.sendEvent(path, QMouseEvent(kind, on_the_first_step, on_the_first_step,
                                         Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                                         Qt.KeyboardModifier.NoModifier))

    assert clicked == [0]


def test_the_separator_keeps_the_spacing_it_was_written_with():
    path = FolderPath("  ›  ")

    path.set_path(["Landscape", "All", "Images"])

    assert QTextDocumentFragment.fromHtml(path.text()).toPlainText() == "Landscape  ›  All  ›  Images"


def test_a_name_reads_as_it_is_written_whatever_it_holds():
    path = FolderPath(" / ")

    path.set_path(["Tom & Jerry", "<b>scene one</b>"])

    assert QTextDocumentFragment.fromHtml(path.text()).toPlainText() == "Tom & Jerry / <b>scene one</b>"
    assert _links(path) == [("0", "Tom &amp; Jerry")]


def test_the_steps_to_draw_as_links_can_be_named():
    path = FolderPath("  ›  ")

    path.set_path(["Landscape", "All", "Images"], linked=(1, 2))

    assert _links(path) == [("1", "All"), ("2", "Images")]


def test_words_can_lead_the_path_without_being_a_step_of_it():
    path = FolderPath("  ›  ")

    path.set_path(["Landscape", "All"], linked=(1,), lead="Search: “cats & dogs” in ")

    assert path.plain_text() == "Search: “cats & dogs” in Landscape  ›  All"
    assert QTextDocumentFragment.fromHtml(path.text()).toPlainText() == path.plain_text()
    assert _links(path) == [("1", "All")]


def _light_blue_ink(path: FolderPath) -> int:
    path.resize(path.sizeHint())
    drawn = QPixmap(path.size())
    drawn.fill(BG_PRIMARY)
    path.render(drawn, flags=QWidget.RenderFlag.DrawChildren)
    image = drawn.toImage()
    return sum(1 for x in range(image.width()) for y in range(image.height())
               if QColor(image.pixel(x, y)) == BLUE_LIGHT)


def test_a_step_that_is_a_link_is_drawn_in_the_familys_light_blue():
    linked, plain = FolderPath(" / "), FolderPath(" / ")

    linked.set_path(["Library", "big_batch"])
    plain.set_path(["Library", "big_batch"], linked=())

    assert _light_blue_ink(linked) > 20
    assert _light_blue_ink(plain) == 0


def test_a_long_path_wraps_between_its_steps_where_it_is_let_wrap():
    path = FolderPath("  ›  ")
    path.setWordWrap(True)
    path.set_path(["Landscape", *["SDXL Text-to-Image"] * 6])
    one_line = path.heightForWidth(10_000)

    assert path.heightForWidth(300) > one_line
