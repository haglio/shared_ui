"""shared_ui.colors.family_palette: the roles the desktop theme would fill in.

A style sheet dresses what it names.  What it does not name stays the palette's,
and the palette an app starts with is the desktop's -- which put the user's
accent color, an orange, behind every selected word in these dark apps.  These
tests hand in a fabricated desktop accent as the base and check that no role the
family owns comes back still wearing it.
"""

from __future__ import annotations

from collections import Counter

import pytest
from PyQt6.QtGui import QColor, QPalette, QPixmap
from PyQt6.QtWidgets import QLineEdit, QWidget

from shared_ui import palette as tokens
from shared_ui.colors import BG_PRIMARY, BLUE, TEXT_PRIMARY, family_palette

# Stands in for the color Windows hands an app that never says otherwise.
# Invented, so a machine whose accent happens to match the family's blue cannot
# make these pass for the wrong reason.
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
    """A palette with the accent in every role the family means to take back."""
    base = QPalette()
    for role in _OWNED:
        base.setColor(role, _DESKTOP_ACCENT)
    return base


@pytest.fixture
def selection_pixels(qapp):
    """What a field with its words picked actually puts on the screen, tallied
    by color, drawn while the application wears the family palette.

    The QApplication is one object for the whole session and the suite may
    collect in any order, so the palette is put back: a test that dressed it and
    walked away would decide what the tests after it were looking at.
    """
    was = qapp.palette()
    qapp.setPalette(family_palette(_desktop_palette()))
    try:
        field = QLineEdit()
        field.setText("selected words")
        field.resize(220, 30)
        field.selectAll()

        picture = QPixmap(field.size())
        picture.fill(BG_PRIMARY)  # the dark canvas these fields sit on
        field.render(picture, flags=QWidget.RenderFlag.DrawChildren)
        image = picture.toImage()

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
    """The rule the style sheet is already held to.  A color spelled in place
    here is a near-blue nobody can find again -- and the point of this function
    is that there is one blue, not that the orange became some other orange."""
    family = {tokens.as_hex(getattr(tokens, name)) for name in dir(tokens) if name.isupper()}

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
    """Windows sat black text on its accent.  On a dark app's blue that would be
    the darkest thing on the screen, which is not what picking words looks
    like."""
    result = family_palette(_desktop_palette())

    ground = result.color(QPalette.ColorRole.Highlight)
    ink = result.color(QPalette.ColorRole.HighlightedText)

    assert ink.lightness() > ground.lightness() + 60


def test_the_roles_it_does_not_own_are_left_where_they_were():
    """A style computes a widget's bevels and shadows from that widget's own
    ground, and the tooltip is the style sheet's; naming either here would fix
    one answer across grounds that differ."""
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


def test_a_field_paints_its_selection_in_the_family_blue(selection_pixels):
    """The palette is not a record of an intention: it is what a field reaches
    for when it draws the words you have picked."""
    assert selection_pixels[_DESKTOP_ACCENT.name()] == 0
    assert selection_pixels[BLUE.name()] > 100, selection_pixels.most_common(5)


def test_the_selected_words_are_still_legible_once_painted(selection_pixels):
    """The ink as well as the ground: a selection drawn in the family's blue with
    the desktop's black text would pass every check above and read as a hole."""
    assert selection_pixels[TEXT_PRIMARY.name()] > 20, selection_pixels.most_common(5)
