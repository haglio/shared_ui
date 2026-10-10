"""shared_ui.loading_panel: the loading screen every app in the family shows,
rendered once with Pillow so each toolkit draws the same picture."""

from __future__ import annotations

from PIL import Image

from shared_ui.loading_panel import DESKTOP, LoadingPanel, render
from shared_ui.palette import (
    LOADING_ACCENT,
    LOADING_GROUND,
    LOADING_HINT,
    LOADING_STATUS,
    LOADING_TROUGH,
    PREVIEW_INK,
)


def _panel(**changes) -> LoadingPanel:
    return LoadingPanel(**{"wordmark": "Fun Time", "status": "Starting...", **changes})


class TestTheGround:
    def test_the_panel_is_the_bar_wide_plus_its_padding_on_the_loading_ground(self):
        image = render(_panel())

        assert image.mode == "RGB"
        assert image.width == DESKTOP.bar[0] + 2 * DESKTOP.padding
        assert image.getpixel((0, 0)) == LOADING_GROUND
        assert image.getpixel((image.width - 1, image.height - 1)) == LOADING_GROUND


def _box_of(image, color) -> tuple[int, int, int, int]:
    """``(left, top, right, lower)`` of every pixel in *color*."""
    pixels = image.load()
    xs = [x for y in range(image.height) for x in range(image.width) if pixels[x, y] == color]
    ys = [y for y in range(image.height) for x in range(image.width) if pixels[x, y] == color]
    assert xs, f"nothing in {color}"
    return min(xs), min(ys), max(xs), max(ys)


class TestTheBar:
    def test_the_fill_spans_the_fraction_of_the_track(self):
        left, top, right, lower = _box_of(render(_panel(fraction=None)), LOADING_TROUGH)
        assert (right - left + 1, lower - top + 1) == DESKTOP.bar

        image = render(_panel(fraction=0.5))

        middle = (top + lower) // 2
        assert image.getpixel((left + DESKTOP.bar[0] // 4, middle)) == LOADING_ACCENT
        assert image.getpixel((left + 3 * DESKTOP.bar[0] // 4, middle)) == LOADING_TROUGH


def _above(image, lower: int):
    return image.crop((0, 0, image.width, lower))


def _has(image, color) -> bool:
    pixels = image.load()
    return any(pixels[x, y] == color for y in range(image.height) for x in range(image.width))


class TestTheWordmark:
    def test_it_is_lettered_in_the_accent_above_the_bar(self):
        image = render(_panel(fraction=None))
        bar_top = _box_of(image, LOADING_TROUGH)[1]

        assert _has(_above(image, bar_top), LOADING_ACCENT)

    def test_a_preview_build_letters_it_in_the_preview_ink_instead(self):
        image = render(_panel(fraction=None, ink=PREVIEW_INK))
        bar_top = _box_of(image, LOADING_TROUGH)[1]

        assert _has(_above(image, bar_top), PREVIEW_INK)
        assert not _has(_above(image, bar_top), LOADING_ACCENT)


class TestTheStatusLine:
    def test_it_says_what_is_happening_between_the_name_and_the_bar(self):
        image = render(_panel(status="Checking the video engine...", fraction=None))
        bar_top = _box_of(image, LOADING_TROUGH)[1]
        name_bottom = _box_of(_above(image, bar_top), LOADING_ACCENT)[3]

        left, top, right, _bottom = _box_of(image, LOADING_STATUS)
        assert name_bottom < top < bar_top
        assert DESKTOP.padding <= left and right < image.width - DESKTOP.padding

    def test_a_line_wider_than_the_bar_is_cut_to_it(self):
        image = render(_panel(status="Reading video lengths " * 12, fraction=None))

        left, _top, right, _bottom = _box_of(image, LOADING_STATUS)
        assert DESKTOP.padding <= left and right < image.width - DESKTOP.padding


class TestTheHint:
    def test_it_sits_under_the_bar_in_the_subtler_tone(self):
        image = render(_panel(hint="Press Esc to cancel opening Fun Time", fraction=None))
        bar_bottom = _box_of(image, LOADING_TROUGH)[3]

        assert _box_of(image, LOADING_HINT)[1] > bar_bottom

    def test_its_line_is_kept_whether_or_not_there_is_one_so_the_panel_never_jumps(self):
        with_hint = render(_panel(hint="Press Esc to cancel opening Fun Time"))
        without = render(_panel(hint=""))

        assert with_hint.size == without.size
        assert not _has(without, LOADING_HINT)


class TestTheIcon:
    _ICON_INK = (10, 200, 30)

    def test_it_sits_centered_at_the_top_scaled_to_its_row(self):
        icon = Image.new("RGBA", (64, 64), (*self._ICON_INK, 255))

        image = render(_panel(icon=icon))

        left, top, right, lower = _box_of(image, self._ICON_INK)
        assert (right - left + 1, lower - top + 1) == (DESKTOP.icon, DESKTOP.icon)
        assert top == DESKTOP.padding
        assert left == image.width // 2 - DESKTOP.icon // 2

    def test_without_one_the_row_is_left_to_the_ground(self):
        image = render(_panel(icon=None))

        assert image.getpixel((image.width // 2, DESKTOP.padding + DESKTOP.icon // 2)) == LOADING_GROUND
