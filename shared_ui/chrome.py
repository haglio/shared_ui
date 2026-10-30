"""The family's chrome as Qt style-sheet rules, built from the tokens.

The tokens kept the colors in step, and the apps still looked like five
programs: each had written its own rules for the same three widgets -- six
`QPushButton` rule sets, three `QMenu` rule sets, and one app's tray menu with
none at all, rendering native beside another's dark one.  The padding, the
corner radius, the border and what a hover does had drifted freely.  These are
those rules, once, so an app applies them and adds only what is its own.

Apply :func:`family_stylesheet` to the ``QApplication``, not to a window.  A
tooltip is a top-level popup, so a rule set on a window never reaches it, and
Windows 11's dark mode then paints the tooltip unreadably -- which is how
tooltips came to look "missing".  A tray menu with no window to inherit from
takes :func:`menu_rules` itself.

No Qt is imported here: a sheet is a string, and the numbers come from
:mod:`shared_ui.palette`.
"""

from __future__ import annotations

from shared_ui.palette import (
    BG_BUTTON,
    BG_BUTTON_ACTIVE,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BLUE,
    BORDER_SUBTLE,
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


def ground_rules() -> str:
    """The dark ground and the primary text, on every widget."""
    return f"""
    QMainWindow, QWidget {{
        background-color: {as_hex(BG_PRIMARY)};
        color: {as_hex(TEXT_PRIMARY)};
    }}"""


def tooltip_rules() -> str:
    """A tooltip readable on a dark desktop.

    Square corners on purpose: a rounded style-sheet tooltip on Windows paints
    artifact rectangles around itself.
    """
    return f"""
    QToolTip {{
        background-color: {as_hex(BG_TERTIARY)};
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        padding: {BUTTON_PAD_V}px {BUTTON_PAD_H_TIGHT}px;
    }}"""


_MENU_ROW_PAD_V = BUTTON_PAD_V
_MENU_ROW_PAD_H = BUTTON_PAD_H

# Qt's layout, not the family's: it draws a menu row's icon against the row's
# own edge, and starts the row's words past its padding and a column as wide as
# the small icon size plus four.
_QT_MENU_ICON = 16
_ROOM_BEFORE_MENU_WORDS = _MENU_ROW_PAD_H + _QT_MENU_ICON + 4

_CHECKED_GROUND_MARGIN = GAP_SMALL
_MENU_ICON_BOX_LEFT = (_ROOM_BEFORE_MENU_WORDS - _QT_MENU_ICON) // 2 - _CHECKED_GROUND_MARGIN

_MENU_ARROW = 9
_MENU_ARROW_RIGHT = (_MENU_ROW_PAD_H - _MENU_ARROW) // 2


def menu_rules() -> str:
    """Every right-click and tray menu.

    The ground rule paints a menu's rows on the same flat background as the
    menu itself, which leaves the row under the cursor looking exactly like the
    rows either side of it -- so a menu gives no sign of what a click would
    land on.  The highlight is the blue a dropdown marks its rows with, and a
    row that cannot be clicked never wears it: hovering something unclickable
    must not promise a click.
    """
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
        color: {as_hex(TEXT_PRIMARY)};
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


def button_rules() -> str:
    """A push button at rest, hovered, on, pressed and disabled.

    A control that is ON sits on a lighter ground than one at rest -- the rule
    the tokens state -- and a press flashes the blue that means more than
    "engaged".
    """
    return f"""
    QPushButton {{
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        border-radius: {BUTTON_RADIUS}px;
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
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        border-radius: {BUTTON_RADIUS}px;
        padding: {BUTTON_ICON_INSET}px {GAP_MEDIUM}px;
        font-weight: bold;
    }}{control_ground(BG_BUTTON, "QToolButton")}{control_ground(BG_BUTTON_ACTIVE, "QToolButton:checked")}
    QToolButton:disabled {{
        background-color: {as_hex(BG_SECONDARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
    }}"""


def toolbar_rules() -> str:
    """A toolbar's buttons as the family's buttons, for the toolbar it is set on.

    Not part of the family sheet: Qt draws a toolbar's buttons faint and
    edge to edge, and an app opts its toolbar into these by setting them on it.
    """
    return f"""
    QToolBar {{
        spacing: {BUTTON_GAP}px;
    }}
    QToolButton {{
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        border-radius: {BUTTON_RADIUS}px;
        {toolbar_padding(right=BUTTON_PAD_H_TIGHT)}
    }}{control_ground(BG_BUTTON, "QToolButton")}
    QToolButton:pressed {{
        background-color: {as_hex(BLUE)};
    }}
    QToolButton:disabled {{
        background-color: {as_hex(BG_SECONDARY)};
        color: {as_hex(TEXT_MUTED)};
    }}"""


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


def family_stylesheet() -> str:
    """Every rule above, for an app that dresses itself whole.

    An app's own rules go after it in the same sheet, or on the window: a
    later rule of equal specificity wins, and an id selector out-specifies
    every rule here, so a `QPushButton#generate` keeps its blue.
    """
    return (f"{ground_rules()}\n{tooltip_rules()}\n{menu_rules()}\n{button_rules()}"
            f"\n{icon_button_rules()}\n{item_view_rules()}")
