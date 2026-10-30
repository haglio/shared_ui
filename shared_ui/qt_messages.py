"""What Qt says about the videos the apps open.

Qt's FFmpeg backend writes out every video it opens, the file's tags among them,
and a video ComfyUI made carries its prompt in those tags, so it never reaches an
app's log.
"""
from __future__ import annotations

from PyQt6.QtCore import QLoggingCategory

_FORMAT_DUMP = "qt.multimedia.ffmpeg.mediadataholder"


def silence_the_ffmpeg_format_dump() -> None:
    QLoggingCategory.setFilterRules(f"{_FORMAT_DUMP}.info=false")
