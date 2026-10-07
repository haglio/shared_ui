from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap

from shared_ui.colors import PREVIEW_INK
from shared_ui.preview import Preview


def app_icon(path: Path, preview: Preview | None) -> QIcon:
    icon = QIcon(str(path))
    if preview is None:
        return icon
    inked = QIcon()
    for size in icon.availableSizes():
        inked.addPixmap(_in_preview_ink(icon.pixmap(size)))
    return inked


def _in_preview_ink(letter: QPixmap) -> QPixmap:
    image = letter.toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(image)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), PREVIEW_INK)
    painter.end()
    return QPixmap.fromImage(image)
