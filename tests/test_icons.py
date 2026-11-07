from __future__ import annotations

import base64
import logging
import math
import re
import uuid
from itertools import pairwise

import pytest
from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QLabel

from shared_ui import icons
from shared_ui.colors import GREEN, RED, TEXT_MUTED, TEXT_PRIMARY
from shared_ui.icon_geometry import (
    CANVAS,
    ICONS,
    PEN_WIDTH,
    STAND_IN,
    Arc,
    Ellipse,
    Line,
    Path,
    Polygon,
    RoundedRect,
    icon_names,
)
from shared_ui.orientation import LANDSCAPE, PORTRAIT
from shared_ui.spacing import BUTTON_FILLING_ICON, BUTTON_ICON, BUTTON_SIZE_HUD

_AN_ICON_THIS_VERSION_LACKS = "an_icon_from_another_version"
_EVERY_ICON_AND_THE_STAND_IN = (*icon_names(), _AN_ICON_THIS_VERSION_LACKS)


def _drawn_by_the_public_route(monkeypatch, name: str, shapes: tuple) -> None:
    monkeypatch.setitem(ICONS, name, shapes)


def _blank(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    return pixmap


def _ink(pixmap: QPixmap, *, alpha_above: int = 32) -> set[tuple[int, int]]:
    image = pixmap.toImage()
    return {
        (x, y)
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() > alpha_above
    }


def _solid_ink(pixmap: QPixmap) -> set[tuple[int, int]]:
    return _ink(pixmap, alpha_above=127)


def _as_a_menu_row_shows(name: str) -> QPixmap:
    return icons.qt_icon(name).pixmap(QSize(BUTTON_ICON, BUTTON_ICON))


def _ink_rect(pixmap: QPixmap) -> tuple[int, int, int, int]:
    return _ink_rect_of(_ink(pixmap))


def _ink_rect_of(ink: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    assert ink, "nothing was drawn"
    xs = [x for x, _y in ink]
    ys = [y for _x, y in ink]
    return min(xs), min(ys), max(xs), max(ys)


def _ink_pixels(pixmap: QPixmap) -> int:
    return len(_ink(pixmap))


def _pieces(ink: set[tuple[int, int]]) -> int:
    unvisited, pieces = set(ink), 0
    while unvisited:
        pieces += 1
        stack = [unvisited.pop()]
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = (x + dx, y + dy)
                    if neighbor in unvisited:
                        unvisited.discard(neighbor)
                        stack.append(neighbor)
    return pieces


def test_every_registered_icon_inks_something_so_no_button_comes_up_empty():
    for name in icon_names():
        pixmap = icons.icon_pixmap(name, 48, TEXT_PRIMARY)
        assert not pixmap.isNull(), name
        assert _ink_pixels(pixmap) > 0, name


def test_the_icons_are_all_different():
    drawn = {
        name: icons.icon_pixmap(name, 48, TEXT_PRIMARY).toImage()
        for name in _EVERY_ICON_AND_THE_STAND_IN
    }
    names = sorted(drawn)
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            assert drawn[first] != drawn[second], f"{first} and {second} draw alike"


_ONE_BAR = {"minus", "more", "more_vertical"}
_IN_A_CORNER = {"regenerate_corner"}
_RUNS_TO_THE_EDGE = {"headset", "control_off"}
_MOST_OF_THE_CANVAS = 0.6
_AS_NARROW_AS_A_CHEVRON = 0.4


def test_every_icon_fills_its_canvas_or_the_eye_loses_it_once_it_is_scaled_onto_a_tree_row():
    for name in set(_EVERY_ICON_AND_THE_STAND_IN) - _ONE_BAR - _IN_A_CORNER:
        left, upper, right, lower = _ink_rect(icons.icon_pixmap(name, 48, TEXT_PRIMARY))
        width, height = right - left, lower - upper
        assert max(width, height) >= _MOST_OF_THE_CANVAS * 48, f"{name} is small in its frame"
        assert min(width, height) >= _AS_NARROW_AS_A_CHEVRON * 48, f"{name} is thin in its frame"


def test_an_icon_s_ink_stays_inside_its_canvas_with_room_for_its_caps_and_heads():
    for name in set(_EVERY_ICON_AND_THE_STAND_IN) - _RUNS_TO_THE_EDGE:
        left, upper, right, lower = _ink_rect(icons.icon_pixmap(name, 2 * 48, TEXT_PRIMARY))
        assert min(left, upper) >= 1, f"{name} is clipped by its canvas"
        assert max(right, lower) <= 2 * 48 - 2, f"{name} is clipped by its canvas"


def test_a_one_bar_icon_still_spans_its_canvas_the_long_way():
    for name in _ONE_BAR:
        left, upper, right, lower = _ink_rect(icons.icon_pixmap(name, 48, TEXT_PRIMARY))
        assert max(right - left, lower - upper) >= 0.6 * 48, f"{name} is short in its frame"


_SHOWS_A_CANVAS_UNIT = 2 * 48


def test_the_speed_pair_is_one_control_drawn_twice_in_ink_however_the_geometry_spells_it():
    (bar,) = ICONS["minus"]
    scale = _SHOWS_A_CANVAS_UNIT / CANVAS
    minus = _ink(icons.icon_pixmap("minus", _SHOWS_A_CANVAS_UNIT, TEXT_PRIMARY))
    plus = _ink(icons.icon_pixmap("plus", _SHOWS_A_CANVAS_UNIT, TEXT_PRIMARY))

    assert minus <= plus
    the_second_bar = plus - minus
    assert the_second_bar
    assert all(abs(x + 0.5 - _SHOWS_A_CANVAS_UNIT / 2) <= scale * bar.width / 2 + 1 for x, _y in the_second_bar)


def test_the_hollow_plus_traces_the_solid_one():
    solid = icons.icon_pixmap("plus", 48, TEXT_PRIMARY)
    hollow = icons.icon_pixmap("plus_outline", 48, TEXT_PRIMARY)
    for solid_edge, hollow_edge in zip(_ink_rect(solid), _ink_rect(hollow), strict=True):
        assert abs(solid_edge - hollow_edge) <= 2
    assert hollow.toImage().pixelColor(24, 24).alpha() < 32
    assert solid.toImage().pixelColor(24, 24).alpha() > 32


def test_every_icon_sits_in_the_middle_of_its_canvas_so_a_bank_of_buttons_lines_up():
    for name in set(_EVERY_ICON_AND_THE_STAND_IN) - _IN_A_CORNER:
        left, upper, right, lower = _ink_rect(icons.icon_pixmap(name, 48, TEXT_PRIMARY))
        assert abs((left + right) / 2 - 24) <= 0.12 * 48, f"{name} sits off-center"
        assert abs((upper + lower) / 2 - 24) <= 0.12 * 48, f"{name} sits off-center"


def test_an_icon_is_drawn_in_the_color_it_is_asked_for_a_red_delete_or_a_green_favorite():
    for color in (RED, GREEN, TEXT_PRIMARY):
        image = icons.icon_pixmap("star", 48, color).toImage()
        assert image.pixelColor(24, 25) == color


def test_an_icon_scales_to_the_size_it_is_asked_for():
    for size in (16, 24, 48, 96):
        pixmap = icons.icon_pixmap("mic", size, TEXT_PRIMARY)
        assert pixmap.size() == QSize(size, size)


_ANTIALIASING_FATTENS_A_SMALL_ICON = 1.3


def test_a_small_icon_is_the_same_icon_rather_than_a_heavier_one():
    sizes = (24, 48, 96)
    rects = [_ink_rect(icons.icon_pixmap("mic", size, TEXT_PRIMARY)) for size in sizes]
    widths = [(right - left) / size
              for (left, _upper, right, _lower), size in zip(rects, sizes, strict=True)]
    heights = [(lower - upper) / size
               for (_left, upper, _right, lower), size in zip(rects, sizes, strict=True)]
    assert max(widths) - min(widths) < 0.06
    assert max(heights) - min(heights) < 0.06
    coverage = [
        _ink_pixels(icons.icon_pixmap("mic", size, TEXT_PRIMARY)) / (size * size)
        for size in sizes
    ]
    assert max(coverage) < _ANTIALIASING_FATTENS_A_SMALL_ICON * min(coverage)


def test_an_icon_carries_a_normal_and_a_dimmed_rendering():
    icon = icons.qt_icon("trash", color=RED)
    size = QSize(48, 48)
    normal = icon.pixmap(size, QIcon.Mode.Normal)
    disabled = icon.pixmap(size, QIcon.Mode.Disabled)
    assert _ink_pixels(normal) > 0
    assert _ink_pixels(disabled) > 0
    assert normal.toImage() != disabled.toImage()


def test_a_disabled_icon_is_the_muted_gray_whatever_its_color():
    for color in (RED, GREEN, None):
        icon = icons.qt_icon("star", color=color)
        image = icon.pixmap(QSize(48, 48), QIcon.Mode.Disabled).toImage()
        assert image.pixelColor(24, 25) == TEXT_MUTED


def test_an_uncolored_icon_wears_the_chrome_text_color():
    icon = icons.qt_icon("star")
    image = icon.pixmap(QSize(48, 48), QIcon.Mode.Normal).toImage()
    assert image.pixelColor(24, 25) == TEXT_PRIMARY


def test_the_pixmap_and_the_qt_icon_draw_the_very_same_icon():
    from_pixmap = icons.icon_pixmap("mic", 48, TEXT_PRIMARY)
    from_icon = icons.qt_icon("mic", size=48).pixmap(QSize(48, 48), QIcon.Mode.Normal)
    assert from_pixmap.toImage() == from_icon.toImage()


def test_painting_into_a_caller_s_painter_draws_that_same_icon_too():
    direct = icons.icon_pixmap("play", 48, TEXT_PRIMARY)
    composed = _blank(48)
    painter = QPainter(composed)
    icons.draw_icon(painter, "play", TEXT_PRIMARY)
    painter.end()
    assert composed.toImage() == direct.toImage()


def test_an_icon_lands_where_the_caller_placed_it():
    canvas = _blank(48)
    painter = QPainter(canvas)
    icons.draw_icon(painter, "star", TEXT_PRIMARY, size=24, x=12, y=12)
    painter.end()
    left, upper, right, lower = _ink_rect(canvas)
    assert left >= 12
    assert right <= 36
    assert upper >= 12
    assert lower <= 36


def test_drawing_an_icon_leaves_the_caller_s_painter_as_it_found_it():
    canvas = _blank(64)
    painter = QPainter(canvas)
    painter.translate(8, 8)
    painter.setPen(QPen(QColor(GREEN), 3))
    painter.setBrush(QColor(RED))
    icons.draw_icon(painter, "clock", TEXT_PRIMARY, size=24)
    assert painter.pen().color() == QColor(GREEN)
    assert painter.pen().widthF() == 3
    assert painter.brush().color() == QColor(RED)
    assert painter.transform().dx() == 8
    assert painter.transform().dy() == 8
    painter.end()


def test_an_icon_drawn_over_a_chip_keeps_the_chip_underneath():
    canvas = _blank(48)
    painter = QPainter(canvas)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(GREEN))
    painter.drawRoundedRect(QRectF(3, 3, 42, 42), 12, 12)
    icons.draw_icon(painter, "play", RED, size=26, x=11, y=11)
    painter.end()
    image = canvas.toImage()
    assert image.pixelColor(6, 24) == QColor(GREEN)
    assert image.pixelColor(0, 0).alpha() == 0


_THE_ICONS = (
    "bolt", "cells_in_circle", "chart", "check", "chevron_down", "chevron_left",
    "chevron_right", "chevron_up", "chevrons_left", "chevrons_right", "circle",
    "clip_to_scene", "clips", "clock", "compilation",
    "control_off", "copy", "cross", "crown", "database", "disc", "enhance_filter", "enlarge", "error",
    "expand_horizontal", "export", "external_link", "filter", "flask", "flat_2d", "flip_ends",
    "fmode", "folder", "full", "funscript_jump", "grid", "headset", "human",
    "info", "jigsaw", "landscape", "latest", "lock", "log", "loop", "mic", "minus", "monitor",
    "moon", "more", "more_vertical", "pair_in_circle", "park", "pause", "pencil", "photo", "play", "plus",
    "plus_outline", "portrait", "portrait_and_landscape", "portrait_beside_landscape", "power",
    "question", "redo_arrow", "regenerate_corner", "release", "reset", "restart", "retract",
    "save", "scene_to_clip", "settings", "shield", "shuffle", "slideshow",
    "snowflake_struck_out", "speaker", "speaker_off", "star", "star_outline", "star_ring",
    "stop", "tag", "thumbs_up", "trash", "undo_arrow", "unlock", "versions", "vr_hemisphere",
    "warning", "wave", "wave_sawtooth", "wave_square", "wave_triangle", "working",
)


def test_the_icons_this_family_draws_are_the_ones_the_apps_ask_for():
    assert icon_names() == _THE_ICONS


def test_the_working_icon_is_the_circle_with_a_quarter_left_out():
    (ring,) = ICONS["circle"]
    (arc,) = ICONS["working"]

    assert (arc.x + arc.w / 2, arc.y + arc.h / 2) == (ring.cx, ring.cy)
    assert (arc.w / 2, arc.h / 2) == (ring.rx, ring.ry)
    assert arc.span == 270


_OSR2_CONTROL = ("park", "retract", "release", "control_off")


def _the_device(first: tuple, second: tuple) -> tuple:
    shared = []
    for one, other in zip(first, second, strict=False):
        if one != other:
            break
        shared.append(one)
    return tuple(shared)


def test_the_four_osr2_control_icons_draw_one_device():
    columns = {ICONS[name][0] for name in _OSR2_CONTROL}
    assert len(columns) == 1


def test_the_device_is_the_column_the_sleeve_and_the_arm_between_them():
    device = _the_device(ICONS["release"], ICONS["control_off"])

    assert [type(shape) for shape in device] == [RoundedRect, RoundedRect, Line]


def _the_device_of(name: str) -> tuple:
    return ICONS[name][:len(_the_device(ICONS["release"], ICONS["control_off"]))]


def _beyond_the_device(name: str) -> tuple:
    return ICONS[name][len(_the_device_of(name)):]


def test_control_off_crosses_out_what_driving_points_at():
    arrows = _beyond_the_device("release")
    crosses = _beyond_the_device("control_off")

    assert [type(shape) for shape in arrows] == [Line, Polygon, Line, Polygon]
    assert [type(shape) for shape in crosses] == [Line, Line, Line, Line]


def _sleeve_of(name: str) -> RoundedRect:
    _column, sleeve, _arm = _the_device_of(name)
    return sleeve


def _arrows_of(name: str) -> list[tuple[Line, Polygon]]:
    rest = _beyond_the_device(name)
    return list(zip(rest[::2], rest[1::2], strict=True))


def _crosses_of(name: str) -> list[tuple[Line, Line]]:
    legs = _beyond_the_device(name)
    return list(zip(legs[::2], legs[1::2], strict=True))


def test_control_off_s_crosses_stand_where_release_s_arrowheads_were():
    heads = [sorted(y for _x, y in head.points) for _stem, head in _arrows_of("release")]
    crosses = [(one.y1 + one.y2) / 2 for one, _other in _crosses_of("control_off")]

    assert all(head[0] <= cross <= head[-1] for cross, head in zip(crosses, heads, strict=True))


def test_a_cross_stays_off_the_sleeve():
    sleeve = _sleeve_of("control_off")
    upper, lower = _crosses_of("control_off")

    assert max(upper[0].y1, upper[0].y2) + upper[0].width / 2 < sleeve.y
    assert min(lower[0].y1, lower[0].y2) - lower[0].width / 2 > sleeve.y + sleeve.h


def test_a_cross_takes_most_of_the_band_between_the_sleeve_and_the_frame_s_edge():
    sleeve = _sleeve_of("control_off")
    upper, lower = _crosses_of("control_off")

    assert abs(upper[0].y2 - upper[0].y1) >= 0.6 * sleeve.y
    assert abs(lower[0].y2 - lower[0].y1) >= 0.6 * (CANVAS - sleeve.y - sleeve.h)


_WAVEFORMS = ("wave", "wave_triangle", "wave_square", "wave_sawtooth")


def test_each_waveform_is_drawn_in_the_frame_the_sine_fills():
    sine, *others = (_ink_rect(icons.icon_pixmap(name, 48, TEXT_PRIMARY)) for name in _WAVEFORMS)
    for name, frame in zip(_WAVEFORMS[1:], others, strict=True):
        assert all(abs(edge - sines) <= 1 for edge, sines in zip(frame, sine, strict=True)), name


def test_the_sawtooth_climbs_at_once_and_falls_slowly_as_the_motion_does():
    (saw,) = ICONS["wave_sawtooth"]
    segments = list(pairwise(saw.points))
    climbs = [abs(x2 - x1) for (x1, y1), (x2, y2) in segments if y2 < y1]
    falls = [abs(x2 - x1) for (x1, y1), (x2, y2) in segments if y2 > y1]
    assert climbs
    assert falls
    assert max(climbs) < min(falls)


def test_the_length_icons_are_a_clip_along_one_timeline_the_whole_way_or_only_its_start():
    full_timeline, full_clip = ICONS["full"]
    clips_timeline, clips_clip = ICONS["clips"]

    assert full_timeline == clips_timeline
    assert full_clip.x == clips_clip.x == full_timeline.x1
    assert full_clip.x + full_clip.w == full_timeline.x2
    assert clips_clip.w < full_clip.w / 3


def test_a_jump_between_a_clip_and_its_scene_keeps_the_short_clip_left_of_the_long_one():
    for name in ("clip_to_scene", "scene_to_clip"):
        short, long, *_arrow = ICONS[name]
        assert short.fill, name
        assert long.fill, name
        assert short.x + short.w < long.x, name
        assert short.w < long.w / 2, name
    assert ICONS["clip_to_scene"][:2] == ICONS["scene_to_clip"][:2]


def test_a_jump_s_arrow_is_short_and_thick_with_room_on_either_side():
    for name in ("clip_to_scene", "scene_to_clip"):
        *_clips, stem, head = ICONS[name]
        xs = [stem.x1, stem.x2, *(x for x, _y in head.points)]
        ys = [y for _x, y in head.points]
        assert stem.width >= 8, name
        assert max(ys) - min(ys) >= 20, name
        assert max(xs) - min(xs) <= 24, name
        assert min(xs) - stem.width / 2 >= 8, name
        assert max(xs) + stem.width / 2 <= 40, name


def test_latest_is_its_own_drawing_rather_than_shuffle_uncrossed():
    assert not set(ICONS["latest"]) & set(ICONS["shuffle"])


def _strokes_down_the_middle(name: str, size: int) -> list[int]:
    image = icons.icon_pixmap(name, size, TEXT_PRIMARY).toImage()
    inked = [image.pixelColor(size // 2, y).alpha() > 32 for y in range(size)]
    return [y for y in range(size) if inked[y] and (y == 0 or not inked[y - 1])]


def test_database_is_three_short_cylinders_stacked_under_one_lid():
    _lid_far_edge, lid_near_edge, *rims = _strokes_down_the_middle("database", 96)
    left, _upper, right, _lower = _ink_rect(icons.icon_pixmap("database", 96, TEXT_PRIMARY))
    heights = [lower - upper for upper, lower in pairwise([lid_near_edge, *rims])]

    assert len(rims) == 3
    assert max(heights) - min(heights) <= 1
    assert max(heights) < (right - left) / 2


def _ink_size(name: str) -> tuple[int, int]:
    left, upper, right, lower = _ink_rect(icons.icon_pixmap(name, 48, TEXT_PRIMARY))
    return right - left, lower - upper


def test_portrait_and_landscape_are_one_frame_and_its_quarter_turn():
    tall, wide = _ink_size(PORTRAIT), _ink_size(LANDSCAPE)

    assert tall[1] > tall[0]
    assert tall == wide[::-1]


def test_an_orientation_is_drawn_as_a_frame_rather_than_a_filled_block():
    for name in (PORTRAIT, LANDSCAPE, "portrait_and_landscape"):
        image = icons.icon_pixmap(name, 48, TEXT_PRIMARY).toImage()
        assert image.pixelColor(24, 24).alpha() == 0, name


def test_portrait_and_landscape_is_the_two_frames_crossed():
    assert ICONS["portrait_and_landscape"] == (*ICONS[PORTRAIT], *ICONS[LANDSCAPE])


def test_portrait_beside_landscape_is_the_same_two_frames_side_by_side():
    upright, lying_down = ICONS["portrait_beside_landscape"]
    (portrait,) = ICONS[PORTRAIT]

    assert upright.h / upright.w == pytest.approx(portrait.h / portrait.w)
    assert (lying_down.w, lying_down.h) == (upright.h, upright.w)
    assert upright.x + upright.w < lying_down.x


def test_portrait_beside_landscape_fits_the_square_of_a_button():
    left, upper, right, lower = _ink_rect(
        icons.icon_pixmap("portrait_beside_landscape", BUTTON_FILLING_ICON, TEXT_PRIMARY))

    assert min(left, upper) > 0
    assert max(right, lower) < BUTTON_FILLING_ICON - 1


def test_the_registry_is_what_icon_names_reports():
    names = icon_names()
    assert names == tuple(sorted(names))
    for name in names:
        assert icons.icon_pixmap(name, 24, TEXT_PRIMARY).size() == QSize(24, 24)


def test_icon_names_leaves_no_registered_icon_out_of_the_sweeps(monkeypatch):
    monkeypatch.setitem(ICONS, "_an_icon_added_for_the_test", ICONS["disc"])

    assert set(icon_names()) == set(ICONS)


def test_the_canvas_and_pen_width_are_public_for_a_caller_composing_an_icon_into_its_own_drawing():
    assert {"CANVAS", "PEN_WIDTH"} <= set(icons.__all__)
    assert icons.CANVAS == 48.0
    assert 0 < icons.PEN_WIDTH < icons.CANVAS


def test_an_icon_never_erases_the_ground_it_is_drawn_on():
    for name in _EVERY_ICON_AND_THE_STAND_IN:
        canvas = QPixmap(48, 48)
        canvas.fill(QColor(GREEN))
        painter = QPainter(canvas)
        icons.draw_icon(painter, name, RED)
        painter.end()
        image = canvas.toImage()
        cleared = [
            (x, y)
            for y in range(48)
            for x in range(48)
            if image.pixelColor(x, y).alpha() < 255
        ]
        assert not cleared, f"{name} cleared {len(cleared)} px of what was under it"


def _quit_at_three_quarters_size_in_the_middle_of_the_frame() -> set[tuple[int, int]]:
    canvas = _blank(48)
    painter = QPainter(canvas)
    icons.draw_icon(painter, "power", TEXT_PRIMARY, size=36, x=6, y=6)
    painter.end()
    return _ink(canvas)


def _restart_s_arrow() -> set[tuple[int, int]]:
    restart = _ink(icons.icon_pixmap("restart", 48, TEXT_PRIMARY))
    return restart - _quit_at_three_quarters_size_in_the_middle_of_the_frame()


def _distance_from_the_middle_of_the_frame(pixel: tuple[int, int]) -> float:
    x, y = pixel
    return math.hypot(x + 0.5 - 24, y + 0.5 - 24)


_DEGREES_A_SECTOR = 5


def _sector_counterclockwise_from_three_o_clock(pixel: tuple[int, int]) -> int:
    x, y = pixel
    bearing = math.degrees(math.atan2(24 - y - 0.5, x + 0.5 - 24)) % 360
    return int(bearing // _DEGREES_A_SECTOR)


def _depth_in_each_sector(ink: set[tuple[int, int]]) -> dict[int, float]:
    nearest: dict[int, float] = {}
    farthest: dict[int, float] = {}
    for pixel in ink:
        sector = _sector_counterclockwise_from_three_o_clock(pixel)
        distance = _distance_from_the_middle_of_the_frame(pixel)
        nearest[sector] = min(nearest.get(sector, distance), distance)
        farthest[sector] = max(farthest.get(sector, distance), distance)
    return {sector: farthest[sector] - nearest[sector] for sector in farthest}


def _empty_sectors(ink: set[tuple[int, int]]) -> list[int]:
    inked = {_sector_counterclockwise_from_three_o_clock(pixel) for pixel in ink}
    return [sector for sector in range(360 // _DEGREES_A_SECTOR) if sector not in inked]


def test_restart_carries_quit_at_three_quarters_size_in_its_middle():
    restart = _ink(icons.icon_pixmap("restart", 48, TEXT_PRIMARY))

    assert _quit_at_three_quarters_size_in_the_middle_of_the_frame() <= restart


def test_restart_s_arrow_runs_wholly_outside_the_quit_in_its_middle():
    small_quit = _quit_at_three_quarters_size_in_the_middle_of_the_frame()

    nearest_of_the_arrow = min(map(_distance_from_the_middle_of_the_frame, _restart_s_arrow()))
    farthest_of_the_quit = max(map(_distance_from_the_middle_of_the_frame, small_quit))
    assert nearest_of_the_arrow > farthest_of_the_quit


def test_restart_s_arrow_is_more_than_twice_as_deep_at_its_head_as_along_its_ring():
    depths = sorted(_depth_in_each_sector(_restart_s_arrow()).values())

    along_the_ring = depths[len(depths) // 2]
    assert depths[-1] > 2 * along_the_ring


def test_restart_s_arrow_leaves_its_gap_straight_over_the_bar_of_the_quit_inside():
    gap = _empty_sectors(_restart_s_arrow())

    assert gap == list(range(gap[0], gap[-1] + 1))
    middle_of_the_gap = (gap[0] + gap[-1] + 1) / 2 * _DEGREES_A_SECTOR
    assert abs(middle_of_the_gap - 90) <= _DEGREES_A_SECTOR


def test_restart_s_arrow_runs_counterclockwise_into_its_head_on_the_right_of_the_gap():
    arrow = _restart_s_arrow()
    depths = _depth_in_each_sector(arrow)
    gap = _empty_sectors(arrow)

    head = max(depths, key=depths.get)
    assert gap[0] - 60 // _DEGREES_A_SECTOR <= head < gap[0]


def test_a_menu_row_s_restart_keeps_its_arrow_apart_from_the_quit_inside_it():
    quit_icon = _solid_ink(_as_a_menu_row_shows("power"))
    restart = _solid_ink(_as_a_menu_row_shows("restart"))

    assert _pieces(restart) == _pieces(quit_icon) + 1


def test_the_enhance_filter_reads_as_one_sign_rather_than_two_controls_crowded_together():
    icon = _ink(icons.icon_pixmap("enhance_filter", 48, TEXT_PRIMARY))
    assert _pieces(icon) == 1

    assert any(x <= 8 for x, _y in icon), "the plus's arm is missing"
    assert any(y >= 42 for _x, y in icon), "the funnel's stem is missing"


def test_the_rounded_play_carries_more_weight_than_one_with_hard_points(monkeypatch):
    (triangle,) = ICONS["play"]
    _drawn_by_the_public_route(monkeypatch, "_play_with_hard_points", (Polygon(triangle.points),))

    rounded = _ink_pixels(icons.icon_pixmap("play", 48, TEXT_PRIMARY))
    bare = _ink_pixels(icons.icon_pixmap("_play_with_hard_points", 48, TEXT_PRIMARY))
    assert rounded > bare


def test_a_rounded_polygon_s_points_are_round_rather_than_cut_flat():
    (triangle,) = ICONS["play"]
    tip = max(x for x, _y in triangle.points)

    _left, _upper, right, _lower = _ink_rect(icons.icon_pixmap("play", 2 * 48, TEXT_PRIMARY))

    assert right >= 2 * (tip + triangle.round_radius) - 1
    assert right <= 2 * (tip + triangle.round_radius)


def test_the_play_triangle_is_placed_by_its_weight_so_its_box_leans_right():
    (triangle,) = ICONS["play"]
    centroid = sum(x for x, _y in triangle.points) / len(triangle.points)
    left, _upper, right, _lower = _ink_rect(icons.icon_pixmap("play", 48, TEXT_PRIMARY))

    assert abs(centroid - 24) <= 1
    assert (left + right) / 2 > 24 + 2


def test_an_icon_this_version_does_not_have_is_drawn_as_the_stand_in(monkeypatch):
    _drawn_by_the_public_route(monkeypatch, "_the_stand_in", STAND_IN)
    stand_in = icons.icon_pixmap("_the_stand_in", 48, TEXT_PRIMARY).toImage()

    drawn = icons.icon_pixmap(_AN_ICON_THIS_VERSION_LACKS, 48, TEXT_PRIMARY).toImage()

    assert drawn == stand_in


def test_the_stand_in_wears_its_button_s_color_and_is_gray_only_when_the_button_is_disabled():
    on_the_square_s_left_edge = (4, 24)
    icon = icons.qt_icon(_AN_ICON_THIS_VERSION_LACKS, color=RED)

    normal = icon.pixmap(QSize(48, 48), QIcon.Mode.Normal).toImage()
    disabled = icon.pixmap(QSize(48, 48), QIcon.Mode.Disabled).toImage()

    assert normal.pixelColor(*on_the_square_s_left_edge) == RED
    assert disabled.pixelColor(*on_the_square_s_left_edge) == TEXT_MUTED


def test_each_icon_this_version_does_not_have_is_named_in_the_log_once(caplog):
    first, second = (f"an_icon_first_asked_for_{uuid.uuid4().hex}" for _ in range(2))

    with caplog.at_level(logging.WARNING):
        for name in (first, second, first, second, first):
            icons.icon_pixmap(name, 24, TEXT_PRIMARY)

    for name in (first, second):
        naming_it = [record.levelno for record in caplog.records if name in record.getMessage()]
        assert naming_it == [logging.WARNING], name


def test_a_bar_ends_in_a_round_cap_that_reaches_past_its_endpoint():
    (bar,) = ICONS["minus"]
    left, _upper, right, _lower = _ink_rect(icons.icon_pixmap("minus", 48, TEXT_PRIMARY))
    assert left <= bar.x1 - bar.width / 2 + 1
    assert right >= bar.x2 + bar.width / 2 - 1


def test_a_bar_s_cap_is_round_so_its_corner_is_clear_where_a_square_cap_inks_it():
    (bar,) = ICONS["minus"]
    image = icons.icon_pixmap("minus", 2 * 48, TEXT_PRIMARY).toImage()
    half = bar.width / 2
    corner = (int(2 * (bar.x1 - half)) + 1, int(2 * (bar.y1 - half)) + 1)
    middle_of_the_cap = (int(2 * (bar.x1 - half)), int(2 * bar.y1))

    assert image.pixelColor(*corner).alpha() < 32
    assert image.pixelColor(*middle_of_the_cap).alpha() > 200


def test_two_bars_meet_in_a_round_join_reaching_past_a_bevel_and_short_of_a_miter():
    (check,) = ICONS["check"]
    _first, corner, _last = check.points
    image = icons.icon_pixmap("check", 2 * 48, TEXT_PRIMARY).toImage()
    x, y = int(2 * corner[0]), int(2 * corner[1])

    assert image.pixelColor(x, y + 4).alpha() > 200
    assert image.pixelColor(x, y + 7).alpha() < 32


def test_a_path_written_in_a_frame_of_its_own_fills_the_canvas_that_frame_stands_for(monkeypatch):
    square = Path((("M", 0, 0), ("L", 24, 0), ("L", 24, 24), ("L", 0, 24), ("Z",)), frame=24.0)
    _drawn_by_the_public_route(monkeypatch, "_a_square_in_a_frame_of_24", (square,))

    drawn = icons.icon_pixmap("_a_square_in_a_frame_of_24", 48, TEXT_PRIMARY)

    assert _ink_rect(drawn) == (0, 0, 47, 47)


def test_a_corner_icon_keeps_to_the_corner_its_icon_leaves_free():
    for name in _IN_A_CORNER:
        left, upper, _right, _lower = _ink_rect(icons.icon_pixmap(name, 48, TEXT_PRIMARY))
        assert left >= 24, f"{name} reaches out of the lower right"
        assert upper >= 24, f"{name} reaches out of the lower right"


def _rendered_label(text: str) -> QImage:
    label = QLabel()
    label.setStyleSheet("background: black; color: white;")
    label.setText(text)
    label.resize(200, 30)
    return label.grab().toImage()


@pytest.mark.usefixtures("qapp")
def test_a_line_of_text_can_lead_with_an_icon_drawn_in_its_ink():
    def reds(image) -> list[int]:
        return [x for y in range(image.height()) for x in range(image.width())
                if image.pixelColor(x, y).red() > 150 and image.pixelColor(x, y).green() < 120]

    led = reds(_rendered_label(icons.icon_then_text("mic", "heard it", color=RED, size=16)))

    assert led, "the icon leads the line"
    assert max(led) < 20, "the icon leads the line"


@pytest.mark.usefixtures("qapp")
def test_an_icon_set_among_the_words_is_the_lines_own_icon_alone():
    icon = icons.inline_icon("check", color=RED, size=16)

    assert icon.startswith("<img")
    assert icons.icon_then_text("check", "x", color=RED, size=16) == (
        icon + "&nbsp;x")


@pytest.mark.usefixtures("qapp")
def test_a_line_led_by_an_icon_shows_its_words_as_they_were_written():
    line = icons.icon_then_text("mic", "1 < 2 & <b>bold</b>", color=RED, size=16)

    assert "1 &lt; 2 &amp; &lt;b&gt;bold&lt;/b&gt;" in line


def _of(name: str, kind: type) -> list:
    return [shape for shape in ICONS[name] if isinstance(shape, kind)]


def _cells(name: str) -> list:
    return [shape for shape in _of(name, RoundedRect) if shape.fill]


def _rows(cells) -> list[int]:
    by_row: dict[float, int] = {}
    for cell in cells:
        by_row[round(cell.y, 3)] = by_row.get(round(cell.y, 3), 0) + 1
    return [by_row[top] for top in sorted(by_row)]


def test_the_grid_is_a_frame_packed_with_rows_of_little_squares():
    [frame] = [shape for shape in _of("grid", RoundedRect) if not shape.fill]
    cells = _cells("grid")
    edge = frame.width / 2

    rows = _rows(cells)
    assert len(rows) >= 3
    assert rows == [len(rows)] * len(rows)
    assert all(frame.x + edge < cell.x and cell.x + cell.w < frame.x + frame.w - edge
               and frame.y + edge < cell.y and cell.y + cell.h < frame.y + frame.h - edge for cell in cells)


def _inside_the_ring(cell, ring) -> bool:
    corners = [(cell.x + dx, cell.y + dy) for dx in (0, cell.w) for dy in (0, cell.h)]
    return all(math.dist(corner, (ring.cx, ring.cy)) < ring.rx - ring.width / 2 for corner in corners)


def test_the_cells_in_a_circle_are_a_puzzle_piece_of_little_squares_in_the_no_flakes_ring():
    [ring] = _of("cells_in_circle", Ellipse)
    [no_flakes] = _of("snowflake_struck_out", Ellipse)
    cells = _cells("cells_in_circle")

    assert (ring.cx, ring.cy, ring.rx) == (no_flakes.cx, no_flakes.cy, no_flakes.rx)
    assert _rows(cells) == [2, 5, 2]
    assert all(_inside_the_ring(cell, ring) for cell in cells)


def test_the_pair_in_a_circle_is_two_little_squares_side_by_side_in_that_ring():
    [ring] = _of("pair_in_circle", Ellipse)
    [no_flakes] = _of("snowflake_struck_out", Ellipse)
    cells = _cells("pair_in_circle")

    assert (ring.cx, ring.cy, ring.rx) == (no_flakes.cx, no_flakes.cy, no_flakes.rx)
    assert _rows(cells) == [2]
    assert all(_inside_the_ring(cell, ring) for cell in cells)
    assert cells[1].x - cells[0].x > cells[0].w


def test_the_struck_out_snowflake_is_a_six_armed_flake_in_a_ring_with_a_slash_across_it():
    [ring] = _of("snowflake_struck_out", Ellipse)
    lines = _of("snowflake_struck_out", Line)
    slash = max(lines, key=lambda line: line.width)
    arms = [line for line in lines if line is not slash]
    a_snowflakes_arms = 6

    assert slash.x1 < ring.cx < slash.x2
    assert slash.y1 < ring.cy < slash.y2
    assert len(arms) >= a_snowflakes_arms
    assert all(math.dist(end, (ring.cx, ring.cy)) < ring.rx
               for arm in arms for end in ((arm.x1, arm.y1), (arm.x2, arm.y2)))


def _outline(piece: Path) -> list[tuple[float, float]]:
    scale = icons.CANVAS / piece.frame
    here, points = None, []
    for command, *numbers in piece.commands:
        if command == "M":
            here = (numbers[0] * scale, numbers[1] * scale)
        elif command == "C":
            handles = [(numbers[n] * scale, numbers[n + 1] * scale) for n in (0, 2, 4)]
            points += [tuple((1 - s) ** 3 * p0 + 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s ** 2 * p2
                             + s ** 3 * p3 for p0, p1, p2, p3 in zip(here, *handles, strict=True))
                       for s in (step / 200 for step in range(201))]
            here = handles[-1]
    return points


def _height_across(points, x: float, half_a_slice: float = 0.2) -> float:
    near = [py for px, py in points if abs(px - x) < half_a_slice]
    return max(near) - min(near)


def test_the_jigsaw_is_a_piece_tabbed_left_and_right_and_blanked_above_and_below_in_the_grids_frame():
    [frame] = _of("jigsaw", RoundedRect)
    [piece] = _of("jigsaw", Path)
    outline = _outline(piece)
    xs, ys = [x for x, _ in outline], [y for _, y in outline]
    middle = icons.CANVAS / 2
    side = 11 * (icons.CANVAS - 6) / 26
    half = side / 2

    assert frame == next(shape for shape in _of("grid", RoundedRect) if not shape.fill)
    assert frame.x + frame.width / 2 < min(xs) < max(xs) < frame.x + frame.w - frame.width / 2
    assert frame.y + frame.width / 2 < min(ys) < max(ys) < frame.y + frame.h - frame.width / 2
    for tip, outward in ((min(outline), -1), (max(outline), 1)):
        assert abs(tip[1] - middle) < side / 10
        assert abs(tip[0] - middle) - half > side / 4
        tab = [(x, y) for x, y in outline if outward * (x - middle) > half]
        neck = _height_across(tab, middle + outward * (half + side / 40))
        head = max(_height_across(tab, middle + outward * (half + side * n / 40)) for n in range(2, 10))
        assert head > neck * 1.3
    across_the_middle = [y for x, y in outline if abs(x - middle) < side / 20]
    assert min(across_the_middle) - (middle - half) > side / 4
    assert (middle + half) - max(across_the_middle) > side / 4


def test_the_copy_s_back_sheet_breaks_off_where_the_front_sheet_lies_over_it():
    image = icons.icon_pixmap("copy", 48, TEXT_PRIMARY).toImage()
    [front] = _of("copy", RoundedRect)
    back_sheet_s_left_edge = min(line.x1 for line in _of("copy", Line))
    back_sheet_s_lower_edge = max(line.y1 for line in _of("copy", Line))

    inside_the_front_sheet = ((int(back_sheet_s_left_edge), int(front.y + front.h / 2)),
                              (int(front.x + front.w / 2), int(back_sheet_s_lower_edge)))
    assert all(image.pixelColor(*point).alpha() < 32 for point in inside_the_front_sheet)


def test_the_star_ring_shows_as_a_rim_all_round_a_favorited_star_drawn_over_it():
    canvas = _blank(48)
    painter = QPainter(canvas)
    icons.draw_icon(painter, "star_ring", RED)
    icons.draw_icon(painter, "star", GREEN)
    painter.end()
    rim = {(x, y) for x, y in _ink(canvas) if canvas.toImage().pixelColor(x, y).red() > 200}
    star = _ink_rect(icons.icon_pixmap("star", 48, TEXT_PRIMARY))

    left, upper, right, lower = _ink_rect_of(rim)
    assert left < star[0]
    assert upper < star[1]
    assert right > star[2]
    assert lower > star[3]


def test_an_up_or_down_chevron_is_the_left_or_right_one_turned_a_quarter():
    def turned(name: str) -> set[tuple[float, float]]:
        (chevron,) = ICONS[name]
        return {(y, x) for x, y in chevron.points}

    assert set(ICONS["chevron_up"][0].points) == turned("chevron_left")
    assert set(ICONS["chevron_down"][0].points) == turned("chevron_right")


def test_a_qt_icon_is_drawn_at_the_whole_canvas_for_qt_to_scale_down_crisp():
    [drawn] = icons.qt_icon("mic").availableSizes()

    assert drawn.width() == drawn.height() == CANVAS > max(BUTTON_ICON, BUTTON_FILLING_ICON)


def test_loop_is_two_arrows_chasing_round_a_circuit_rather_than_one_ring():
    heads = _of("loop", Polygon)
    arcs = _of("loop", Arc)

    assert len(heads) == 2
    assert all(arc.span < 180 for arc in arcs)


def test_reset_is_neither_a_bare_gear_nor_a_bare_circular_arrow_but_both():
    rim, _bore = _of("reset", Ellipse)
    teeth = _of("reset", Line)
    [arrow] = _of("reset", Arc)
    [head] = _of("reset", Polygon)

    assert len(teeth) == 8
    assert (arrow.x + arrow.w / 2, arrow.y + arrow.h / 2) > (rim.cx, rim.cy)
    assert max(x for x, _y in head.points) > rim.cx + rim.rx


def test_compilation_is_a_stack_of_three_sheets_where_copy_is_two():
    sheets = _of("compilation", RoundedRect)

    assert len(sheets) == 3
    assert all((sheets[n + 1].x - sheets[n].x, sheets[n + 1].y - sheets[n].y) == (sheets[1].x - sheets[0].x, sheets[1].y - sheets[0].y)
               for n in range(2))


def test_the_headset_is_the_thing_itself_a_visor_with_two_lenses_and_a_strap_either_side():
    [visor] = _of("headset", RoundedRect)
    lenses = _of("headset", Ellipse)
    straps = _of("headset", Line)

    assert [lens.fill for lens in lenses] == [True, True]
    assert len(straps) == 2
    assert min(strap.x1 for strap in straps) < visor.x
    assert max(strap.x2 for strap in straps) > visor.x + visor.w


def test_the_monitor_is_a_screen_on_a_stem_and_a_foot_not_a_headset_struck_out():
    [screen] = _of("monitor", RoundedRect)
    stem, foot = _of("monitor", Line)

    assert not set(ICONS["monitor"]) & set(ICONS["headset"])
    assert stem.x1 == stem.x2
    assert screen.y + screen.h <= stem.y1 < stem.y2 <= foot.y1 == foot.y2


def test_the_flat_screen_leans_where_square_on_it_would_be_a_plain_rectangle_beside_the_dome():
    [frame] = _of("flat_2d", Polygon)
    (left_top, _right_top, _right_low, left_low) = frame.points

    assert left_top[0] != left_low[0]


def test_versions_leans_and_carries_the_swap_arrow_where_copy_stands_square():
    sheets = _of("versions", RoundedRect)
    [swap_line] = _of("versions", Line)
    heads = _of("versions", Polygon)

    assert sheets[0].x != sheets[1].x
    assert sheets[0].y != sheets[1].y
    assert len(heads) == 2
    assert swap_line.x1 != swap_line.x2
    assert swap_line.y1 != swap_line.y2
    assert not _of("copy", Polygon)


def test_funscript_jump_is_an_arrow_running_into_the_f():
    [head] = _of("funscript_jump", Polygon)
    stem, *the_f = _of("funscript_jump", Line)

    assert len(the_f) == 3
    assert max(x for x, _y in head.points) <= min(min(bar.x1, bar.x2) for bar in the_f)
    assert stem.x2 > stem.x1


def test_expand_horizontal_is_as_chunky_as_the_transport_controls_beside_it():
    [bar] = _of("expand_horizontal", Line)
    heads = _of("expand_horizontal", Polygon)

    assert bar.width >= PEN_WIDTH
    assert [head.fill for head in heads] == [True, True]


def test_the_warning_is_a_bar_and_a_dot_under_a_raised_triangles_point():
    [triangle] = _of("warning", Polygon)
    [bar] = _of("warning", Line)
    [dot] = _of("warning", Ellipse)
    point, right, left = triangle.points

    assert point[1] < left[1] == right[1]
    assert bar.x1 == bar.x2 == dot.cx == point[0]
    assert point[1] < bar.y1 < bar.y2 < dot.cy < left[1]


def test_an_icon_drawn_to_fill_a_box_reaches_it_along_one_side_and_sits_in_its_middle():
    canvas = QPixmap(120, 60)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    icons.draw_icon_filling(painter, "question", TEXT_PRIMARY, QRectF(0, 0, 120, 60))
    painter.end()

    left, top, right, bottom = _ink_rect(canvas)
    assert bottom - top >= 56
    assert abs((left + right) / 2 - 60) <= 1.5
    assert abs((top + bottom) / 2 - 30) <= 1.5


def test_a_history_arrow_s_head_is_far_deeper_than_its_ring():
    for name in ("undo_arrow", "redo_arrow"):
        depths = sorted(_depth_in_each_sector(_ink(icons.icon_pixmap(name, 48, TEXT_PRIMARY))).values())
        along_the_ring = depths[len(depths) // 2]
        assert depths[-1] > 2 * along_the_ring, name


def test_a_history_arrow_s_ring_stops_short_of_its_head_leaving_open_space():
    for name in ("undo_arrow", "redo_arrow"):
        gap = _empty_sectors(_ink(icons.icon_pixmap(name, 48, TEXT_PRIMARY)))
        assert len(gap) * _DEGREES_A_SECTOR >= 15, name


def test_the_two_history_icons_are_one_drawing_mirrored_about_the_center_line():
    forward_ring, forward_head = ICONS["redo_arrow"]
    back_ring, back_head = ICONS["undo_arrow"]

    assert (forward_ring.x + forward_ring.w, forward_ring.y) == (CANVAS - back_ring.x, back_ring.y)
    assert (180 - forward_ring.start - forward_ring.span) % 360 == back_ring.start
    assert forward_ring.span == back_ring.span
    assert {(CANVAS - x, y) for x, y in forward_head.points} == set(back_head.points)


def test_the_shuffles_two_lines_are_drawn_under_the_default_pen():
    assert all(shape.width < PEN_WIDTH for shape in ICONS["shuffle"] if isinstance(shape, Line))


def _solid_runs(image: QImage, row: int) -> int:
    inked = [image.pixelColor(x, row).alpha() > 127 for x in range(image.width())]
    return sum(1 for x, is_inked in enumerate(inked) if is_inked and (x == 0 or not inked[x - 1]))


def test_the_shuffle_s_lines_are_still_told_apart_a_step_before_they_cross_at_a_hud_button_s_size():
    image = icons.icon_pixmap("shuffle", BUTTON_SIZE_HUD, TEXT_PRIMARY).toImage()
    a_step_before_the_crossing = BUTTON_SIZE_HUD // 2 - 2

    assert _solid_runs(image, a_step_before_the_crossing) == 2


def test_the_star_outline_s_points_stay_open_rather_than_closing_up():
    image = icons.icon_pixmap("star_outline", 48, TEXT_PRIMARY).toImage()
    (star,) = ICONS["star_outline"]
    top = min(y for _x, y in star.points)

    inside_the_top_point = (24, int(top) + 8)
    assert image.pixelColor(*inside_the_top_point).alpha() < 32


def test_the_hollow_plus_s_middle_reads_empty_at_a_badge_s_size():
    image = icons.icon_pixmap("plus_outline", BUTTON_ICON, TEXT_PRIMARY).toImage()
    middle = BUTTON_ICON // 2

    assert image.pixelColor(middle, middle).alpha() < 32


def test_the_hollow_plus_s_square_tips_land_within_a_pixel_of_the_solid_s_caps_at_a_badge_s_size():
    solid = _ink_rect(icons.icon_pixmap("plus", BUTTON_ICON, TEXT_PRIMARY))
    hollow = _ink_rect(icons.icon_pixmap("plus_outline", BUTTON_ICON, TEXT_PRIMARY))

    assert all(abs(edge - twin) <= 1 for edge, twin in zip(solid, hollow, strict=True))


@pytest.mark.usefixtures("qapp")
def test_an_icon_among_the_words_is_drawn_at_twice_its_size_to_stay_crisp_on_a_screen_that_scales_the_label_up():
    written = re.search(r'base64,([^"]+)"', icons.inline_icon("check", color=RED, size=16)).group(1)

    drawn = QImage.fromData(base64.b64decode(written))

    assert (drawn.width(), drawn.height()) == (32, 32)
