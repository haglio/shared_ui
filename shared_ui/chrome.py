"""A Qt tooltip is a top-level popup, so a rule set on a window never reaches it, and
Windows 11's dark mode then paints it unreadably: apply the sheet to the QApplication."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared_ui.palette import (
    BG_BUTTON,
    BG_BUTTON_ACTIVE,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BLUE,
    BORDER_SUBTLE,
    PICKED_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    Rgb,
    as_hex,
    hovered,
)
from shared_ui.spacing import (
    BUTTON_GAP,
    BUTTON_ICON_INSET,
    BUTTON_PAD_H,
    BUTTON_PAD_H_TIGHT,
    BUTTON_PAD_V,
    BUTTON_RADIUS,
    GAP_MEDIUM,
    GAP_SMALL,
    HAIRLINE,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QToolBar


def ground_rules() -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {as_hex(BG_PRIMARY)};
        color: {as_hex(TEXT_PRIMARY)};
    }}"""


def tooltip_rules() -> str:
    """A rounded style-sheet tooltip on Windows paints artifact rectangles around itself."""
    return f"""
    QToolTip {{
        background-color: {as_hex(BG_TERTIARY)};
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        padding: {BUTTON_PAD_V}px {BUTTON_PAD_H_TIGHT}px;
    }}"""


_MENU_ROW_PAD_V = BUTTON_PAD_V
_MENU_ROW_PAD_H = BUTTON_PAD_H

# Qt draws a menu row's icon against the row's own edge, and starts the row's words past
# its padding and a column as wide as the small icon size plus four.
_QT_MENU_ICON = 16
_ROOM_BEFORE_MENU_WORDS = _MENU_ROW_PAD_H + _QT_MENU_ICON + 4

_CHECKED_GROUND_MARGIN = GAP_SMALL
_MENU_ICON_BOX_LEFT = (_ROOM_BEFORE_MENU_WORDS - _QT_MENU_ICON) // 2 - _CHECKED_GROUND_MARGIN

_MENU_ARROW = 9
_MENU_ARROW_RIGHT = (_MENU_ROW_PAD_H - _MENU_ARROW) // 2


def menu_rules() -> str:
    return f"""
    QMenu {{
        background-color: {as_hex(BG_TERTIARY)};
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        padding: {GAP_SMALL}px 0;
    }}
    QMenu::item {{
        padding: {_MENU_ROW_PAD_V}px {_MENU_ROW_PAD_H}px;
        background-color: transparent;
    }}
    QMenu::item:selected {{
        background-color: {as_hex(BLUE)};
        color: {as_hex(PICKED_TEXT)};
    }}
    QMenu::item:disabled {{
        color: {as_hex(TEXT_MUTED)};
    }}
    QMenu::item:disabled:selected {{
        background-color: transparent;
        color: {as_hex(TEXT_MUTED)};
    }}
    QMenu::icon {{
        left: {_MENU_ICON_BOX_LEFT}px;
        padding: {_CHECKED_GROUND_MARGIN}px;
    }}
    QMenu::icon:checked {{
        background-color: {as_hex(BG_BUTTON_ACTIVE)};
        border-radius: {BUTTON_RADIUS}px;
    }}
    QMenu::right-arrow {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        right: {_MENU_ARROW_RIGHT}px;
        width: {_MENU_ARROW}px;
        height: {_MENU_ARROW}px;
    }}
    QMenu::separator {{
        height: {HAIRLINE}px;
        background-color: {as_hex(BORDER_SUBTLE)};
        margin: {GAP_SMALL}px 0;
    }}"""


def control_ground(color: Rgb, *controls: str) -> str:
    return f"""
    {", ".join(controls)} {{
        background-color: {as_hex(color)};
    }}
    {", ".join(f"{control}:hover" for control in controls)} {{
        background-color: {as_hex(hovered(color))};
    }}"""


_A_BUTTON_S_FRAME = f"""border: 1px solid {as_hex(BORDER_SUBTLE)};
        border-radius: {BUTTON_RADIUS}px;"""


def button_rules() -> str:
    return f"""
    QPushButton {{
        color: {as_hex(TEXT_PRIMARY)};
        {_A_BUTTON_S_FRAME}
        padding: {BUTTON_PAD_V}px {BUTTON_PAD_H}px;
    }}{control_ground(BG_BUTTON, "QPushButton")}{control_ground(BG_BUTTON_ACTIVE, "QPushButton:checked")}
    QPushButton:pressed, QPushButton:checked:pressed {{
        background-color: {as_hex(BLUE)};
    }}
    QPushButton:disabled {{
        background-color: {as_hex(BG_SECONDARY)};
        color: {as_hex(TEXT_MUTED)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
    }}"""


def field_rules() -> str:
    return f"""
    QPlainTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {as_hex(BG_SECONDARY)};
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        border-radius: {BUTTON_RADIUS}px;
        padding: {GAP_SMALL}px;
    }}
    QPlainTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {as_hex(BLUE)};
    }}"""


def tool_button_rules() -> str:
    return f"""
    QToolButton {{
        color: {as_hex(TEXT_PRIMARY)};
        {_A_BUTTON_S_FRAME}
        padding: {BUTTON_ICON_INSET}px {GAP_MEDIUM}px;
        font-weight: bold;
    }}{control_ground(BG_BUTTON, "QToolButton")}{control_ground(BG_BUTTON_ACTIVE, "QToolButton:checked")}
    QToolButton:disabled {{
        background-color: {as_hex(BG_SECONDARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
    }}"""


def toolbar_rules() -> str:
    """Qt draws a toolbar's buttons faint and edge to edge, so an app opts its toolbar into
    these with :func:`style_toolbar` rather than the family sheet carrying them."""
    return f"""
    QToolBar {{
        spacing: {BUTTON_GAP}px;
    }}
    QToolButton {{
        {_A_BUTTON_S_FRAME}
        {toolbar_padding(right=BUTTON_PAD_H_TIGHT)}
    }}{control_ground(BG_BUTTON, "QToolButton")}
    QToolButton:pressed {{
        background-color: {as_hex(BLUE)};
    }}
    QToolButton:disabled {{
        background-color: {as_hex(BG_SECONDARY)};
        color: {as_hex(TEXT_MUTED)};
    }}"""


def style_toolbar(toolbar: QToolBar) -> None:
    toolbar.setStyleSheet(toolbar_rules())
    toolbar.ensurePolished()
    toolbar.setStyleSheet(toolbar_rules())


def toolbar_padding(*, right: int) -> str:
    return f"padding: {BUTTON_PAD_V}px {right}px {BUTTON_PAD_V}px {BUTTON_PAD_H_TIGHT}px;"


ICON_BUTTON_PROPERTY = "iconButton"


def icon_button_rules() -> str:
    return f"""
    QAbstractButton[{ICON_BUTTON_PROPERTY}="true"] {{
        padding: 0px;
    }}"""


def item_view_rules() -> str:
    return """
    QAbstractItemView {
        outline: 0;
    }"""


def picked_item_rules(view: str = "QAbstractItemView") -> str:
    return f"""
    {view}::item:selected {{
        background-color: {as_hex(BLUE)};
        color: {as_hex(PICKED_TEXT)};
    }}"""


def family_stylesheet() -> str:
    """In a Qt style sheet a later rule of equal specificity wins, and an id selector outweighs
    every rule here: an app's own rules go after this sheet or on its window, and a
    ``QPushButton#generate`` keeps its blue."""
    return (f"{ground_rules()}\n{tooltip_rules()}\n{menu_rules()}\n{button_rules()}"
            f"\n{icon_button_rules()}\n{item_view_rules()}")
