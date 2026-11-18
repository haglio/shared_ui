from __future__ import annotations

from types import MappingProxyType

from shared_ui.palette import GREEN, RED, TEXT_PRIMARY, YELLOW, Rgb
from shared_ui.spacing import BUTTON_RADIUS, MARGIN_DIALOG, MARGIN_STANDARD
from shared_ui.type_scale import SIZE_HEADING

MESSAGE_TYPE_SIZE = SIZE_HEADING
MESSAGE_PAD_V = MARGIN_STANDARD
MESSAGE_PAD_H = MARGIN_DIALOG
MESSAGE_RADIUS = BUTTON_RADIUS
MESSAGE_TOP_MARGIN = MARGIN_DIALOG

INFO = "info"
WARNING = "warning"
ERROR = "error"
FAVORITE = "favorite"
MESSAGE_INK: MappingProxyType[str, Rgb] = MappingProxyType(
    {INFO: TEXT_PRIMARY, WARNING: YELLOW, ERROR: RED, FAVORITE: GREEN})

HEARD_MARK = "mic"


def time_to_read_ms(text: str) -> int:
    return max(3000, 1500 + 250 * len(text.split()))
