from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QLabel

from shared_ui.colors import dress_application


@pytest.fixture
def undone(qapp):
    sheet, look = qapp.styleSheet(), qapp.palette()
    yield qapp
    qapp.setStyleSheet(sheet)
    qapp.setPalette(look)
    for dresser in qapp.findChildren(QObject):
        if type(dresser).__module__.startswith("shared_ui.tooltip"):
            qapp.removeEventFilter(dresser)
            dresser.setParent(None)


def test_a_window_opened_in_a_dressed_app_shows_tooltips_while_another_window_is_active(undone):
    dress_application(undone)
    window = QLabel("logo")

    window.show()

    assert window.testAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
    window.close()
