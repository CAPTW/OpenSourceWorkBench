"""Interactive-result controller state, actor lifecycle, and coexistence contracts."""

from __future__ import annotations

from types import SimpleNamespace

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import RESULT_MESH_BINDING_SCHEMA_V2, ResultMeshBinding
from osw.gui.interactive_results_view_model import (
    RESULT_COLORBAR_ACTOR_KEY,
    RESULT_DEFORMED_ACTOR_KEY,
    RESULT_PROBE_ACTOR_KEY,
    RESULT_SCALAR_ACTOR_KEY,
    RESULT_VECTOR_ACTOR_KEY,
    InteractiveResultSessionState,
    ScalarResultOverlaySpec,
)
from osw.gui.mesh_diagnostics_view_model import (
    MESH_QUALITY_ACTOR_KEY,
    MESH_QUALITY_SCALARBAR_ACTOR_KEY,
)
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import mesh_input_ref, scene_view_state_from_toggles
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.mesh.quality import analyze_mesh_cell_quality
from osw.post.result_deformation import DeformationMode
from osw.post.result_field_catalog import ResultBindingStatus
from osw.post.result_probe import ResultProbeRequest, ResultProbeStatus


def _mesh(*, moved: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (2.0 if moved else 1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (1.0, 1.0, 1.0),
        ),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("tetra", ((1, 2, 3, 4),)),
        ),
    )


def _rows(
    values: tuple[tuple[float, ...], ...],
    components: tuple[str, ...],
) -> tuple[ResultRow, ...]:
    return tuple(
        ResultRow(index, dict(zip(components, value, strict=True)))
        for index, value in enumerate(values)
    )


def _dataset() -> ResultDataset:
    return ResultDataset(
        dataset_id="result-1",
        source="fixture-path",
        solver="fixture-provider",
        analysis_type="static",
        fields=(
            ResultField(
                "temperature",
                "point",
                ("value",),
                _rows(((1.0,), (2.0,), (3.0,), (4.0,), (5.0,)), ("value",)),
                "K",
            ),
            ResultField(
                "velocity",
                "point",
                ("vx", "vy", "vz"),
                _rows(
                    (
                        (1.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                        (0.0, 0.0, 1.0),
                        (1.0, 1.0, 0.0),
                        (0.0, 1.0, 1.0),
                    ),
                    ("vx", "vy", "vz"),
                ),
                "m/s",
            ),
            ResultField(
                "u",
                "point",
                ("ux", "uy", "uz"),
                _rows(
                    (
                        (0.0, 0.0, 0.0),
                        (0.1, 0.0, 0.0),
                        (0.0, 0.2, 0.0),
                        (0.0, 0.0, 0.3),
                        (0.1, 0.2, 0.3),
                    ),
                    ("ux", "uy", "uz"),
                ),
                "m",
            ),
        ),
        metadata={
            "title": "Interactive fixture",
            "mesh_length_unit": "m",
            "field_semantics": {
                "u": {
                    "semantic_role": "displacement",
                    "quantity_dimension": "length",
                    "coordinate_system": "global_cartesian",
                }
            },
        },
    )


def _binding(mesh: MeshData) -> ResultMeshBinding:
    return ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id="result-1",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
    )


class ResultSession:
    backend_kind = "fake-interactive-results-v1"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "selection-overlays",
            "setup-overlays",
            "mesh-quality-overlays",
            "result-overlays",
        }
    )

    def __init__(self) -> None:
        self.actors: dict[str, object] = {}
        self.visibility: dict[str, bool] = {}
        self.replacements: list[tuple[str, int]] = []
        self.removals: list[str] = []
        self.close_calls = 0

    @property
    def hosted_widget(self) -> None:
        return None

    def clear(self) -> None:
        self.actors.clear()
        self.visibility.clear()

    def replace_actor(self, semantic_id: str, payload: object, *, generation: int) -> object:
        self.actors[semantic_id] = payload
        self.visibility[semantic_id] = True
        self.replacements.append((semantic_id, generation))
        return SimpleNamespace(rendered=True, diagnostics=())

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.visibility.pop(semantic_id, None)
        self.removals.append(semantic_id)

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = visible

    def set_representation(self, _mode: str) -> None:
        return None

    def request_render(self) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def clear_hover(self) -> None:
        return None

    def clear_current_selection(self) -> None:
        return None

    def close(self) -> None:
        self.close_calls += 1
        self.actors.clear()


class ResultFactory:
    backend_kind = ResultSession.backend_kind
    capabilities = ResultSession.capabilities

    def __init__(self) -> None:
        self.session = ResultSession()

    def create_session(self) -> ResultSession:
        return self.session


class _QualityProvider:
    provider_schema = "osw.mesh_quality.provider.interactive-result-fixture.v1"
    provider_version = "1"

    def evaluate(self, mesh: MeshData) -> tuple[float, ...]:
        count = sum(len(block.data) for block in mesh.cells)
        return tuple(0.75 if index % 2 == 0 else 0.25 for index in range(count))


