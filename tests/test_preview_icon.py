from __future__ import annotations

from PIL import Image, ImageDraw
from PyQt6.QtGui import QImage

from shared_ui.palette import MAGENTA, PREVIEW_INK
from shared_ui.preview import Preview
from shared_ui.preview_icon import app_icon
from shared_ui.preview_icon import icon_file as qt_icon_file
from shared_ui.preview_icon_pil import write_in_preview_ink

_A_PREVIEW = Preview(feature=None)
_QTS_PREMULTIPLIED_ROUNDING = 1


def _as_seen(rgba):
    *color, alpha = rgba
    return (*(round(channel * alpha / 255) for channel in color), alpha)


def _an_apps_icon(tmp_path):
    letter = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(letter).rectangle((64, 64, 191, 191), fill=(*MAGENTA, 255))
    path = tmp_path / "icon.ico"
    letter.save(path, format="ICO", sizes=[(16, 16), (32, 32), (256, 256)])
    return path


def test_a_preview_draws_its_letter_in_the_preview_ink_at_every_size(tmp_path):
    icon = app_icon(_an_apps_icon(tmp_path), _A_PREVIEW)

    assert sorted(size.width() for size in icon.availableSizes()) == [16, 32, 256]
    for size in icon.availableSizes():
        image = icon.pixmap(size).toImage()
        center = image.pixelColor(size.width() // 2, size.height() // 2)
        assert (center.red(), center.green(), center.blue(), center.alpha()) == (*PREVIEW_INK, 255)
        assert image.pixelColor(0, 0).alpha() == 0


def test_the_live_app_keeps_its_magenta_letter(tmp_path):
    image = app_icon(_an_apps_icon(tmp_path), None).pixmap(32, 32).toImage()

    center = image.pixelColor(16, 16)
    assert (center.red(), center.green(), center.blue()) == MAGENTA


def test_a_preview_letter_drawn_by_qt_matches_the_one_written_for_windows_without_it(tmp_path):
    source = _an_apps_icon(tmp_path)
    written = tmp_path / "preview.ico"
    write_in_preview_ink(source, written)
    by_qt = app_icon(source, _A_PREVIEW).pixmap(32, 32).toImage()
    on_disk = Image.open(written)
    on_disk.size = (32, 32)
    on_disk = on_disk.convert("RGBA")

    for x, y in ((0, 0), (16, 16), (8, 8), (24, 24)):
        pixel = by_qt.pixelColor(x, y)
        drawn = _as_seen((pixel.red(), pixel.green(), pixel.blue(), pixel.alpha()))
        written_pixel = _as_seen(on_disk.getpixel((x, y)))
        assert all(abs(a - b) <= _QTS_PREMULTIPLIED_ROUNDING for a, b in zip(drawn, written_pixel))


def test_a_qt_app_without_pillow_still_hands_the_taskbar_its_inked_letter_as_a_file(tmp_path):
    inked = qt_icon_file(_an_apps_icon(tmp_path), _A_PREVIEW, tmp_path / "state")

    assert inked == tmp_path / "state" / "preview_icon.ico"
    image = QImage(str(inked))
    center = image.pixelColor(image.width() // 2, image.height() // 2)
    assert (center.red(), center.green(), center.blue()) == PREVIEW_INK


def test_the_live_qt_app_hands_the_taskbar_its_own_icon_file(tmp_path):
    source = _an_apps_icon(tmp_path)

    assert qt_icon_file(source, None, tmp_path / "state") == source
