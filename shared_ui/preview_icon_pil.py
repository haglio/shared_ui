from __future__ import annotations

from pathlib import Path

from PIL import Image

from shared_ui.palette import PREVIEW_INK
from shared_ui.preview import Preview


def icon_file(source: Path, preview: Preview | None, folder: Path) -> Path:
    if preview is None:
        return source
    inked = folder / f"preview_{source.name}"
    if not inked.exists() or inked.stat().st_mtime < source.stat().st_mtime:
        folder.mkdir(parents=True, exist_ok=True)
        write_in_preview_ink(source, inked)
    return inked


def write_in_preview_ink(source: Path, destination: Path) -> None:
    icon = Image.open(source)
    sizes = sorted(icon.info["sizes"])
    frames = [in_preview_ink(_frame(icon, size)) for size in sizes]
    largest = frames[-1]
    largest.save(destination, format="ICO", sizes=sizes, append_images=frames[:-1])


def _frame(icon: Image.Image, size: tuple[int, int]) -> Image.Image:
    icon.size = size
    return icon.convert("RGBA")


def in_preview_ink(letter: Image.Image) -> Image.Image:
    inked = Image.new("RGBA", letter.size, (*PREVIEW_INK, 0))
    inked.putalpha(letter.getchannel("A"))
    return inked
