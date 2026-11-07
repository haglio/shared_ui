from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from shared_ui.preview import Preview, preview_of, taskbar_identity, window_title

_GIT_ENVIRONMENT = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR")


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "Jane Doe", "GIT_AUTHOR_EMAIL": "jane@example.com",
                        "GIT_COMMITTER_NAME": "Jane Doe", "GIT_COMMITTER_EMAIL": "jane@example.com"})


@pytest.fixture
def worktree(tmp_path, monkeypatch) -> Path:
    for name in _GIT_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
    primary = tmp_path / "example_app"
    primary.mkdir()
    _git("init", "--quiet", "--initial-branch=main", cwd=primary)
    _git("commit", "--quiet", "--allow-empty", "--message=Start", cwd=primary)
    checkout = tmp_path / "scene-one"
    _git("worktree", "add", "--quiet", "-b", "claude/scene-one", str(checkout), cwd=primary)
    return checkout


@pytest.fixture(autouse=True)
def claude_desktop_keeps_no_records(tmp_path, monkeypatch) -> Path:
    local = tmp_path / "local app data"
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming app data"))
    return local


def _claude_session(records: Path, title: str, checkout: Path, *, last_active: int = 1, name: str = "one") -> None:
    folder = records / "claude-code-sessions" / "account" / "project"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"local_{name}.json").write_text(json.dumps(
        {"title": title, "worktreePath": str(checkout), "cwd": str(checkout), "lastActivityAt": last_active}),
        encoding="utf-8")


def test_a_preview_is_named_after_the_claude_session_whose_worktree_it_runs_from(
        worktree, claude_desktop_keeps_no_records):
    _claude_session(claude_desktop_keeps_no_records / "ClaudeProfileB", "Example scene pausing", worktree)

    assert preview_of(worktree).feature == "Example scene pausing"


def test_the_sessions_name_is_found_where_an_app_outside_claudes_package_reads_it(
        worktree, claude_desktop_keeps_no_records):
    package = claude_desktop_keeps_no_records / "Packages" / "Claude_example" / "LocalCache" / "Local"
    _claude_session(package / "Claude", "Example scene pausing", worktree)

    assert preview_of(worktree).feature == "Example scene pausing"


def test_the_sessions_name_comes_before_what_the_branch_describes(worktree, claude_desktop_keeps_no_records):
    _git("config", "branch.claude/scene-one.description", "the example stage's new pause", cwd=worktree)
    _claude_session(claude_desktop_keeps_no_records / "Claude", "Example scene pausing", worktree)

    assert preview_of(worktree).feature == "Example scene pausing"


def test_of_two_sessions_on_one_worktree_the_one_at_work_most_recently_names_it(
        worktree, claude_desktop_keeps_no_records):
    records = claude_desktop_keeps_no_records / "Claude"
    _claude_session(records, "Example scene stalling", worktree, last_active=1, name="older")
    _claude_session(records, "Example scene pausing", worktree, last_active=2, name="newer")

    assert preview_of(worktree).feature == "Example scene pausing"


def test_another_worktrees_session_names_nothing_here(worktree, tmp_path, claude_desktop_keeps_no_records):
    _claude_session(claude_desktop_keeps_no_records / "Claude", "Example scene stalling", tmp_path / "scene-two")

    assert preview_of(worktree).feature == "claude/scene-one"


def test_a_session_record_that_cannot_be_read_is_passed_over(worktree, claude_desktop_keeps_no_records):
    folder = claude_desktop_keeps_no_records / "Claude" / "claude-code-sessions" / "account" / "project"
    folder.mkdir(parents=True)
    (folder / "local_torn.json").write_text('{"title": "Example scene pausing", "worktreePath": ', encoding="utf-8")

    assert preview_of(worktree).feature == "claude/scene-one"


def test_the_primary_checkout_is_the_live_app(tmp_path):
    (tmp_path / ".git").mkdir()

    assert preview_of(tmp_path) is None


