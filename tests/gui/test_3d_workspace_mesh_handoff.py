"""Offscreen tests for the 3D workspace mesh hand-off into the viewer.

The meshio import path (`attach_mesh_to_project`) stores the latest imported mesh
and feeds it to the "3D Mesh Preview" panel: populate-on-open plus refresh-if-open,
latest wins, and never auto-opening the dialog on import. All tests run headless
with a fake scene adapter, so no live PyVista/VTK rendering is required.
"""

from __future__ import annotations

import importlib.util
import os
from types import SimpleNamespace

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshModel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class _NullSceneAdapter:
    """Fake adapter; its methods are never invoked by the hand-off (set_mesh only)."""

    def load_mesh(self, mesh: object, scene_input: object, scene_state: object) -> object:
        return SimpleNamespace(warnings=(), rendered=False)

    def set_view_state(self, scene_state: object) -> None:
        return None

    def export_screenshot_record(self, path: object, **_kwargs: object) -> object:
        raise AssertionError("hand-off must not export screenshots")


def _mesh_model(mesh_id: str = "demo-mesh") -> MeshModel:
    return MeshModel(
        id=mesh_id,
        name=mesh_id,
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _import_result(mesh_id: str = "demo-mesh") -> object:
    return SimpleNamespace(mesh=_mesh_model(mesh_id), diagnostics=None)


def _window(app: object) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(mesh_scene_adapter_factory=_NullSceneAdapter)


def test_import_stores_latest_without_opening_dialog(app: object) -> None:
    window = _window(app)

    assert window.attach_mesh_to_project(_import_result("demo-mesh")) is True

    assert window.last_imported_mesh_data is not None
    assert window.last_imported_mesh_ref == "demo-mesh"
    # No auto-open: importing does not create/show the preview dialog.
    assert window.mesh_viewer_dialog is None
    assert window.mesh_viewer is None
    del app


def test_open_after_import_populates_panel(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("demo-mesh"))

    dialog = window.open_mesh_viewer()

    assert dialog.objectName() == "oswMeshViewerDialog"
    panel = window.mesh_viewer
    assert panel is not None
    assert "Nodes: 3" in panel.summary_label.text()
    assert panel.current_state().mesh_ref == "demo-mesh"
    del app


def test_import_while_open_refreshes_panel(app: object) -> None:
    window = _window(app)
    dialog = window.open_mesh_viewer()
    assert "No mesh loaded" in window.mesh_viewer.summary_label.text()

    window.attach_mesh_to_project(_import_result("live-mesh"))

    # Same dialog instance; content refreshed in place (no re-open needed).
    assert window.mesh_viewer_dialog is dialog
    assert "Nodes: 3" in window.mesh_viewer.summary_label.text()
    assert window.mesh_viewer.current_state().mesh_ref == "live-mesh"
    del app


def test_latest_wins_across_multiple_imports(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.attach_mesh_to_project(_import_result("mesh-b"))

    window.open_mesh_viewer()

    assert window.last_imported_mesh_ref == "mesh-b"
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-b"
    del app


def test_open_populate_does_not_clobber_existing_mesh(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.open_mesh_viewer()
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"

    # Re-opening must not re-apply the stored latest over the current panel mesh.
    window.open_mesh_viewer()
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    del app


def test_import_diagnostics_only_result_is_friendly(app: object) -> None:
    window = _window(app)

    ok = window.attach_mesh_to_project(
        SimpleNamespace(mesh=None, diagnostics=SimpleNamespace(summary=lambda: "no mesh"))
    )

    assert ok is False
    assert window.last_imported_mesh_data is None
    assert window.mesh_viewer_dialog is None
    del app


def test_store_helper_derives_mesh_data_and_ref(app: object) -> None:
    window = _window(app)

    window._store_imported_mesh_for_viewer(_mesh_model("seq-mesh"))

    assert window.last_imported_mesh_ref == "seq-mesh"
    # The stored payload is a MeshData (converted from the MeshModel), not the model.
    assert hasattr(window.last_imported_mesh_data, "points")
    assert not hasattr(window.last_imported_mesh_data, "to_mesh_data")
    del app
