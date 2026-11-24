from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from app_support.subprocess_utils import hidden_subprocess_kwargs

from shared_ui.claude_desktop_sessions import session_records

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


@dataclass(frozen=True)
class _ClaudeSession:
    title: str
    last_active: float
    on_the_checkouts_branch: bool


def _name_of_the_claude_session_working_in(checkout: Path) -> str | None:
    sessions = _claude_sessions_working_in(checkout, set(_branches_the_checkout_stands_on(checkout)))
    on_its_branch = [session for session in sessions if session.on_the_checkouts_branch]
    if on_its_branch:
        return max(on_its_branch, key=lambda session: session.last_active).title
    return sessions[0].title if len(sessions) == 1 else None


def _claude_sessions_working_in(checkout: Path, branches: set[str]) -> list[_ClaudeSession]:
    here = _same_folder_key(checkout)
    found: dict[object, _ClaudeSession] = {}
    for record in session_records():
        try:
            session = json.loads(record.read_text(encoding="utf-8"))
            folder = session.get("worktreePath") or session.get("cwd")
            title = session.get("title")
            branch = session.get("branch")
        except (OSError, ValueError, AttributeError):
            continue
        if (not isinstance(folder, str) or not isinstance(title, str) or not title.strip()
                or _same_folder_key(folder) != here or session.get("isArchived") is True):
            continue
        if isinstance(branch, str) and branches and branch not in branches:
            continue
        last_active = session.get("lastActivityAt")
        found[session.get("sessionId") or record] = _ClaudeSession(
            title=title.strip(), last_active=last_active if isinstance(last_active, (int, float)) else 0,
            on_the_checkouts_branch=branch in branches)
    return list(found.values())


def _same_folder_key(folder: Path | str) -> str:
    return os.path.normcase(os.path.normpath(str(folder)))



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
