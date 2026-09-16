"""Every family checkout this one runs is named at a version, not left to chance.

A sibling used to be whatever copy happened to sit beside this checkout, so a
change landing in one repo reached every consumer the same minute -- and a change
whose other half had not landed turned all of them red at once, in their own
gates, with no cause in their own history. A pin ends that: this repo runs the
copy it was built against until it says otherwise.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"

# `app-support @ git+https://github.com/haglio/app_support@v0.1.138`
PIN = re.compile(
    r"^(?P<package>[A-Za-z0-9._-]+)\s*@\s*git\+https://github\.com/haglio/"
    r"(?P<repo>[A-Za-z0-9._-]+)@(?P<tag>v[0-9][^\s]*)$"
)


def _raw() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def pinned_repos() -> dict[str, str]:
    """Which family repo each pinned requirement names, and at what tag."""
    found = {}
    for requirement in _raw()["project"]["dependencies"]:
        match = PIN.match(requirement.strip())
        if match:
            found[match["repo"]] = match["tag"]
    return found


def test_every_sibling_this_repo_declares_is_pinned():
    siblings = _raw()["tool"]["haglio"]["siblings"]

    assert set(siblings) <= set(pinned_repos()), (
        "a sibling with no pin is the old arrangement: this repo would run "
        f"whatever copy sat beside it. Unpinned: {sorted(set(siblings) - set(pinned_repos()))}"
    )


def test_a_pin_names_a_repo_this_one_declares_as_a_sibling():
    siblings = set(_raw()["tool"]["haglio"]["siblings"])

    assert set(pinned_repos()) <= siblings, (
        "a pinned family repo that is not a declared sibling is one nobody "
        f"counted: {sorted(set(pinned_repos()) - siblings)}"
    )
