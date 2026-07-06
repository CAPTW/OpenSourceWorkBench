"""Offscreen tests for project-tree mesh selection driving 3D workspace preview.

The selected mesh context is GUI-local and preview-first. These tests use a fake
scene adapter and in-memory meshes only; they do not render, save projects,
parse solver artifacts, generate meshes, or execute external tools.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Callable, Sequence
from types import SimpleNamespace

import pytest

from osw.core.project_schema import MeshRef, Project, ProjectMetadata, ResultRef
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import MESH_BINDING_METADATA_KEY
from osw.mesh.mesh_model import MeshCellBlock, MeshData, MeshModel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtCore, QtWidgets
else:
    QtCore = None
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class _NullSceneAdapter:
    def load_mesh(self, mesh: object, scene_input: object, scene_state: object) -> object:
        return SimpleNamespace(warnings=(), rendered=False)

    def set_view_state(self, scene_state: object) -> None:
        return None

    def export_screenshot_record(self, path: object, **_kwargs: object) -> object:
        raise AssertionError("selected-mesh UX must not export screenshots")


def _mesh_data() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _mesh_model(mesh_id: str) -> MeshModel:
    return MeshModel(
        id=mesh_id,
        name=mesh_id,
        points=_mesh_data().points,
        cells=_mesh_data().cells,
        source_path=f"meshes/{mesh_id}.vtu",
    )


def _import_result(mesh_id: str) -> object:
    return SimpleNamespace(mesh=_mesh_model(mesh_id), diagnostics=None)


def _result_dataset(mesh_ref: str, dataset_id: str = "rd-1") -> ResultDataset:
    field = ResultField(
        name="stress",
        location="node",
        components=("magnitude",),
        rows=tuple(
            ResultRow(item, {"magnitude": float(item) * 10.0})
            for item in (0, 1, 2)
        ),
    )
    return ResultDataset(
        dataset_id=dataset_id,
        source=f"{dataset_id}.json",
        solver="fake",
        analysis_type="static",
        fields=(field,),
        metadata={"mesh_ref": mesh_ref},
    )


def _result_ref(result_id: str = "rd-1") -> ResultRef:
    return ResultRef(
        id=result_id,
        path=f"results/{result_id}.json",
        kind="result_dataset",
        metadata={},
    )


def _project(
    *,
    meshes: Sequence[MeshRef] = (),
    results: Sequence[ResultRef] = (),
) -> Project:
    return Project(
        metadata=ProjectMetadata(name="Selected Mesh UX Fixture"),
        meshes=meshes,
        results=results,
    )


def _window(
    app: object,
    *,
    project: Project | None = None,
    confirm: Callable[[str], bool] | None = None,
) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(
        project=project,
        mesh_scene_adapter_factory=_NullSceneAdapter,
        result_mesh_binding_confirmation=confirm,
    )


def _walk_tree(tree: object) -> list[object]:
    items: list[object] = []

    def visit(item: object) -> None:
        items.append(item)
        for index in range(item.childCount()):
            visit(item.child(index))

    for top_index in range(tree.topLevelItemCount()):
        visit(tree.topLevelItem(top_index))
    return items


def _find_mesh_item(window: object, mesh_ref: str) -> object:
    for item in _walk_tree(window.project_tree):
        payload = window.project_tree_panel.item_payload(item)
        if payload.get("mesh_ref") == mesh_ref or payload.get("id") == mesh_ref:
            return item
    raise AssertionError(f"mesh item not found: {mesh_ref}")


def _find_label(window: object, label: str) -> object:
    for item in _walk_tree(window.project_tree):
        if item.text(0) == label:
            return item
    raise AssertionError(f"tree label not found: {label}")


def _select_result_field(window: object) -> None:
    window.mesh_viewer.scalar_selector.setCurrentText("result: stress")


def test_project_tree_mesh_rows_expose_stable_payload(app: object) -> None:
    assert QtCore is not None
    mesh_ref = MeshRef(id="mesh-id", name="duplicate-label", path="meshes/a.vtu", format="vtu")
    window = _window(app, project=_project(meshes=(mesh_ref,)))

    item = _find_mesh_item(window, "mesh-id")
    payload = window.project_tree_panel.item_payload(item)

    assert item.data(0, QtCore.Qt.ItemDataRole.UserRole) == "mesh_ref"
    assert payload["mesh_ref"] == "mesh-id"
    assert payload["name"] == "duplicate-label"
    assert payload["path"] == "meshes/a.vtu"
    del app


def test_selecting_available_project_tree_mesh_records_context_without_saving(
    app: object,
) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    before = window.current_project.to_dict()

    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    context = window.selected_mesh_context
    assert context is not None
    assert context.mesh_ref == "mesh-a"
    assert context.source == "project_tree"
    assert context.mesh is not None
    assert window.current_project.to_dict() == before
    assert window.mesh_viewer_dialog is None
    del app


def test_selected_project_tree_mesh_opens_viewer_even_when_not_latest(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.attach_mesh_to_project(_import_result("mesh-b"))
    assert window.last_imported_mesh_ref == "mesh-b"

    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))
    window.open_mesh_viewer()

    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    assert "Selected project tree mesh" in window.mesh_viewer.status_label.text()
    del app


def test_metadata_only_project_tree_mesh_is_diagnostic_and_non_destructive(
    app: object,
) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.open_mesh_viewer()
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    metadata_mesh = MeshRef(
        id="metadata-only",
        name="metadata-only.vtu",
        path="meshes/metadata-only.vtu",
        format="vtu",
    )
    project = _project(meshes=(*window.current_project.meshes, metadata_mesh))
    window.set_project(project)
    before = window.current_project.to_dict()

    window.project_tree.setCurrentItem(_find_mesh_item(window, "metadata-only"))

    context = window.selected_mesh_context
    assert context is not None
    assert context.mesh is None
    assert "no in-memory MeshData" in context.diagnostics[0]
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    assert "no in-memory MeshData" in window.mesh_viewer.status_label.text()
    assert window.current_project.to_dict() == before
    del app


def test_non_mesh_project_tree_selection_leaves_active_mesh_unchanged(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))
    window.open_mesh_viewer()

    window.project_tree.setCurrentItem(_find_label(window, "Geometry"))

    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh_ref == "mesh-a"
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    assert window.properties_panel.row_value("Selection") == "Geometry"
    del app


def test_latest_imported_mesh_remains_fallback_without_selection(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.attach_mesh_to_project(_import_result("mesh-b"))

    window.open_mesh_viewer()

    assert window.selected_mesh_context is None
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-b"
    del app


def test_selecting_mesh_restages_result_dataset_for_active_mesh(app: object) -> None:
    window = _window(app)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.attach_mesh_to_project(_import_result("mesh-b"))
    window.add_result_dataset(_result_dataset("mesh-a"))

    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))
    window.open_mesh_viewer()

    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    assert window.mesh_viewer.current_result_dataset_id() == "rd-1"
    assert "active mesh 'mesh-a'" in window.mesh_viewer.binding_status_label.text()
    del app


def test_confirmed_binding_uses_selected_project_tree_mesh(app: object) -> None:
    confirmations: list[str] = []

    def _confirm(message: str) -> bool:
        confirmations.append(message)
        return True

    result_ref = _result_ref()
    window = _window(app, project=_project(results=(result_ref,)), confirm=_confirm)
    window.attach_mesh_to_project(_import_result("mesh-a"))
    window.attach_mesh_to_project(_import_result("mesh-b"))
    dataset = _result_dataset("mesh-a")
    original_metadata = dict(dataset.metadata)
    window.add_result_dataset(dataset)
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))
    window.open_mesh_viewer()
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(confirmations) == 1
    assert "Mesh: mesh-a" in confirmations[0]
    updated = window.current_project.results[0]
    assert updated is not result_ref
    assert updated.metadata["source_mesh_ref"] == "mesh-a"
    assert updated.metadata[MESH_BINDING_METADATA_KEY]["mesh_ref"] == "mesh-a"
    assert result_ref.metadata == {}
    assert dataset.metadata == original_metadata
    del app