def _analyze_quality(mesh: MeshData, **kwargs: object) -> object:
    allowed = {
        key: value
        for key, value in kwargs.items()
        if key in {"threshold", "degenerate_epsilon", "zero_edge_tolerance"}
    }
    return analyze_mesh_cell_quality(mesh, provider=_QualityProvider(), **allowed)


def _controller() -> tuple[ActiveSceneController, ResultSession]:
    factory = ResultFactory()
    controller = ActiveSceneController(factory, mesh_quality_analyzer=_analyze_quality)
    mesh = _mesh()
    controller.load_mesh(mesh, mesh_input_ref("mesh-1"), scene_view_state_from_toggles())
    controller.set_interactive_result_dataset(_dataset(), _binding(mesh), result_ref_id="ref-1")
    return controller, factory.session


def test_session_state_is_renderer_neutral_serializable_and_catalog_backed() -> None:
    controller, session = _controller()

    state = controller.interactive_result_state
    catalog = controller.interactive_result_field_catalog
    payload = state.to_dict()

    assert isinstance(state, InteractiveResultSessionState)
    assert state.active_result_id == "result-1"
    assert state.binding_status == "READY"
    assert catalog is not None
    assert catalog.binding_status is ResultBindingStatus.READY
    assert tuple(item.field_id for item in catalog.fields) == (
        "temperature",
        "velocity",
        "u",
    )
    assert "actor" not in repr(payload).lower()
    assert "vtk" not in repr(payload).lower()
    assert session.actors.keys() == {"base_mesh", "wireframe"}
    controller.close()


def test_deformed_scalar_vector_and_probe_use_one_semantic_actor_each() -> None:
    controller, session = _controller()
    original_mesh = _mesh()

    deformation = controller.set_deformed_result(
        "u",
        mode="DEFORMED",
        scale_mode="MANUAL",
        manual_scale=2.0,
    )
    scalar = controller.set_scalar_result(
        "temperature",
        component="scalar",
        range_mode="MANUAL",
        manual_range=(0.0, 6.0),
        colormap="turbo",
    )
    vector = controller.set_vector_result(
        "velocity",
        maximum_glyph_count=3,
        scale_mode="AUTO",
    )
    probe = controller.probe_result(
        ResultProbeRequest(
            dataset_id="result-1",
            field_name="temperature",
            component="scalar",
            association="point",
            stable_entity_key=1,
            mesh_fingerprint=compute_mesh_fingerprint(original_mesh).digest,
        )
    )

    assert deformation.applied and scalar.applied and vector.applied
    assert probe.status is ResultProbeStatus.RESOLVED
    assert set(session.actors) >= {
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
        RESULT_PROBE_ACTOR_KEY,
    }
    assert all(list(session.actors).count(key) == 1 for key in session.actors)
    scalar_payload = session.actors[RESULT_SCALAR_ACTOR_KEY]
    assert isinstance(scalar_payload, ScalarResultOverlaySpec)
    assert scalar_payload.mesh is not None
    assert scalar_payload.mesh.points != original_mesh.points
    assert vector.positions[1] != original_mesh.points[1]
    assert controller.actor_records[RESULT_DEFORMED_ACTOR_KEY].pickable is True
    assert controller.actor_records[RESULT_VECTOR_ACTOR_KEY].pickable is False
    assert controller.actor_records[RESULT_PROBE_ACTOR_KEY].pickable is False
    assert controller.actor_records[RESULT_SCALAR_ACTOR_KEY].metadata["result_id"] == "result-1"
    assert controller.actor_records["base_mesh"].visible is False

    assert controller.clear_deformed_result() is True
    assert RESULT_DEFORMED_ACTOR_KEY not in session.actors
    assert RESULT_PROBE_ACTOR_KEY in session.actors
    assert controller.interactive_result_state.probe_mode == "point"
    assert controller.actor_records["base_mesh"].visible is False  # scalar remains primary
    controller.close()


def test_scalar_then_deformation_is_order_independent_and_restores_original_geometry() -> None:
    controller, session = _controller()
    original_mesh = _mesh()

    assert controller.set_scalar_result("temperature", component="scalar").applied
    deformation = controller.set_deformed_result(
        "u",
        mode="DEFORMED",
        scale_mode="MANUAL",
        manual_scale=2.0,
    )

    assert deformation.applied is True
    deformed_scalar = session.actors[RESULT_SCALAR_ACTOR_KEY]
    assert isinstance(deformed_scalar, ScalarResultOverlaySpec)
    assert deformed_scalar.mesh is not None
    assert deformed_scalar.mesh.points != original_mesh.points
    assert session.visibility[RESULT_DEFORMED_ACTOR_KEY] is False

    assert controller.clear_deformed_result() is True
    original_scalar = session.actors[RESULT_SCALAR_ACTOR_KEY]
    assert isinstance(original_scalar, ScalarResultOverlaySpec)
    assert original_scalar.mesh is not None
    assert original_scalar.mesh.points == original_mesh.points
    assert RESULT_DEFORMED_ACTOR_KEY not in session.actors
    controller.close()