def test_a_worktree_is_a_preview(worktree):
    assert preview_of(worktree) is not None


def test_a_preview_demos_the_feature_its_branch_describes(worktree):
    _git("config", "branch.claude/scene-one.description", "the example stage's new pause", cwd=worktree)

    assert preview_of(worktree).feature == "the example stage's new pause"


def test_a_description_written_over_several_lines_names_the_feature_by_its_first(worktree):
    _git("config", "branch.claude/scene-one.description",
         "the example stage's new pause\n\nWhy it pauses, at length.\n", cwd=worktree)

    assert preview_of(worktree).feature == "the example stage's new pause"


def test_a_worktree_taken_off_its_branch_still_names_the_feature_that_branch_describes(worktree):
    _git("config", "branch.claude/scene-one.description", "the example stage's new pause", cwd=worktree)
    _git("checkout", "--quiet", "--detach", cwd=worktree)

    assert preview_of(worktree).feature == "the example stage's new pause"


def _stop_a_rebase_on_a_conflict(checkout: Path, *how: str) -> None:
    for where, line in ((checkout.parent / "example_app", "one way"), (checkout, "another way")):
        (where / "scene.txt").write_text(line, encoding="utf-8")
        _git("add", "scene.txt", cwd=where)
        _git("commit", "--quiet", "--message=Write the scene", cwd=where)
    with pytest.raises(subprocess.CalledProcessError):
        _git("rebase", *how, "main", cwd=checkout)


@pytest.mark.parametrize("how_git_replays_the_commits", ["--merge", "--apply"])
def test_a_worktree_stopped_partway_through_a_rebase_still_names_the_feature_its_branch_describes(
        worktree, how_git_replays_the_commits):
    _git("config", "branch.claude/scene-one.description", "the example stage's new pause", cwd=worktree)
    _stop_a_rebase_on_a_conflict(worktree, how_git_replays_the_commits)

    assert preview_of(worktree).feature == "the example stage's new pause"


def test_a_preview_no_session_or_description_names_is_named_after_its_branch(worktree):
    assert preview_of(worktree).feature == "claude/scene-one"


def test_a_preview_where_git_cannot_be_run_is_named_after_its_folder(worktree, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "nothing on it"))

    assert preview_of(worktree).feature == "scene-one"


def test_a_git_that_never_answers_is_given_up_on(worktree, monkeypatch):
    def never_answers(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", never_answers)

    assert preview_of(worktree).feature == "scene-one"


def test_the_live_app_wears_its_own_name():
    assert window_title("Example App", None) == "Example App"


def test_a_preview_is_named_for_the_feature_it_demos():
    preview = Preview(feature="the example stage's new pause")

    assert window_title("Example App", preview) == "Example App \u2014 preview of the example stage's new pause"


def test_a_preview_nobody_described_is_still_named_a_preview():
    assert window_title("Example App", Preview(feature=None)) == "Example App \u2014 preview"


def test_a_long_description_is_cut_at_a_word_so_a_tray_tooltip_can_hold_it_whole():
    feature = "the example stage's new pause, which waits for the scene to settle before it starts again"
    title = window_title("Example App", Preview(feature=feature))

    assert title == "Example App \u2014 preview of the example stage's new pause, which waits for the scene to\u2026"


def test_a_long_description_with_no_word_to_cut_at_is_cut_at_the_longest_that_fits():
    title = window_title("Example App", Preview(feature="x" * 90))

    assert title == "Example App \u2014 preview of " + "x" * 59 + "\u2026"


def test_the_live_app_keeps_the_taskbar_button_its_pin_carries():
    assert taskbar_identity("Example.App", None) == "Example.App"


def test_a_preview_gets_a_taskbar_button_of_its_own_beside_the_live_apps():
    preview = Preview(feature=None)

    assert taskbar_identity("Example.App", preview) == "Example.App.Preview"
