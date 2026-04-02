"""Tests for shared_ui.generate_web_tokens."""

from __future__ import annotations

from PyQt6.QtGui import QColor

from shared_ui.generate_web_tokens import (
    collect_color_tokens,
    collect_font_tokens,
    qcolor_to_hex,
    render_css,
)


class TestQColorToHex:
    def test_produces_6_digit_lowercase_hex(self):
        assert qcolor_to_hex(QColor(24, 24, 24)) == "#181818"

    def test_mixed_channels(self):
        assert qcolor_to_hex(QColor(0x30, 0x80, 0xE0)) == "#3080e0"

    def test_white(self):
        assert qcolor_to_hex(QColor(255, 255, 255)) == "#ffffff"

    def test_black(self):
        assert qcolor_to_hex(QColor(0, 0, 0)) == "#000000"


class TestCollectColorTokens:
    def test_finds_all_qcolor_constants(self):
        from shared_ui import colors

        expected_count = sum(
            1
            for name in dir(colors)
            if not name.startswith("_") and isinstance(getattr(colors, name), QColor)
        )
        tokens = collect_color_tokens()
        assert len(tokens) == expected_count

    def test_names_are_kebab_cased_css_vars(self):
        tokens = collect_color_tokens()
        for name, _value in tokens:
            assert name.startswith("--"), f"{name} doesn't start with --"
            assert name == name.lower(), f"{name} has uppercase chars"
            assert "_" not in name, f"{name} contains underscores"

    def test_bg_primary_maps_correctly(self):
        tokens = dict(collect_color_tokens())
        assert tokens["--bg-primary"] == "#181818"

    def test_aliases_resolve_to_values(self):
        tokens = dict(collect_color_tokens())
        # TOGGLE_ON = BLUE — should resolve to same hex
        assert tokens["--toggle-on"] == tokens["--blue"]


class TestCollectFontTokens:
    def test_includes_font_families(self):
        tokens = dict(collect_font_tokens())
        assert "--font-ui" in tokens
        assert "--font-mono" in tokens

    def test_font_ui_has_web_fallbacks(self):
        tokens = dict(collect_font_tokens())
        assert tokens["--font-ui"] == '"Segoe UI", system-ui, sans-serif'

    def test_font_mono_has_fallback_chain(self):
        tokens = dict(collect_font_tokens())
        assert tokens["--font-mono"] == '"Cascadia Mono", Consolas, monospace'

    def test_includes_size_tiers_in_px(self):
        tokens = dict(collect_font_tokens())
        assert tokens["--size-body"] == "11px"
        assert tokens["--size-title"] == "16px"
        assert tokens["--size-heading"] == "14px"
        assert tokens["--size-small"] == "9px"
        assert tokens["--size-tiny"] == "8px"


class TestRenderCss:
    def test_starts_with_generation_comment(self):
        css = render_css(collect_color_tokens(), collect_font_tokens())
        assert css.startswith("/* Auto-generated")

    def test_wraps_in_root_selector(self):
        css = render_css(collect_color_tokens(), collect_font_tokens())
        assert ":root {" in css
        assert css.rstrip().endswith("}")

    def test_contains_known_color_token(self):
        css = render_css(collect_color_tokens(), collect_font_tokens())
        assert "--bg-primary: #181818;" in css

    def test_contains_known_font_token(self):
        css = render_css(collect_color_tokens(), collect_font_tokens())
        assert '--font-ui: "Segoe UI", system-ui, sans-serif;' in css

    def test_minimal_input(self):
        css = render_css([("--test-color", "#abcdef")], [("--test-font", "serif")])
        assert "--test-color: #abcdef;" in css
        assert "--test-font: serif;" in css


class TestCli:
    def test_writes_to_file(self, tmp_path):
        import subprocess
        import sys

        out = tmp_path / "tokens.css"
        subprocess.check_call(
            [
                sys.executable,
                "C:/path/to/suite-root/projects/shared_ui/generate_web_tokens.py",
                "--output",
                str(out),
            ],
        )
        content = out.read_text(encoding="utf-8")
        assert ":root {" in content
        assert "--bg-primary:" in content

    def test_prints_to_stdout_without_output_flag(self):
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "C:/path/to/suite-root/projects/shared_ui/generate_web_tokens.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert ":root {" in result.stdout
        assert "--bg-primary:" in result.stdout
