"""One query's matches across a window's text fields: found, painted, walked."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtGui import QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from shared_ui.colors import BG_PRIMARY, BLUE, TEXT_PRIMARY, YELLOW

__all__ = ["TextFind"]

_EVERY_MATCH = BLUE.darker(150)
_THE_CURRENT_MATCH = YELLOW


class TextFind:
    def __init__(self, reveal: Callable[[QTextEdit], None] | None = None):
        self._reveal_field = reveal
        self._fields: list = []
        self._matches: list[tuple] = []
        self._index = -1
        self._query = ""

    def set_fields(self, fields) -> int:
        self._paint([])
        self._fields = list(fields)
        return self._run(reset=True)

    def search(self, query: str) -> int:
        self._query = query
        total = self._run(reset=True)
        if self._matches:
            self._reveal()
        return total

    def refresh(self) -> int:
        return self._run(reset=False)

    def _run(self, *, reset: bool) -> int:
        previous = self._index
        self._matches = self._collect()
        if not self._matches:
            self._index = -1
        elif reset or previous < 0:
            self._index = 0
        else:
            self._index = min(previous, len(self._matches) - 1)
        self._paint(self._matches)
        return len(self._matches)

    def _collect(self) -> list[tuple]:
        query = self._query.lower()
        if not query:
            return []
        found = []
        for field in self._fields:
            text = field.toPlainText().lower()
            at = text.find(query)
            while at >= 0:
                found.append((field, at))
                at = text.find(query, at + len(query))
        return found

    def count(self) -> int:
        return len(self._matches)

    def position(self) -> int:
        return self._index + 1 if self._index >= 0 else 0

    def step(self, delta: int):
        if not self._matches:
            return
        self._index = (self._index + delta) % len(self._matches)
        self._paint(self._matches)
        self._reveal()

    def clear(self):
        self._query = ""
        self._matches = []
        self._index = -1
        self._paint([])
        self._fields = []

    def _reveal(self):
        field, at = self._matches[self._index]
        if self._reveal_field is not None:
            self._reveal_field(field)
        field.setTextCursor(self._cursor(field, at, select=False))
        field.ensureCursorVisible()

    def _paint(self, matches):
        for field in self._fields:
            field.setExtraSelections([
                self._selection(field, at, current=(i == self._index))
                for i, (owner, at) in enumerate(matches) if owner is field
            ])

    def _selection(self, field, at: int, *, current: bool):
        selection = QTextEdit.ExtraSelection()
        selection.cursor = self._cursor(field, at)
        style = QTextCharFormat()
        style.setBackground(_THE_CURRENT_MATCH if current else _EVERY_MATCH)
        style.setForeground(BG_PRIMARY if current else TEXT_PRIMARY)
        selection.format = style
        return selection

    def _cursor(self, field, at: int, *, select: bool = True) -> QTextCursor:
        cursor = QTextCursor(field.document())
        cursor.setPosition(at)
        if select:
            cursor.setPosition(at + len(self._query), QTextCursor.MoveMode.KeepAnchor)
        return cursor
