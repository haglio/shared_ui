from __future__ import annotations

import html
import sys
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app_support import copyable_alert
from PySide6.QtCore import QObject, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from shared_ui import palette
from shared_ui.chrome import button_rules
from shared_ui.colors import (
    BG_TERTIARY,
    TEXT_SECONDARY,
    family_palette,
)
from shared_ui.fonts import SIZE_BODY, make_font
from shared_ui.gui_thread_collection import the_application
from shared_ui.icons import icon_pixmap
from shared_ui.spacing import GAP_DIALOG, GAP_MEDIUM, MARGIN_DIALOG

# Windows' own message dialogs draw their icon at this size.
ICON_SIZE = 32

MESSAGE_WIDTH_MIN = 340
MESSAGE_WIDTH_MAX = 480

DISMISSED = QDialog.DialogCode.Accepted.value + 1

WORK_ON_THIS = "Work on this"
WORK_ON_THIS_TIP = "Opens a new session in Claude Desktop with what to look into typed in, ready to send"



class _GuiThreadCall(QObject):
    """Qt builds widgets on the GUI thread or not at all. The slot is decorated so the call
    is queued to the thread this object was moved to, whichever thread asks."""

    _requested = Signal(object)

    def __init__(self, gui_thread: QThread) -> None:
        super().__init__()
        self._requested.connect(self._run)
        self.moveToThread(gui_thread)

    @Slot(object)
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
    ERROR = ("error", palette.RED)
    WARNING = ("warning", palette.YELLOW)
    INFO = ("info", palette.BLUE)

    @property
    def icon(self) -> str:
        return self.value[0]

    @property
    def ink(self) -> palette.Rgb:
        return self.value[1]


def icon_pixmap_for(level: Level, size: int) -> QPixmap:
    return icon_pixmap(level.icon, size, QColor(*level.ink))


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


@dataclass(frozen=True)
class _AlertLook:
    level: Level = Level.ERROR
    icon: Path | QIcon | None = None
    button_text: str = "OK"
    links: Sequence[Link] = ()
    dismissible: bool = False
    work_on_this: str | None = None


def _claim_a_taskbar_identity_unless_the_app_has(app: str) -> None:
    if sys.platform != "win32":
        return
    from app_support import win32  # noqa: PLC0415  (winreg, which it imports, is Windows' own)

    try:
        if win32.claimed_app_user_model_id() is None:
            win32.set_app_user_model_id(copyable_alert.taskbar_identity(app))
    except OSError:
        pass


class AlertDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        **look,
    ) -> None:
        super().__init__()
        chosen = _AlertLook(**look)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )
        if chosen.icon is not None:
            given = chosen.icon
            self.setWindowIcon(given if isinstance(given, QIcon) else QIcon(str(given)))
            _claim_a_taskbar_identity_unless_the_app_has(title if isinstance(given, QIcon) else str(given))
        self.setPalette(family_palette(self.palette()))
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_TERTIARY.name()}; }}
            QLabel {{ color: {TEXT_SECONDARY.name()}; background: transparent; }}
            {button_rules()}
        """)
        icon = QLabel()
        icon.setPixmap(icon_pixmap_for(chosen.level, ICON_SIZE))
        icon.setAlignment(Qt.AlignmentFlag.AlignTop)

        body = QLabel(message)
        body.setFont(make_font(size=SIZE_BODY))
        body.setWordWrap(True)
        body.setMinimumWidth(MESSAGE_WIDTH_MIN)
        body.setMaximumWidth(MESSAGE_WIDTH_MAX)

        column = QVBoxLayout()
        column.setSpacing(GAP_MEDIUM)
        column.addWidget(body)
        for link in chosen.links:
            column.addWidget(_link_line(link))

        said = QHBoxLayout()
        said.setSpacing(GAP_DIALOG)
        said.addWidget(icon)
        said.addLayout(column, stretch=1)

        ok = _button(chosen.button_text, self.accept)
        ok.setDefault(True)

        buttons = QHBoxLayout()
        buttons.addStretch()
        if chosen.level is Level.ERROR:
            buttons.addWidget(self._offer_to_copy(title, message))
        if chosen.work_on_this is not None:
            self._work_on_this = chosen.work_on_this
            work_on_this = _button(WORK_ON_THIS, self._open_and_close)
            work_on_this.setToolTip(WORK_ON_THIS_TIP)
            buttons.addWidget(work_on_this)
        buttons.addWidget(ok)
        if chosen.dismissible:
            buttons.addWidget(_button("Dismiss", lambda: self.done(DISMISSED)))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            MARGIN_DIALOG, MARGIN_DIALOG, MARGIN_DIALOG, MARGIN_DIALOG
        )
        outer.setSpacing(GAP_DIALOG)
        outer.addLayout(said)
        outer.addLayout(buttons)
        if chosen.level is Level.ERROR:
            self._keep_copy_as_wide_as_copied()

    def _offer_to_copy(self, title: str, message: str) -> QPushButton:
        self._said = copyable_alert.said(title, message)
        self._copy = _button(copyable_alert.COPY, self._copy_and_say_so)
        self._copy.setToolTip(copyable_alert.COPY_TIP)
        self._back_to_copy = QTimer(self, singleShot=True, interval=copyable_alert.COPIED_SHOWN_MS)
        self._back_to_copy.timeout.connect(self._offer_to_copy_again)
        return self._copy

    def _keep_copy_as_wide_as_copied(self) -> None:
        self._copy.ensurePolished()
        self._copy.setMinimumWidth(self._copy.sizeHint().width())

    def _copy_and_say_so(self) -> None:
        QApplication.clipboard().setText(self._said)
        self._copy.setText(copyable_alert.COPIED)
        self._back_to_copy.start()

    def _offer_to_copy_again(self) -> None:
        self._copy.setText(copyable_alert.COPY)

    def _open_and_close(self) -> None:
        QDesktopServices.openUrl(QUrl(self._work_on_this))
        self.accept()


def show_alert(title: str, message: str, **look) -> bool:
    app = the_application(QApplication, [])

    def open_it() -> int:
        return AlertDialog(title, message, **look).exec()

    on_gui_thread = QThread.currentThread() == app.thread()
    closed_with = open_it() if on_gui_thread else _GuiThreadCall(app.thread()).call(open_it)
    return closed_with == DISMISSED


def show_error(title: str, message: str, *, icon: Path | QIcon | None = None, button_text: str = "OK",
               links: Sequence[Link] = (), dismissible: bool = False, work_on_this: str | None = None) -> bool:
    return show_alert(title, message, level=Level.ERROR, icon=icon, button_text=button_text, links=links,
                      dismissible=dismissible, work_on_this=work_on_this)


def show_warning(title: str, message: str, *, icon: Path | QIcon | None = None, button_text: str = "OK",
                 links: Sequence[Link] = (), dismissible: bool = False) -> bool:
    return show_alert(title, message, level=Level.WARNING, icon=icon, button_text=button_text, links=links,
                      dismissible=dismissible)
