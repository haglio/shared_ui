from __future__ import annotations

from itertools import pairwise

from shared_ui.palette import BG_PRIMARY, BLUE, BLUE_LIGHT, GREEN, RED, YELLOW, Rgb

_HEATMAP_STEPS: tuple[tuple[float, Rgb], ...] = (
    (0.0, BG_PRIMARY), (100.0, BLUE), (200.0, BLUE_LIGHT), (300.0, GREEN), (400.0, YELLOW),
    (500.0, RED),
)


def heat_at(speed: float) -> Rgb:
    for (low, low_color), (high, high_color) in pairwise(_HEATMAP_STEPS):
        if speed <= high:
            share = (speed - low) / (high - low)
            return tuple(round(a + (b - a) * share) for a, b in zip(low_color, high_color, strict=True))
    return _HEATMAP_STEPS[-1][1]
