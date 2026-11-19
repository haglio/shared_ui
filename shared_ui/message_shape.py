from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
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

_ANSWERING_WHAT_HE_SAID: ContextVar[bool] = ContextVar("answering_what_he_said", default=False)


@contextmanager
def answering_what_he_said() -> Iterator[None]:
    token = _ANSWERING_WHAT_HE_SAID.set(True)
    try:
        yield
    finally:
        _ANSWERING_WHAT_HE_SAID.reset(token)


def is_answering_what_he_said() -> bool:
    return _ANSWERING_WHAT_HE_SAID.get()


def mark_of_a_message_said_now(mark: str = "") -> str:
    return mark or (HEARD_MARK if is_answering_what_he_said() else "")


def time_to_read_ms(text: str) -> int:
    return max(3000, 1500 + 250 * len(text.split()))
