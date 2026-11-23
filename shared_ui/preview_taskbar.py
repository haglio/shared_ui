"""A preview claims a taskbar identity no pinned shortcut names, so Windows has
nothing to dress its button in but what the window says; a window too busy to
say its own icon, as a loading screen is, then wears pythonw's."""
from __future__ import annotations

from pathlib import Path

from app_support.win32 import TaskbarApp

from shared_ui.preview import Preview, window_title
from shared_ui.preview_icon_pil import icon_file

__all__ = ["PREVIEW_LAUNCHER", "preview_on_the_taskbar"]

PREVIEW_LAUNCHER = "launch_preview_" + "branch.vbs"


def preview_on_the_taskbar(app_name: str, icon: Path, preview: Preview | None, checkout: Path,
                           folder: Path) -> TaskbarApp | None:
    if preview is None:
        return None
    return TaskbarApp(name=window_title(app_name, preview), icon=icon_file(icon, preview, folder),
                      relaunch=f'wscript.exe "{checkout / PREVIEW_LAUNCHER}"')
