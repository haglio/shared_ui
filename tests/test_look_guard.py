"""shared_ui.look_guard: what an app spells of its own look, found in its source."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from shared_ui.look_guard import LookNotRead, assert_the_look_is_shared_uis, looks_of_its_own


def _git(checkout: Path, *args: str) -> None:
    quiet = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    subprocess.run(["git", "-C", str(checkout), *args], check=True, capture_output=True, env=quiet)


@pytest.fixture
def app(tmp_path):
    """A checkout holding one package, every file handed to it tracked."""
    checkout = tmp_path / "an_app"
    (checkout / "parlor").mkdir(parents=True)
    _git(checkout, "init", "-q")

    def track(files: dict[str, str]) -> Path:
        for name, text in files.items():
            path = checkout / "parlor" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        _git(checkout, "add", "--", *(f"parlor/{name}" for name in files))
        return checkout

    return track


def _found(checkout: Path) -> list[str]:
    return looks_of_its_own(checkout, [checkout / "parlor"])


def test_a_color_in_a_style_sheet_is_named_with_its_place(app):
    checkout = app({"tiles.py": 'SHEET = "QLabel { color: #7a7a7a; }"\n'})

    assert _found(checkout) == ["parlor/tiles.py:1: color #7a7a7a"]


@pytest.mark.parametrize("line", [
    "SHEET = 'background: rgba(0, 0, 0, 0.55);'",
    "SHEET = 'QWidget { color: white; }'",
    "INK = QColor(255, 255, 255)",
    "INK = QColor('#1f4d2a')",
    "INK = QColor.fromRgbF(0.2, 0.4, 0.6)",
    "_TRACK = (56, 56, 62)",
    "HANDLE_COLOR = (0.85, 0.85, 0.9, 0.35)",
    "draw.line(points, fill=(200, 70, 70))",
    "draw.text(where, words, fill='white')",
    "image = Image.new('RGB', size, (64, 64, 64))",
    "painter.fillRect(rect, Qt.GlobalColor.black)",
    "STAGE = ('upscale', (0xED, 0xC9, 0x48))",
    "GRADIENT = [(0.0, (10, 14, 30)), (100.0, (30, 70, 230))]",
    "GL.glClearColor(0.1, 0.1, 0.1, 1.0)",
    "painter.setPen(QColor(0x80, 0x80, 0x80))",
    "draw.rectangle(box, fill=(0, 0, 0))",
    "self._ground_color = (10, 10, 10)",
])
def test_a_color_spelled_any_other_way_is_named_too(app, line):
    checkout = app({"tiles.py": f"{line}\n"})

    found = _found(checkout)

    assert found, line
    assert all(finding.startswith("parlor/tiles.py:1: color ") for finding in found), found


@pytest.mark.parametrize("line", [
    "INK = QColor(*palette.BLUE)",
    "CHIP = QColor(*palette.BLACK, 160)",
    "SHEET = f'QLabel {{ color: {as_hex(TEXT_MUTED)}; }}'",
    "draw.line(points, fill=(*RED, 255))",
    "image = Image.new('RGBA', size, (0, 0, 0, 0))",
    "probe = Image.new('L', size, 0)",
    "SHEET = 'QWidget { background: transparent; }'",
    "pixmap.fill(Qt.GlobalColor.transparent)",
    "MARGINS = (4, 4, 4, 4)",
    "SHEET = 'QPushButton#add { padding: 0; }'",
    "LINK = 'page.html#fade'",
    "SEEN = 'a #123 in a sentence'",
    "IMAGE_ICON, LR_LOADFROMFILE, WM_SETICON = 1, 0x10, 0x80",
    "CLIP = ['-f', 'lavfi', '-i', 'color=c=gray:s=576x384:r=30']",
])
def test_a_color_taken_from_shared_ui_or_no_color_at_all_passes(app, line):
    checkout = app({"tiles.py": f"{line}\n"})

    assert _found(checkout) == []


@pytest.mark.parametrize(("line", "named"), [
    ("CARD_BORDER = '#3f3f3f'", "color #3f3f3f"),
    ("INK = QColor('#1f4d2a')", "color #1f4d2a"),
    ("INK = QColor('black')", "color QColor('black')"),
])
def test_one_color_is_named_once(app, line, named):
    checkout = app({"tiles.py": f"{line}\n"})

    assert _found(checkout) == [f"parlor/tiles.py:1: {named}"]


def test_a_typed_symbol_is_named_and_typography_is_not(app):
    checkout = app({"tiles.py": (
        'CROWN = "\U0001F451"\n'
        'MINUS = "−"\n'
        'TITLE = "Unlocked · Shuffle — waiting… → next, at 90°"\n'
    )})

    assert _found(checkout) == [
        "parlor/tiles.py:1: symbol \U0001F451 (U+1F451 CROWN)",
        "parlor/tiles.py:2: symbol − (U+2212 MINUS SIGN)",
    ]


def test_a_docstring_may_name_a_symbol_or_a_color(app):
    checkout = app({"tiles.py": (
        '"""Draws the ✕ in the white #ffffff would."""\n'
        "def close():\n"
        '    """The ✕ closes it."""\n'
    )})

    assert _found(checkout) == []


