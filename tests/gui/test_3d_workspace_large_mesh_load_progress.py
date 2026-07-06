"""Offscreen tests for metadata-only MeshRef load progress state.

These tests use fake readers and in-memory meshes only. They do not spawn
processes, execute solvers, parse solver artifacts, generate/convert meshes,
render PyVista/VTK scenes, auto-save projects, or mutate project schema state.
"""

from __future__ import annotations

import importlib.util
import os
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
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
    from PySide6 import QtWidgets
else:
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
        raise AssertionError("large mesh progress tests must not export screenshots")


class _Diagnostics:
    def __init__(self, message: str) -> None:
        self.message = message

    def summary(self) -> str:
        return self.message


class _BlockingReader:
    def __init__(self, result_factory: Callable[[Path], object]) -> None:
        self.result_factory = result_factory
        self.calls: list[Path] = []
        self.started = threading.Event()
        self.release = threading.Event()

    def __call__(self, path: str | Path) -> object:
        resolved = Path(path)
        self.calls.append(resolved)
        self.started.set()
        if not self.release.wait(timeout=5):
            raise AssertionError("test reader was not released")
        return self.result_factory(resolved)


def _mesh_data() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _mesh_model(mesh_id: str, *, source_path: str = "") -> MeshModel:
    return MeshModel(
        id=mesh_id,
        name=mesh_id,
        points=_mesh_data().points,
        cells=_mesh_data().cells,
        source_path=source_path,
    )


def _success(mesh_id: str = "mesh-a", *, source_path: str = "") -> object:
    return SimpleNamespace(
        mesh=_mesh_model(mesh_id, source_path=source_path),
        diagnostics=(),
        format="vtu",
        source_path=source_path,
    )


def _failure(message: str = "meshio unavailable") -> object:
    return SimpleNamespace(mesh=None, diagnostics=_Diagnostics(message), format="vtu")


def _project(
    *,
    meshes: Sequence[MeshRef] = (),
    results: Sequence[ResultRef] = (),
) -> Project:
    return Project(
        metadata=ProjectMetadata(name="Large Mesh Load Progress Fixture"),
        meshes=meshes,
        results=results,
    )


def _result_ref(result_id: str = "rd-1") -> ResultRef:
    return ResultRef(
        id=result_id,
        path=f"results/{result_id}.json",
        kind="result_dataset",
        metadata={},
    )


def _result_dataset(mesh_ref: str, dataset_id: str = "rd-1") -> ResultDataset:
    field = ResultField(
        name="stress",
        location="node",
        components=("magnitude",),
        rows=tuple(ResultRow(item, {"magnitude": float(item)}) for item in (0, 1, 2)),
    )
    return ResultDataset(
        dataset_id=dataset_id,
        source=f"{dataset_id}.json",
        solver="fake",
        analysis_type="static",
        fields=(field,),
        metadata={"mesh_ref": mesh_ref},
    )


def _window(
    app: object,
    *,
    project: Project,
    reader: Callable[[str | Path], object],
    confirm: Callable[[str], bool] | None = None,
) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(
        project=project,
        mesh_scene_adapter_factory=_NullSceneAdapter,
        metadata_mesh_reader=reader,
        result_mesh_binding_confirmation=confirm,
        metadata_mesh_load_async=True,
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


def _pump_until(app: object, predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    assert QtWidgets is not None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)
    assert predicate()


def _diagnostics(panel: object) -> list[str]:
    return [panel.diagnostics_list.item(i).text() for i in range(panel.diagnostics_list.count())]


def _select_result_field(window: object) -> None:
    window.mesh_viewer.scalar_selector.setCurrentText("result: stress")


def test_load_enters_progress_state_and_rejects_reentry(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _BlockingReader(lambda path: _success("mesh-a", source_path=str(path)))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="mesh-a", path=str(source_path), format="vtu"),)),
        reader=reader,
    )
    window.open_mesh_viewer()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    started = window.load_selected_project_tree_mesh_data()

    assert started is True
    assert reader.started.wait(timeout=1)
    assert reader.calls == [source_path]
    assert window._metadata_mesh_load_state.status == "loading"
    assert "Loading mesh data" in window.mesh_viewer.status_label.text()
    assert window.menu_actions["Load mesh data for selected mesh..."].isEnabled() is False

    second = window.load_selected_project_tree_mesh_data()

    assert second is False
    assert reader.calls == [source_path]
    assert "already in progress" in window.mesh_viewer.status_label.text()

    reader.release.set()
    _pump_until(app, lambda: window._metadata_mesh_load_state.status == "succeeded")
    assert window.menu_actions["Load mesh data for selected mesh..."].isEnabled() is True
    del app


