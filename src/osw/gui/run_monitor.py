"""Run monitor placeholder for prepared workflow status."""

from __future__ import annotations

from .qt_compat import require_qt_widgets


def build_run_monitor(parent: object | None = None) -> object:
    _, QtWidgets = require_qt_widgets()

    monitor = QtWidgets.QPlainTextEdit(parent)
    monitor.setObjectName("runMonitor")
    monitor.setReadOnly(True)
    monitor.setPlainText(
        "Run monitor idle. OSW GUI prepares workflows but does not launch solvers."
    )
    return monitor