def test_an_icon_from_outside_shared_ui_is_named(app):
    checkout = app({"tiles.py": (
        "import qtawesome as qta\n"
        "warning = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)\n"
        "style.drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorTabClose, option, painter)\n"
        "folder = QIcon.fromTheme('folder')\n"
        "from qtawesome import icon\n"
    )})

    assert _found(checkout) == [
        "parlor/tiles.py:1: icon qtawesome",
        "parlor/tiles.py:2: icon QApplication.style().standardIcon",
        "parlor/tiles.py:2: icon QStyle.StandardPixmap.SP_MessageBoxWarning",
        "parlor/tiles.py:3: icon QStyle.PrimitiveElement.PE_IndicatorTabClose",
        "parlor/tiles.py:4: icon QIcon.fromTheme",
        "parlor/tiles.py:5: icon qtawesome",
    ]


def test_a_page_the_app_serves_is_read_for_its_colors_too(app):
    checkout = app({"static/page.html": "<style>\n  body { background: #1e1e2e; }\n</style>\n"})

    assert _found(checkout) == ["parlor/static/page.html:2: color #1e1e2e"]


def test_only_what_the_checkout_tracks_is_read(app):
    checkout = app({"tiles.py": "WIDTH = 4\n"})
    (checkout / "parlor" / "private.js").write_text("note.style.color = '#00ff00';\n", encoding="utf-8")

    assert _found(checkout) == []


def test_a_package_that_tracks_nothing_is_refused_rather_than_passed(app):
    checkout = app({"tiles.py": "WIDTH = 4\n"})

    with pytest.raises(LookNotRead, match="drawing_room"):
        looks_of_its_own(checkout, [checkout / "drawing_room"])


def test_the_failure_says_where_each_one_is_and_where_it_belongs(app):
    checkout = app({"tiles.py": "_TRACK = (56, 56, 62)\nPENCIL = '✎'\n"})

    with pytest.raises(AssertionError) as failure:
        assert_the_look_is_shared_uis(checkout, [checkout / "parlor"])

    assert "parlor/tiles.py:1: color _TRACK = (56, 56, 62)" in str(failure.value)
    assert "parlor/tiles.py:2: symbol ✎ (U+270E LOWER RIGHT PENCIL)" in str(failure.value)
    assert "shared_ui" in str(failure.value)


def test_an_allowance_takes_out_what_it_names_wherever_the_line_moves(app):
    checkout = app({"aim.py": "\n\ncanvas = Image.new('RGB', size, (114, 114, 114))\n"})

    assert_the_look_is_shared_uis(checkout, [checkout / "parlor"],
                                  allowing=("parlor/aim.py: color (114, 114, 114)",))


@pytest.mark.parametrize("line", [
    "SHEET = 'QLabel { font-size: 15px; }'",
    "SHEET = 'body { font: 14px/1.45 sans-serif; }'",
    "SHEET = 'code { font-family: Consolas, monospace; }'",
    "font.setPointSize(8)",
    "font.setPixelSize(30)",
    "font = QFont('Arial')",
    "font = QFont(FONT_UI, 12)",
    "font = make_font(size=12)",
    "font = ImageFont.truetype('arial.ttf', 13)",
    "_TITLE_PT = 17",
    "BANNER_FONT_PX = 44",
    "font.setPointSize(font.pointSize() + 1)",
    "font = make_font(size=max(SIZE_TINY, round(height * 0.03)))",
    "HEADSET = Metrics(icon=96, wordmark_px=30, status_px=17)",
])
def test_a_face_or_a_text_size_of_its_own_is_named(app, line):
    assert _found(app({"tiles.py": line + "\n"}))


