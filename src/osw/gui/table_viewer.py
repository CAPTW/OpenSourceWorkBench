"""Table viewer placeholder for structured OSW data."""

from __future__ import annotations

from .qt_compat import require_qt_widgets


def build_table_viewer(parent: object | None = None) -> object:
    _, QtWidgets = require_qt_widgets()

    viewer = QtWidgets.QWidget(parent)
    viewer.setObjectName("tableViewer")

    layout = QtWidgets.QVBoxLayout(viewer)
    label = QtWidgets.QLabel("Table viewer placeholder")
    label.setObjectName("tableViewerPlaceholder")
    layout.addWidget(label)
    layout.addStretch(1)
    return viewer
