"""The family's alert dialog."""

from __future__ import annotations

import threading
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QMargins, QPoint, Qt, QThread, QTimer, QUrl
from PyQt6.QtGui import QPalette, QPixmap, QTextDocument
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QStyle

from shared_ui.alert import (
    MARK_SIZE,
    MESSAGE_WIDTH_MAX,
    MESSAGE_WIDTH_MIN,
    AlertDialog,
    Level,
    Link,
    show_alert,
)
from shared_ui.colors import (
    BG_BUTTON,
    BG_TERTIARY,
    BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from shared_ui.fonts import SIZE_BODY, make_font
from shared_ui.spacing import GAP_DIALOG, GAP_MEDIUM, MARGIN_DIALOG


def test_the_dialog_carries_the_title_and_the_message():
    dlg = AlertDialog("Example App", "The scene file could not be read.")

    assert dlg.windowTitle() == "Example App"
    assert "The scene file could not be read." in [
        label.text() for label in dlg.findChildren(QLabel)
    ]


def _click(line: QLabel) -> None:
    QTest.mouseClick(line, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     QPoint(4, line.height() // 2))


def test_a_link_under_the_message_opens_the_folder_it_names(tmp_path):
    folder = tmp_path / "scene one & two"
    dlg = AlertDialog("Example App", "The script matches no video.",
                      links=[Link("Open its folder", folder)])
    line, = [label for label in dlg.findChildren(QLabel) if "Open its folder" in label.text()]

    with patch("shared_ui.alert.QDesktopServices") as desktop:
        dlg.show()
        QTest.qWaitForWindowExposed(dlg)
        _click(line)
        dlg.close()

    desktop.openUrl.assert_called_once_with(QUrl.fromLocalFile(str(folder)))


def test_a_link_reads_as_written_even_where_it_looks_like_markup(tmp_path):
    written = "scene <one> & two.funscript"
    dlg = AlertDialog("Example App", "Nothing to do.", links=[Link(written, tmp_path)])

    line, = [label for label in dlg.findChildren(QLabel)
             if label.textFormat() == Qt.TextFormat.RichText]
    shown = QTextDocument()
    shown.setHtml(line.text())
    assert shown.toPlainText() == written


def test_a_long_link_wraps_in_the_message_column_rather_than_widening_the_dialog(tmp_path):
    long_name = " ".join(["a-fairly-long-file-name.funscript"] * 10)
    dlg = AlertDialog("Example App", "Nothing to do.", links=[Link(long_name, tmp_path)])

    assert dlg.sizeHint().width() <= 600


def test_a_link_wears_the_familys_blue_in_an_app_that_never_set_the_familys_palette(tmp_path):
    dlg = AlertDialog("Example App", "Nothing to do.", links=[Link("Open its folder", tmp_path)])

    line, = [label for label in dlg.findChildren(QLabel) if "Open its folder" in label.text()]
    assert line.palette().color(QPalette.ColorRole.Link) == BLUE


def test_the_links_sit_a_family_gap_under_the_message(tmp_path):
    dlg = AlertDialog("Example App", "Nothing to do.", links=[Link("Open its folder", tmp_path)])

    said = dlg.layout().itemAt(0).layout()
    column = said.itemAt(1).layout()
    assert column.spacing() == GAP_MEDIUM


def test_a_link_is_set_in_the_body_font_the_message_wears(tmp_path):
    dlg = AlertDialog("Example App", "Nothing to do.",
                      links=[Link("Open its folder", tmp_path)])

    line, = [label for label in dlg.findChildren(QLabel) if "Open its folder" in label.text()]
    assert line.font() == make_font(size=SIZE_BODY)


def test_the_dialog_wears_the_familys_ground_and_text_colors():
    dlg = AlertDialog("Example App", "The scene file could not be read.")

    style = dlg.styleSheet()
    assert BG_TERTIARY.name() in style
    assert TEXT_SECONDARY.name() in style
    assert TEXT_PRIMARY.name() in style
    assert BG_BUTTON.name() in style


def test_one_button_dismisses_the_dialog_and_says_what_the_caller_asked():
    dlg = AlertDialog("Example App", "Nothing to do.", button_text="Got it")

    button, = dlg.findChildren(QPushButton)
    assert button.text() == "Got it"

    button.click()
    assert dlg.result() == QDialog.DialogCode.Accepted


def test_the_button_says_ok_when_the_caller_does_not_care():
    dlg = AlertDialog("Example App", "Nothing to do.")

    button, = dlg.findChildren(QPushButton)
    assert button.text() == "OK"


def test_the_message_and_the_button_are_set_in_the_familys_body_font():
    dlg = AlertDialog("Example App", "Nothing to do.")

    button, = dlg.findChildren(QPushButton)
    message, = [lbl for lbl in dlg.findChildren(QLabel) if lbl.text()]

    assert message.font() == make_font(size=SIZE_BODY)
    assert button.font() == make_font(size=SIZE_BODY)


def test_a_long_message_wraps_rather_than_stretching_off_the_screen():
    """Evolver's stage failures list up to thirty file paths at a time, and a
    label with nothing holding it back lays every one of them out on one line."""
    dlg = AlertDialog("Example App", " ".join(["a-fairly-long-file-name.mp4"] * 40))

    assert dlg.sizeHint().width() <= 600


def test_the_message_column_has_a_floor_as_well_as_a_ceiling():
    """The ceiling is what the wrapping test above proves.  The floor is the
    other half: a wrapping label with nothing under it picks a column narrow
    enough to break a sentence that already fitted -- the broker's two-line
    idle notice came out over three lines at 260 pixels wide."""
    dlg = AlertDialog("Example App", "Nothing to do.")

    body, = [lbl for lbl in dlg.findChildren(QLabel) if lbl.text()]
    assert body.minimumWidth() == MESSAGE_WIDTH_MIN
    assert body.maximumWidth() == MESSAGE_WIDTH_MAX


@pytest.mark.parametrize(
    "level, standard",
    [
        (Level.ERROR, QStyle.StandardPixmap.SP_MessageBoxCritical),
        (Level.WARNING, QStyle.StandardPixmap.SP_MessageBoxWarning),
        (Level.INFO, QStyle.StandardPixmap.SP_MessageBoxInformation),
    ],
)
def test_the_level_picks_the_mark_beside_the_message(level, standard):
    dlg = AlertDialog("Example App", "Nothing to do.", level=level)

    mark, = [lbl for lbl in dlg.findChildren(QLabel) if not lbl.text()]
    expected = dlg.style().standardIcon(standard).pixmap(MARK_SIZE, MARK_SIZE)
    assert mark.pixmap().toImage() == expected.toImage()


def test_the_dialog_wears_the_apps_own_icon(tmp_path):
    """Windows takes a dialog's taskbar button from its window icon, so without
    one the alert appears under the python interpreter's."""
    icon = tmp_path / "app.png"
    drawn = QPixmap(16, 16)
    drawn.fill(BLUE)
    drawn.save(str(icon))

    dlg = AlertDialog("Example App", "Nothing to do.", icon=icon)

    assert not dlg.windowIcon().isNull()


def test_the_alert_opens_in_front_of_whatever_the_user_is_looking_at():
    """Several of these apps are launched hidden from a shortcut, so they have
    no claim on the foreground; an alert that opens under the window in front
    is indistinguishable from having crashed silently."""
    dlg = AlertDialog("Example App", "Nothing to do.")

    assert dlg.windowFlags() & Qt.WindowType.WindowStaysOnTopHint


def test_show_alert_opens_the_dialog_the_caller_described(tmp_path):
    icon = tmp_path / "app.png"
    links = [Link("Open its folder", tmp_path)]
    with patch("shared_ui.alert.AlertDialog") as dialog:
        show_alert(
            "Example App",
            "Nothing to do.",
            level=Level.INFO,
            icon=icon,
            button_text="Got it",
            links=links,
        )

    dialog.assert_called_once_with(
        "Example App", "Nothing to do.", level=Level.INFO, icon=icon, button_text="Got it",
        links=links,
    )
    dialog.return_value.exec.assert_called_once_with()


def test_show_alert_builds_a_qapplication_when_the_process_has_none():
    """Several callers are dying processes and command-line tools that never
    built one -- the alert is the only Qt they will ever put on the screen."""
    with (
        patch("shared_ui.alert.AlertDialog"),
        patch("shared_ui.alert.QApplication") as application,
    ):
        application.instance.return_value = None
        application.return_value.thread.return_value = QThread.currentThread()
        show_alert("Example App", "Nothing to do.")

    application.assert_called_once_with([])


def test_an_alert_raised_off_the_gui_thread_still_opens_on_it(qapp):
    """Evolver's pipeline stages say what went wrong from a worker thread, and
    Qt builds widgets on the GUI thread or not at all."""
    opened_on = []
    finished = threading.Event()

    class RecordingDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def exec(self):
            opened_on.append(threading.get_ident())

    def raise_it():
        try:
            show_alert("Example App", "Nothing to do.")
        finally:
            finished.set()

    worker = threading.Thread(target=raise_it)
    watchdog = QTimer()
    watchdog.setInterval(20)
    watchdog.timeout.connect(lambda: finished.is_set() and qapp.quit())

    with patch("shared_ui.alert.AlertDialog", RecordingDialog):
        QTimer.singleShot(0, worker.start)
        QTimer.singleShot(10_000, qapp.quit)
        watchdog.start()
        qapp.exec()
        watchdog.stop()
        worker.join(timeout=10)

    assert not worker.is_alive()
    assert opened_on == [threading.get_ident()]


def test_the_dialog_is_spaced_by_the_familys_dialog_tokens():
    """A notice is a window of its own with nothing else in it; at the density
    of a packed toolbar it reads as cramped."""
    dlg = AlertDialog("Example App", "Nothing to do.")

    margins = dlg.layout().contentsMargins()
    assert margins == QMargins(
        MARGIN_DIALOG, MARGIN_DIALOG, MARGIN_DIALOG, MARGIN_DIALOG)
    assert dlg.layout().spacing() == GAP_DIALOG
