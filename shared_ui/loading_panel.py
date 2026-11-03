from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from shared_ui.lettering import REGULAR_FACE, WORDMARK_FACE, fit_text, load_font
from shared_ui.palette import (
    LOADING_ACCENT,
    LOADING_GROUND,
    LOADING_HINT,
    LOADING_STATUS,
    LOADING_TROUGH,
    Rgb,
)
from shared_ui.spacing import GAP_DIALOG, GAP_MEDIUM, MARGIN_DIALOG
from shared_ui.type_scale import SIZE_HEADING, SIZE_SMALL, SIZE_TINY, in_pixels


@dataclass(frozen=True)
class Metrics:
    padding: int = MARGIN_DIALOG
    icon: int = 128
    wordmark_px: int = in_pixels(SIZE_HEADING)
    status_px: int = in_pixels(SIZE_SMALL)
    hint_px: int = in_pixels(SIZE_TINY)
    bar: tuple[int, int] = (360, 18)
    gaps: tuple[int, int, int, int] = (GAP_DIALOG, GAP_MEDIUM, GAP_MEDIUM, GAP_MEDIUM)

    @property
    def width(self) -> int:
        return self.bar[0] + 2 * self.padding


DESKTOP = Metrics()


@dataclass(frozen=True)
class LoadingPanel:
    wordmark: str
    status: str
    fraction: float | None = None
    hint: str = ""
    ink: Rgb = LOADING_ACCENT
    icon: Image.Image | None = None


def icon_image(path: Path | None) -> Image.Image | None:
    if path is None:
        return None
    try:
        return Image.open(path).convert("RGBA")
    except (OSError, ValueError):
        return None


def render(panel: LoadingPanel, metrics: Metrics = DESKTOP) -> Image.Image:
    wordmark_font, status_font, hint_font = _fonts(metrics)
    icon_top, wordmark_top, status_top, bar_top, hint_top, _height = _tops(metrics)
    image = Image.new("RGB", size(metrics), LOADING_GROUND)
    draw = ImageDraw.Draw(image)
    center = metrics.width // 2
    if panel.icon is not None:
        icon = panel.icon.convert("RGBA").resize((metrics.icon, metrics.icon), Image.LANCZOS)
        image.paste(icon, (center - metrics.icon // 2, icon_top), icon)

    def centered(top: int, text: str, font, ink: Rgb) -> None:
        draw.text((center, top), fit_text(font, text, metrics.bar[0]), font=font, fill=ink,
                  anchor="ma")

    centered(wordmark_top, panel.wordmark, wordmark_font, panel.ink)
    centered(status_top, panel.status, status_font, LOADING_STATUS)
    _bar(draw, metrics, bar_top, panel.fraction)
    centered(hint_top, panel.hint, hint_font, LOADING_HINT)
    return image


def bar_box(metrics: Metrics = DESKTOP) -> tuple[int, int, int, int]:
    return (metrics.padding, _tops(metrics)[3], *metrics.bar)


def size(metrics: Metrics = DESKTOP) -> tuple[int, int]:
    return metrics.width, _tops(metrics)[-1]


def _fonts(metrics: Metrics):
    return (load_font(metrics.wordmark_px, WORDMARK_FACE), load_font(metrics.status_px, REGULAR_FACE),
            load_font(metrics.hint_px, REGULAR_FACE))


def _tops(metrics: Metrics) -> tuple[int, ...]:
    wordmark_font, status_font, hint_font = _fonts(metrics)
    rows = (metrics.icon, _line_height(wordmark_font), _line_height(status_font), metrics.bar[1],
            _line_height(hint_font))
    tops, top = [], metrics.padding
    for row, gap in zip(rows, (*metrics.gaps, metrics.padding), strict=True):
        tops.append(top)
        top += row + gap
    return (*tops, top)


def _bar(draw: ImageDraw.ImageDraw, metrics: Metrics, top: int, fraction: float | None) -> None:
    width, height = metrics.bar
    left = metrics.padding
    draw.rectangle([left, top, left + width - 1, top + height - 1], fill=LOADING_TROUGH)
    filled = 0 if fraction is None else round(width * max(0.0, min(1.0, fraction)))
    if filled:
        draw.rectangle([left, top, left + filled - 1, top + height - 1], fill=LOADING_ACCENT)


def _line_height(font) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent
