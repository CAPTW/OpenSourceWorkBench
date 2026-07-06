"""Offscreen tests for explicit metadata-only MeshRef load routing.

The route is user-triggered and GUI-local. These tests use fake mesh readers,
small in-memory meshes, and no live PyVista/VTK rendering, solver execution,
parser execution, mesh generation, mesh conversion, project auto-save, or
ProjectSchema mutation.
"""

from __future__ import annotations

import importlib.util
import os
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
        raise AssertionError("metadata-only load route must not export screenshots")


class _Diagnostics:
    def __init__(self, message: str) -> None:
        self.message = message

    def summary(self) -> str:
        return self.message


class _Reader:
    def __init__(self, factory: Callable[[Path], object]) -> None:
        self.factory = factory
        self.calls: list[Path] = []

    def __call__(self, path: str | Path) -> object:
        resolved = Path(path)
        self.calls.append(resolved)
        return self.factory(resolved)


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


def _success(mesh_id: str = "loaded-mesh", *, source_path: str = "") -> object:
    return SimpleNamespace(
        mesh=_mesh_model(mesh_id, source_path=source_path),
        diagnostics=(),
        format="vtu",
        source_path=source_path,
    )


def _failure(message: str = "mesh read failed") -> object:
    return SimpleNamespace(
        mesh=None,
        diagnostics=_Diagnostics(message),
        format="vtu",
    )


def _project(
    *,
    meshes: Sequence[MeshRef] = (),
    results: Sequence[ResultRef] = (),
) -> Project:
    return Project(
        metadata=ProjectMetadata(name="Metadata MeshRef Load Fixture"),
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


def _window(
    app: object,
    *,
    project: Project | None = None,
    reader: Callable[[str | Path], object] | None = None,
    picker: Callable[[], str | Path | None] | None = None,
    confirm: Callable[[str], bool] | None = None,
) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(
        project=project,
        mesh_scene_adapter_factory=_NullSceneAdapter,
        metadata_mesh_reader=reader,
        metadata_mesh_file_picker=picker,
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


def _diagnostics(panel: object) -> list[str]:
    return [panel.diagnostics_list.item(i).text() for i in range(panel.diagnostics_list.count())]


def _select_result_field(window: object) -> None:
    window.mesh_viewer.scalar_selector.setCurrentText("result: stress")


def test_metadata_only_selection_remains_diagnostic_and_does_not_load(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "metadata-only.vtu"
    reader = _Reader(lambda path: _success(source_path=str(path)))
    window = _window(
        app,
        project=_project(
            meshes=(
                MeshRef(
                    id="metadata-only",
                    name="metadata-only.vtu",
                    path=str(source_path),
                    format="vtu",
                ),
            )
        ),
        reader=reader,
    )

    window.project_tree.setCurrentItem(_find_mesh_item(window, "metadata-only"))

    assert reader.calls == []
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh is None
    assert "no in-memory MeshData" in window.selected_mesh_context.diagnostics[0]
    del app


def test_explicit_load_from_absolute_source_path_updates_transient_context(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _Reader(lambda path: _success("mesh-a", source_path=str(path)))
    window = _window(
        app,
        project=_project(
            meshes=(MeshRef(id="mesh-a", name="mesh-a.vtu", path=str(source_path), format="vtu"),)
        ),
        reader=reader,
    )
    before = window.current_project.to_dict()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    loaded = window.load_selected_project_tree_mesh_data()

    assert loaded is True
    assert reader.calls == [source_path]
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.source == "project_tree_load"
    assert window.selected_mesh_context.mesh is not None
    assert window.last_imported_mesh_ref is None
    assert window.current_project.to_dict() == before
    assert window.mesh_viewer is None

    window.open_mesh_viewer()
    assert window.mesh_viewer.current_state().mesh_ref == "mesh-a"
    assert "Loaded project tree mesh" in window.mesh_viewer.status_label.text()
    del app


def test_explicit_load_uses_file_picker_when_source_path_is_missing(
    app: object,
    tmp_path: Path,
) -> None:
    picked_path = tmp_path / "picked.vtu"
    reader = _Reader(lambda path: _success("mesh-picked", source_path=str(path)))
    picker_calls: list[str] = []
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="mesh-picked", name="picked.vtu", format="vtu"),)),
        reader=reader,
        picker=lambda: picker_calls.append("called") or picked_path,
    )
    before = window.current_project.to_dict()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-picked"))

    loaded = window.load_selected_project_tree_mesh_data()

    assert loaded is True
    assert picker_calls == ["called"]
    assert reader.calls == [picked_path]
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh_ref == "mesh-picked"
    assert window.selected_mesh_context.payload["loaded_path"] == str(picked_path)
    assert window.current_project.to_dict() == before
    del app


