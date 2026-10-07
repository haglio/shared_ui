from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap

from shared_ui.colors import PREVIEW_INK
from shared_ui.preview import Preview, inked_icon_file


def icon_file(source: Path, preview: Preview | None, folder: Path) -> Path:
    return inked_icon_file(source, preview, folder, _write_in_preview_ink)


def _write_in_preview_ink(source: Path, destination: Path) -> None:
    icon = _inked(QIcon(str(source)))
    largest = max(icon.availableSizes(), key=lambda size: size.width())
    icon.pixmap(largest).save(str(destination), "ICO")


def app_icon(path: Path, preview: Preview | None) -> QIcon:
    icon = QIcon(str(path))
    return icon if preview is None else _inked(icon)


def _inked(icon: QIcon) -> QIcon:
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
