from __future__ import annotations

import os
import subprocess
import sys

import pytest

from shared_ui.body_text import body_text_pixels

_QT_BODY_TEXT = ("from PySide6.QtGui import QFontInfo\n"
                 "from PySide6.QtWidgets import QApplication\n"
                 "app = QApplication([])\n"
                 "print(QFontInfo(app.font()).pixelSize())\n")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows sets the body text's size")
def test_body_text_is_the_size_qt_letters_an_apps_windows_in():
    qt = subprocess.run([sys.executable, "-c", _QT_BODY_TEXT], capture_output=True, text=True,
                        env={k: v for k, v in os.environ.items() if k != "QT_QPA_PLATFORM"},
                        check=True)

    assert body_text_pixels() == int(qt.stdout.split()[-1])
