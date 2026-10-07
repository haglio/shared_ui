from __future__ import annotations

from PIL import Image, ImageDraw

from shared_ui.palette import MAGENTA, PREVIEW_INK
from shared_ui.preview_icon_pil import write_in_preview_ink

_SIZES = [(16, 16), (32, 32), (256, 256)]


def _an_apps_icon(tmp_path):
    letter = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(letter).rectangle((64, 64, 191, 191), fill=(*MAGENTA, 255))
    path = tmp_path / "icon.ico"
    letter.save(path, format="ICO", sizes=_SIZES)
    return path


def _frame(path, size):
    image = Image.open(path)
    image.size = size
    return image.convert("RGBA")


def test_a_preview_icon_file_carries_every_size_in_the_preview_ink(tmp_path):
    written = tmp_path / "preview.ico"

    write_in_preview_ink(_an_apps_icon(tmp_path), written)

    assert sorted(Image.open(written).info["sizes"]) == _SIZES
    for width, height in _SIZES:
        frame = _frame(written, (width, height))
        assert frame.getpixel((width // 2, height // 2)) == (*PREVIEW_INK, 255)
        assert frame.getpixel((0, 0))[3] == 0
