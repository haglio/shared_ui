"""The strip Ctrl+F opens over a window's text: a query field, a match count, the
two steps between matches, and a close."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QToolButton,
    QWidget,
)

from shared_ui.chrome import field_rules, tool_button_rules
from shared_ui.icons import glyph_icon
from shared_ui.palette import TEXT_MUTED, as_hex
from shared_ui.spacing import GAP_MEDIUM, GAP_SMALL
from shared_ui.text_find import TextFind

__all__ = ["FindBar"]


def _look() -> str:
    return f"""{field_rules()}{tool_button_rules()}
    QToolButton {{
        padding: {GAP_SMALL}px;
    }}
    QLabel#findCount {{
        color: {as_hex(TEXT_MUTED)};
    }}"""


class _QueryField(QLineEdit):
    pressed = pyqtSignal()

    def mousePressEvent(self, event):
        self.pressed.emit()
        super().mousePressEvent(event)


class FindBar(QWidget):
    typing_invited = pyqtSignal()

    def __init__(self, label: str, placeholder: str, *, dismiss_key: str = "",
                 reveal: Callable[[QTextEdit], None] | None = None, parent=None):
        super().__init__(parent)
        self._find = TextFind(reveal)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, GAP_SMALL, 0, 0)
        row.setSpacing(GAP_MEDIUM)
        row.addWidget(QLabel(label))
        self._query = _QueryField()
        self._query.pressed.connect(self.typing_invited)
        self._query.setPlaceholderText(placeholder)
        self._query.setClearButtonEnabled(True)
        self._query.textChanged.connect(self._search)
        self._query.returnPressed.connect(self._on_return)
        row.addWidget(self._query, 1)
        self._count = QLabel("")
        self._count.setObjectName("findCount")
        row.addWidget(self._count)
        self._prev_btn = self._step_button("chevron_up", "Previous match (Shift+Enter)", -1)
        self._next_btn = self._step_button("chevron_down", "Next match (Enter)", 1)
        row.addWidget(self._prev_btn)
        row.addWidget(self._next_btn)
        close = QToolButton()
        close.setIcon(glyph_icon("cross"))
        close.setToolTip(f"Close the find ({dismiss_key})" if dismiss_key else "Close the find")
        close.clicked.connect(self.close_find)
        row.addWidget(close)
        self.setStyleSheet(_look())
        self.hide()

    def _step_button(self, mark: str, tooltip: str, delta: int) -> QToolButton:
        button = QToolButton()
        button.setIcon(glyph_icon(mark))
        button.setToolTip(tooltip)
        button.clicked.connect(lambda _checked=False, d=delta: self._step(d))
        button.setEnabled(False)
        return button

    def _on_return(self):
        shift = QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier
        self._step(-1 if shift else 1)

    def open_find(self, fields):
        self._find.set_fields(fields)
        self.show()
        self._query.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._query.selectAll()
        self._search(self._query.text())
        self.typing_invited.emit()

    def retarget(self, fields):
        if not self.isVisible():
            return
        if not fields:
            self.close_find()
            return
        self._find.set_fields(fields)
        self._search(self._query.text())

    def refresh(self):
        if not self.isVisible():
            return
        self._find.refresh()
        self._show_count()

    def close_find(self):
        self._find.clear()
        self.hide()

    def _search(self, text: str):
        self._find.search(text)
        self._show_count()

    def _step(self, delta: int):
        self._find.step(delta)
        self._show_count()

    def _show_count(self):
        total = self._find.count()
        if not self._query.text():
            self._count.setText("")
        elif total:
            self._count.setText(f"{self._find.position()} of {total}")
        else:
            self._count.setText("No matches")
        for button in (self._prev_btn, self._next_btn):
            button.setEnabled(total > 1)
