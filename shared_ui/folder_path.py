from __future__ import annotations

import html
from collections.abc import Collection, Mapping, Sequence

from shared_ui.colors import BLUE_LIGHT, TEXT_PRIMARY
from shared_ui.icons import icon_then_text
from shared_ui.qt.QtCore import Qt, Signal
from shared_ui.qt.QtGui import QColor
from shared_ui.qt.QtWidgets import QLabel

_LINK_STYLE = f"color: {BLUE_LIGHT.name()}; text-decoration: none;"


class FolderPath(QLabel):
    step_clicked = Signal(int)

    def __init__(self, separator: str, parent=None):
        super().__init__(parent)
        self._separator = separator
        self._plain = ""
        self.setTextFormat(Qt.TextFormat.RichText)
        self.linkActivated.connect(lambda step: self.step_clicked.emit(int(step)))

    def set_path(self, steps: Sequence[str], *, linked: Collection[int] | None = None,
                 lead: str = "", icons: Mapping[int, str | tuple[str, QColor]] | None = None,
                 ) -> None:
        if linked is None:
            linked = range(len(steps) - 1)
        icons = icons or {}
        self._plain = lead + self._separator.join(steps)
        drawn = [self._drawn(step, name, step in linked, icons.get(step))
                 for step, name in enumerate(steps)]
        self.setText(f'<span style="white-space: pre-wrap;">{html.escape(lead)}'
                     f'{html.escape(self._separator).join(drawn)}</span>')

    def plain_text(self) -> str:
        return self._plain

    def _drawn(self, step: int, name: str, is_link: bool,
               icon: str | tuple[str, QColor] | None) -> str:
        if not icon:
            named = html.escape(name)
        else:
            icon_name, color = (icon, TEXT_PRIMARY) if isinstance(icon, str) else icon
            named = icon_then_text(icon_name, name, color=color, size=self.fontMetrics().height())
        return _link(step, named) if is_link else named


def _link(step: int, named: str) -> str:
    return f'<a href="{step}" style="{_LINK_STYLE}">{named}</a>'
