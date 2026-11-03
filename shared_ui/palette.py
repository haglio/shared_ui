from __future__ import annotations

Rgb = tuple[int, int, int]
RGB_CHANNELS = 3
CHANNEL_MAX = 255

BG_PRIMARY: Rgb = (24, 24, 24)
BG_SECONDARY: Rgb = (40, 40, 40)
BG_TERTIARY: Rgb = (50, 50, 50)
BG_BUTTON: Rgb = (62, 62, 62)
BG_KEYCAP: Rgb = (72, 72, 72)
BG_BUTTON_ACTIVE: Rgb = (92, 92, 92)

TEXT_PRIMARY: Rgb = (240, 240, 240)
TEXT_SECONDARY: Rgb = (230, 230, 230)
TEXT_MUTED: Rgb = (120, 120, 120)

BORDER_DEFAULT: Rgb = (210, 210, 210)
BORDER_SUBTLE: Rgb = BG_BUTTON_ACTIVE
BORDER_PANEL: Rgb = TEXT_MUTED

BLUE: Rgb = (48, 128, 224)
BLUE_LIGHT: Rgb = (140, 192, 240)
GREEN: Rgb = (48, 160, 48)
RED: Rgb = (255, 60, 60)
YELLOW: Rgb = (255, 200, 120)
MAGENTA: Rgb = (200, 80, 160)
WHITE: Rgb = (255, 255, 255)
BLACK: Rgb = (0, 0, 0)

LOADING_GROUND: Rgb = (26, 26, 46)
LOADING_ACCENT: Rgb = (233, 69, 96)
LOADING_TROUGH: Rgb = (22, 33, 62)
LOADING_STATUS: Rgb = BORDER_DEFAULT
LOADING_HINT: Rgb = (122, 122, 149)

TOGGLE_ON: Rgb = BLUE
TOGGLE_OFF: Rgb = TEXT_MUTED
TOGGLE_HANDLE: Rgb = WHITE

PREVIEW_INK: Rgb = YELLOW


HOVER_LIFT = 30


def hovered(rgb: Rgb) -> Rgb:
    return tuple(min(CHANNEL_MAX, channel + HOVER_LIFT) for channel in rgb)


def as_hex(rgb: Rgb) -> str:
    red, green, blue = rgb
    return f"#{red:02x}{green:02x}{blue:02x}"


def as_rgba(rgb: Rgb, alpha: float) -> str:
    red, green, blue = rgb
    return f"rgba({red}, {green}, {blue}, {alpha:g})"


def as_fractions(rgb: Rgb, alpha: float = 1.0) -> tuple[float, float, float, float]:
    red, green, blue = rgb
    return (red / CHANNEL_MAX, green / CHANNEL_MAX, blue / CHANNEL_MAX, alpha)


def nearest(rgb: Rgb) -> Rgb:
    family = {value for name, value in globals().items()
              if name.isupper() and isinstance(value, tuple) and len(value) == RGB_CHANNELS}
    return min(family, key=lambda color: sum((a - b) ** 2 for a, b in zip(color, rgb, strict=True)))