def test_cancelled_file_choice_preserves_previous_active_mesh(
    app: object,
) -> None:
    reader = _Reader(lambda path: _success(source_path=str(path)))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="metadata-only", name="metadata.vtu"),)),
        reader=reader,
        picker=lambda: None,
    )
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    before = window.current_project.to_dict()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "metadata-only"))

    loaded = window.load_selected_project_tree_mesh_data()

    assert loaded is False
    assert reader.calls == []
    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert "No source path is stored" in window.mesh_viewer.status_label.text()
    assert any("MeshData load was canceled" in item for item in _diagnostics(window.mesh_viewer))
    assert window.current_project.to_dict() == before
    del app


def test_failed_import_preserves_previous_active_mesh_and_reports_diagnostics(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "bad.vtu"
    reader = _Reader(lambda _path: _failure("could not read selected mesh"))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="bad-mesh", path=str(source_path), format="vtu"),)),
        reader=reader,
    )
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    before = window.current_project.to_dict()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "bad-mesh"))

    loaded = window.load_selected_project_tree_mesh_data()

    assert loaded is False
    assert reader.calls == [source_path]
    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert "Could not load MeshData" in window.mesh_viewer.status_label.text()
    assert any("could not read selected mesh" in item for item in _diagnostics(window.mesh_viewer))
    assert window.current_project.to_dict() == before
    del app


def test_path_mismatch_warns_and_does_not_make_mesh_active(
    app: object,
    tmp_path: Path,
) -> None:
    expected_path = tmp_path / "expected.vtu"
    picked_path = tmp_path / "other.vtu"
    reader = _Reader(lambda path: _success("other", source_path=str(path)))
    window = _window(
        app,
        project=_project(
            meshes=(MeshRef(id="mesh-a", name="mesh-a.vtu", path=str(expected_path), format="vtu"),)
        ),
        reader=reader,
    )
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    before = window.current_project.to_dict()
    window.project_tree.setCurrentItem(_find_mesh_item(window, "mesh-a"))

    loaded = window.load_selected_project_tree_mesh_data(path=picked_path)

    assert loaded is False
    assert reader.calls == [picked_path]
    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert "does not match" in window.mesh_viewer.status_label.text()
    assert window.selected_mesh_context is not None
    assert window.selected_mesh_context.mesh is None
    assert window.current_project.to_dict() == before
    del app


def test_non_mesh_row_does_not_execute_load_route(app: object) -> None:
    reader = _Reader(lambda path: _success(source_path=str(path)))
    window = _window(
        app,
        project=_project(meshes=(MeshRef(id="mesh-a", name="mesh-a.vtu"),)),
        reader=reader,
    )
    window._store_imported_mesh_for_viewer(_mesh_data(), mesh_ref="latest")
    window.open_mesh_viewer()
    window.project_tree.setCurrentItem(_find_label(window, "Geometry"))

    loaded = window.load_selected_project_tree_mesh_data()

    assert loaded is False
    assert reader.calls == []
    assert window.mesh_viewer.current_state().mesh_ref == "latest"
    assert "Select a mesh row" in window.mesh_viewer.status_label.text()
    del app


def test_loaded_mesh_still_requires_confirmed_result_binding(
    app: object,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "mesh-a.vtu"
    reader = _Reader(lambda path: _success("mesh-a", source_path=str(path)))
    confirmations: list[str] = []
    result_ref = _result_ref()
    window = _window(
        app,
        project=_project(
            meshes=(MeshRef(id="mesh-a", name="mesh-a.vtu", path=str(source_path), format="vtu"),),
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
    assert result_ref.metadata == {}

    window.open_mesh_viewer()
    _select_result_field(window)
    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(confirmations) == 1
    assert MESH_BINDING_METADATA_KEY in window.current_project.results[0].metadata
    assert result_ref.metadata == {}
    assert dataset.metadata == original_dataset_metadata
    del app
