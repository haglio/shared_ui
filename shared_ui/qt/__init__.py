from __future__ import annotations

import importlib
import sys
import types
from collections.abc import Callable, Mapping

BINDINGS = ("PySide6", "PyQt6")
_MODULES = ("QtCore", "QtGui", "QtWidgets", "QtTest", "QtSvg", "QtNetwork")

_Helpers = tuple[Callable[[object], bool], Callable[[object], bool], Callable[[object], None]]


def chosen_binding(loaded: Mapping[str, object] = sys.modules,
                   importing: Callable[[str], object] = importlib.import_module) -> str:
    for name in BINDINGS:
        if name in loaded:
            return name
    for name in BINDINGS:
        try:
            importing(name)
        except ImportError:
            continue
        return name
    raise ImportError(f"neither of {', '.join(BINDINGS)} is installed")


def under_pyside6_names(name: str, module: types.ModuleType, **added: object) -> types.ModuleType:
    renamed = types.ModuleType(name)
    renamed.__dict__.update(vars(module), **added, __name__=f"{__name__}.{name}")
    return renamed


def _pyside6() -> _Helpers:
    import shiboken6  # noqa: PLC0415

    def is_deleted(found: object) -> bool:
        return not shiboken6.isValid(found)

    return is_deleted, shiboken6.ownedByPython, shiboken6.delete


def _pyqt6() -> _Helpers:  # pragma: no cover -- every app still on PyQt6 runs it, as does tests/test_qt.py's child
    from PyQt6 import QtCore, QtGui, sip  # noqa: PLC0415

    sys.modules[f"{__name__}.QtCore"] = under_pyside6_names(
        "QtCore", QtCore, Signal=QtCore.pyqtSignal, Slot=QtCore.pyqtSlot)
    sys.modules[f"{__name__}.QtGui"] = under_pyside6_names("QtGui", QtGui, Qt=QtCore.Qt)
    return sip.isdeleted, sip.ispyowned, sip.delete


BINDING = chosen_binding()
for _module in _MODULES:
    sys.modules[f"{__name__}.{_module}"] = importlib.import_module(f"{BINDING}.{_module}")
is_deleted, owned_by_python, delete = _pyside6() if BINDING == "PySide6" else _pyqt6()

__all__ = ["BINDING", "delete", "is_deleted", "owned_by_python"]
