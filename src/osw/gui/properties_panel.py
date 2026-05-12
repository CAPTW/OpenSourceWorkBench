"""Properties panel placeholder for selected project items."""

from __future__ import annotations

from .qt_compat import require_qt_widgets


def build_properties_panel(parent: object | None = None) -> object:
    _, QtWidgets = require_qt_widgets()

    panel = QtWidgets.QWidget(parent)
    panel.setObjectName("propertiesPanel")

    layout = QtWidgets.QFormLayout(panel)
    layout.addRow("Project", QtWidgets.QLabel("No project loaded"))
    layout.addRow("Units", QtWidgets.QLabel("Not configured"))
    layout.addRow("Selection", QtWidgets.QLabel("Nothing selected"))
    return panel