def test_same_fingerprint_replacement_restores_configuration_not_native_handles() -> None:
    controller, session = _controller()
    mesh = _mesh()
    controller.set_deformed_result(
        "u",
        mode="OVERLAY",
        scale_mode="MANUAL",
        manual_scale=3.0,
    )
    controller.set_scalar_result(
        "temperature",
        component="scalar",
        range_mode="MANUAL",
        manual_range=(0.0, 10.0),
        colormap="plasma",
    )
    controller.set_vector_result(
        "velocity",
        maximum_glyph_count=2,
        scale_mode="MANUAL",
        scale=4.0,
    )
    probe = controller.probe_result(
        ResultProbeRequest(
            dataset_id="result-1",
            field_name="temperature",
            component="scalar",
            association="point",
            stable_entity_key=1,
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        )
    )
    assert probe.status is ResultProbeStatus.RESOLVED
    generation = controller.generation
    prior_scalar_payload = session.actors[RESULT_SCALAR_ACTOR_KEY]
    prior_probe_payload = session.actors[RESULT_PROBE_ACTOR_KEY]

    controller.load_mesh(
        MeshData(points=mesh.points, cells=mesh.cells),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )

    assert controller.generation == generation + 1
    assert controller.interactive_result_resolution is not None
    assert controller.interactive_result_resolution.state.value == "RESOLVED"
    assert set(session.actors) >= {
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
        RESULT_PROBE_ACTOR_KEY,
    }
    assert session.actors[RESULT_SCALAR_ACTOR_KEY] is not prior_scalar_payload
    state = controller.interactive_result_state
    assert state.deformation_mode == "OVERLAY"
    assert state.deformation_manual_scale == 3.0
    assert state.range_mode == "MANUAL"
    assert state.manual_range == (0.0, 10.0)
    assert state.colormap == "plasma"
    assert state.vector_max_glyph_count == 2
    assert state.vector_manual_scale == 4.0
    assert state.probe_mode == "point"
    assert session.actors[RESULT_PROBE_ACTOR_KEY] is not prior_probe_payload
    controller.close()


def test_different_fingerprint_marks_stale_and_removes_every_result_resource() -> None:
    controller, session = _controller()
    controller.set_deformed_result("u", mode="DEFORMED")
    controller.set_scalar_result("temperature", component="scalar")
    controller.set_vector_result("velocity", maximum_glyph_count=2)

    controller.load_mesh(
        _mesh(moved=True),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )

    assert controller.interactive_result_resolution is not None
    assert controller.interactive_result_resolution.state.value == "STALE"
    assert controller.interactive_result_state.binding_status == "STALE_MESH"
    assert not any(key.startswith("result:") for key in session.actors)
    assert controller.interactive_result_state.stale_reason == "MESH_FINGERPRINT_MISMATCH"
    assert controller.actor_records["base_mesh"].visible is True
    controller.close()


def test_last_explicit_primary_scalar_activation_wins_and_restores_visibility() -> None:
    controller, session = _controller()
    assert controller.analyze_mesh_quality() is not None
    assert controller.set_mesh_quality_coloring_visible(True) is True
    assert session.visibility[MESH_QUALITY_ACTOR_KEY] is True

    assert controller.set_scalar_result("temperature", component="scalar").applied is True
    assert session.visibility[RESULT_SCALAR_ACTOR_KEY] is True
    assert session.visibility[MESH_QUALITY_ACTOR_KEY] is False
    assert session.visibility[MESH_QUALITY_SCALARBAR_ACTOR_KEY] is False

    assert controller.set_mesh_quality_coloring_visible(True) is True
    assert session.visibility[RESULT_SCALAR_ACTOR_KEY] is False
    assert session.visibility[RESULT_COLORBAR_ACTOR_KEY] is False
    assert session.visibility[MESH_QUALITY_ACTOR_KEY] is True

    assert controller.set_mesh_quality_coloring_visible(False) is True
    assert session.visibility[RESULT_SCALAR_ACTOR_KEY] is True
    assert session.visibility[RESULT_COLORBAR_ACTOR_KEY] is True
    controller.close()


def test_close_is_idempotent_and_clears_result_registry() -> None:
    controller, session = _controller()
    controller.set_deformed_result("u", mode=DeformationMode.DEFORMED)
    controller.set_scalar_result("temperature", component="scalar")
    controller.set_vector_result("velocity")

    controller.close()
    controller.close()

    assert session.close_calls == 1
    assert controller.actor_records == {}
