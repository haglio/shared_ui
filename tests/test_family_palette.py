from __future__ import annotations

from collections import Counter

import pytest
from PyQt6.QtGui import QColor, QPalette, QPixmap
from PyQt6.QtWidgets import QLineEdit, QWidget

from shared_ui import palette as tokens
from shared_ui.chrome import family_stylesheet
from shared_ui.colors import (
    BG_PRIMARY,
    BG_SECONDARY,
    BLUE,
    BLUE_LIGHT,
    TEXT_PRIMARY,
    WHITE,
    dress_application,
    family_palette,
)

# Stands in for the color Windows hands an app that never says otherwise: invented, so a
# machine whose accent matches the family's blue cannot make these pass for the wrong reason.
_DESKTOP_ACCENT = QColor(210, 70, 54)

_OWNED = (
    QPalette.ColorRole.Highlight,
    QPalette.ColorRole.HighlightedText,
    QPalette.ColorRole.Link,
    QPalette.ColorRole.LinkVisited,
    QPalette.ColorRole.Accent,
    QPalette.ColorRole.BrightText,
    QPalette.ColorRole.AlternateBase,
)

_GROUPS = (
    QPalette.ColorGroup.Active,
    QPalette.ColorGroup.Inactive,
    QPalette.ColorGroup.Disabled,
)


def _desktop_palette() -> QPalette:
    base = QPalette()
    for role in _OWNED:
        base.setColor(role, _DESKTOP_ACCENT)
    return base


@pytest.fixture
def selection_pixels(qapp):
    was = qapp.palette()
    qapp.setPalette(family_palette(_desktop_palette()))
    try:
        field = QLineEdit()
        field.setText("selected words")
        field.resize(220, 30)
        field.selectAll()

        pixmap = QPixmap(field.size())
        pixmap.fill(BG_PRIMARY)
        field.render(pixmap, flags=QWidget.RenderFlag.DrawChildren)
        image = pixmap.toImage()

        yield Counter(
            QColor(image.pixel(x, y)).name()
            for y in range(image.height()) for x in range(image.width())
        )
    finally:
        qapp.setPalette(was)


def test_no_role_the_family_owns_keeps_the_desktops_color():
    result = family_palette(_desktop_palette())

    strays = sorted(
        f"{role.name} ({group.name})"
        for role in _OWNED for group in _GROUPS
        if result.color(group, role) == _DESKTOP_ACCENT
    )

    assert not strays, strays


def test_every_role_it_restates_is_a_family_color():
    family = {tokens.as_hex(value) for name in dir(tokens) if name.isupper()
              for value in [getattr(tokens, name)] if isinstance(value, tuple)}

    result = family_palette(_desktop_palette())

    strays = sorted(
        f"{role.name}={result.color(role).name()}"
        for role in _OWNED if result.color(role).name() not in family
    )
    assert not strays, strays


def test_a_selection_is_the_one_blue():
    result = family_palette(_desktop_palette())

    assert result.color(QPalette.ColorRole.Highlight) == BLUE


def test_selected_words_read_against_the_ground_they_sit_on():
    result = family_palette(_desktop_palette())

    ground = result.color(QPalette.ColorRole.Highlight)
    ink = result.color(QPalette.ColorRole.HighlightedText)

    assert ink.lightness() > ground.lightness() + 60


def test_the_roles_it_does_not_own_are_left_where_they_were():
    marker = QColor(1, 2, 3)
    untouched = (
        QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.Button,
        QPalette.ColorRole.Text, QPalette.ColorRole.Shadow, QPalette.ColorRole.Midlight,
        QPalette.ColorRole.ToolTipBase, QPalette.ColorRole.ToolTipText,
    )
    base = _desktop_palette()
    for role in untouched:
        base.setColor(role, marker)

    result = family_palette(base)

    moved = sorted(role.name for role in untouched if result.color(role) != marker)
    assert not moved, moved


@pytest.fixture
def an_undressed_application(qapp):
    was_palette, was_sheet = qapp.palette(), qapp.styleSheet()
    qapp.setPalette(_desktop_palette())
    qapp.setStyleSheet("")
    try:
        yield qapp
    finally:
        qapp.setStyleSheet(was_sheet)
        qapp.setPalette(was_palette)


def test_an_application_takes_the_family_palette_and_sheet_together(an_undressed_application):
    dress_application(an_undressed_application)

    assert an_undressed_application.palette().color(QPalette.ColorRole.Highlight) == BLUE
    assert an_undressed_application.styleSheet() == family_stylesheet()


def test_an_application_with_a_sheet_of_its_own_still_takes_the_family_palette(an_undressed_application):
    dress_application(an_undressed_application, sheet="QWidget { margin: 0px; }")

    assert an_undressed_application.palette().color(QPalette.ColorRole.Highlight) == BLUE
    assert an_undressed_application.styleSheet() == "QWidget { margin: 0px; }"


def test_a_field_paints_its_selection_in_the_family_blue(selection_pixels):
    assert selection_pixels[_DESKTOP_ACCENT.name()] == 0
    assert selection_pixels[BLUE.name()] > 100, selection_pixels.most_common(5)


def test_the_selected_words_are_still_legible_once_painted(selection_pixels):
    assert selection_pixels[TEXT_PRIMARY.name()] > 20, selection_pixels.most_common(5)


def test_a_banded_row_is_a_ground_of_the_family_and_never_white():
    assert family_palette().color(QPalette.ColorRole.AlternateBase) == BG_SECONDARY


def test_a_visited_link_is_the_blues_lighter_step():
    assert family_palette().color(QPalette.ColorRole.LinkVisited) == BLUE_LIGHT


def test_text_on_the_accent_is_white():
    assert family_palette().color(QPalette.ColorRole.BrightText) == WHITE
