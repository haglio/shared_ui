from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from app_support.subprocess_utils import hidden_subprocess_kwargs

_GIVE_UP_ON_GIT_AFTER_SECONDS = 5
_LONGEST_FEATURE = 60
_WHERE_EACH_KIND_OF_REBASE_NAMES_ITS_BRANCH = ("--git-path", "rebase-merge/head-name",
                                               "--git-path", "rebase-apply/head-name")


@dataclass(frozen=True)
class Preview:
    feature: str | None


@cache
def preview_of(checkout: Path) -> Preview | None:
    if not (checkout / ".git").is_file():
        return None
    return Preview(feature=_feature_described_on_the_branch_of(checkout))


def _feature_described_on_the_branch_of(checkout: Path) -> str | None:
    for branch in _branches_the_checkout_stands_on(checkout):
        description = _git(checkout, "config", "--get", f"branch.{branch}.description")
        if description:
            return description.splitlines()[0]
    return None


def _branches_the_checkout_stands_on(checkout: Path) -> Iterator[str]:
    current = _git(checkout, "branch", "--show-current")
    if current:
        yield current
        return
    yield from _branches_a_rebase_under_way_returns_to(checkout)
    yield from _git(checkout, "branch", "--points-at", "HEAD", "--format=%(refname:short)").splitlines()


def _branches_a_rebase_under_way_returns_to(checkout: Path) -> Iterator[str]:
    answer = _git(checkout, "rev-parse", *_WHERE_EACH_KIND_OF_REBASE_NAMES_ITS_BRANCH)
    for where_git_keeps_the_name in answer.splitlines():
        try:
            ref = (checkout / where_git_keeps_the_name).read_text(encoding="utf-8")
        except OSError:
            continue
        yield ref.strip().removeprefix("refs/heads/")


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


def inked_icon_file(source: Path, preview: Preview | None, folder: Path,
                    write_in_preview_ink: Callable[[Path, Path], None]) -> Path:
    if preview is None:
        return source
    inked = folder / f"preview_{source.name}"
    if not inked.exists() or inked.stat().st_mtime < source.stat().st_mtime:
        folder.mkdir(parents=True, exist_ok=True)
        write_in_preview_ink(source, inked)
    return inked
