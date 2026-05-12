"""Optional PySide6 compatibility helpers."""

from __future__ import annotations

import importlib.util
from typing import Any


class PySide6UnavailableError(RuntimeError):
    """Raised when the optional PySide6 GUI extra is not installed."""


def pyside6_missing_message() -> str:
    return (
        "PySide6 is not installed. Install the optional GUI extra with "
        "`python -m pip install -e .[gui]`, then run `python -m osw.cli gui` again."
    )


def is_pyside6_available() -> bool:
    return importlib.util.find_spec("PySide6") is not None


def require_qt_widgets() -> tuple[Any, Any]:
    try:
        from PySide6 import QtCore, QtWidgets
    except ModuleNotFoundError as exc:
        raise PySide6UnavailableError(pyside6_missing_message()) from exc
    return QtCore, QtWidgets
