"""The family's loading screen as a Qt window, for the apps that boot in Qt:
the panel alone, borderless, under a caption of the app's choosing."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout

from shared_ui.loading_panel import LoadingPanel, icon_image, render
from shared_ui.palette import LOADING_ACCENT, PREVIEW_INK
from shared_ui.preview import Preview
from shared_ui.preview_icon_pil import in_preview_ink

CANCELING = "Canceling..."


class LoadingWindow(QDialog):
    canceled = pyqtSignal()

    def __init__(
        self,
        *,
        caption: str,
        wordmark: str,
        icon: Path | None,
        preview: Preview | None,
        steps: Sequence[str | tuple[str, float]],
        cancel_hint: str = "",
    ) -> None:
        super().__init__()
        self.setWindowTitle(caption)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self._done_before = _work_done_before_each(steps)
        self._canceling = False
        self._panel = LoadingPanel(
            wordmark=wordmark,
            status=next(iter(self._done_before)),
            fraction=0.0,
            hint=cancel_hint,
            ink=LOADING_ACCENT if preview is None else PREVIEW_INK,
            icon=_inked(icon_image(icon), preview),
        )
        self._picture = QLabel(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._picture)
        self._show_the_panel()

    @property
    def panel(self) -> LoadingPanel:
        return self._panel

    def say(self, step: str) -> None:
        if self._canceling:
            return
        self._panel = replace(
            self._panel, status=step,
            fraction=self._done_before.get(step, self._panel.fraction),
        )
        self._show_the_panel()

    def reject(self) -> None:
        self._canceling = True
        self._panel = replace(self._panel, status=CANCELING, hint="")
        self._show_the_panel()
        self.canceled.emit()

    def _show_the_panel(self) -> None:
        image = render(self._panel)
        qimage = QImage(
            image.tobytes(), image.width, image.height, 3 * image.width,
            QImage.Format.Format_RGB888,
        )
        self._picture.setPixmap(QPixmap.fromImage(qimage))
        self.setFixedSize(image.width, image.height)


class LoadingCanceled(BaseException):
    """He closed the loading window, or pressed Esc on it, before the app was up."""


class Loading:
    """An app's start walked through its loading window, or through the log
    where the start has no window of its own."""

    def __init__(self, app: QApplication, logger: logging.Logger,
                 window: LoadingWindow | None) -> None:
        self._app = app
        self._logger = logger
        self._window = window
        self._canceled = False
        if window is not None:
            window.canceled.connect(self._cancel)

    def _cancel(self) -> None:
        self._canceled = True

    def say(self, step: str) -> None:
        if self._window is None:
            self._logger.info("Boot: %s", step)
        else:
            self._window.say(step)
        self.stop_if_canceled()

    def stop_if_canceled(self) -> None:
        self._app.processEvents()
        if self._canceled:
            raise LoadingCanceled

    def done(self) -> None:
        if self._window is not None:
            self._window.accept()
            self._app.processEvents()


def _inked(icon: Image.Image | None, preview: Preview | None) -> Image.Image | None:
    return icon if icon is None or preview is None else in_preview_ink(icon)


def _work_done_before_each(steps: Sequence[str | tuple[str, float]]) -> dict[str, float]:
    weighted = [(step, 1.0) if isinstance(step, str) else step for step in steps]
    total = sum(weight for _step, weight in weighted)
    done, before = 0.0, {}
    for step, weight in weighted:
        before[step] = done / total
        done += weight
    return before
