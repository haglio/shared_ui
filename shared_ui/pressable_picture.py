"""What :mod:`shared_ui.pressable_drawing` was called before an item was an image or
a video, kept for the checkouts that still paint one through ``picture()``."""

from __future__ import annotations

from shared_ui.pressable_drawing import PressableDrawing


class PressablePicture(PressableDrawing):
    def drawing(self) -> tuple[bytes, tuple[int, int]]:
        return self.picture()
