"""An app's loading screen taking over from the one its launcher showed from the
click, and leaving the pictures the launcher shows at the next."""

from __future__ import annotations

import io
import os
from collections.abc import Mapping
from dataclasses import replace

from app_support import loading_screen

from shared_ui.loading_panel import LoadingPanel, bar_box, render


class TakingOver:
    def __init__(self, place: loading_screen.MeetingPlace | None) -> None:
        self._place = place
        self._shown = place.standing() if place is not None else None

    @classmethod
    def from_the_launcher(cls, environment: Mapping[str, str] = os.environ) -> TakingOver:
        return cls(loading_screen.meeting_place(environment))

    @property
    def _standing_at(self) -> tuple[int, int] | None:
        return None if self._shown is None else (self._shown.left, self._shown.top)

    def panel_for(self, size: tuple[int, int]) -> tuple[int, int] | None:
        app = None if self._place is None else self._place.where_the_app_comes_up()
        if app is None or (screens := loading_screen.screens()) is None:
            return self._standing_at
        return loading_screen.on_the_apps_monitor(size, screens, app, panel_at=self._standing_at).panel_on_screen

    def carried(self, fraction: float) -> float:
        start = 0.0 if self._shown is None else self._shown.fraction
        return start + (1 - start) * fraction

    def done(self, panel: LoadingPanel, *, covers_every_monitor: bool) -> None:
        if self._place is None:
            return
        self._place.say_taken()
        opening = replace(panel, fraction=0.0)
        self._place.leave_pictures(
            opening=_png(opening), full=_png(replace(opening, fraction=1.0)),
            updating=[_png(replace(opening, status=line)) for line in self._place.lines],
            bar=bar_box(), covers_every_monitor=covers_every_monitor)


def _png(panel: LoadingPanel) -> bytes:
    written = io.BytesIO()
    render(panel).save(written, format="PNG")
    return written.getvalue()
