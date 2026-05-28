from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class FakeGmshAdapter:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def generate_mesh(self, request: object) -> object:
        from osw.mesh.gmsh_model import GmshMeshResult, GmshMeshStatus

        self.requests.append(request)
        return GmshMeshResult(GmshMeshStatus.OK, request)


def test_gmsh_mesh_dialog_object_names(app: object) -> None:
    from osw.gui.dialogs.gmsh_mesh_dialog import GmshMeshDialog

    dialog = GmshMeshDialog(adapter=FakeGmshAdapter())

    assert dialog.objectName() == "oswGmshMeshDialog"
    assert dialog.geometry_kind_combo.objectName() == "oswGmshGeometryKindCombo"
    assert dialog.mesh_dimension_combo.objectName() == "oswGmshMeshDimensionCombo"
    assert dialog.global_mesh_size_edit.objectName() == "oswGmshGlobalMeshSizeEdit"
    assert dialog.output_name_edit.objectName() == "oswGmshOutputNameEdit"
    assert dialog.generate_geo_button.objectName() == "oswGmshGenerateGeoButton"
    assert dialog.run_button.objectName() == "oswGmshRunButton"
    assert dialog.diagnostics_list.objectName() == "oswGmshDiagnosticsList"
    assert dialog.preview_text.objectName() == "oswGmshPreviewText"
    assert dialog.result_summary.objectName() == "oswGmshMeshResultSummary"


def test_gmsh_mesh_dialog_generates_geo_without_gmsh(app: object) -> None:
    from osw.gui.dialogs.gmsh_mesh_dialog import GmshMeshDialog

    dialog = GmshMeshDialog(adapter=FakeGmshAdapter())
    script = dialog.generate_geo_preview()

    assert "Box(1)" in script
    assert dialog.preview_text.toPlainText() == script


def test_gmsh_mesh_dialog_run_uses_injected_adapter(app: object) -> None:
    from osw.gui.dialogs.gmsh_mesh_dialog import GmshMeshDialog

    adapter = FakeGmshAdapter()
    dialog = GmshMeshDialog(adapter=adapter)
    result = dialog.run_gmsh_mesh()

    assert adapter.requests
    assert getattr(result.status, "value", result.status) == "ok"
    assert "Status: ok" in dialog.result_summary.text()


def test_gmsh_mesh_dialog_theme_switching(app: object) -> None:
    from osw.gui.dialogs.gmsh_mesh_dialog import GmshMeshDialog
    from osw.gui.theme_tokens import get_theme_tokens

    dialog = GmshMeshDialog(adapter=FakeGmshAdapter())

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))
    assert dialog.styleSheet()
