from __future__ import annotations

from pathlib import Path

from PIL import Image

from shared_ui.preview import Preview
from shared_ui.preview_taskbar import PREVIEW_LAUNCHER, preview_on_the_taskbar


def _an_icon(folder: Path) -> Path:
    icon = folder / "icon.ico"
    Image.new("RGBA", (32, 32), (200, 40, 160, 255)).save(icon, format="ICO")
    return icon


def test_the_app_he_uses_day_to_day_leaves_its_taskbar_button_to_its_pinned_shortcut(tmp_path):
    assert preview_on_the_taskbar("Scripture", _an_icon(tmp_path), None, tmp_path, tmp_path) is None


def test_a_preview_names_its_taskbar_button_wears_its_letter_in_preview_ink_and_starts_again_from_its_launcher(
        tmp_path):
    icon = _an_icon(tmp_path)

    button = preview_on_the_taskbar("Scripture", icon, Preview("the example"), tmp_path / "checkout",
                                    tmp_path / "state")

    assert button.name == "Scripture — preview of the example"
    assert button.icon == tmp_path / "state" / "preview_icon.ico"
    assert button.icon.is_file()
    assert button.relaunch == f'wscript.exe "{tmp_path / "checkout" / PREVIEW_LAUNCHER}"'
