from __future__ import annotations

import os

from PIL import Image, ImageDraw

from shared_ui.palette import MAGENTA, PREVIEW_INK
from shared_ui.preview import Preview
from shared_ui.preview_icon_pil import icon_file, in_preview_ink, write_in_preview_ink

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


def test_a_letter_drawn_in_memory_takes_the_preview_ink_and_keeps_its_edges():
    letter = Image.new("RGBA", (4, 1), (0, 0, 0, 0))
    letter.putpixel((1, 0), (*MAGENTA, 255))
    letter.putpixel((2, 0), (*MAGENTA, 96))

    inked = in_preview_ink(letter)

    assert [inked.getpixel((x, 0))[3] for x in range(4)] == [0, 255, 96, 0]
    assert inked.getpixel((1, 0))[:3] == inked.getpixel((2, 0))[:3] == PREVIEW_INK


def test_the_live_app_wears_its_own_icon_file(tmp_path):
    source = _an_apps_icon(tmp_path)

    assert icon_file(source, None, tmp_path / "state") == source


def test_a_preview_wears_the_letter_inked_into_a_file_of_its_own(tmp_path):
    source = _an_apps_icon(tmp_path)

    inked = icon_file(source, Preview(feature=None), tmp_path / "state")

    assert inked == tmp_path / "state" / "preview_icon.ico"
    assert _frame(inked, (32, 32)).getpixel((16, 16)) == (*PREVIEW_INK, 255)


def test_the_inked_file_is_written_once_and_again_only_after_the_letter_changes(tmp_path):
    source = _an_apps_icon(tmp_path)
    inked = icon_file(source, Preview(feature=None), tmp_path / "state")
    inked.write_bytes(b"read by every process of the session")

    assert icon_file(source, Preview(feature=None), tmp_path / "state").read_bytes() == (
        b"read by every process of the session")

    os.utime(source, (inked.stat().st_mtime + 10,) * 2)
    icon_file(source, Preview(feature=None), tmp_path / "state")

    assert _frame(inked, (32, 32)).getpixel((16, 16)) == (*PREVIEW_INK, 255)
