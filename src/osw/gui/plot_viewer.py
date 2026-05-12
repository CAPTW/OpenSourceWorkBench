"""Plot viewer placeholder for future Matplotlib/PyVista surfaces."""

from __future__ import annotations

from .qt_compat import require_qt_widgets


def build_plot_viewer(parent: object | None = None) -> object:
    _, QtWidgets = require_qt_widgets()

    viewer = QtWidgets.QWidget(parent)
    viewer.setObjectName("plotViewer")

    layout = QtWidgets.QVBoxLayout(viewer)
    label = QtWidgets.QLabel("Plot viewer placeholder")
    label.setObjectName("plotViewerPlaceholder")
    layout.addWidget(label)
    layout.addStretch(1)
    return viewer
