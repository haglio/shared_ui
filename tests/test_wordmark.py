from __future__ import annotations

from shared_ui.palette import LOADING_ACCENT, PREVIEW_INK
from shared_ui.preview import Preview
from shared_ui.wordmark import wordmark_ink


def test_an_apps_own_wordmark_wears_the_loading_accent():
    assert wordmark_ink(None) == LOADING_ACCENT


def test_a_previews_wordmark_wears_the_preview_ink():
    assert wordmark_ink(Preview("the scene list")) == PREVIEW_INK
