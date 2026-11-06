from __future__ import annotations

import html
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from PyQt6.QtCore import QEvent, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import QDialog, QTextBrowser, QToolTip, QVBoxLayout, QWidget

from shared_ui.find_bar import FindBar
from shared_ui.palette import (
    BG_KEYCAP,
    BG_PRIMARY,
    BG_SECONDARY,
    BLUE,
    BORDER_SUBTLE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    as_hex,
)
from shared_ui.spacing import GAP_DIALOG, GAP_MEDIUM, GAP_SMALL, HAIRLINE, MARGIN_STANDARD
from shared_ui.type_scale import FONT_UI, SIZE_BODY, SIZE_HEADING

REFERENCE_WINDOW_TITLE = "Hotkeys & Voice Commands Reference"
HOTKEY_HEADER = "Hotkey"
CONTROLLER_HEADER = "VR Controller"
VOICE_HEADER = "Voice command"

VOICE_COLUMN_PX = 220
CONTROLLER_COLUMN_PX = 120
HOTKEY_BLOCK_PX = 300
ACTION_COLUMN_AT_LEAST_PX = 150


@dataclass(frozen=True)
class CommandRef:
    description: str
    voice: tuple[str, ...]
    commands: tuple[str, ...] = ()
    key_columns: tuple[tuple[str, ...], ...] = ()
    detail: str = ""
    controller: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReferenceGroup:
    title: str
    rows: tuple[CommandRef, ...]

    @property
    def has_keys(self) -> bool:
        return any(key for row in self.rows for column in row.key_columns for key in column)

    @property
    def has_controller(self) -> bool:
        return any(row.controller for row in self.rows)


@dataclass(frozen=True)
class ReferenceSection:
    title: str
    groups: tuple[ReferenceGroup, ...]
    key_headers: tuple[str, ...] = (HOTKEY_HEADER,)
    note: str = ""

    @property
    def rows(self) -> tuple[CommandRef, ...]:
        return tuple(row for group in self.groups for row in group.rows)

    @property
    def has_keys(self) -> bool:
        return any(group.has_keys for group in self.groups)

    @property
    def has_controller(self) -> bool:
        return any(group.has_controller for group in self.groups)


def _controller_column_px(sections: tuple[ReferenceSection, ...]) -> int:
    return CONTROLLER_COLUMN_PX if any(section.has_controller for section in sections) else 0


def narrowest_page_px(sections: tuple[ReferenceSection, ...]) -> int:
    return (HOTKEY_BLOCK_PX + _controller_column_px(sections) + VOICE_COLUMN_PX
            + ACTION_COLUMN_AT_LEAST_PX)


def _tooltips(sections: tuple[ReferenceSection, ...]) -> tuple[str, ...]:
    return tuple(
        text
        for section in sections
        for text in (section.note, *(row.detail for row in section.rows))
        if text
    )


def reference_details(sections: tuple[ReferenceSection, ...]) -> dict[str, str]:
    return {f"detail:{index}": text for index, text in enumerate(_tooltips(sections))}


_BG = as_hex(BG_PRIMARY)
_HEADER_BG = as_hex(BG_SECONDARY)
_TEXT = as_hex(TEXT_PRIMARY)
_MUTED = as_hex(TEXT_MUTED)
_ACCENT = as_hex(BLUE)
_KEYCAP_BG = as_hex(BG_KEYCAP)
BORDER = as_hex(BORDER_SUBTLE)

_CELL_PADDING = f"padding:{GAP_SMALL}px {MARGIN_STANDARD}px"


def _keycap(label: str) -> str:
    return (
        f'<span style="background:{_KEYCAP_BG};border:{HAIRLINE}px solid {BORDER};'
        f'padding:0 {GAP_SMALL}px;color:{_TEXT};font-family:\'{FONT_UI}\'">'
        f"{html.escape(label)}</span>"
    )


def _spanning(columns: int) -> str:
    return f' colspan="{columns}"' if columns > 1 else ""


