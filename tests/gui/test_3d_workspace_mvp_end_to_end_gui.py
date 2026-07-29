"""Deterministic MainWindow acceptance flow for the complete local 3D MVP."""

from __future__ import annotations

import hashlib
import os
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_io import load_project, save_project
from osw.core.project_schema import (
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ResultRef,
)
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.selection import (
    EntityKind,
    EntityLocator,
    NamedSelection,
    SelectionTargetRef,
)
from osw.core.selection_resolution import (
    CELL_ORDINAL_NAMESPACE,
    NODE_ORDINAL_NAMESPACE,
)
from osw.core.solver_setup import (
    FixedSupportRecord,
    ForceLoadRecord,
    MaterialAssignmentRecord,
    SetupReadiness,
)
from osw.core.units import Quantity
from osw.core.workspace_3d import (
    ACTIVE_SCENE_SCHEMA,
    ActiveSceneCameraState,
    ActiveSceneRestoreStatus,
    ActiveSceneResultState,
    ActiveSceneState,
    MeshQualityViewState,
    active_scene_state_digest,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.scene_model import SceneScreenshotRecord
from osw.solvers.calculix.adapter import prepare_solver_setup

MESH_REF = "mesh-mvp-e2e"
PROJECT_NAME = "project-mvp-e2e"
MATERIAL_ID = "material-steel"
RESULT_REF_ID = "result-ref-1"
RESULT_DATASET_ID = "result-dataset-1"


@pytest.fixture(scope="module")
def app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _mesh(*, changed: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (2.5 if changed else 2.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
    )


def _material() -> Material:
    return Material(
        MATERIAL_ID,
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )


def _dataset() -> ResultDataset:
    return ResultDataset(
        dataset_id=RESULT_DATASET_ID,
        source="memory",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("value",),
                rows=tuple(
                    ResultRow(index, {"value": value})
                    for index, value in enumerate((10.0, 20.0, 30.0, 40.0))
                ),
                unit="K",
            ),
            ResultField(
                name="displacement",
                location="node",
                components=("ux", "uy", "uz"),
                rows=(
                    ResultRow(0, {"ux": 1.0, "uy": 0.0, "uz": 0.0}),
                    ResultRow(1, {"ux": 0.0, "uy": 2.0, "uz": 0.0}),
                    ResultRow(2, {"ux": 0.0, "uy": 0.0, "uz": 3.0}),
                    ResultRow(3, {"ux": 0.0, "uy": 0.0, "uz": 0.0}),
                ),
                unit="mm",
            ),
        ),
        metadata={"mesh_ref": MESH_REF},
    )


def _project() -> Project:
    return Project(
        metadata=ProjectMetadata(name=PROJECT_NAME),
        materials=(_material(),),
        results=(
            ResultRef(
                id=RESULT_REF_ID,
                name="In-memory deterministic result",
                metadata={"result_dataset_id": RESULT_DATASET_ID},
            ),
        ),
        schema_version="0.3",
    )


def _selection(
    mesh: MeshData,
    *,
    selection_id: str,
    name: str,
    kind: EntityKind,
    entity_ids: tuple[int | str, ...],
) -> NamedSelection:
    fingerprint = compute_mesh_fingerprint(mesh)
    namespace = (
        NODE_ORDINAL_NAMESPACE
        if kind is EntityKind.NODE
        else CELL_ORDINAL_NAMESPACE
    )
    locator = EntityLocator(
        fingerprint.schema,
        MESH_REF,
        fingerprint.digest,
        kind,
        namespace,
        entity_ids,
    )
    target = SelectionTargetRef(
        kind,
        entity_ids,
        MESH_REF,
        locator=locator,
    )
    return NamedSelection(
        selection_id,
        name,
        entity_kind=kind,
        targets=(target,),
        source_mesh_ref=MESH_REF,
    )


