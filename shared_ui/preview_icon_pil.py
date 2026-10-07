from __future__ import annotations

from pathlib import Path

from PIL import Image

from shared_ui.palette import PREVIEW_INK


def write_in_preview_ink(source: Path, destination: Path) -> None:
    icon = Image.open(source)
    sizes = sorted(icon.info["sizes"])
    frames = [_in_preview_ink(_frame(icon, size)) for size in sizes]
    largest = frames[-1]
    largest.save(destination, format="ICO", sizes=sizes, append_images=frames[:-1])


def _frame(icon: Image.Image, size: tuple[int, int]) -> Image.Image:
    icon.size = size
    return icon.convert("RGBA")


def _in_preview_ink(letter: Image.Image) -> Image.Image:
    inked = Image.new("RGBA", letter.size, (*PREVIEW_INK, 0))
    inked.putalpha(letter.getchannel("A"))
    return inked