def _cell(content: str, width: int, *, span: str = "") -> str:
    return (f'<td width="{width}" valign="top"{span} style="{_CELL_PADDING};color:{_TEXT}">'
            f"{content}</td>")


def _head(label: str, width: int, *, span: str = "", underlined: bool = False,
          align: str = "center") -> str:
    rule = f";border-bottom:{HAIRLINE}px solid {BORDER}" if underlined else ""
    text = f'<b style="color:{_MUTED}">{html.escape(label)}</b>' if label else ""
    return (f'<td width="{width}" align="{align}" valign="middle"{span} style="{_CELL_PADDING}{rule}">'
            f"{text}</td>")


def _anchored(text: str, anchor: str, *, color: str) -> str:
    return f'<a href="{anchor}" style="color:{color};text-decoration:none">{html.escape(text)}</a>'


def _shared_out(total: int, parts: int) -> tuple[int, ...]:
    if not parts:
        return ()
    each = total // parts
    return (*(each,) * (parts - 1), total - each * (parts - 1))


@dataclass(frozen=True)
class _Columns:
    width: int
    keys: tuple[int, ...]
    has_controller: bool
    controller: int
    voice: int = VOICE_COLUMN_PX

    @classmethod
    def laid_out(cls, width: int, group: ReferenceGroup, section: ReferenceSection,
                 *, controller: int) -> _Columns:
        keys = _shared_out(HOTKEY_BLOCK_PX, len(section.key_headers) if group.has_keys else 0)
        return cls(width, keys, group.has_controller, controller)

    @property
    def action(self) -> int:
        return (self.width - self.controller - self.voice
                - (HOTKEY_BLOCK_PX if self.keys else 0))

    @property
    def action_span(self) -> str:
        return _spanning(1 + (not self.keys))


def _no_input() -> str:
    return f'<span style="color:{_MUTED}">—</span>'


def _header_rows(section: ReferenceSection, columns: _Columns) -> str:
    row = f'<tr style="background:{_HEADER_BG}">'
    forked = len(columns.keys) > 1
    rows = ' rowspan="2"' if forked else ""
    action = _head("Action", columns.action, span=columns.action_span + rows, align="left")
    controller = (_head(CONTROLLER_HEADER if columns.has_controller else "", columns.controller,
                        span=rows) if columns.controller else "")
    tail = controller + _head(VOICE_HEADER, columns.voice, span=rows) + "</tr>"
    if not columns.keys:
        return row + action + tail
    if not forked:
        return row + action + _head(HOTKEY_HEADER, columns.keys[0]) + tail
    return (
        row + action
        + _head(HOTKEY_HEADER, HOTKEY_BLOCK_PX, span=_spanning(len(columns.keys)), underlined=True)
        + tail
        + row + "".join(_head(header, width)
                        for header, width in zip(section.key_headers, columns.keys, strict=True))
        + "</tr>"
    )


def _input_cells(row: CommandRef, columns: _Columns) -> str:
    cells = [
        _cell(" ".join(_keycap(key) for key in column) or _no_input(), width)
        for column, width in zip(row.key_columns if columns.keys else (), columns.keys, strict=True)
    ]
    if not columns.controller:
        return "".join(cells)
    inputs = (html.escape(", ".join(row.controller)) or _no_input()) if columns.has_controller else ""
    return "".join(cells) + _cell(inputs, columns.controller)


