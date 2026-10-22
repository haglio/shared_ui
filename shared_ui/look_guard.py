"""What an app spells of its own look: a color, a typed glyph or an icon that
does not come from shared_ui, found in the source it tracks."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import unicodedata
from collections.abc import Iterable
from pathlib import Path

_LONG_HEX = re.compile(r"(?<![\w#&/])(#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}))\b(?!\s*\{)")
_SHORT_HEX = re.compile(r"(?:^|[:=][^;{}:=]*?)(?<![\w#&/])(#[0-9a-fA-F]{3,4})\b(?!\s*\{)")
_CSS_FUNCTION = re.compile(r"\b(?:rgba?|hsla?)\(\s*[\d.]", re.IGNORECASE)
_NAMED = ("white|black|red|green|blue|gray|grey|yellow|orange|purple|cyan|magenta|silver|"
          "navy|teal|lime|maroon|olive|gold|darkgray|lightgray|darkgrey|lightgrey")
_CSS_NAMED = re.compile(r"\b(?:color|background(?:-color)?|border(?:-[a-z]+)*|outline(?:-color)?|fill)"
                        r"\s*(?::|=\s*['\"])\s*[^;{}'\"]*?\b(?:" + _NAMED + r")\b", re.IGNORECASE)
_NAMED_ALONE = re.compile(r"(?:" + _NAMED + r")", re.IGNORECASE)
_BYTE = re.compile(r"0[xX][0-9a-fA-F]{1,2}")
_COLOR_NAME = re.compile(
    r"color|ink|fill|bg|background|foreground|fg|border|outline|tint|shade|track|plate|"
    r"ground|glyph|chip|scrim|gr[ae]y|white|black|red|green|blue|amber|yellow|orange|"
    r"magenta|purple|cyan|accent|highlight|hover|muted|dim|edge|cursor|pill|placeholder|"
    r"swatch|shadow|glow", re.IGNORECASE)
_COLOR_KEYWORDS = {"fill", "outline", "color", "ink", "background", "foreground", "bg", "fg"}
_QCOLOR_FROM = {"fromRgb", "fromRgbF", "fromHsv", "fromHsvF", "fromHsl", "fromHslF",
                "fromString", "fromCmyk", "fromCmykF"}
_GL_COLORS = {"glClearColor", "glColor3f", "glColor4f", "glUniform3f", "glUniform4f"}
_MASK_MODES = {"1", "L", "I", "F"}
_TYPOGRAPHY = set("°©®™")
_MINUS_SIGN = "−"


class LookNotRead(Exception):
    pass


def _tracked(root: Path, package: Path) -> list[Path]:
    quiet = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", str(package)],
                            capture_output=True, text=True, encoding="utf-8", env=quiet)
    files = [root / name for name in listed.stdout.split("\0") if name]
    if not files:
        raise LookNotRead(f"nothing to read: {root} tracks nothing under {package}\n{listed.stderr}")
    return files


def _hexes(text: str) -> list[str]:
    return [match.group(1) for pattern in (_LONG_HEX, _SHORT_HEX) for match in pattern.finditer(text)]


def _a_glyph(character: str) -> bool:
    if character in _TYPOGRAPHY:
        return False
    return unicodedata.category(character) in ("So", "Co") or character == _MINUS_SIGN


def _in_text(text: str) -> list[str]:
    found = [f"color {spelled}" for spelled in _hexes(text)]
    found += [f"color {match.group(0)}...)" for match in _CSS_FUNCTION.finditer(text)]
    found += [f"color '{match.group(0)}'" for match in _CSS_NAMED.finditer(text)]
    found += [f"glyph {character} (U+{ord(character):04X} {unicodedata.name(character, '?')})"
              for character in dict.fromkeys(text) if _a_glyph(character)]
    return found


def _number(node: ast.AST) -> float | None:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    return None


def _a_named_color(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant) and isinstance(node.value, str)
            and bool(_NAMED_ALONE.fullmatch(node.value)))


def _channels(node: ast.AST) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) not in (3, 4):
        return False
    channels = [_number(element) for element in node.elts]
    if None in channels or channels == [0, 0, 0, 0]:
        return False
    if all(type(channel) is int for channel in channels):
        return all(0 <= channel <= 255 for channel in channels)
    return all(0.0 <= channel <= 1.0 for channel in channels)


def _a_color(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _hexes(node.value) == [node.value] or _a_named_color(node)
    return _channels(node)


def _bytes_in_hex(node: ast.AST, source: str) -> bool:
    return (isinstance(node, ast.Tuple) and len(node.elts) in (3, 4)
            and all(_BYTE.fullmatch(ast.get_source_segment(source, element) or "")
                    for element in node.elts))


def _a_stop(node: ast.AST) -> bool:
    return (isinstance(node, ast.Tuple) and len(node.elts) == 2
            and _number(node.elts[0]) is not None and _channels(node.elts[1]))


def _names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Attribute):
        return [target.attr]
    return []


def _dotted(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    elif isinstance(node, ast.Call):
        parts.append(_dotted(node.func) + "()")
    return ".".join(reversed(parts))


def _spelled(node: ast.AST, source: str) -> str:
    return ast.get_source_segment(source, node) or ast.unparse(node)


def _in_call(call: ast.Call, source: str) -> list[str]:
    name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
    spreads_a_family_color = bool(call.args) and isinstance(call.args[0], ast.Starred)
    if (name == "QColor" or name in _QCOLOR_FROM) and not spreads_a_family_color and any(
            _number(arg) is not None or _a_named_color(arg) for arg in call.args):
        return [f"color {_spelled(call, source)}"]
    if name in _GL_COLORS and sum(_number(arg) is not None for arg in call.args) >= 3:
        return [f"color {_spelled(call, source)}"]
    found = [f"color {keyword.arg}={_spelled(keyword.value, source)}" for keyword in call.keywords
             if keyword.arg in _COLOR_KEYWORDS and _a_color(keyword.value)]
    if name == "new" and _dotted(call.func).endswith("Image.new") and len(call.args) >= 3:
        mode, color = call.args[0], call.args[2]
        masked = isinstance(mode, ast.Constant) and mode.value in _MASK_MODES
        if not masked and (_a_color(color) or _number(color) is not None):
            found.append(f"color {_spelled(color, source)}")
    return found


def _in_assignment(assignment: ast.Assign | ast.AnnAssign, source: str) -> list[str]:
    value = assignment.value
    targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
    names = [name for target in targets for name in _names(target)]
    if value is None or not any(_COLOR_NAME.search(name) for name in names):
        return []
    if _channels(value) or _a_named_color(value):
        return [f"color {names[0]} = {_spelled(value, source)}"]
    return []


def _an_icon_from_elsewhere(node: ast.AST) -> str | None:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        modules = [alias.name for alias in node.names]
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        return "qtawesome" if any(name.split(".")[0] == "qtawesome" for name in modules) else None
    if isinstance(node, ast.Attribute):
        held_in = _dotted(node.value)
        if (held_in.endswith("StandardPixmap") and node.attr.startswith("SP_")) or (
                held_in.endswith("PrimitiveElement") and node.attr.startswith("PE_Indicator")):
            return _dotted(node)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr in ("standardIcon", "fromTheme"):
        return _dotted(node.func)
    return None


def _a_global_color(node: ast.AST) -> bool:
    return (isinstance(node, ast.Attribute) and _dotted(node.value) == "Qt.GlobalColor"
            and node.attr != "transparent")


def _docstrings(tree: ast.Module) -> set[int]:
    return {id(node.body[0].value) for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)}


def _in_node(node: ast.AST, source: str) -> list[str]:
    found = []
    icon = _an_icon_from_elsewhere(node)
    if icon:
        found.append(f"icon {icon}")
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        found += _in_text(node.value)
    elif isinstance(node, ast.Call):
        found += _in_call(node, source)
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        found += _in_assignment(node, source)
    elif _a_global_color(node):
        found.append(f"color {_dotted(node)}")
    if _bytes_in_hex(node, source) or _a_stop(node):
        found.append(f"color {_spelled(node, source)}")
    return found


def _in_python(source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    prose = _docstrings(tree)
    return sorted({(node.lineno, what) for node in ast.walk(tree) if id(node) not in prose
                   for what in _in_node(node, source)})


def _in_page(source: str) -> list[tuple[int, str]]:
    return [(number, what) for number, line in enumerate(source.splitlines(), 1)
            for what in _in_text(line)]


_READERS = {".py": _in_python, ".html": _in_page, ".css": _in_page, ".js": _in_page,
            ".qss": _in_page, ".svg": _in_page}


def looks_of_its_own(root: Path, packages: Iterable[Path]) -> list[str]:
    found = []
    for package in packages:
        for path in _tracked(root, package):
            read = _READERS.get(path.suffix)
            if read is not None:
                where = path.relative_to(root).as_posix()
                found.extend(f"{where}:{line}: {what}"
                             for line, what in read(path.read_text(encoding="utf-8")))
    return found


def _without_its_line(finding: str) -> str:
    where, _line, what = finding.split(":", 2)
    return f"{where}:{what}"


def assert_the_look_is_shared_uis(root: Path, packages: Iterable[Path], *,
                                  allowing: Iterable[str] = ()) -> None:
    allowed = set(allowing)
    found = [finding for finding in looks_of_its_own(root, packages)
             if _without_its_line(finding) not in allowed]
    assert not found, ("These draw a color, a glyph or an icon of their own; take each from "
                       "shared_ui (its palette, its glyphs, its marks) instead:\n" + "\n".join(found))