def _project_with_setup(
    mesh: MeshData,
    *,
    active_scene: ActiveSceneState | None = None,
) -> Project:
    selections = (
        _selection(
            mesh,
            selection_id="ns-material-cell",
            name="Material Cell",
            kind=EntityKind.CELL,
            entity_ids=("0:0",),
        ),
        _selection(
            mesh,
            selection_id="ns-fixed-nodes",
            name="Fixed Node",
            kind=EntityKind.NODE,
            entity_ids=(0,),
        ),
        _selection(
            mesh,
            selection_id="ns-force-nodes",
            name="Force Node",
            kind=EntityKind.NODE,
            entity_ids=(1,),
        ),
    )
    setup = PhysicsSetup(
        setup_id="structural",
        name="Structural Setup",
        analysis_type="linear_static",
        domain="STRUCTURAL",
        material_assignment_records=(
            MaterialAssignmentRecord(
                "setup-material",
                "Steel assignment",
                MATERIAL_ID,
                "ns-material-cell",
            ),
        ),
        fixed_support_records=(
            FixedSupportRecord(
                "setup-fixed",
                "Fixed support",
                "ns-fixed-nodes",
                (1, 2, 3),
            ),
        ),
        force_load_records=(
            ForceLoadRecord(
                "setup-force",
                "Force",
                "ns-force-nodes",
                Quantity(100.0, "N"),
                (1.0, 0.0, 0.0),
                coordinate_system="GLOBAL",
                application_mode="PER_NODE",
            ),
        ),
    )
    return Project(
        metadata=ProjectMetadata(name=PROJECT_NAME),
        materials=(_material(),),
        physics=setup,
        results=(
            ResultRef(
                id=RESULT_REF_ID,
                name="In-memory deterministic result",
                metadata={"result_dataset_id": RESULT_DATASET_ID},
            ),
        ),
        selections=selections,
        active_scene=active_scene,
        schema_version="0.3",
    )


class _DeterministicUuidSource:
    def __init__(self) -> None:
        self._next = 1

    def __call__(self) -> object:
        value = self._next
        self._next += 1
        return SimpleNamespace(hex=f"{value:012x}{'0' * 20}")