def render_reference_html(sections: tuple[ReferenceSection, ...], width: int) -> str:
    parts: list[str] = [
        (f'<body style="background:{_BG};color:{_TEXT};'
         f'font-family:\'{FONT_UI}\';font-size:{SIZE_BODY}pt">'),
    ]
    anchors = iter(reference_details(sections))
    controller = _controller_column_px(sections)
    for section in sections:
        title = (_anchored(section.title, next(anchors), color=_ACCENT) if section.note
                 else html.escape(section.title))
        parts.append(f'<h3 style="color:{_ACCENT};font-size:{SIZE_HEADING}pt;'
                     f'margin:{GAP_DIALOG}px 0 {GAP_SMALL}px 0">{title}</h3>')
        for group in section.groups:
            if group.title:
                parts.append(
                    f'<h4 style="color:{_TEXT};margin:{GAP_MEDIUM}px 0 {GAP_SMALL}px 0">'
                    f"{html.escape(group.title)}</h4>"
                )
            columns = _Columns.laid_out(width, group, section, controller=controller)
            parts.append(f'<table width="{width}" cellspacing="0" cellpadding="0">')
            parts.append(_header_rows(section, columns))
            for row in group.rows:
                action = (_anchored(row.description, next(anchors), color=_TEXT) if row.detail
                          else html.escape(row.description))
                phrases = ", ".join(f'“{html.escape(p)}”' for p in row.voice) or _no_input()
                parts.append("<tr>" + _cell(action, columns.action, span=columns.action_span)
                             + _input_cells(row, columns) + _cell(phrases, columns.voice) + "</tr>")
            parts.append("</table>")
    parts.append("</body>")
    return "".join(parts)


class ReferenceBrowser(QTextBrowser):
    def __init__(self, sections: tuple[ReferenceSection, ...], parent: QWidget | None = None, *,
                 tooltip=QToolTip, on_rerendered: Callable[[], None] = lambda: None) -> None:
        super().__init__(parent)
        self._sections = sections
        self._show_tip, self._hide_tip = tooltip.showText, tooltip.hideText
        self._on_rerendered = on_rerendered
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._narrowest = narrowest_page_px(sections)
        self.setMinimumWidth(self._narrowest + self._width_around_the_page())
        self._detail_of = reference_details(sections).get
        self._page_width = 0
        self._render()

    def _width_around_the_page(self) -> int:
        return (2 * (self.frameWidth() + round(self.document().documentMargin()))
                + self.verticalScrollBar().sizeHint().width())

    def _render(self) -> None:
        page = max(self._narrowest,
                   self.viewport().width() - 2 * round(self.document().documentMargin()))
        if page == self._page_width:
            return
        self._page_width = page
        scrolled = self.verticalScrollBar().value()
        self.setHtml(render_reference_html(self._sections, page))
        self.verticalScrollBar().setValue(scrolled)
        self._on_rerendered()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render()

    def detail_at(self, viewport_pos) -> str:
        return self._detail_of(self.anchorAt(viewport_pos), "")

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            detail = self.detail_at(self.viewport().mapFromGlobal(event.globalPos()))
            if detail:
                self._show_tip(event.globalPos(), f"<p>{html.escape(detail)}</p>", self)
            else:
                self._hide_tip()
            return True
        return super().event(event)


REFERENCE_FIRST_SIZE = QSize(1000, 800)
ROOM_FOR_THE_FRAME_PX = 48


def reference_first_size(available: QSize, *, at_least_wide: int) -> QSize:
    return QSize(max(at_least_wide, min(REFERENCE_FIRST_SIZE.width(),
                                        available.width() - ROOM_FOR_THE_FRAME_PX)),
                 min(REFERENCE_FIRST_SIZE.height(), available.height() - ROOM_FOR_THE_FRAME_PX))


class ReferenceDialog(QDialog):
    typing_invited = pyqtSignal()

    def __init__(self, sections: tuple[ReferenceSection, ...], *, icon: QIcon,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(REFERENCE_WINDOW_TITLE)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowIcon(icon)
        find_bar = FindBar("Find:", "a key or a word…")
        find_bar.setContentsMargins(MARGIN_STANDARD, 0, MARGIN_STANDARD, MARGIN_STANDARD)
        find_bar.typing_invited.connect(self.typing_invited)
        self.browser = ReferenceBrowser(sections, self, on_rerendered=find_bar.refresh)
        self.open_find = partial(find_bar.open_find, [self.browser])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        layout.addWidget(find_bar)
        QShortcut(QKeySequence.StandardKey.Find, self).activated.connect(self.open_find)
        self.setMinimumWidth(self.browser.minimumWidth())
        screen = (QGuiApplication.primaryScreen() if parent is None else parent.screen())
        self.resize(reference_first_size(screen.availableGeometry().size(),
                                         at_least_wide=self.minimumWidth()))
