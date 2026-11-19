from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

_YES = QMessageBox.StandardButton.Yes
_NO = QMessageBox.StandardButton.No


def yes_or_no(parent: QWidget | None, title: str, question: str) -> QMessageBox:
    box = QMessageBox(QMessageBox.Icon.Question, title, question, _YES | _NO, parent)
    box.setDefaultButton(_YES)
    box.setEscapeButton(_NO)
    return box


def asked(parent: QWidget | None, title: str, question: str) -> bool:
    return QMessageBox.question(parent, title, question, _YES | _NO, _YES) == _YES
