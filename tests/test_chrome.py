"""shared_ui.chrome: the family's style-sheet rules, read back off the sheet."""

from __future__ import annotations

import re

from PyQt6.QtGui import QColor

from shared_ui import chrome, palette

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


def test_every_color_on_the_sheet_is_a_palette_color():
    sheet = chrome.family_stylesheet()
    allowed = {palette.as_hex(getattr(palette, name)) for name in dir(palette) if name.isupper()}

    strays = sorted({hex_ for hex_ in _HEX.findall(sheet) if hex_.lower() not in allowed})

    assert not strays, f"colors spelled in place instead of taken from the palette: {strays}"
    assert sheet.count("{") == sheet.count("}")


def test_the_family_sheet_is_every_fragment():
    sheet = chrome.family_stylesheet()

    for fragment in (chrome.ground_rules(), chrome.tooltip_rules(),
                     chrome.menu_rules(), chrome.button_rules()):
        assert fragment in sheet


def test_a_button_that_is_on_sits_on_a_lighter_ground_than_one_at_rest():
    """One rule across the family, so a toggled button reads the same whichever
    app it is in.  Compared rather than name-matched, so it survives a palette
    change and still fails an inversion."""
    rules = _rules(chrome.button_rules())

    at_rest = QColor(_background(rules["QPushButton"]))
    on = QColor(_background(rules["QPushButton:checked"]))

    assert on.lightness() > at_rest.lightness()


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


def test_a_tooltip_has_square_corners():
    # A rounded style-sheet tooltip on Windows paints artifact boxes around itself.
    rules = _rules(chrome.tooltip_rules())

    assert "QToolTip" in rules
    assert "border-radius" not in rules["QToolTip"]