class _RecordingSession:
    backend_kind = "fake-mvp-e2e"
    capabilities = frozenset(
        {
            "axes",
            "camera",
            "clipping",
            "hosted-widget",
            "interactive",
            "interactive-results",
            "mesh-preview",
            "mesh-quality-overlays",
            "picking",
            "representation",
            "result-overlays",
            "scene-screenshot",
            "selection-overlays",
            "semantic-actors",
            "semantic-visibility",
            "setup-overlays",
        }
    )

    def __init__(self) -> None:
        self.widget = QtWidgets.QWidget()
        self.actors: dict[str, object] = {}
        self.named_overlays: dict[str, tuple[str, tuple[int, ...], int]] = {}
        self.visibility: dict[str, bool] = {}
        self.calls: list[tuple[object, ...]] = []
        self.pick_callback: Callable[[object], object] | None = None
        self.base_load_count = 0
        self.capture_count = 0
        self.clear_count = 0
        self.close_count = 0
        self.camera = ActiveSceneCameraState(
            position=(6.0, 5.0, 4.0),
            focal_point=(0.0, 0.0, 0.0),
            view_up=(0.0, 0.0, 1.0),
            view_preset="isometric",
        )
        self.applied_cameras: list[ActiveSceneCameraState] = []

    @property
    def hosted_widget(self) -> object:
        return self.widget

    def clear(self) -> None:
        self.clear_count += 1
        self.actors.clear()
        self.named_overlays.clear()
        self.visibility.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        if semantic_id == "base_mesh":
            self.base_load_count += 1
        self.actors[semantic_id] = payload
        self.visibility[semantic_id] = True
        self.calls.append(("replace", semantic_id, generation))
        return SimpleNamespace(rendered=True, warnings=(), diagnostics=())

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.visibility.pop(semantic_id, None)

    def request_render(self) -> None:
        self.calls.append(("render",))

    def fit_to_scene(self) -> None:
        self.calls.append(("fit",))

    def set_camera_preset(self, preset: str) -> None:
        self.calls.append(("camera", preset))

    def get_camera_state(self) -> ActiveSceneCameraState:
        return self.camera

    def apply_camera_state(self, camera: ActiveSceneCameraState) -> None:
        self.camera = camera
        self.applied_cameras.append(camera)

    def set_interaction_mode(self, mode: str) -> None:
        self.calls.append(("interaction", mode))

    def set_axes_visible(self, visible: bool) -> None:
        self.calls.append(("axes", bool(visible)))

    def set_representation(self, mode: str) -> None:
        self.calls.append(("representation", mode))

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = bool(visible)

    def isolate_actor(self, semantic_id: str) -> None:
        for key in self.visibility:
            self.visibility[key] = key == semantic_id

    def show_all_actors(self) -> None:
        for key in self.visibility:
            self.visibility[key] = True

    def enable_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("clip-enable", axis, origin))

    def update_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("clip-update", axis, origin))

    def clear_clipping(self) -> None:
        self.calls.append(("clip-clear",))

    def set_pick_mode(
        self,
        mode: str,
        callback: Callable[[object], object],
    ) -> None:
        self.pick_callback = callback
        self.calls.append(("pick-mode", mode))

    def disable_picking(self) -> None:
        self.pick_callback = None

    def set_hover_entities(
        self,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("hover", kind, indices, generation))

    def clear_hover(self) -> None:
        self.calls.append(("clear-hover",))

    def set_current_selection(
        self,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("current-selection", kind, indices, generation))

    def clear_current_selection(self) -> None:
        self.calls.append(("clear-current-selection",))

    def set_named_selection_overlay(
        self,
        selection_id: str,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.named_overlays[selection_id] = (kind, indices, generation)

    def remove_named_selection_overlay(self, selection_id: str) -> None:
        self.named_overlays.pop(selection_id, None)

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: object,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        self.capture_count += 1
        target = Path(path)
        target.write_bytes(b"\x89PNG\r\n\x1a\n" + b"osw-mvp-e2e")
        assert mesh is not None
        return SceneScreenshotRecord(
            id=record_id,
            path=str(target),
            caption=caption,
            scene_state=scene_state,
            mesh_ref=mesh_ref,
            selection_ids=tuple(selection_ids),
            created_by=created_by,
        )

    def emit_pick(
        self,
        *,
        controller: object,
        entity_kind: str,
        backend_index: int,
    ) -> object:
        assert self.pick_callback is not None
        fingerprint = controller.current_mesh_fingerprint
        assert fingerprint is not None
        return self.pick_callback(
            {
                "generation": controller.generation,
                "mesh_ref": controller.current_mesh_ref,
                "mesh_fingerprint": fingerprint.digest,
                "entity_kind": entity_kind,
                "backend_index": backend_index,
                "intent": "replace",
            }
        )

    def close(self) -> None:
        self.close_count += 1
        self.actors.clear()
        self.named_overlays.clear()


class _RecordingFactory:
    backend_kind = _RecordingSession.backend_kind
    capabilities = _RecordingSession.capabilities

    def __init__(self) -> None:
        self.sessions: list[_RecordingSession] = []

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> _RecordingSession:
        session = _RecordingSession()
        self.sessions.append(session)
        return session

    @property
    def current(self) -> _RecordingSession:
        return self.sessions[-1]


class _FailingFactory:
    backend_kind = "pyvistaqt"
    capabilities = _RecordingSession.capabilities

    def __init__(self) -> None:
        self.create_count = 0

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> object:
        from osw.gui.workspace_scene_controller import (
            SceneRendererInitializationError,
        )

        self.create_count += 1
        raise SceneRendererInitializationError("renderer backend unavailable")


def _forbid_processes(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    calls: list[object] = []

    def blocked(*_args: object, **_kwargs: object) -> object:
        calls.append(object())
        pytest.fail("The deterministic MVP validation must not start a process.")

    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    return calls


def _prepare_provider(
    calls: list[object],
) -> Callable[[Project, object, str], object]:
    def prepare(project: Project, mesh: object, mesh_ref: str) -> object:
        calls.append((project, mesh, mesh_ref))
        return prepare_solver_setup(project, mesh=mesh, mesh_ref=mesh_ref)

    return prepare


def _pick_and_create(
    window: object,
    session: _RecordingSession,
    *,
    kind: str,
    backend_index: int,
    name: str,
) -> NamedSelection:
    controller = window.active_scene_controller
    assert controller.set_pick_mode(kind)
    assert session.emit_pick(
        controller=controller,
        entity_kind="cell" if kind == "cell" else "node",
        backend_index=backend_index,
    )
    before = len(window.current_project.selections)
    window._on_create_named_selection(name, "")
    assert len(window.current_project.selections) == before + 1
    return window.current_project.selections[-1]


def _saved_state(mesh: MeshData) -> ActiveSceneState:
    fingerprint = compute_mesh_fingerprint(mesh)
    return ActiveSceneState(
        mesh_ref=MESH_REF,
        mesh_fingerprint=fingerprint.digest,
        camera=ActiveSceneCameraState(
            position=(7.0, 6.0, 5.0),
            focal_point=(0.0, 0.0, 0.0),
            view_up=(0.0, 0.0, 1.0),
            view_preset="isometric",
        ),
        representation="wireframe",
        axes_visible=False,
        result_state=ActiveSceneResultState(
            result_ref_id=RESULT_REF_ID,
            result_dataset_id=RESULT_DATASET_ID,
            binding_schema="osw.result_mesh_binding.v2",
            mesh_fingerprint=fingerprint.digest,
            scalar_field="temperature",
            scalar_component="value",
            scalar_association="point",
            vector_field="displacement",
            vector_components=("ux", "uy", "uz"),
            vector_association="point",
            vector_visible=True,
            glyph_scale=1.0,
            glyph_max_count=2,
        ),
        mesh_quality_state=MeshQualityViewState(
            metric_schema="osw.mesh_quality.edge_aspect_ratio.v1",
            threshold=2.0,
            highlight_visible=True,
        ),
        selection_mode="cell",
    )


def test_3d_workspace_mvp_end_to_end_round_trip(
    app: QtWidgets.QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from osw.gui import main_window as main_window_module

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        main_window_module,
        "uuid4",
        _DeterministicUuidSource(),
    )
    mesh = _mesh()
    dataset = _dataset()
    project_path = tmp_path / "project-mvp-e2e.osw.json"
    screenshot_path = tmp_path / "scene-shot-1.png"
    report_path = tmp_path / "mvp-report.html"
    save_calls: list[str] = []
    load_calls: list[str] = []
    prepare_calls: list[object] = []
    factory = _RecordingFactory()

    def saver(project: Project, path: str) -> None:
        save_calls.append(path)
        save_project(project, path)

    def loader(path: str) -> Project:
        load_calls.append(path)
        return load_project(path)

    window = main_window_module.MainWindow(
        project=_project(),
        scene_renderer_factory=factory,
        result_mesh_binding_confirmation=lambda _message: True,
        project_save_path_picker=lambda: str(project_path),
        project_saver=saver,
        setup_preview_provider=_prepare_provider(prepare_calls),
    )
    process_calls = _forbid_processes(monkeypatch)
    session = factory.current
    assert window.current_project.schema_version == "0.3"
    assert window.project_dirty is False
    assert session.base_load_count == 0
    assert session.capture_count == 0
    assert process_calls == []
    assert save_calls == []

    generation = window.active_scene_controller.generation
    window.load_mesh_into_viewer(mesh, mesh_ref=MESH_REF)
    window.last_imported_mesh_data = mesh
    window.last_imported_mesh_ref = MESH_REF
    controller = window.active_scene_controller
    fingerprint = compute_mesh_fingerprint(mesh)
    assert controller.generation == generation + 1
    assert session.base_load_count == 1
    assert controller.current_mesh_ref == MESH_REF
    assert controller.current_mesh_fingerprint == fingerprint
    assert set(session.actors) == {"base_mesh", "wireframe"}
    assert save_calls == []

    assert controller.set_camera_preset("isometric")
    assert controller.set_representation("surface_with_edges")
    assert controller.set_axes_visible(True)
    assert controller.fit_to_scene()
    assert set(key for key in session.actors if key in {"base_mesh", "wireframe"}) == {
        "base_mesh",
        "wireframe",
    }

    material_selection = _pick_and_create(
        window,
        session,
        kind="cell",
        backend_index=0,
        name="Material Cell",
    )
    fixed_selection = _pick_and_create(
        window,
        session,
        kind="node",
        backend_index=0,
        name="Fixed Node",
    )
    force_selection = _pick_and_create(
        window,
        session,
        kind="node",
        backend_index=1,
        name="Force Node",
    )
    selections = (material_selection, fixed_selection, force_selection)
    assert tuple(item.id for item in selections) == (
        "selection-000000000001",
        "selection-000000000002",
        "selection-000000000003",
    )
    assert material_selection.targets[0].locator.entity_ids == ("0:0",)
    assert fixed_selection.targets[0].locator.entity_ids == (0,)
    assert force_selection.targets[0].locator.entity_ids == (1,)
    assert material_selection.entity_kind is EntityKind.CELL
    assert fixed_selection.entity_kind is EntityKind.NODE
    assert force_selection.entity_kind is EntityKind.NODE
    assert all(
        item.targets[0].locator.mesh_fingerprint == fingerprint.digest
        for item in selections
    )
    assert all(
        controller.named_selection_resolutions[item.id].state.value == "RESOLVED"
        for item in selections
    )
    assert "backend_index" not in str(
        [item.to_dict() for item in window.current_project.selections]
    )

    window._on_create_setup_record(
        {
            "kind": "Material",
            "name": "Steel assignment",
            "target_selection_id": material_selection.id,
            "material_id": MATERIAL_ID,
        }
    )
    window._on_create_setup_record(
        {
            "kind": "Fixed Support",
            "name": "Fixed support",
            "target_selection_id": fixed_selection.id,
            "translational_dofs": (1, 2, 3),
        }
    )
    window._on_create_setup_record(
        {
            "kind": "Force",
            "name": "Force",
            "target_selection_id": force_selection.id,
            "magnitude": 100.0,
            "unit": "N",
            "direction": (1.0, 0.0, 0.0),
            "coordinate_system": "GLOBAL",
            "application_mode": "PER_NODE",
        }
    )
    setup = window.current_project.primary_physics
    assert setup is not None
    setup_records = (
        *setup.material_assignment_records,
        *setup.fixed_support_records,
        *setup.force_load_records,
    )
    assert tuple(record.id for record in setup_records) == (
        "setup-material-000000000004",
        "setup-fixed-support-000000000005",
        "setup-force-000000000006",
    )
    assert all(
        controller.setup_statuses[record.id].state is SetupReadiness.READY
        for record in setup_records
    )
    setup_actor_keys = tuple(
        key for key in controller.actor_records if key.startswith("setup:")
    )
    assert len(setup_actor_keys) == len(set(setup_actor_keys)) == 3
    assert sum(":material:" in key for key in setup_actor_keys) == 1
    assert sum(":fixed-support:" in key for key in setup_actor_keys) == 1
    assert sum(":force:" in key for key in setup_actor_keys) == 1

    window._on_prepare_setup_preview()
    assert len(prepare_calls) == 1
    prepared = prepare_solver_setup(
        window.current_project,
        mesh=mesh,
        mesh_ref=MESH_REF,
    )
    assert prepared.eligible is True
    assert prepared.execution_mode == "prepare_only"
    assert prepared.element_sets[0][1] == (1,)
    assert prepared.node_sets == (
        (f"FIX_{setup.fixed_support_records[0].id.upper().replace('-', '_')}", (1,)),
        (f"FORCE_{setup.force_load_records[0].id.upper().replace('-', '_')}", (2,)),
    )
    assert "*BOUNDARY" in prepared.input_preview
    assert ", 1, 100" in prepared.input_preview
    assert not hasattr(prepared, "command")

    window._project_dirty = False
    analysis = controller.analyze_mesh_quality()
    assert analysis is not None
    assert analysis.mesh_fingerprint.digest == fingerprint.digest
    assert analysis.evaluated_count == 1
    assert controller.set_mesh_quality_threshold(2.0)
    assert controller.set_mesh_quality_highlight_visible(True)
    diagnostics_model = controller.mesh_quality_view_model
    assert diagnostics_model.metric_schema == "osw.mesh_quality.edge_aspect_ratio.v1"
    assert diagnostics_model.bad_count == 1
    assert diagnostics_model.bad_cell_keys == diagnostics_model.table_bad_cell_keys
    quality_payload = session.actors["mesh_quality:bad_cells"]
    assert quality_payload.stable_cell_keys == diagnostics_model.bad_cell_keys
    actors_before_isolate = set(session.actors)
    assert controller.set_mesh_quality_isolated(True)
    assert controller.restore_mesh_quality_visibility()
    assert set(session.actors) == actors_before_isolate
    assert set(setup_actor_keys).issubset(session.actors)
    assert window.project_dirty is False

    window.last_result_datasets = [dataset]
    window._sync_mesh_viewer_result_datasets()
    panel = window.mesh_viewer
    assert panel is not None
    panel.scalar_selector.setCurrentText("result: temperature")
    assert window.persist_mesh_viewer_result_binding() is True
    binding_payload = window.current_project.results[0].metadata["mesh_binding"]
    assert binding_payload["schema"] == "osw.result_mesh_binding.v2"
    assert binding_payload["mesh_fingerprint"] == fingerprint.digest
    assert window.project_dirty is True
    window._project_dirty = False

    panel.range_mode_selector.setCurrentText("AUTO")
    panel.colorbar_toggle.setChecked(True)
    panel.apply_scalar_button.click()
    scalar = controller.interactive_results_view_model.scalar
    assert scalar is not None and scalar.applied
    assert scalar.data_range == (10.0, 40.0)
    assert scalar.display_range == (10.0, 40.0)
    assert {"result:scalar", "result:colorbar"}.issubset(session.actors)

    panel.vector_selector.setCurrentText("result vector: displacement")
    panel.glyph_toggle.setChecked(True)
    panel.glyph_scale_input.setValue(1.0)
    panel.glyph_max_count_input.setValue(2)
    panel.apply_vector_button.click()
    vector = controller.interactive_results_view_model.vector
    assert vector is not None and vector.applied
    assert vector.candidate_count == 3
    assert vector.sampled_count == 2
    assert vector.zero_vector_count == 1
    assert vector.selected_candidate_ranks == (0, 2)
    assert vector.stable_entity_keys == (0, 2)
    assert "result:vector" in session.actors

    selections_before_probe = tuple(window.current_project.selections)
    probe = panel.probe_result_entity("point", 1)
    table = panel.set_selected_result_entities("point", (3, 1, 0))
    assert probe is not None and probe.value == 20.0 and probe.unit == "K"
    assert table is not None
    assert tuple(row.stable_entity_key for row in table.rows) == (0, 1, 3)
    assert tuple(row.value for row in table.rows) == (10.0, 20.0, 40.0)
    assert window.current_project.selections == list(selections_before_probe)
    assert {"result:probe", "result:scalar", "result:vector"}.issubset(
        session.actors
    )
    assert window.project_dirty is False

    controller.set_active_named_selection_ids(tuple(item.id for item in selections))
    assert controller.set_camera_preset("isometric")
    assert controller.set_representation("surface_with_edges")
    assert controller.set_axes_visible(True)
    scene = controller.snapshot_active_scene_state()
    assert scene is not None
    assert scene.schema == ACTIVE_SCENE_SCHEMA
    assert scene.mesh_ref == MESH_REF
    assert scene.mesh_fingerprint == fingerprint.digest
    assert scene.result_state is not None
    assert scene.mesh_quality_state is not None
    scene_digest = active_scene_state_digest(scene)
    assert scene_digest == active_scene_state_digest(
        ActiveSceneState.from_dict(scene.to_dict())
    )
    scene_text = str(scene.to_dict())
    assert "backend_index" not in scene_text
    assert "probe" not in scene_text
    assert "selected_result_table" not in scene_text

    window._project_dirty = False
    window._pick_scene_screenshot_target_path = lambda: str(screenshot_path)
    record = window.capture_scene_screenshot_to_report_candidates()
    assert record is not None
    assert session.capture_count == 1
    assert screenshot_path.is_file()
    image_bytes = screenshot_path.read_bytes()
    provenance = record.metadata["osw.active_scene.provenance"]
    assert provenance["active_scene_digest"] == scene_digest
    assert provenance["image_sha256"] == hashlib.sha256(image_bytes).hexdigest()
    assert provenance["image_byte_length"] == len(image_bytes) > 0
    assert window.current_project.report_screenshots == []
    assert window.project_dirty is False
    assert save_calls == []

    window._confirm_persist_scene_screenshots = lambda count: count == 1
    assert window.persist_staged_scene_screenshots() == 1
    assert len(window.current_project.report_screenshots) == 1
    assert window.project_dirty is True
    assert save_calls == []

    capture_count = session.capture_count
    preview = window.generate_report_preview(log=False)
    rendered_preview = "\n".join(
        block
        for section in preview.sections
        for block in getattr(section, "content_blocks", ())
    )
    assert "Active scene: osw.active_scene.v1" in rendered_preview
    assert fingerprint.digest[:12] in rendered_preview
    assert "temperature" in rendered_preview
    assert "edge_aspect_ratio" in rendered_preview
    assert str(tmp_path) not in rendered_preview
    exported = window.export_current_report(output_path=report_path)
    assert exported == report_path
    assert report_path.is_file()
    assert session.capture_count == capture_count
    assert process_calls == []

    assert window.save_project_as() is True
    assert save_calls == [str(project_path)]
    assert project_path.is_file()
    assert window.current_project.active_scene is not None
    assert len(window.current_project.report_screenshots) == 1
    assert window.project_dirty is False
    first_controller = window.active_scene_controller
    window.close()
    first_controller.close()
    assert session.close_count == 1

    reopen_factory = _RecordingFactory()
    reopened = main_window_module.MainWindow(
        project=_project(),
        scene_renderer_factory=reopen_factory,
        project_open_path_picker=lambda: str(project_path),
        project_loader=loader,
        result_mesh_binding_confirmation=lambda _message: True,
    )
    sessions_before_open = len(reopen_factory.sessions)
    assert reopened.open_project() is True
    assert load_calls == [str(project_path)]
    assert sum(item.base_load_count for item in reopen_factory.sessions) == 0
    assert reopened.last_imported_mesh_data is None
    assert reopened.last_result_datasets == ()
    assert reopened.active_scene_controller.active_scene_restore_result.status is (
        ActiveSceneRestoreStatus.PENDING
    )
    assert len(reopen_factory.sessions) >= sessions_before_open
    assert reopened.project_dirty is False

    reopened.load_mesh_into_viewer(mesh, mesh_ref=MESH_REF)
    restore = reopened.active_scene_controller.active_scene_restore_result
    assert restore.status is ActiveSceneRestoreStatus.PARTIAL
    assert restore.reason_codes == ("RESULT_DATASET_NOT_AVAILABLE",)
    assert reopen_factory.current.base_load_count == 1
    assert reopened.project_dirty is False
    assert len(reopened.active_scene_controller.setup_statuses) == 3
    assert all(
        item.state is SetupReadiness.READY
        for item in reopened.active_scene_controller.setup_statuses.values()
    )
    assert "mesh_quality:bad_cells" in reopen_factory.current.actors

    reopened.last_result_datasets = [dataset]
    reopened._sync_mesh_viewer_result_datasets()
    restored = reopened.active_scene_controller.restore_pending_active_scene_state()
    assert restored.status is ActiveSceneRestoreStatus.RESTORED
    assert restored.reason_codes == ()
    assert {
        "result:scalar",
        "result:colorbar",
        "result:vector",
    }.issubset(reopen_factory.current.actors)
    restored_model = reopened.active_scene_controller.interactive_results_view_model
    assert restored_model.probe is None
    assert restored_model.table is None
    assert len(reopened.current_project.report_screenshots) == 1
    assert reopened.project_dirty is False

    reopened.active_scene_controller.clear_interactive_results()
    reopened.active_scene_controller.clear_mesh_quality_overlay()
    reopened.active_scene_controller.set_solver_setup(None)
    reopened.active_scene_controller.set_named_selections(())
    reopened.active_scene_controller.clear()
    reopened_controller = reopened.active_scene_controller
    reopened.close()
    reopened_controller.close()
    assert reopen_factory.current.close_count == 1
    assert reopen_factory.current.actors == {}
    assert process_calls == []
    assert set(tmp_path.iterdir()) == {
        project_path,
        screenshot_path,
        report_path,
    }
    del app


def test_3d_workspace_mvp_same_count_changed_mesh_blocks_restore(
    app: QtWidgets.QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from osw.gui.main_window import MainWindow

    monkeypatch.chdir(tmp_path)
    original = _mesh()
    changed = _mesh(changed=True)
    saved = _project_with_setup(original, active_scene=_saved_state(original))
    project_path = tmp_path / "stale-project.osw.json"
    save_project(saved, project_path)
    factory = _RecordingFactory()
    window = MainWindow(
        project=_project(),
        scene_renderer_factory=factory,
        project_open_path_picker=lambda: str(project_path),
        project_loader=lambda path: load_project(path),
    )
    process_calls = _forbid_processes(monkeypatch)
    assert window.open_project() is True
    assert sum(item.base_load_count for item in factory.sessions) == 0
    assert window.project_dirty is False

    window.load_mesh_into_viewer(changed, mesh_ref=MESH_REF)
    controller = window.active_scene_controller
    result = controller.active_scene_restore_result
    assert len(original.points) == len(changed.points) == 4
    original_cell_count = sum(block.count for block in original.cells)
    changed_cell_count = sum(block.count for block in changed.cells)
    assert original_cell_count == changed_cell_count == 1
    assert compute_mesh_fingerprint(original) != compute_mesh_fingerprint(changed)
    assert result.status is ActiveSceneRestoreStatus.STALE
    assert result.reason_codes == ("MESH_FINGERPRINT_MISMATCH",)
    assert factory.current.applied_cameras == []
    assert not any(
        key.startswith(("setup:", "result:", "mesh_quality:"))
        for key in factory.current.actors
    )
    assert all(
        resolution.state.value == "STALE"
        and resolution.reason_code == "MESH_FINGERPRINT_MISMATCH"
        for resolution in controller.named_selection_resolutions.values()
    )
    assert all(
        status.state is SetupReadiness.BLOCKED
        for status in controller.setup_statuses.values()
    )
    assert controller.interactive_results_view_model.scalar is None
    assert controller.mesh_quality_view_model.analysis_available is False
    assert window.project_dirty is False
    assert process_calls == []
    window.close()
    assert set(tmp_path.iterdir()) == {project_path}
    del app


def test_3d_workspace_mvp_renderer_fallback_preserves_nonrendering_flow(
    app: QtWidgets.QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from osw.gui.main_window import MainWindow

    monkeypatch.chdir(tmp_path)
    mesh = _mesh()
    dataset = _dataset()
    prepare_calls: list[object] = []
    save_calls: list[str] = []
    project_path = tmp_path / "fallback-project.osw.json"
    screenshot_path = tmp_path / "fallback-scene.png"
    factory = _FailingFactory()

    def saver(project: Project, path: str) -> None:
        save_calls.append(path)
        save_project(project, path)

    window = MainWindow(
        project=_project_with_setup(mesh),
        scene_renderer_factory=factory,
        result_mesh_binding_confirmation=lambda _message: True,
        project_save_path_picker=lambda: str(project_path),
        project_saver=saver,
        setup_preview_provider=_prepare_provider(prepare_calls),
    )
    process_calls = _forbid_processes(monkeypatch)
    window.load_mesh_into_viewer(mesh, mesh_ref=MESH_REF)
    window.last_imported_mesh_data = mesh
    window.last_imported_mesh_ref = MESH_REF
    controller = window.active_scene_controller
    assert controller.fallback_reason == "renderer backend unavailable"
    assert controller.current_mesh_fingerprint == compute_mesh_fingerprint(mesh)
    assert controller.actor_records == {}
    assert all(
        resolution.state.value == "RESOLVED"
        for resolution in controller.named_selection_resolutions.values()
    )
    assert all(
        status.state is SetupReadiness.READY
        for status in controller.setup_statuses.values()
    )

    window._on_prepare_setup_preview()
    assert len(prepare_calls) == 1
    prepared = prepare_calls[0]
    assert prepared[1] is mesh
    preview_text = window.setup_overlay_panel.preview_text.toPlainText()
    assert "*MATERIAL" in preview_text
    assert "*CLOAD" in preview_text

    window.last_result_datasets = [dataset]
    window._sync_mesh_viewer_result_datasets()
    panel = window.mesh_viewer
    assert panel is not None
    panel.scalar_selector.setCurrentText("result: temperature")
    assert window.persist_mesh_viewer_result_binding() is True
    binding = window.current_project.results[0].metadata["mesh_binding"]
    assert binding["schema"] == "osw.result_mesh_binding.v2"
    window._project_dirty = False

    scalar = controller.set_scalar_result(
        "temperature",
        component="value",
        render=False,
    )
    vector = controller.set_vector_result(
        "displacement",
        components=("ux", "uy", "uz"),
        maximum_glyph_count=2,
        scale=1.0,
    )
    probe = panel.probe_result_entity("point", 1)
    table = panel.set_selected_result_entities("point", (3, 1, 0))
    assert scalar.applied and scalar.data_range == (10.0, 40.0)
    assert vector.applied and vector.sampled_count == 2
    assert vector.stable_entity_keys == (0, 2)
    assert probe is not None and probe.value == 20.0
    assert table is not None
    assert tuple(row.stable_entity_key for row in table.rows) == (0, 1, 3)
    assert controller.actor_records == {}

    analysis = controller.analyze_mesh_quality()
    assert analysis is not None and analysis.evaluated_count == 1
    assert controller.set_mesh_quality_threshold(2.0)
    assert controller.mesh_quality_view_model.bad_cell_keys == ("0:0",)
    assert controller.set_mesh_quality_highlight_visible(True) is False
    assert controller.set_mesh_quality_isolated(True) is False
    window._refresh_mesh_diagnostics_panel()
    assert window.mesh_diagnostics_panel.table.rowCount() == 1
    assert not window.mesh_diagnostics_panel.highlight_check.isEnabled()
    assert not window.mesh_diagnostics_panel.isolate_check.isEnabled()
    assert "unavailable" in window.mesh_diagnostics_panel.status_label.text().lower()
    assert controller.actor_records == {}

    state = controller.snapshot_active_scene_state()
    assert state is not None
    assert state.mesh_fingerprint == compute_mesh_fingerprint(mesh).digest
    assert state.result_state is not None
    assert state.mesh_quality_state is not None
    assert "backend_index" not in str(state.to_dict())

    window._pick_scene_screenshot_target_path = lambda: str(screenshot_path)
    before_assets = tuple(window.current_project.report_screenshots)
    before_dirty = window.project_dirty
    assert window.capture_scene_screenshot_to_report_candidates() is None
    assert not screenshot_path.exists()
    assert window.current_project.report_screenshots == list(before_assets)
    assert window.project_dirty is before_dirty
    assert window.generate_report_preview(log=False) is not None

    assert window.save_project_as() is True
    assert save_calls == [str(project_path)]
    assert project_path.is_file()
    assert window.project_dirty is False
    window.close()

    reopen_factory = _FailingFactory()
    reopened = MainWindow(
        project=_project(),
        scene_renderer_factory=reopen_factory,
        project_open_path_picker=lambda: str(project_path),
        project_loader=lambda path: load_project(path),
    )
    assert reopened.open_project() is True
    assert reopened.last_imported_mesh_data is None
    assert reopened.last_result_datasets == ()
    assert reopened.active_scene_controller.active_scene_restore_result.status is (
        ActiveSceneRestoreStatus.PENDING
    )
    assert reopened.project_dirty is False
    reopened.close()
    assert process_calls == []
    assert set(tmp_path.iterdir()) == {project_path}
    del app
