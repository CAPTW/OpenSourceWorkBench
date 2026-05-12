"""Result viewer placeholder for structured OSW datasets."""

from __future__ import annotations

from .qt_compat import require_qt_widgets


def build_result_viewer(parent: object | None = None) -> object:
    _, QtWidgets = require_qt_widgets()

    viewer = QtWidgets.QWidget(parent)
    viewer.setObjectName("resultViewer")

    layout = QtWidgets.QVBoxLayout(viewer)
    label = QtWidgets.QLabel("Result viewer placeholder")
    label.setObjectName("resultViewerPlaceholder")
    layout.addWidget(label)
    layout.addStretch(1)
    return viewer
