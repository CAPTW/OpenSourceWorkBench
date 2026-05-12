"""Properties panel for selected project items."""

from __future__ import annotations

from typing import Any

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

DEFAULT_PROPERTIES = {
    "Project": "No project loaded",
    "Units": "Not configured",
    "Selection": "Nothing selected",
    "Workflow step": "Select a project item",
}

NODE_PROPERTIES = {
    "OSW Project": {
        "Selection": "OSW Project",
        "Workflow step": "Project overview",
    },
    "Geometry": {
        "Selection": "Geometry",
        "Workflow step": "Import or preview standard geometry",
    },
    "Mesh": {
        "Selection": "Mesh",
        "Workflow step": "Import or generate mesh",
    },
    "Scripts": {
        "Selection": "Scripts",
        "Workflow step": "Preview script data safely",
    },
    "Physics": {
        "Selection": "Physics",
        "Workflow step": "Configure units, materials, and boundary data",
    },
    "Solvers": {
        "Selection": "Solvers",
        "Workflow step": "Prepare bounded solver workflows",
    },
    "Results": {
        "Selection": "Results",
        "Workflow step": "Inspect structured result datasets",
    },
    "Reports": {
        "Selection": "Reports",
        "Workflow step": "Export an HTML report",
    },
}


def properties_for_node(node_label: str) -> dict[str, str]:
    rows = dict(DEFAULT_PROPERTIES)
    rows.update(NODE_PROPERTIES.get(node_label, {"Selection": node_label or "Nothing selected"}))
    return rows


class PropertiesPanel(_BaseWidget):
    """Small form panel that mirrors the active project tree selection."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("propertiesPanel")
        self._labels: dict[str, Any] = {}

        layout = QtWidgets.QFormLayout(self)
        for key, value in DEFAULT_PROPERTIES.items():
            value_label = QtWidgets.QLabel(value)
            value_label.setObjectName(_row_object_name(key))
            self._labels[key] = value_label
            layout.addRow(key, value_label)

    def set_node_selection(self, node_label: str) -> None:
        self.set_properties(properties_for_node(node_label))

    def set_properties(self, rows: dict[str, str]) -> None:
        for key, value in rows.items():
            label = self._labels.get(key)
            if label is not None:
                label.setText(value)

    def row_value(self, key: str) -> str:
        label = self._labels[key]
        return label.text()


def build_properties_panel(parent: object | None = None) -> object:
    return PropertiesPanel(parent)


def _row_object_name(key: str) -> str:
    words = "".join(part.capitalize() for part in key.split())
    return f"property{words}"
