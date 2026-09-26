"""The dialog the family shows when an app has to stop and say something."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
)

from shared_ui.colors import (
    BG_BUTTON,
    BG_KEYCAP,
    BG_TERTIARY,
    BORDER_SUBTLE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    family_palette,
)
from shared_ui.fonts import SIZE_BODY, make_font
from shared_ui.spacing import GAP_DIALOG, GAP_MEDIUM, MARGIN_DIALOG

# The mark beside the message, in pixels square.  Windows' own message dialogs
# draw theirs at this size.
MARK_SIZE = 32

# The band the message column lives in.  Below the floor a wrapping label
# picks a column narrow enough to break a sentence that already fitted; above
# the ceiling a stage failure's list of file paths lays out on one line.
MESSAGE_WIDTH_MIN = 340
MESSAGE_WIDTH_MAX = 480

DISMISSED = QDialog.DialogCode.Accepted.value + 1


class _GuiThreadCall(QObject):
    """Runs work on the GUI thread, blocking the thread that asked for it.

    Qt builds widgets on the GUI thread or not at all, and several callers here
    are background workers: evolver's pipeline stages report a failure from the
    thread the pipeline runs on.  The slot is decorated because PyQt routes an
    undecorated Python callable through a proxy that stays put in the
    connecting thread -- which delivers the work back to the very thread this
    exists to leave.
    """

    _requested = pyqtSignal(object)

    def __init__(self, gui_thread: QThread) -> None:
        super().__init__()
        self._requested.connect(self._run)
        self.moveToThread(gui_thread)

    @pyqtSlot(object)
    def _run(self, work: Callable[[], None]) -> None:
        work()

    def call[T](self, work: Callable[[], T]) -> T:
        done = threading.Event()
        outcome: list[T] = []
        failure: list[BaseException] = []

        def run_and_release() -> None:
            try:
                outcome.append(work())
            except BaseException as exc:
                failure.append(exc)
            finally:
                self.deleteLater()
                done.set()

        self._requested.emit(run_and_release)
        done.wait()
        if failure:
            raise failure[0]
        return outcome[0]


class Level(Enum):
    """How bad the news is, in the mark the dialog draws beside it."""

    ERROR = QStyle.StandardPixmap.SP_MessageBoxCritical
    WARNING = QStyle.StandardPixmap.SP_MessageBoxWarning
    INFO = QStyle.StandardPixmap.SP_MessageBoxInformation


@dataclass(frozen=True)
class Link:
    text: str
    target: Path


def _link_line(link: Link) -> QLabel:
    url = QUrl.fromLocalFile(str(link.target)).toString(QUrl.ComponentFormattingOption.FullyEncoded)
    line = QLabel(f'<a href="{html.escape(url)}">{html.escape(link.text)}</a>')
    line.setTextFormat(Qt.TextFormat.RichText)
    line.setTextInteractionFlags(
        Qt.TextInteractionFlag.LinksAccessibleByMouse
        | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
    )
    line.linkActivated.connect(lambda href: QDesktopServices.openUrl(QUrl(href)))
    line.setFont(make_font(size=SIZE_BODY))
    line.setWordWrap(True)
    return line


def _button(text: str, on_click: Callable[[], None]) -> QPushButton:
    button = QPushButton(text)
    button.setFont(make_font(size=SIZE_BODY))
    button.clicked.connect(on_click)
    return button


class AlertDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        *,
        level: Level = Level.ERROR,
        icon: Path | None = None,
        button_text: str = "OK",
        links: Sequence[Link] = (),
        dismissible: bool = False,
    ) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )
        if icon is not None:
            self.setWindowIcon(QIcon(str(icon)))
        self.setPalette(family_palette(self.palette()))
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_TERTIARY.name()}; }}
            QLabel {{ color: {TEXT_SECONDARY.name()}; }}
            QPushButton {{
                color: {TEXT_PRIMARY.name()};
                background: {BG_BUTTON.name()};
                border: 1px solid {BORDER_SUBTLE.name()};
                padding: 4px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{ background: {BG_KEYCAP.name()}; }}
            QPushButton:pressed {{ background: {BG_TERTIARY.name()}; }}
        """)
        mark = QLabel()
        mark.setPixmap(self.style().standardIcon(level.value).pixmap(MARK_SIZE, MARK_SIZE))
        mark.setAlignment(Qt.AlignmentFlag.AlignTop)

        body = QLabel(message)
        body.setFont(make_font(size=SIZE_BODY))
        body.setWordWrap(True)
        body.setMinimumWidth(MESSAGE_WIDTH_MIN)
        body.setMaximumWidth(MESSAGE_WIDTH_MAX)

        column = QVBoxLayout()
        column.setSpacing(GAP_MEDIUM)
        column.addWidget(body)
        for link in links:
            column.addWidget(_link_line(link))

        said = QHBoxLayout()
        said.setSpacing(GAP_DIALOG)
        said.addWidget(mark)
        said.addLayout(column, stretch=1)

        ok = _button(button_text, self.accept)
        ok.setDefault(True)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(ok)
        if dismissible:
            buttons.addWidget(_button("Dismiss", lambda: self.done(DISMISSED)))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            MARGIN_DIALOG, MARGIN_DIALOG, MARGIN_DIALOG, MARGIN_DIALOG
        )
        outer.setSpacing(GAP_DIALOG)
        outer.addLayout(said)
        outer.addLayout(buttons)


def show_alert(
    title: str,
    message: str,
    *,
    level: Level = Level.ERROR,
    icon: Path | None = None,
    button_text: str = "OK",
    links: Sequence[Link] = (),
    dismissible: bool = False,
) -> bool:
    """Block until the alert is closed, and say whether it was closed with Dismiss."""
    app = QApplication.instance() or QApplication([])

    def open_it() -> int:
        return AlertDialog(
            title, message, level=level, icon=icon, button_text=button_text,
            links=links, dismissible=dismissible,
        ).exec()

    on_gui_thread = QThread.currentThread() == app.thread()
    closed_with = open_it() if on_gui_thread else _GuiThreadCall(app.thread()).call(open_it)
    return closed_with == DISMISSED
