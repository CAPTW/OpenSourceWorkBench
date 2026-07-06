"""Offscreen tests for the general file-import mesh hand-off into the viewer.

The general import path (`import_file` -> `workflow_session.import_path`) yields a
`WorkbenchItem` whose `mesh_data` is an already-built `MeshData`; MainWindow feeds
the last such item into the "3D Mesh Preview" panel using its `item_id` as the
mesh reference, preserving populate-on-open + refresh-if-open, latest wins, and
no auto-open. All tests run headless with a fake scene adapter (no live render).
"""

from __future__ import annotations

import importlib.util
import os
from types import SimpleNamespace

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData

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


def _mesh_data() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _mesh_item(item_id: str) -> object:
    return SimpleNamespace(item_id=item_id, mesh_data=_mesh_data())


def _non_mesh_item(item_id: str) -> object:
    return SimpleNamespace(item_id=item_id, mesh_data=None)


def _operation(*items: object) -> object:
    return SimpleNamespace(items=tuple(items))


def _window(app: object) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(mesh_scene_adapter_factory=_NullSceneAdapter)


def test_store_workflow_mesh_stores_latest_without_opening(app: object) -> None:
    window = _window(app)

    window._store_workflow_mesh_for_viewer(_operation(_mesh_item("mesh-3")))

    assert window.last_imported_mesh_ref == "mesh-3"
    assert window.last_imported_mesh_data is not None
    # No auto-open: feeding a mesh does not create/show the preview dialog.
    assert window.mesh_viewer_dialog is None
    assert window.mesh_viewer is None
    del app


def test_open_after_general_import_populates(app: object) -> None:
    window = _window(app)
    window._store_workflow_mesh_for_viewer(_operation(_mesh_item("mesh-3")))

    dialog = window.open_mesh_viewer()

    assert dialog.objectName() == "oswMeshViewerDialog"
    panel = window.mesh_viewer
    assert "Nodes: 3" in panel.summary_label.text()
    assert panel.current_state().mesh_ref == "mesh-3"
    del app


def test_general_import_while_open_refreshes_in_place(app: object) -> None:
    window = _window(app)
    dialog = window.open_mesh_viewer()
    assert "No mesh loaded" in window.mesh_viewer.summary_label.text()

    window._store_workflow_mesh_for_viewer(_operation(_mesh_item("live")))

    # Same dialog instance; content refreshed in place (no re-open needed).
    assert window.mesh_viewer_dialog is dialog
    assert "Nodes: 3" in window.mesh_viewer.summary_label.text()
    assert window.mesh_viewer.current_state().mesh_ref == "live"
    del app


def test_latest_wins_within_operation(app: object) -> None:
    window = _window(app)

    window._store_workflow_mesh_for_viewer(_operation(_mesh_item("mesh-a"), _mesh_item("mesh-b")))

    assert window.last_imported_mesh_ref == "mesh-b"
    del app


def test_non_mesh_items_are_ignored(app: object) -> None:
    window = _window(app)

    window._store_workflow_mesh_for_viewer(
        _operation(_non_mesh_item("geo-1"), _non_mesh_item("script-1"))
    )

    assert window.last_imported_mesh_data is None
    assert window.last_imported_mesh_ref is None
    assert window.mesh_viewer_dialog is None
    del app


def test_mixed_operation_feeds_only_mesh_item(app: object) -> None:
    window = _window(app)

    window._store_workflow_mesh_for_viewer(
        _operation(_non_mesh_item("geo-1"), _mesh_item("mesh-x"), _non_mesh_item("mat-1"))
    )

    assert window.last_imported_mesh_ref == "mesh-x"
    assert window.last_imported_mesh_data is not None
    del app


def test_explicit_mesh_ref_overrides_derived(app: object) -> None:
    # A bare MeshData has no id/name; the explicit mesh_ref must be used.
    window = _window(app)

    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="explicit-1")

    assert window.last_imported_mesh_ref == "explicit-1"
    del app


def test_import_file_feeds_general_mesh_item(app: object, monkeypatch) -> None:
    from osw.gui.workflow_service import WorkbenchItem, WorkflowOperation

    window = _window(app)
    item = WorkbenchItem(
        item_id="mesh-7",
        section="Mesh",
        label="Mesh: demo.msh",
        item_type="Mesh (gmsh)",
        workflow_step="Imported mesh preview",
        status="Imported",
        summary="3 nodes, 1 elements",
        path="demo.msh",
        mesh_data=_mesh_data(),
    )
    operation = WorkflowOperation(
        title="Import", status="Imported", logs=(), items=(item,), selected_item_id="mesh-7"
    )
    monkeypatch.setattr(window.workflow_session, "import_path", lambda _path: operation)

    window.import_file("demo.msh")

    assert window.last_imported_mesh_ref == "mesh-7"
    assert window.last_imported_mesh_data is item.mesh_data
    # Import must not auto-open the preview dialog.
    assert window.mesh_viewer_dialog is None
    del app
