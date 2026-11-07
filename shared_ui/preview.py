from __future__ import annotations

import json
import os
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
    return Preview(feature=_name_of_the_claude_session_working_in(checkout)
                   or _name_the_branch_gives(checkout))


def _name_of_the_claude_session_working_in(checkout: Path) -> str | None:
    newest = max(_claude_sessions_working_in(checkout), key=lambda session: session[0], default=None)
    return newest[1] if newest else None


def _claude_sessions_working_in(checkout: Path) -> Iterator[tuple[float, str]]:
    here = _same_folder_key(checkout)
    for record in _claude_desktop_session_records():
        try:
            session = json.loads(record.read_text(encoding="utf-8"))
            folder = session.get("worktreePath") or session.get("cwd")
            title = session.get("title")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(folder, str) and isinstance(title, str) and title.strip() and _same_folder_key(folder) == here:
            last_active = session.get("lastActivityAt")
            yield (last_active if isinstance(last_active, (int, float)) else 0), title.strip()


def _same_folder_key(folder: Path | str) -> str:
    return os.path.normcase(os.path.normpath(str(folder)))


def _claude_desktop_session_records() -> Iterator[Path]:
    local = os.environ.get("LOCALAPPDATA")
    places = [Path(base) for base in (os.environ.get("APPDATA"), local) if base]
    if local:
        places += [cache / kind for cache in Path(local).glob("Packages/Claude_*/LocalCache")
                   for kind in ("Roaming", "Local")]
    for place in places:
        yield from place.glob("Claude*/claude-code-sessions/*/*/*.json")


def _name_the_branch_gives(checkout: Path) -> str:
    branches = list(_branches_the_checkout_stands_on(checkout))
    for branch in branches:
        description = _git(checkout, "config", "--get", f"branch.{branch}.description")
        if description:
            return description.splitlines()[0]
    return branches[0] if branches else checkout.name


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
