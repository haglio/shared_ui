"""A window put in front with the keyboard when it opens, whoever started its
process."""

from __future__ import annotations

from app_support.win32 import force_foreground_window
from PyQt6.QtGui import QGuiApplication


def bring_to_front(window) -> None:
    window.raise_()
    window.activateWindow()
    if _drawn_by_windows():
        force_foreground_window(int(window.winId()))


def _drawn_by_windows() -> bool:
    return QGuiApplication.platformName() == "windows"
