"""What Qt says about the videos the apps open."""
from __future__ import annotations

import pytest
from PyQt6.QtCore import QLoggingCategory

from shared_ui.qt_messages import silence_the_ffmpeg_format_dump


@pytest.fixture
def qt_category():
    yield QLoggingCategory
    QLoggingCategory.setFilterRules("")


def test_the_ffmpeg_format_dump_says_nothing_of_a_videos_tags(qt_category):
    silence_the_ffmpeg_format_dump()

    assert not qt_category("qt.multimedia.ffmpeg.mediadataholder").isInfoEnabled()


def test_the_rest_of_qt_multimedia_still_warns(qt_category):
    silence_the_ffmpeg_format_dump()

    assert qt_category("qt.multimedia.ffmpeg").isWarningEnabled()
    assert qt_category("qt.multimedia.ffmpeg.mediadataholder").isWarningEnabled()
