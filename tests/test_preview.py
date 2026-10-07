from __future__ import annotations

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


def test_a_preview_nobody_described_names_no_feature(worktree):
    assert preview_of(worktree).feature is None


def test_a_preview_opens_with_no_feature_named_where_git_cannot_be_run(worktree, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "nothing on it"))

    assert preview_of(worktree).feature is None


def test_a_git_that_never_answers_is_given_up_on(worktree, monkeypatch):
    def never_answers(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", never_answers)

    assert preview_of(worktree).feature is None


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
