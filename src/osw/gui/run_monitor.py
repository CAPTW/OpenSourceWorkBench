"""Run monitor for prepared workflow status."""

from __future__ import annotations

from typing import Any

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BasePlainTextEdit: Any = QtWidgets.QPlainTextEdit if QtWidgets is not None else object


def format_run_log(message: str, *, level: str = "info") -> str:
    return f"[{level.upper()}] {message}"


def append_run_log(monitor: object, message: str, *, level: str = "info") -> None:
    monitor.appendPlainText(format_run_log(message, level=level))


class RunMonitor(_BasePlainTextEdit):
    """Read-only monitor with a small append API for workflow status."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("runMonitor")
        self.setReadOnly(True)
        self.setPlainText(
            "Run monitor idle. OSW GUI prepares workflows but does not launch solvers."
        )

    def append_log(self, message: str, *, level: str = "info") -> None:
        append_run_log(self, message, level=level)


def build_run_monitor(parent: object | None = None) -> object:
    return RunMonitor(parent)
