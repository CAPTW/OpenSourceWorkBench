"""Controller snapshot, pending restore, and fail-closed restore tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dataclasses import replace

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import (
    RESULT_MESH_BINDING_SCHEMA_V2,
    ResultMeshBinding,
)
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _mesh(*, offset: float = 0.0) -> MeshData:
    return MeshData(
        points=(
            (offset, 0.0, 0.0),
            (offset + 1.0, 0.0, 0.0),
            (offset, 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class SceneSession:
    backend_kind = "fake-current-session"
    capabilities = frozenset(
        {
            "axes",
            "camera",
            "clipping",
            "interactive-results",
            "mesh-preview",
            "mesh-quality-overlays",
            "representation",
            "semantic-actors",
            "semantic-visibility",
            "setup-overlays",
        }
    )

    def __init__(self) -> None:
        from osw.core.workspace_3d import ActiveSceneCameraState

        self.camera = ActiveSceneCameraState(
            position=(4.0, 3.0, 2.0),
            focal_point=(0.0, 0.0, 0.0),
            view_up=(0.0, 0.0, 1.0),
        )
        self.actors: dict[str, object] = {}
        self.visibility: dict[str, bool] = {}
        self.applied_cameras: list[object] = []
        self.representations: list[str] = []
        self.axes: list[bool] = []
        self.render_calls = 0
        self.closed = False

    def clear(self) -> None:
        self.actors.clear()
        self.visibility.clear()

    def replace_actor(
        self, semantic_id: str, payload: object, *, generation: int
    ) -> object:
        self.actors[semantic_id] = (payload, generation)
        self.visibility[semantic_id] = True
        return SimpleNamespace(warnings=(), rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.visibility.pop(semantic_id, None)

    def request_render(self) -> None:
        self.render_calls += 1

    def fit_to_scene(self) -> None:
        return None

    def set_camera_preset(self, preset: str) -> None:
        return None

    def set_interaction_mode(self, mode: str) -> None:
        return None

    def set_axes_visible(self, visible: bool) -> None:
        self.axes.append(bool(visible))

    def set_representation(self, mode: str) -> None:
        self.representations.append(mode)

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = bool(visible)

    def isolate_actor(self, semantic_id: str) -> None:
        for key in self.visibility:
            self.visibility[key] = key == semantic_id

    def show_all_actors(self) -> None:
        for key in self.visibility:
            self.visibility[key] = True

    def enable_clipping(self, axis: str, origin: float) -> None:
        return None

    def update_clipping(self, axis: str, origin: float) -> None:
        return None

    def clear_clipping(self) -> None:
        return None

    def get_camera_state(self) -> object:
        return self.camera

    def apply_camera_state(self, camera: object) -> None:
        self.camera = camera
        self.applied_cameras.append(camera)

    def close(self) -> None:
        self.closed = True


class SceneFactory:
    backend_kind = SceneSession.backend_kind
    capabilities = SceneSession.capabilities

    def __init__(self, session: SceneSession | None = None) -> None:
        self.session = session or SceneSession()

    def create_session(self) -> SceneSession:
        return self.session


def _saved_state(mesh: MeshData, **changes: object) -> object:
    from osw.core.workspace_3d import (
        ActiveSceneCameraState,
        ActiveSceneResultState,
        ActiveSceneState,
    )

    values = {
        "mesh_ref": "mesh-1",
        "mesh_fingerprint": compute_mesh_fingerprint(mesh).digest,
        "camera": ActiveSceneCameraState(
            position=(8.0, 7.0, 6.0),
            focal_point=(0.0, 0.0, 0.0),
            view_up=(0.0, 0.0, 1.0),
        ),
        "representation": "wireframe",
        "axes_visible": False,
        "selection_mode": "cell",
    }
    values.update(changes)
    if values.pop("result_unavailable", False):
        values["result_state"] = ActiveSceneResultState(
            result_ref_id="result-1",
            result_dataset_id="dataset-not-loaded",
            binding_schema="osw.result_mesh_binding.v2",
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
            scalar_field="stress",
            scalar_component="value",
            scalar_association="cell",
        )
    return ActiveSceneState(**values)


def test_snapshot_is_pure_ordered_and_excludes_transient_probe_pick_and_table() -> None:
    session = SceneSession()
    controller = ActiveSceneController(SceneFactory(session))
    mesh = _mesh()
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(show_edges=True, show_axes=False),
    )
    controller.set_pick_mode("cell")
    controller.set_active_named_selection_ids(("selection-2", "selection-1"))

    state = controller.snapshot_active_scene_state()

    assert state is not None
    assert state.mesh_ref == "mesh-1"
    assert state.mesh_fingerprint == compute_mesh_fingerprint(mesh).digest
    assert state.camera.position == (4.0, 3.0, 2.0)
    assert state.representation == "surface_with_edges"
    assert state.axes_visible is False
    assert state.active_named_selection_ids == ("selection-1", "selection-2")
    assert state.selection_mode == "cell"
    payload = state.to_dict()
    text = str(payload).casefold()
    assert "probe" not in text
    assert "hover" not in text
    assert "backend_index" not in text
    assert "selected_result_table" not in text
    assert "visibility_snapshot" not in text


def test_snapshot_preserves_existing_result_ref_identity_without_dataset_rows() -> None:
    controller = ActiveSceneController(SceneFactory())
    mesh = _mesh()
    fingerprint = compute_mesh_fingerprint(mesh)
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    dataset = ResultDataset(
        dataset_id="dataset-1",
        source="memory",
        solver="fixture",
        analysis_type="static",
    )
    binding = ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id=dataset.dataset_id,
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature={"node_count": 3, "cell_count": 1},
    )

    controller.set_interactive_result_dataset(
        dataset,
        binding,
        result_ref_id="result-ref-1",
    )

    state = controller.snapshot_active_scene_state()
    assert state is not None
    assert state.result_state is not None
    assert state.result_state.result_ref_id == "result-ref-1"
    assert state.result_state.result_dataset_id == "dataset-1"
    assert "rows" not in state.result_state.to_dict()


def test_pending_state_restores_only_after_exact_explicit_mesh_load() -> None:
    from osw.core.workspace_3d import ActiveSceneRestoreStatus

    mesh = _mesh()
    session = SceneSession()
    controller = ActiveSceneController(SceneFactory(session))
    pending = controller.set_pending_active_scene_state(_saved_state(mesh))

    assert pending.status is ActiveSceneRestoreStatus.PENDING
    assert pending.reason_codes == ("ACTIVE_MESH_NOT_LOADED",)
    assert session.applied_cameras == []

    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )

    restored = controller.active_scene_restore_result
    assert restored.status is ActiveSceneRestoreStatus.RESTORED
    assert restored.reason_codes == ()
    assert session.representations[-1] == "wireframe"
    assert session.axes[-1] is False
    assert len(session.applied_cameras) == 1
    assert session.render_calls >= 1


def test_changed_same_count_mesh_is_stale_and_applies_no_saved_substate() -> None:
    from osw.core.workspace_3d import ActiveSceneRestoreStatus

    original = _mesh()
    changed = _mesh(offset=5.0)
    session = SceneSession()
    controller = ActiveSceneController(SceneFactory(session))
    controller.set_pending_active_scene_state(_saved_state(original))

    controller.load_mesh(
        changed,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )

    result = controller.active_scene_restore_result
    assert result.status is ActiveSceneRestoreStatus.STALE
    assert result.reason_codes == ("MESH_FINGERPRINT_MISMATCH",)
    assert session.applied_cameras == []
    assert "wireframe" not in session.representations


def test_missing_result_dataset_yields_partial_restore_without_auto_load() -> None:
    from osw.core.workspace_3d import ActiveSceneRestoreStatus

    mesh = _mesh()
    controller = ActiveSceneController(SceneFactory())
    controller.set_pending_active_scene_state(
        _saved_state(mesh, result_unavailable=True)
    )

    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )

    result = controller.active_scene_restore_result
    assert result.status is ActiveSceneRestoreStatus.PARTIAL
    assert result.reason_codes == ("RESULT_DATASET_NOT_AVAILABLE",)


def test_controller_close_clears_saved_pending_state() -> None:
    mesh = _mesh()
    controller = ActiveSceneController(SceneFactory())
    controller.set_pending_active_scene_state(_saved_state(mesh))

    controller.close()

    assert controller.pending_active_scene_state is None


def test_capture_request_writes_only_explicit_external_target(tmp_path: Path) -> None:
    from osw.core.workspace_3d import ActiveSceneScreenshotRequest

    class CaptureSession(SceneSession):
        capabilities = SceneSession.capabilities | frozenset({"scene-screenshot"})

        def export_screenshot_record(self, path: str, **kwargs: object) -> object:
            from osw.post.scene_model import build_screenshot_record

            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"scene-bytes")
            return build_screenshot_record(
                path,
                record_id=str(kwargs["record_id"]),
                scene_state=kwargs["scene_state"],
                mesh_ref=str(kwargs["mesh_ref"]),
            )

    session = CaptureSession()
    controller = ActiveSceneController(SceneFactory(session))
    mesh = _mesh()
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    target = tmp_path / "explicit-scene.png"

    result = controller.capture_active_scene_screenshot(
        ActiveSceneScreenshotRequest(
            record_id="shot-1",
            output_path=str(target),
            caption="Current scene",
        )
    )

    assert result.status == "CAPTURED"
    assert result.record is not None
    assert result.record.path == str(target)
    assert result.image_sha256
    assert result.image_byte_length == target.stat().st_size
    assert result.record.metadata["osw.active_scene.state"]["mesh_ref"] == "mesh-1"
    assert result.record.metadata["osw.active_scene.provenance"]["active_scene_digest"]


def test_restore_captured_scene_is_exact_then_stale_after_fingerprint_change(
    tmp_path: Path,
) -> None:
    from osw.core.workspace_3d import (
        ActiveSceneRestoreStatus,
        ActiveSceneScreenshotRequest,
    )

    class CaptureSession(SceneSession):
        capabilities = SceneSession.capabilities | frozenset({"scene-screenshot"})

        def export_screenshot_record(self, path: str, **kwargs: object) -> object:
            from osw.post.scene_model import build_screenshot_record

            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"scene-bytes")
            return build_screenshot_record(
                path,
                record_id=str(kwargs["record_id"]),
                scene_state=kwargs["scene_state"],
                mesh_ref=str(kwargs["mesh_ref"]),
            )

    original = _mesh()
    changed = _mesh(offset=5.0)
    session = CaptureSession()
    controller = ActiveSceneController(SceneFactory(session))
    controller.load_mesh(
        original,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(show_edges=False, show_axes=True),
    )
    controller.set_representation("wireframe")
    capture = controller.capture_active_scene_screenshot(
        ActiveSceneScreenshotRequest(
            record_id="shot-1",
            output_path=str(tmp_path / "shot.png"),
        )
    )
    assert capture.record is not None

    restored = controller.restore_captured_active_scene(capture.record)
    assert restored.status is ActiveSceneRestoreStatus.RESTORED
    assert session.representations[-1] == "wireframe"

    controller.load_mesh(
        changed,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    before_stale = list(session.representations)
    stale = controller.restore_captured_active_scene(capture.record)
    assert stale.status is ActiveSceneRestoreStatus.STALE
    assert stale.reason_codes == ("MESH_FINGERPRINT_MISMATCH",)
    assert session.representations == before_stale


def test_snapshot_and_restore_preserve_deformed_and_vector_result_state() -> None:
    from osw.core.workspace_3d import ActiveSceneRestoreStatus

    mesh = _mesh()
    fingerprint = compute_mesh_fingerprint(mesh)
    dataset = ResultDataset(
        dataset_id="dataset-1",
        source="memory",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="disp",
                location="node",
                components=("ux", "uy", "uz"),
                rows=(
                    ResultRow(0, {"ux": 0.1, "uy": 0.0, "uz": 0.0}),
                    ResultRow(1, {"ux": 0.0, "uy": 0.1, "uz": 0.0}),
                    ResultRow(2, {"ux": 0.0, "uy": 0.0, "uz": 0.1}),
                ),
                unit="mm",
            ),
        ),
        metadata={
            "mesh_length_unit": "mm",
            "field_semantics": {
                "disp": {
                    "semantic_role": "displacement",
                    "quantity_dimension": "length",
                    "coordinate_system": "global_cartesian",
                }
            },
        },
    )
    binding = ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id=dataset.dataset_id,
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature={"node_count": 3, "cell_count": 1},
    )
    controller = ActiveSceneController(SceneFactory())
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    controller.set_interactive_result_dataset(
        dataset,
        binding,
        result_ref_id="result-ref-1",
    )
    controller._interactive_result_state = replace(
        controller.interactive_result_state,
        vector_field_id="disp",
        vector_visible=True,
        vector_max_glyph_count=80,
        vector_scale_mode="MANUAL",
        vector_manual_scale=2.5,
        deformation_field_id="disp",
        deformation_mode="DEFORMED",
        deformation_scale_mode="MANUAL",
        deformation_manual_scale=1.25,
    )

    snapshot = controller.snapshot_active_scene_state()
    assert snapshot is not None
    assert snapshot.result_state is not None
    assert snapshot.result_state.deformation_mode == "DEFORMED"
    assert snapshot.result_state.vector_visible is True
    assert snapshot.result_state.glyph_max_count == 80

    fresh = ActiveSceneController(SceneFactory())
    fresh.set_pending_active_scene_state(snapshot)
    fresh.load_mesh(mesh, mesh_input_ref("mesh-1"), scene_view_state_from_toggles())
    assert fresh.active_scene_restore_result.status is ActiveSceneRestoreStatus.PARTIAL
    assert "RESULT_DATASET_NOT_AVAILABLE" in fresh.active_scene_restore_result.reason_codes

    fresh.set_interactive_result_dataset(dataset, binding, result_ref_id="result-ref-1")
    assert fresh.active_scene_restore_result.status in {
        ActiveSceneRestoreStatus.RESTORED,
        ActiveSceneRestoreStatus.PARTIAL,
    }
    restored_state = fresh.interactive_result_state
    assert restored_state.deformation_field_id == "disp"
    assert restored_state.vector_field_id == "disp"
