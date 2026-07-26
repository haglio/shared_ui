"""Dead-code detection test.

Runs vulture against the shared_ui source modules and fails if any
unreported dead code is found.  False positives (public-API tokens,
Qt/pytest framework hooks) are whitelisted below.
"""

from __future__ import annotations

from pathlib import Path

import vulture

_REPO_ROOT = Path(__file__).resolve().parent.parent

# -- Whitelist ---------------------------------------------------------------
# Names that vulture flags but are intentionally public API or framework hooks.
#
# Framework callbacks:
#   qapp              – pytest autouse fixture (conftest.py)
#
# Qt method overrides (invoked by the C++ event loop, never from Python):
#   paintEvent, sizeHint, minimumSizeHint – widget hooks (check_box.py)
#
# Public-API tokens (consumed by downstream projects, not within this repo):
#   Every ALL_CAPS constant in colors.py, fonts.py, spacing.py is part of the
#   library's public surface.  Rather than listing each individually, the test
#   exempts module-level ALL_CAPS names from those modules.
FRAMEWORK_HOOKS = {
    "qapp",  # pytest fixture – conftest.py
}

QT_OVERRIDES = {
    "paintEvent",
    "sizeHint",
    "minimumSizeHint",
}

_TOKEN_MODULES = {"colors", "fonts", "spacing"}


def _is_public_token(result: vulture.core.Result) -> bool:
    """True if *result* is an ALL_CAPS name in a token module."""
    module = result.filename.stem
    if module not in _TOKEN_MODULES:
        return False
    return result.name.isupper()


def _is_whitelisted(result: vulture.core.Result) -> bool:
    if result.name in FRAMEWORK_HOOKS:
        return True
    if result.name in QT_OVERRIDES:
        return True
    if _is_public_token(result):
        return True
    return False


class TestNoDeadCode:
    def test_vulture_finds_no_unwhitelisted_dead_code(self):
        v = vulture.Vulture()
        v.scavenge(
            [
                str(_REPO_ROOT / "shared_ui"),
                str(_REPO_ROOT / "tests"),
            ],
        )

        violations = [r for r in v.get_unused_code() if not _is_whitelisted(r)]

        if violations:
            report = "\n".join(
                f"  {r.filename}:{r.first_lineno} – {r.name} ({r.confidence}%)"
                for r in violations
            )
            raise AssertionError(f"Dead code found:\n{report}")

