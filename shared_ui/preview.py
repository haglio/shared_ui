from __future__ import annotations

import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from app_support.subprocess_utils import hidden_subprocess_kwargs

_GIVE_UP_ON_GIT_AFTER_SECONDS = 5
_LONGEST_FEATURE = 60


@dataclass(frozen=True)
class Preview:
    feature: str | None


@cache
def preview_of(checkout: Path) -> Preview | None:
    if not (checkout / ".git").is_file():
        return None
    return Preview(feature=_feature_described_on_the_branch_of(checkout))


def _feature_described_on_the_branch_of(checkout: Path) -> str | None:
    branch = _git(checkout, "branch", "--show-current")
    description = _git(checkout, "config", "--get", f"branch.{branch}.description")
    return description.splitlines()[0] if description else None


def _git(checkout: Path, *args: str) -> str:
    try:
        done = subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True,
                              check=False, timeout=_GIVE_UP_ON_GIT_AFTER_SECONDS,
                              **hidden_subprocess_kwargs())
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout.strip()


def window_title(app_name: str, preview: Preview | None) -> str:
    if preview is None:
        return app_name
    if preview.feature is None:
        return f"{app_name} — preview"
    return f"{app_name} — preview of {_cut_to_fit(preview.feature)}"


def _cut_to_fit(feature: str) -> str:
    if len(feature) <= _LONGEST_FEATURE:
        return feature
    last_word_that_fits = feature.rfind(" ", 0, _LONGEST_FEATURE)
    if last_word_that_fits <= 0:
        last_word_that_fits = _LONGEST_FEATURE - 1
    return feature[:last_word_that_fits] + "…"


def taskbar_identity(live: str, preview: Preview | None) -> str:
    if preview is None:
        return live
    return f"{live}.Preview"
