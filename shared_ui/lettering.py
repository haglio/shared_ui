from __future__ import annotations

import re
from functools import cache

from PIL import ImageFont

# Segoe UI by file, the way Pillow loads a face: "b" is its bold, "z" its bold
# italic -- the lean the app's name wears everywhere else it is written.
BOLD_FACE = "segoeuib.ttf"
REGULAR_FACE = "segoeui.ttf"
WORDMARK_FACE = "segoeuiz.ttf"


@cache
def load_font(px: int, face: str = BOLD_FACE) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(face, px)
    except OSError:
        return ImageFont.load_default(px)


def fit_text(font, text: str, width: int) -> str:
    if font.getlength(text) <= width or not text:
        return text
    kept = text
    while font.getlength(kept + "…") > width:
        if not kept:
            return ""
        kept = kept[:-1]
    return kept + "…"


def wrap_text(font, text: str, width: int, *, max_lines: int | None = None) -> list[str]:
    if not text.strip():
        return []
    lines = [line for paragraph in text.split("\n")
             for line in _wrapped(font, paragraph, width)]
    if max_lines is not None and len(lines) > max_lines:
        lines[max_lines - 1:] = [" ".join(lines[max_lines - 1:])]
    return lines


def _wrapped(font, paragraph: str, width: int) -> list[str]:
    lines = [paragraph[:len(paragraph) - len(paragraph.lstrip())]]
    for word in re.findall(r"\S+\s*", paragraph):
        if lines[-1].strip() and font.getlength(lines[-1] + word.rstrip()) > width:
            lines.append("")
        lines[-1] += word
    return [line.rstrip() for line in lines]
