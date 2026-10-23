from __future__ import annotations

import html
from collections.abc import Collection, Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel

from shared_ui.colors import BLUE_LIGHT

_LINK_STYLE = f"color: {BLUE_LIGHT.name()}; text-decoration: none;"


class FolderPath(QLabel):
    step_clicked = pyqtSignal(int)

    def __init__(self, separator: str, parent=None):
        super().__init__(parent)
        self._separator = separator
        self._plain = ""
        self.setTextFormat(Qt.TextFormat.RichText)
        self.linkActivated.connect(lambda step: self.step_clicked.emit(int(step)))

    def set_path(self, steps: Sequence[str], *, linked: Collection[int] | None = None,
                 lead: str = "") -> None:
        if linked is None:
            linked = range(len(steps) - 1)
        self._plain = lead + self._separator.join(steps)
        drawn = [_link(step, name) if step in linked else html.escape(name)
                 for step, name in enumerate(steps)]
        self.setText(f'<span style="white-space: pre-wrap;">{html.escape(lead)}'
                     f'{html.escape(self._separator).join(drawn)}</span>')

    def plain_text(self) -> str:
        return self._plain


def _link(step: int, name: str) -> str:
    return f'<a href="{step}" style="{_LINK_STYLE}">{html.escape(name)}</a>'
