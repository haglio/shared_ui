from __future__ import annotations

import ctypes
import sys
from functools import lru_cache

from shared_ui.type_scale import SIZE_SMALL, in_pixels

__all__ = ["body_text_pixels"]

_SPI_GETNONCLIENTMETRICS = 0x29


class _LogFont(ctypes.Structure):
    _fields_ = [("height", ctypes.c_long), ("rest", ctypes.c_long * 4), ("flags", ctypes.c_byte * 8),
                ("face", ctypes.c_wchar * 32)]


class _NonClientMetrics(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint), ("sizes", ctypes.c_int * 5), ("caption", _LogFont),
                ("small_sizes", ctypes.c_int * 2), ("small_caption", _LogFont),
                ("menu_sizes", ctypes.c_int * 2), ("menu", _LogFont), ("status", _LogFont),
                ("message", _LogFont), ("padded_border", ctypes.c_int)]


@lru_cache(maxsize=1)
def body_text_pixels() -> int:
    if sys.platform != "win32":
        return in_pixels(SIZE_SMALL)
    metrics = _NonClientMetrics()
    metrics.size = ctypes.sizeof(metrics)
    if not ctypes.windll.user32.SystemParametersInfoW(_SPI_GETNONCLIENTMETRICS, metrics.size,
                                                      ctypes.byref(metrics), 0):
        return in_pixels(SIZE_SMALL)
    return abs(metrics.message.height)
