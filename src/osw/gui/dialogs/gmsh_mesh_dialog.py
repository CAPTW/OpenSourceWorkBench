"""Theme-aware Gmsh mesh generation preview dialog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.mesh.gmsh_adapter import GmshAdapter
from osw.mesh.gmsh_geometry import generate_geo_script
from osw.mesh.gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshSizeField,
)

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class GmshMeshDialog(_BaseDialog):
    """Preview and explicitly run bounded primitive Gmsh requests."""

    if QtCore is not None:
        geoGenerated = QtCore.Signal(str)
        meshGenerated = QtCore.Signal(object)

    def __init__(
        self,
        parent: object | None = None,
        *,
        adapter: object | None = None,
        theme_tokens: ThemeTokens | None = None,
        output_dir: str | Path = Path("artifacts") / "mesh",
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswGmshMeshDialog")
        self.setWindowTitle("Generate Mesh with Gmsh")
        self.resize(900, 680)
        self._tokens = theme_tokens or DARK_TOKENS
        self.adapter = adapter or GmshAdapter()
        self.output_dir = Path(output_dir)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.geometry_kind_combo = QtWidgets.QComboBox(self)
        self.geometry_kind_combo.setObjectName("oswGmshGeometryKindCombo")
        self.geometry_kind_combo.addItems(
            [
                GmshGeometryKind.BOX.value,
                GmshGeometryKind.RECTANGLE.value,
                GmshGeometryKind.CYLINDER.value,
                GmshGeometryKind.SPHERE.value,
                GmshGeometryKind.PLATE_WITH_HOLE.value,
            ]
        )
        form.addRow("Geometry", self.geometry_kind_combo)

        self.mesh_dimension_combo = QtWidgets.QComboBox(self)
        self.mesh_dimension_combo.setObjectName("oswGmshMeshDimensionCombo")
        self.mesh_dimension_combo.addItems(
            [GmshMeshDimension.DIM2.value, GmshMeshDimension.DIM3.value]
        )
        self.mesh_dimension_combo.setCurrentText(GmshMeshDimension.DIM3.value)
        form.addRow("Dimension", self.mesh_dimension_combo)

        self.global_mesh_size_edit = QtWidgets.QLineEdit("0.05", self)
        self.global_mesh_size_edit.setObjectName("oswGmshGlobalMeshSizeEdit")
        form.addRow("Mesh Size", self.global_mesh_size_edit)

        self.output_name_edit = QtWidgets.QLineEdit("box", self)
        self.output_name_edit.setObjectName("oswGmshOutputNameEdit")
        form.addRow("Output", self.output_name_edit)

        self.preview_text = QtWidgets.QPlainTextEdit(self)
        self.preview_text.setObjectName("oswGmshPreviewText")
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswGmshDiagnosticsList")
        layout.addWidget(self.diagnostics_list)

        self.result_summary = QtWidgets.QLabel("No mesh run yet.", self)
        self.result_summary.setObjectName("oswGmshMeshResultSummary")
        layout.addWidget(self.result_summary)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.generate_geo_button = QtWidgets.QPushButton("Generate Geo", self)
        self.generate_geo_button.setObjectName("oswGmshGenerateGeoButton")
        self.run_button = QtWidgets.QPushButton("Run Gmsh", self)
        self.run_button.setObjectName("oswGmshRunButton")
        buttons.addWidget(self.generate_geo_button)
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)

        self.generate_geo_button.clicked.connect(self.generate_geo_preview)
        self.run_button.clicked.connect(self.run_gmsh_mesh)
        self.geometry_kind_combo.currentTextChanged.connect(self._sync_dimension_for_kind)
        self.set_theme_tokens(self._tokens)
        self.generate_geo_preview()

    def current_request(self) -> GmshMeshRequest:
        kind = GmshGeometryKind(self.geometry_kind_combo.currentText())
        return GmshMeshRequest(
            geometry=GmshGeometrySpec(
                kind,
                _default_parameters(kind),
                geometry_id=f"{kind.value}_preview",
                units="m",
            ),
            mesh_dimension=self.mesh_dimension_combo.currentText(),
            mesh_size=GmshMeshSizeField(global_size=float(self.global_mesh_size_edit.text())),
            output_dir=self.output_dir,
            output_name=self.output_name_edit.text() or "gmsh_mesh",
            convert_to_vtu=True,
        )

    def generate_geo_preview(self) -> str:
        self.diagnostics_list.clear()
        try:
            script = generate_geo_script(self.current_request())
        except Exception as exc:
            script = ""
            self.diagnostics_list.addItem(str(exc))
        self.preview_text.setPlainText(script)
        self.geoGenerated.emit(script)
        return script

    def run_gmsh_mesh(self) -> object:
        self.diagnostics_list.clear()
        result = self.adapter.generate_mesh(self.current_request())
        self.result_summary.setText(f"Status: {getattr(result.status, 'value', result.status)}")
        diagnostics = getattr(result, "diagnostics", None)
        if diagnostics is not None:
            for message in getattr(diagnostics, "messages", ()):
                self.diagnostics_list.addItem(f"{message.severity.value}: {message.message}")
        self.meshGenerated.emit(result)
        return result

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswGmshMeshDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLineEdit, QComboBox, QPlainTextEdit, QListWidget {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton {"
            f"background-color: {tokens.accent};"
            f"color: {tokens.bg_app};"
            f"border: 1px solid {tokens.primary_hover};"
            "padding: 6px 12px;"
            "}"
        )

    def _sync_dimension_for_kind(self, kind_text: str) -> None:
        if kind_text in {GmshGeometryKind.RECTANGLE.value, GmshGeometryKind.PLATE_WITH_HOLE.value}:
            self.mesh_dimension_combo.setCurrentText(GmshMeshDimension.DIM2.value)
            return
        self.mesh_dimension_combo.setCurrentText(GmshMeshDimension.DIM3.value)


def _default_parameters(kind: GmshGeometryKind) -> dict[str, object]:
    if kind is GmshGeometryKind.RECTANGLE:
        return {"width": 1.0, "height": 0.5}
    if kind is GmshGeometryKind.CYLINDER:
        return {"radius": 0.25, "height": 1.0}
    if kind is GmshGeometryKind.SPHERE:
        return {"radius": 0.5}
    if kind is GmshGeometryKind.PLATE_WITH_HOLE:
        return {"width": 1.0, "height": 0.5, "hole_radius": 0.1, "center": (0.5, 0.25)}
    return {"length": 1.0, "width": 0.2, "height": 0.1}
