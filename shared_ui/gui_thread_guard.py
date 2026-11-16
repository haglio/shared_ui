"""A Qt application made by hand leaves Python's cycle collector free to start on a worker
thread, which frees widgets there and crashes the GUI thread later; see gui_thread_collection."""

from __future__ import annotations

import ast
from pathlib import Path

from shared_ui.tracked import tracked

_APPLICATION_KINDS = {"QApplication", "QGuiApplication", "QCoreApplication"}
_WHERE_SHARED_UI_TURNS_IT_ON_ITSELF = {Path("shared_ui", "application.py")}


def _made_by_hand(tree: ast.AST) -> list[int]:
    return [node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Call) and _kind_called(node.func) in _APPLICATION_KINDS]


def _kind_called(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def assert_every_application_collects_on_its_gui_thread(root: Path) -> None:
    files, complaint = tracked(root)
    sources = [path for path in files if path.suffix == ".py"
               and path.relative_to(root) not in _WHERE_SHARED_UI_TURNS_IT_ON_ITSELF]
    if not sources:
        raise AssertionError(f"nothing to read: {root} tracks no Python files\n{complaint}")
    made = [f"{path.relative_to(root).as_posix()}:{line}" for path in sources
            for line in _made_by_hand(ast.parse(path.read_text(encoding="utf-8"), str(path)))]
    assert not made, (
        "These make a Qt application by hand, so Python may collect cycles on a worker thread "
        "and free widgets there; make it with shared_ui.gui_thread_collection.the_application "
        "or shared_ui.application.application instead:\n  " + "\n  ".join(made))
