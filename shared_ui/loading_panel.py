"""The loading screen every app in the family shows while it starts: the app's
icon, its name, a line saying what is happening, a progress bar and a hint,
on one navy ground.  Rendered once, with Pillow, so a Tk cover, a Qt window, a
pygame surface and a headset all show the same picture."""

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


@dataclass(frozen=True)
class Metrics:
    """The panel's sizes, in pixels."""

    padding: int = 24
    icon: int = 128
    wordmark_px: int = 24
    status_px: int = 13
    hint_px: int = 11
    bar: tuple[int, int] = (360, 18)
    gaps: tuple[int, int, int, int] = (12, 10, 10, 8)

    @property
    def width(self) -> int:
        return self.bar[0] + 2 * self.padding


DESKTOP = Metrics()


@dataclass(frozen=True)
class LoadingPanel:
    """What the panel says right now."""

    wordmark: str
    status: str
    fraction: float | None = None
    hint: str = ""
    ink: Rgb = LOADING_ACCENT
    icon: Image.Image | None = None


def icon_image(path: Path | None) -> Image.Image | None:
    """An app's icon file as the panel takes it, or None for a panel without one."""
    if path is None:
        return None
    try:
        return Image.open(path).convert("RGBA")
    except (OSError, ValueError):
        return None


def render(panel: LoadingPanel, metrics: Metrics = DESKTOP) -> Image.Image:
    wordmark_font = load_font(metrics.wordmark_px, WORDMARK_FACE)
    status_font = load_font(metrics.status_px, REGULAR_FACE)
    hint_font = load_font(metrics.hint_px, REGULAR_FACE)
    rows = (
        metrics.icon,
        _line_height(wordmark_font),
        _line_height(status_font),
        metrics.bar[1],
        _line_height(hint_font),
    )
    image = Image.new("RGB", (metrics.width, sum(rows) + sum(metrics.gaps) + 2 * metrics.padding), LOADING_GROUND)
    draw = ImageDraw.Draw(image)
    center = metrics.width // 2
    top = metrics.padding
    if panel.icon is not None:
        icon = panel.icon.convert("RGBA").resize((metrics.icon, metrics.icon), Image.LANCZOS)
        image.paste(icon, (center - metrics.icon // 2, top), icon)
    top += rows[0] + metrics.gaps[0]
    _centered(draw, center, top, panel.wordmark, wordmark_font, panel.ink, metrics.bar[0])
    top += rows[1] + metrics.gaps[1]
    _centered(draw, center, top, panel.status, status_font, LOADING_STATUS, metrics.bar[0])
    top += rows[2] + metrics.gaps[2]
    _bar(draw, metrics, top, panel.fraction)
    top += rows[3] + metrics.gaps[3]
    _centered(draw, center, top, panel.hint, hint_font, LOADING_HINT, metrics.bar[0])
    return image


def _centered(draw: ImageDraw.ImageDraw, center: int, top: int, text: str, font, ink: Rgb,
              width: int) -> None:
    if text:
        draw.text((center, top), fit_text(font, text, width), font=font, fill=ink, anchor="ma")


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
