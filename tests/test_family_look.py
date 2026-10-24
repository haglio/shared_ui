"""shared_ui's own widgets wear the look it gives every app: its steps, none of their own."""
from __future__ import annotations

from pathlib import Path

from shared_ui.look_guard import assert_the_look_is_shared_uis

_CHECKOUT = Path(__file__).resolve().parents[1]
_WHERE_THE_LOOK_IS_DEFINED = {"palette.py", "spacing.py", "type_scale.py", "fonts.py", "icon_geometry.py",
                              "app_icon.py", "toggle_geometry.py", "look_guard.py"}


def test_everything_shared_uis_own_widgets_draw_with_comes_from_its_own_set():
    modules = [path for path in sorted((_CHECKOUT / "shared_ui").glob("*.py"))
               if path.name not in _WHERE_THE_LOOK_IS_DEFINED]
    assert_the_look_is_shared_uis(_CHECKOUT, modules)
