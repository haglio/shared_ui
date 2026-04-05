"""Dead-code detection test.

Runs vulture against the shared_ui source modules and fails if any
unreported dead code is found.  False positives (public-API tokens,
Qt/pytest framework hooks) are whitelisted below.

Also checks for *semantic* dead code that vulture cannot detect — e.g.
dict keys or string comparisons that reference deleted constants.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import vulture

_REPO_ROOT = Path(__file__).resolve().parent.parent

# -- Whitelist ---------------------------------------------------------------
# Names that vulture flags but are intentionally public API or framework hooks.
#
# Qt overrides / framework callbacks:
#   qapp              – pytest autouse fixture (conftest.py)
#
# Public-API tokens (consumed by downstream projects, not within this repo):
#   Every ALL_CAPS constant in colors.py, fonts.py, spacing.py is part of the
#   library's public surface.  Rather than listing each individually, the test
#   exempts module-level ALL_CAPS names from those modules.
FRAMEWORK_HOOKS = {
    "qapp",  # pytest fixture – conftest.py
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
    if _is_public_token(result):
        return True
    return False


def _load_local_module(name: str):
    """Import a module from the repo root (not the installed package)."""
    path = _REPO_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _font_family_values() -> set[str]:
    """Return the set of font family string values defined in fonts.py."""
    fonts = _load_local_module("fonts")
    return {
        getattr(fonts, name)
        for name in dir(fonts)
        if name.startswith("FONT_") and isinstance(getattr(fonts, name), str)
    }


def _font_fallback_keys() -> set[str]:
    """Extract dict keys from _FONT_FAMILY_FALLBACKS in generate_web_tokens.py."""
    source = (_REPO_ROOT / "generate_web_tokens.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_FONT_FAMILY_FALLBACKS":
                    return {key.value for key in node.value.keys}
    raise LookupError("_FONT_FAMILY_FALLBACKS not found in generate_web_tokens.py")


class TestNoDeadCode:
    def test_vulture_finds_no_unwhitelisted_dead_code(self):
        v = vulture.Vulture()
        v.scavenge(
            [
                str(_REPO_ROOT / "colors.py"),
                str(_REPO_ROOT / "fonts.py"),
                str(_REPO_ROOT / "spacing.py"),
                str(_REPO_ROOT / "generate_web_tokens.py"),
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

    def test_font_fallback_keys_match_actual_fonts(self):
        """Every key in _FONT_FAMILY_FALLBACKS must be a value of a FONT_* constant."""
        actual = _font_family_values()
        orphaned = _font_fallback_keys() - actual
        assert not orphaned, f"Orphaned fallback keys (no matching font constant): {orphaned}"