def test_cancel_before_completion_preserves_previous_active_mesh(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _BlockingReader(lambda path: _success("mesh-a", source_path=str(path)))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="mesh-a", path=str(source_path), format="vtu"),)),
        reader=reader,
    )
    before = window.current_project.to_dict()
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    assert window.load_selected_project_tree_mesh_data() is True
    assert reader.started.wait(timeout=1)
    assert window.cancel_selected_project_tree_mesh_load() is True
    assert window._metadata_mesh_load_state.status == "cancel_requested"

    reader.release.set()
    _pump_until(app, lambda: window._metadata_mesh_load_state.status == "canceled")

    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh is None
    assert "canceled" in window.mesh_viewer.status_label.text()
    assert window.current_project.to_dict() == before
    del app


def test_success_commits_only_after_reader_completion(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _BlockingReader(lambda path: _success("mesh-a", source_path=str(path)))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="mesh-a", path=str(source_path), format="vtu"),)),
        reader=reader,
    )
    before = window.current_project.to_dict()
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    assert window.load_selected_project_tree_mesh_data() is True
    assert reader.started.wait(timeout=1)
    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh is None

    reader.release.set()
    _pump_until(app, lambda: window._metadata_mesh_load_state.status == "succeeded")

    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.source == "project_tree_load"
    assert window.selected_mesh_context.mesh is not None
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    assert window.current_project.to_dict() == before
    del app


def test_import_failure_preserves_previous_active_mesh(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _BlockingReader(lambda _path: _failure("meshio missing"))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="mesh-a", path=str(source_path), format="vtu"),)),
        reader=reader,
    )
    before = window.current_project.to_dict()
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    assert window.load_selected_project_tree_mesh_data() is True
    assert reader.started.wait(timeout=1)
    reader.release.set()
    _pump_until(app, lambda: window._metadata_mesh_load_state.status == "failed")

    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert "Could not load MeshData" in window.mesh_viewer.status_label.text()
    assert any("meshio missing" in item for item in _diagnostics(window.mesh_viewer))
    assert window.current_project.to_dict() == before
    del app


def test_stale_selection_completion_does_not_commit_loaded_mesh(
    app: object,
    tmp_path: Path,
) -> None:
    source_a = tmp_path / "mesh-a.vtu"
    source_b = tmp_path / "mesh-b.vtu"
    reader = _BlockingReader(lambda path: _success("mesh-a", source_path=str(path)))
    window = _window(
        app,
        project=_project(
            meshes=(
                MeshRef(id="mesh-a", path=str(source_a), format="vtu"),
                MeshRef(id="mesh-b", path=str(source_b), format="vtu"),
            )
        ),
        reader=reader,
    )
    before = window.current_project.to_dict()
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    assert window.load_selected_project_tree_mesh_data() is True
    assert reader.started.wait(timeout=1)
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-b"))
    reader.release.set()
    _pump_until(app, lambda: window._metadata_mesh_load_state.status == "stale")

    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh_ref == "mesh-b"
    assert window.selected_mesh_context.mesh is None
    assert "selected project-tree mesh changed" in window.mesh_viewer.status_label.text()
    assert window.current_project.to_dict() == before
    del app


def test_result_binding_remains_confirmation_first_after_async_load(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _BlockingReader(lambda path: _success("mesh-a", source_path=str(path)))
    result_ref = _result_ref()
    confirmations: list[str] = []
    window = _window(
        app,
        project=_project(
            meshes=(MeshRef(id="mesh-a", path=str(source_path), format="vtu"),),
            results=(result_ref,),
        ),
        reader=reader,
        confirm=lambda message: confirmations.append(message) or True,
    )
    dataset = _result_dataset("mesh-a")
    original_dataset_metadata = dict(dataset.metadata)
    window.add_result_dataset(dataset)
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    assert window.load_selected_project_tree_mesh_data() is True
    assert reader.started.wait(timeout=1)
    reader.release.set()
    _pump_until(app, lambda: window._metadata_mesh_load_state.status == "succeeded")

    assert result_ref.metadata == {}
    assert window.current_project.results[0].metadata == {}

    window.open_mesh_viewer()
    _select_result_field(window)
    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(confirmations) == 1
    assert MESH_BINDING_METADATA_KEY in window.current_project.results[0].metadata
    assert result_ref.metadata == {}
    assert dataset.metadata == original_dataset_metadata
    del app