@pytest.mark.parametrize(("line", "named"), [
    ("SHEET = \"code { font-family: 'Courier New', monospace; }\"",
     ["parlor/tiles.py:1: face font-family: 'Courier New', monospace"]),
    ("SHEET = 'p { font: __TYPE_SIZE_SMALL__/1.4 monospace; }'",
     ["parlor/tiles.py:1: face font: __TYPE_SIZE_SMALL__/1.4 monospace"]),
    ("PAGE = \"p { font-family: '__TYPE_FONT_UI__'; font: __TYPE_SIZE_SMALL__/1.4 '__TYPE_FONT_UI__'; }\"", []),
])
def test_a_face_is_named_in_quotes_and_in_the_font_shorthand(app, line, named):
    assert _found(app({"tiles.py": line + "\n"})) == named


def test_a_text_size_a_record_carries_is_named(app):
    checkout = app({"tiles.py": "class Metrics:\n    wordmark_px: int = 24\n"})

    assert _found(checkout) == ["parlor/tiles.py:2: text size wordmark_px = 24"]


@pytest.mark.parametrize("line", [
    "SHEET = 'QLabel { padding: 2px 6px; }'",
    "SHEET = 'QFrame { border-radius: 6px; }'",
    "SHEET = '.row { margin-top: 3px; gap: 14px; }'",
    "layout.setContentsMargins(6, 6, 6, 6)",
    "layout.setSpacing(10)",
    "layout.addSpacing(12)",
    "SHEET = '.hint { margin: 1em 0; }'",
    "SHEET = '.dest { margin-top: 0.8em; }'",
    "_ROW_INSET = QMargins(3, 3, 3, 3)",
])
def test_a_spacing_of_its_own_is_named(app, line):
    assert _found(app({"tiles.py": line + "\n"}))


@pytest.mark.parametrize("line", [
    "SHEET = f\"QLabel {{ font-size: {SIZE_SMALL}pt; font-family: '{FONT_UI}'; }}\"",
    "SHEET = f'QLabel {{ padding: {GAP_SMALL}px {GAP_MEDIUM}px; border-radius: {BUTTON_RADIUS}px; }}'",
    "SHEET = 'QLabel { padding: 0; margin: 0px; font: inherit; }'",
    "font.setPointSize(SIZE_BODY)",
    "font = make_font(size=SIZE_HEADING, bold=True)",
    "layout.setContentsMargins(0, 0, 0, 0)",
    "layout.setSpacing(GAP_SMALL)",
    "_ICON_PX = 48",
    "SHEET = '#clip { margin: 0 auto; padding: 0em; }'",
    "font.setPixelSize(in_pixels(SIZE_BODY))",
    "font = QFont(FONT_UI, -1)",
    "HEADSET = Metrics(icon=96, wordmark_px=in_pixels(SIZE_HEADING))",
])
def test_the_familys_own_type_and_spacing_or_none_at_all_passes(app, line):
    assert _found(app({"tiles.py": line + "\n"})) == []


@pytest.mark.parametrize(("line", "named"), [
    ("NOTICE_TOP_MARGIN = 28", ["parlor/tiles.py:1: spacing NOTICE_TOP_MARGIN = 28"]),
    ("_ROW_GAP_PX = 6", ["parlor/tiles.py:1: spacing _ROW_GAP_PX = 6"]),
    ("_EDGE_MARGIN = 0", []),
    ("_TOP_MARGIN = MARGIN_DIALOG", []),
    ("_SLAT_GAP_DEG = 2.0", []),
    ("roi_padding: int = 20", []),
    ("min_gap = 10", []),
])
def test_a_spacing_is_named_by_what_its_name_says_it_spaces(app, line, named):
    assert _found(app({"tiles.py": line + "\n"})) == named


def test_a_face_and_a_text_size_are_named_as_they_are_written(app):
    checkout = app({"tiles.py": "SHEET = 'QLabel { font-size: 10px; font-family: Consolas, monospace; }'\n"})

    assert _found(checkout) == ["parlor/tiles.py:1: face font-family: Consolas, monospace",
                                "parlor/tiles.py:1: text size font-size: 10px"]


@pytest.mark.parametrize(("line", "named"), [
    ("_SMALL_PX = 11", ["parlor/tiles.py:1: text size _SMALL_PX = 11"]),
    ("_ROW_PX = 12", ["parlor/tiles.py:1: text size _ROW_PX = 12"]),
    ("BANNER_MAX_WIDTH_PX = 1600", []),
    ("_ICON_SIDE_PX = 12", []),
    ("_LEGEND_POINT_SIZE = 8", ["parlor/tiles.py:1: text size _LEGEND_POINT_SIZE = 8"]),
])
def test_a_size_is_a_text_size_by_what_its_name_says_it_sizes(app, line, named):
    assert _found(app({"tiles.py": line + "\n"})) == named
