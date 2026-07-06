"""Offscreen tests for confirmed ResultDataset-to-mesh binding persistence.

The GUI flow is confirmation-first and metadata-only. These tests inject a
confirmation callback and a fake scene adapter; they do not render, save project
files, parse solver artifacts, generate meshes, or execute external tools.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Callable, Sequence
from types import SimpleNamespace

import pytest

from osw.core.project_schema import Project, ProjectMetadata, ResultRef
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import MESH_BINDING_METADATA_KEY, ResultMeshBinding
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.scene_model import SceneInputRef, SceneScreenshotRecord, SceneViewState

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


class RecordingSceneAdapter:
    def __init__(self) -> None:
        self.load_calls: list[tuple[MeshData, SceneInputRef, SceneViewState]] = []

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: SceneInputRef,
        scene_state: SceneViewState,
    ) -> object:
        self.load_calls.append((mesh, scene_input, scene_state))
        return SimpleNamespace(warnings=(), rendered=False)

    def set_view_state(self, scene_state: SceneViewState) -> None:
        return None

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: SceneViewState,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        return SceneScreenshotRecord(id=record_id, path=str(path), scene_state=scene_state)


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _result_dataset(
    dataset_id: str = "rd-1",
    *,
    mesh_ref: str | None = "mesh-1",
) -> ResultDataset:
    field = ResultField(
        name="stress",
        location="node",
        components=("magnitude",),
        rows=tuple(
            ResultRow(item, {"magnitude": float(item) * 10.0}) for item in (0, 1, 2)
        ),
    )
    metadata = {"mesh_ref": mesh_ref} if mesh_ref is not None else {}
    return ResultDataset(
        dataset_id=dataset_id,
        source=f"{dataset_id}.json",
        solver="fake",
        analysis_type="static",
        fields=(field,),
        metadata=metadata,
    )


def _project(*results: ResultRef) -> Project:
    return Project(
        metadata=ProjectMetadata(name="Binding GUI Flow Fixture"),
        results=results,
    )


def _result_ref(
    result_id: str = "rd-1",
    *,
    metadata: dict[str, object] | None = None,
) -> ResultRef:
    return ResultRef(
        id=result_id,
        path=f"results/{result_id}.json",
        kind="result_dataset",
        metadata=metadata or {},
    )


def _window(
    *,
    app: object,
    project: Project | None = None,
    confirm: bool | None = True,
    selector: Callable[[Sequence[object]], object | None] | None = None,
) -> tuple[object, list[str]]:
    from osw.gui.main_window import MainWindow

    assert app is not None
    confirmations: list[str] = []

    def _confirm(message: str) -> bool:
        confirmations.append(message)
        return bool(confirm)

    window = MainWindow(
        project=project or _project(_result_ref()),
        mesh_scene_adapter_factory=RecordingSceneAdapter,
        result_mesh_binding_confirmation=_confirm,
        result_mesh_binding_target_selector=selector,
    )
    return window, confirmations


def _recording_selector(
    recorded: list[tuple[object, ...]],
    selection: object | None,
) -> Callable[[Sequence[object]], object | None]:
    def _select(candidates: Sequence[object]) -> object | None:
        recorded.append(tuple(candidates))
        return selection

    return _select


def _stage_dataset(window: object, dataset: ResultDataset | None = None) -> ResultDataset:
    staged = dataset or _result_dataset()
    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    window.add_result_dataset(staged)
    window.open_mesh_viewer()
    return staged


def _select_result_field(window: object) -> None:
    window.mesh_viewer.scalar_selector.setCurrentText("result: stress")


def _diagnostics(panel: object) -> list[str]:
    return [panel.diagnostics_list.item(i).text() for i in range(panel.diagnostics_list.count())]


def test_preview_staging_does_not_mutate_project_metadata(app: object) -> None:
    result_ref = _result_ref(metadata={"keep": "yes"})
    window, _confirmations = _window(app=app, project=_project(result_ref))

    dataset = _stage_dataset(window)

    assert window.current_project.results[0].metadata == {"keep": "yes"}
    assert dataset.metadata == {"mesh_ref": "mesh-1"}
    assert "not persisted" in window.mesh_viewer.binding_status_label.text()
    del app


def test_confirmed_binding_replaces_one_result_ref(app: object) -> None:
    result_ref = _result_ref(metadata={"keep": "yes"})
    other_ref = _result_ref("rd-2", metadata={"other": "yes"})
    window, confirmations = _window(app=app, project=_project(result_ref, other_ref))
    dataset = _stage_dataset(window)
    original_metadata = dict(dataset.metadata)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(confirmations) == 1
    assert "does not save the project file" in confirmations[0]
    updated = window.current_project.results[0]
    untouched = window.current_project.results[1]
    assert updated is not result_ref
    assert untouched is other_ref
    assert updated.metadata["keep"] == "yes"
    assert updated.metadata["source_mesh_ref"] == "mesh-1"
    binding = updated.metadata["mesh_binding"]
    assert binding["mesh_ref"] == "mesh-1"
    assert binding["result_dataset_id"] == "rd-1"
    assert binding["field_id"] == "stress"
    assert binding["mesh_signature"] == {"node_count": 3, "cell_count": 1}
    assert result_ref.metadata == {"keep": "yes"}
    assert dataset.metadata == original_metadata
    assert "Persisted result/mesh binding" in window.mesh_viewer.binding_status_label.text()
    del app


def test_confirmation_cancel_does_not_mutate_project(app: object) -> None:
    result_ref = _result_ref(metadata={"keep": "yes"})
    window, confirmations = _window(app=app, project=_project(result_ref), confirm=False)
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert len(confirmations) == 1
    assert window.current_project.results[0] is result_ref
    assert window.current_project.results[0].metadata == {"keep": "yes"}
    assert "not persisted" in window.mesh_viewer.binding_status_label.text()
    del app


def test_no_active_mesh_blocks_without_confirmation(app: object) -> None:
    result_ref = _result_ref()
    window, confirmations = _window(app=app, project=_project(result_ref))
    window.open_mesh_viewer()

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert "No active mesh" in window.mesh_viewer.binding_status_label.text()
    assert MESH_BINDING_METADATA_KEY not in result_ref.metadata
    del app


def test_no_staged_dataset_blocks_without_confirmation(app: object) -> None:
    result_ref = _result_ref()
    window, confirmations = _window(app=app, project=_project(result_ref))
    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    window.open_mesh_viewer()

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert "No result dataset is staged" in window.mesh_viewer.binding_status_label.text()
    assert MESH_BINDING_METADATA_KEY not in result_ref.metadata
    del app


def test_missing_result_field_blocks_when_required(app: object) -> None:
    result_ref = _result_ref()
    window, confirmations = _window(app=app, project=_project(result_ref))
    _stage_dataset(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert "Select a result field" in window.mesh_viewer.binding_status_label.text()
    assert MESH_BINDING_METADATA_KEY not in result_ref.metadata
    del app


def test_no_matching_result_ref_blocks_without_confirmation(app: object) -> None:
    result_ref = _result_ref("unrelated")
    window, confirmations = _window(app=app, project=_project(result_ref))
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert "No persisted ResultRef target" in window.mesh_viewer.binding_status_label.text()
    assert MESH_BINDING_METADATA_KEY not in result_ref.metadata
    del app


def test_exact_result_ref_match_wins_over_metadata_match(app: object) -> None:
    first = _result_ref("rd-1")
    second = _result_ref("other", metadata={"result_dataset_id": "rd-1"})
    window, confirmations = _window(app=app, project=_project(first, second))
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(confirmations) == 1
    assert MESH_BINDING_METADATA_KEY in window.current_project.results[0].metadata
    assert MESH_BINDING_METADATA_KEY not in window.current_project.results[1].metadata
    del app


def test_multiple_metadata_result_ref_matches_require_explicit_selection(
    app: object,
) -> None:
    first = _result_ref("first", metadata={"result_dataset_id": "rd-1"})
    second = _result_ref("second", metadata={"dataset_id": "rd-1"})
    selections: list[tuple[object, ...]] = []
    window, confirmations = _window(
        app=app,
        project=_project(first, second),
        selector=_recording_selector(selections, None),
    )
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert len(selections) == 1
    assert len(selections[0]) == 2
    labels = [candidate.label for candidate in selections[0]]
    assert all("metadata match" in label for label in labels)
    assert any("id=first" in label for label in labels)
    assert any("id=second" in label for label in labels)
    assert "target selection was cancelled" in window.mesh_viewer.binding_status_label.text()
    assert any(
        "No ResultRef target was selected" in item
        for item in _diagnostics(window.mesh_viewer)
    )
    assert MESH_BINDING_METADATA_KEY not in first.metadata
    assert MESH_BINDING_METADATA_KEY not in second.metadata
    del app


def test_duplicate_exact_result_refs_can_select_one_before_confirmation(
    app: object,
) -> None:
    first = _result_ref("rd-1")
    second = _result_ref("rd-1", metadata={"label": "duplicate"})
    selections: list[tuple[object, ...]] = []
    window, confirmations = _window(
        app=app,
        project=_project(first, second),
        selector=_recording_selector(selections, 1),
    )
    dataset = _stage_dataset(window)
    original_metadata = dict(dataset.metadata)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(selections) == 1
    assert len(confirmations) == 1
    assert len(window.current_project.results) == 2
    assert window.current_project.results[0] is first
    updated = window.current_project.results[1]
    assert updated is not second
    assert updated.metadata["label"] == "duplicate"
    assert updated.metadata["source_mesh_ref"] == "mesh-1"
    assert updated.metadata["mesh_binding"]["result_dataset_id"] == "rd-1"
    assert MESH_BINDING_METADATA_KEY not in first.metadata
    assert second.metadata == {"label": "duplicate"}
    assert dataset.metadata == original_metadata
    del app


def test_selected_target_then_rejected_confirmation_leaves_project_unchanged(
    app: object,
) -> None:
    first = _result_ref("first", metadata={"result_dataset_id": "rd-1"})
    second = _result_ref("second", metadata={"dataset_id": "rd-1"})
    selections: list[tuple[object, ...]] = []
    window, confirmations = _window(
        app=app,
        project=_project(first, second),
        confirm=False,
        selector=_recording_selector(selections, 0),
    )
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert len(selections) == 1
    assert len(confirmations) == 1
    assert window.current_project.results[0] is first
    assert window.current_project.results[1] is second
    assert MESH_BINDING_METADATA_KEY not in first.metadata
    assert MESH_BINDING_METADATA_KEY not in second.metadata
    assert "confirmation was cancelled" in window.mesh_viewer.binding_status_label.text()
    del app


def test_source_path_candidates_can_be_shown_and_selected(app: object) -> None:
    first = _result_ref("first", metadata={"source": "rd-1.json"})
    second = _result_ref("second", metadata={"source_path": "rd-1.json"})
    selections: list[tuple[object, ...]] = []
    window, confirmations = _window(
        app=app,
        project=_project(first, second),
        selector=_recording_selector(selections, 1),
    )
    dataset = _stage_dataset(window)
    original_metadata = dict(dataset.metadata)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is True
    assert len(selections) == 1
    labels = [candidate.label for candidate in selections[0]]
    assert all("source/path match" in label for label in labels)
    assert any("id=first" in label for label in labels)
    assert any("id=second" in label for label in labels)
    assert len(confirmations) == 1
    assert window.current_project.results[0] is first
    updated = window.current_project.results[1]
    assert updated is not second
    assert updated.metadata["source_path"] == "rd-1.json"
    assert updated.metadata["source_mesh_ref"] == "mesh-1"
    assert updated.metadata["mesh_binding"]["field_id"] == "stress"
    assert MESH_BINDING_METADATA_KEY not in first.metadata
    assert second.metadata == {"source_path": "rd-1.json"}
    assert dataset.metadata == original_metadata
    del app


def test_stale_selected_multi_target_candidate_surfaces_without_mutation(
    app: object,
) -> None:
    stale_binding = ResultMeshBinding(
        mesh_ref="mesh-2",
        result_dataset_id="rd-1",
        field_id="stress",
        mesh_signature={"node_count": 3, "cell_count": 1},
    )
    first = _result_ref(
        "first",
        metadata={
            "result_dataset_id": "rd-1",
            "mesh_binding": stale_binding.to_dict(),
        },
    )
    second = _result_ref("second", metadata={"dataset_id": "rd-1"})
    selections: list[tuple[object, ...]] = []
    window, confirmations = _window(
        app=app,
        project=_project(first, second),
        selector=_recording_selector(selections, 0),
    )
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert len(selections) == 1
    assert confirmations == []
    assert window.current_project.results[0] is first
    assert window.current_project.results[1] is second
    assert MESH_BINDING_METADATA_KEY in first.metadata
    assert MESH_BINDING_METADATA_KEY not in second.metadata
    assert any("active mesh" in item for item in _diagnostics(window.mesh_viewer))
    del app


def test_existing_stale_binding_surfaces_without_mutation(app: object) -> None:
    stale_binding = ResultMeshBinding(
        mesh_ref="mesh-2",
        result_dataset_id="rd-1",
        field_id="stress",
        mesh_signature={"node_count": 3, "cell_count": 1},
    )
    result_ref = _result_ref(metadata={"mesh_binding": stale_binding.to_dict()})
    window, confirmations = _window(app=app, project=_project(result_ref))
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert window.current_project.results[0] is result_ref
    assert any("active mesh" in item for item in _diagnostics(window.mesh_viewer))
    del app


def test_existing_count_mismatch_surfaces_without_mutation(app: object) -> None:
    mismatched_binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="rd-1",
        field_id="stress",
        mesh_signature={"node_count": 99, "cell_count": 1},
    )
    result_ref = _result_ref(metadata={"mesh_binding": mismatched_binding.to_dict()})
    window, confirmations = _window(app=app, project=_project(result_ref))
    _stage_dataset(window)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert confirmations == []
    assert window.current_project.results[0] is result_ref
    assert any("node count" in item for item in _diagnostics(window.mesh_viewer))
    del app


def test_proposal_metadata_mismatch_surfaces_after_confirmation_without_mutation(
    app: object,
) -> None:
    result_ref = _result_ref()
    window, confirmations = _window(app=app, project=_project(result_ref))
    dataset = _result_dataset(mesh_ref="mesh-2")
    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    window.open_mesh_viewer()
    window.mesh_viewer.set_result_dataset(dataset)
    _select_result_field(window)

    persisted = window.persist_mesh_viewer_result_binding()

    assert persisted is False
    assert len(confirmations) == 1
    assert MESH_BINDING_METADATA_KEY not in result_ref.metadata
    assert any(
        "does not match explicit mesh ref" in item
        for item in _diagnostics(window.mesh_viewer)
    )
    del app
