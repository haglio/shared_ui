from __future__ import annotations

import html
import re

from shared_ui.type_scale import FONT_CODE

__all__ = ["as_rich_text"]

_IN_BACKTICKS = re.compile(r"`([^`\n]+)`")


def as_rich_text(text: str) -> str:
    escaped = html.escape(text, quote=False)
    coded = _IN_BACKTICKS.sub(
        lambda name: f"<span style=\"font-family:'{FONT_CODE}'\">{name.group(1)}</span>", escaped)
    return "<qt>" + coded.replace("\n", "<br>") + "</qt>"
