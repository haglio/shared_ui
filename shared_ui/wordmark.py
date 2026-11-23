from __future__ import annotations

from shared_ui.palette import LOADING_ACCENT, PREVIEW_INK, Rgb
from shared_ui.preview import Preview


def wordmark_ink(preview: Preview | None) -> Rgb:
    return LOADING_ACCENT if preview is None else PREVIEW_INK
