"""Result viewer for structured OSW mesh and result previews."""

from __future__ import annotations

from typing import Any

from osw.mesh.mesh_model import MeshData
from osw.post.pyvista_scene import PyVistaSceneConfig, PyVistaSceneState, build_scene_state

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class ResultViewer(_BaseWidget):
    """PySide6 panel that shows PyVista-ready mesh preview metadata."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("resultViewer")
        self.surface_toggle = QtWidgets.QCheckBox("Surface", self)
        self.surface_toggle.setObjectName("surfaceToggle")
        self.surface_toggle.setChecked(True)
        self.edge_toggle = QtWidgets.QCheckBox("Edges", self)
        self.edge_toggle.setObjectName("edgeToggle")
        self.axis_toggle = QtWidgets.QCheckBox("Axes", self)
        self.axis_toggle.setObjectName("axisToggle")
        self.axis_toggle.setChecked(True)
        self.grid_toggle = QtWidgets.QCheckBox("Grid", self)
        self.grid_toggle.setObjectName("gridToggle")
        self.scalar_field_placeholder = QtWidgets.QLabel("Scalar field: none", self)
        self.scalar_field_placeholder.setObjectName("scalarFieldPlaceholder")
        self.summary_label = QtWidgets.QLabel("Result viewer placeholder", self)
        self.summary_label.setObjectName("resultViewerPlaceholder")
        self.summary_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        toggles = QtWidgets.QHBoxLayout()
        toggles.addWidget(self.surface_toggle)
        toggles.addWidget(self.edge_toggle)
        toggles.addWidget(self.axis_toggle)
        toggles.addWidget(self.grid_toggle)
        toggles.addStretch(1)
        layout.addLayout(toggles)
        layout.addWidget(self.scalar_field_placeholder)
        layout.addWidget(self.summary_label)
        layout.addStretch(1)

    def load_mesh_preview(self, mesh_data: MeshData) -> PyVistaSceneState:
        state = build_scene_state(mesh_data, config=self._scene_config())
        self.summary_label.setText(_mesh_summary_text(state))
        return state

    def _scene_config(self) -> PyVistaSceneConfig:
        return PyVistaSceneConfig(
            show_surface=self.surface_toggle.isChecked(),
            show_edges=self.edge_toggle.isChecked(),
            show_axes=self.axis_toggle.isChecked(),
            show_grid=self.grid_toggle.isChecked(),
            scalar_field=None,
        )


def build_result_viewer(parent: object | None = None) -> object:
    return ResultViewer(parent)


def _mesh_summary_text(state: PyVistaSceneState) -> str:
    return (
        f"Nodes: {state.mesh_info.nodes}\n"
        f"Elements: {state.mesh_info.elements}\n"
        f"Cell types: {', '.join(state.mesh_info.cell_types) or 'none'}\n"
        f"Bounds: {state.bounding_box.minimum} to {state.bounding_box.maximum}"
    )
