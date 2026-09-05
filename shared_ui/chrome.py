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
    as_hex,
)
from shared_ui.spacing import BUTTON_PAD_H, BUTTON_PAD_V, BUTTON_RADIUS


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
    artifact boxes around itself.
    """
    return f"""
    QToolTip {{
        background-color: {as_hex(BG_TERTIARY)};
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        padding: 4px 6px;
    }}"""


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
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 6px 20px;
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
    QMenu::separator {{
        height: 1px;
        background-color: {as_hex(BORDER_SUBTLE)};
        margin: 4px 0;
    }}"""


def button_rules() -> str:
    """A push button at rest, hovered, on, pressed and disabled.

    A control that is ON sits on a lighter ground than one at rest -- the rule
    the tokens state -- and a press flashes the blue that means more than
    "engaged".
    """
    return f"""
    QPushButton {{
        background-color: {as_hex(BG_BUTTON)};
        color: {as_hex(TEXT_PRIMARY)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
        border-radius: {BUTTON_RADIUS}px;
        padding: {BUTTON_PAD_V}px {BUTTON_PAD_H}px;
    }}
    QPushButton:hover {{
        background-color: {as_hex(BG_TERTIARY)};
    }}
    QPushButton:checked {{
        background-color: {as_hex(BG_BUTTON_ACTIVE)};
    }}
    QPushButton:pressed {{
        background-color: {as_hex(BLUE)};
    }}
    QPushButton:disabled {{
        background-color: {as_hex(BG_SECONDARY)};
        color: {as_hex(TEXT_MUTED)};
        border: 1px solid {as_hex(BORDER_SUBTLE)};
    }}"""


def family_stylesheet() -> str:
    """Every rule above, for an app that dresses itself whole.

    An app's own rules go after it in the same sheet, or on the window: a
    later rule of equal specificity wins, and an id selector out-specifies
    every rule here, so a `QPushButton#generate` keeps its blue.
    """
    return f"{ground_rules()}\n{tooltip_rules()}\n{menu_rules()}\n{button_rules()}"
