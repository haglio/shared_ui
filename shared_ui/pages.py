"""A page -- HTML, a style sheet, a script -- names the family's look and gets it spelled.

``__PALETTE_<NAME>__`` is that color's ``#rrggbb``, ``__TYPE_<NAME>__`` the face or a size
in pixels, ``__SPACING_<NAME>__`` that spacing in pixels.
"""

from __future__ import annotations

import re

from shared_ui import palette, spacing, type_scale

_NAMED = re.compile(r"__(PALETTE|TYPE|SPACING)_([A-Z_]+?)__")


def with_family_look(page: str) -> str:
    return _NAMED.sub(_spelled, page)


def _spelled(named: re.Match[str]) -> str:
    kind, name = named.groups()
    if kind == "PALETTE":
        return palette.as_hex(vars(palette)[name])
    if kind == "SPACING":
        return f"{vars(spacing)[name]}px"
    value = vars(type_scale)[name]
    return value if isinstance(value, str) else f"{type_scale.in_pixels(value)}px"
