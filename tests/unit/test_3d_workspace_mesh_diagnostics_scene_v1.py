"""Scene ownership contracts for Scaled Jacobian diagnostics."""

from __future__ import annotations

from types import SimpleNamespace

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import RESULT_MESH_BINDING_SCHEMA_V2, ResultMeshBinding
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.mesh.quality import MeshDiagnosticsStatus, analyze_mesh_cell_quality


class Provider:
    provider_schema = "osw.mesh_quality.provider.scene-fixture.v1"
    provider_version = "1"

    def __init__(self, values: tuple[float, ...]) -> None:
        self.values = values
        self.calls = 0

    def evaluate(self, _mesh: MeshData) -> tuple[float, ...]:
        self.calls += 1
        return self.values


def _mesh(*, changed: bool = False) -> MeshData:
    apex = (0.0, 0.0, 1.25 if changed else 1.0)
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            apex,
            (1.0, 1.0, 0.0),
        ),
        cells=(
            MeshCellBlock(
                "tetra",
                ((0, 1, 2, 3), (0, 2, 1, 3), (0, 1, 2, 4)),
            ),
        ),
    )


class DiagnosticsSession:
    backend_kind = "fake-diagnostics-v1"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "selection-overlays",
            "mesh-quality-overlays",
            "result-overlays",
        }
    )

    def __init__(self) -> None:
        self.actors: dict[str, object] = {}
        self.visibility: dict[str, bool] = {}
        self.current_selection: tuple[str, tuple[int, ...]] | None = None
        self.close_calls = 0

    @property
    def hosted_widget(self) -> None:
        return None

    def clear(self) -> None:
        self.actors.clear()
        self.visibility.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.actors[semantic_id] = payload
        self.visibility[semantic_id] = True
        return SimpleNamespace(warnings=(), rendered=True, generation=generation)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.visibility.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def set_representation(self, _mode: str) -> None:
        return None

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = visible

    def isolate_actor(self, _semantic_id: str) -> None:
        return None

    def clear_isolation(self) -> None:
        return None

    def show_all_actors(self) -> None:
        return None

    def set_current_selection(
        self,
        kind: str,
        indices: tuple[int, ...],
        _generation: int,
    ) -> None:
        self.current_selection = (kind, indices)

    def clear_current_selection(self) -> None:
        self.current_selection = None

    def clear_hover(self) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def close(self) -> None:
        self.close_calls += 1
        self.clear()


class Factory:
    backend_kind = DiagnosticsSession.backend_kind
    capabilities = DiagnosticsSession.capabilities

    def __init__(self) -> None:
        self.session = DiagnosticsSession()

    def create_session(self) -> DiagnosticsSession:
        return self.session


def _controller(provider: Provider) -> tuple[ActiveSceneController, Factory]:
    def analyzer(mesh: MeshData, **kwargs: object) -> object:
        return analyze_mesh_cell_quality(
            mesh,
            threshold=float(kwargs.get("threshold", 0.0)),
            provider=provider,
        )

    factory = Factory()
    controller = ActiveSceneController(factory, mesh_quality_analyzer=analyzer)
    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-quality-v1"),
        scene_view_state_from_toggles(),
    )
    return controller, factory


def test_projection_has_distinct_quality_bad_good_and_scalar_bar_resources() -> None:
    from osw.gui.mesh_diagnostics_view_model import (
        MESH_BAD_ELEMENTS_ACTOR_KEY,
        MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
        MESH_QUALITY_ACTOR_KEY,
        MESH_QUALITY_SCALARBAR_ACTOR_KEY,
        build_mesh_diagnostics_overlay_specs,
    )

    analysis = analyze_mesh_cell_quality(_mesh(), provider=Provider((1.0, -1.0, 0.0)))
    specs = build_mesh_diagnostics_overlay_specs(analysis)

    assert specs.quality.actor_key == MESH_QUALITY_ACTOR_KEY == "mesh_quality"
    assert specs.quality.entity_indices == (0, 1, 2)
    assert specs.quality.values == (1.0, -1.0, 0.0)
    assert specs.quality.display_range == (-1.0, 1.0)
    assert specs.bad.actor_key == MESH_BAD_ELEMENTS_ACTOR_KEY == "mesh_bad_elements"
    assert specs.bad.stable_cell_keys == ("0:1", "0:2")
    assert specs.good.actor_key == MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY
    assert specs.good.entity_indices == (0,)
    assert specs.scalar_bar.actor_key == MESH_QUALITY_SCALARBAR_ACTOR_KEY
    assert "Scaled Jacobian" in specs.scalar_bar.title


def test_controller_coloring_filter_selection_and_generic_isolation_conflict() -> None:
    from osw.gui.mesh_diagnostics_view_model import (
        MESH_BAD_ELEMENTS_ACTOR_KEY,
        MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
        MESH_QUALITY_ACTOR_KEY,
        MESH_QUALITY_SCALARBAR_ACTOR_KEY,
    )

    controller, factory = _controller(Provider((1.0, -1.0, 0.0)))
    analysis = controller.analyze_mesh_quality()
    assert analysis is not None

    assert controller.set_mesh_quality_coloring_visible(True)
    assert controller.set_mesh_quality_highlight_visible(True)
    assert set(factory.session.actors) >= {
        "base_mesh",
        MESH_QUALITY_ACTOR_KEY,
        MESH_QUALITY_SCALARBAR_ACTOR_KEY,
        MESH_BAD_ELEMENTS_ACTOR_KEY,
    }
    assert controller.actor_records[MESH_QUALITY_ACTOR_KEY].category == "diagnostic"
    assert controller.actor_records[MESH_BAD_ELEMENTS_ACTOR_KEY].category == "diagnostic"
    assert controller.actor_records[MESH_BAD_ELEMENTS_ACTOR_KEY].pickable is False
    assert controller.actor_records[MESH_QUALITY_SCALARBAR_ACTOR_KEY].category == "helper"
    assert controller.set_mesh_quality_filter_mode("hide_bad")
    assert MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY in factory.session.actors
    assert factory.session.visibility["base_mesh"] is False

    assert controller.select_mesh_quality_bad_cells()
    target = controller.current_selection_target
    assert target is not None and target.locator is not None
    assert target.locator.entity_ids == ("0:1", "0:2")
    assert factory.session.current_selection == ("cell", (1, 2))

    assert controller.set_mesh_quality_filter_mode("clear")
    assert MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY not in factory.session.actors
    assert controller.isolate_actor("base_mesh")
    assert controller.set_mesh_quality_filter_mode("isolate_bad") is False
    assert controller.clear_isolation()
    assert controller.set_mesh_quality_filter_mode("isolate_bad")
    assert controller.mesh_quality_filter_mode == "isolate_bad"


def test_same_fingerprint_recomputes_and_changed_fingerprint_becomes_stale() -> None:
    from osw.gui.mesh_diagnostics_view_model import MESH_QUALITY_ACTOR_KEY

    provider = Provider((1.0, -1.0, 0.0))
    controller, factory = _controller(provider)
    first = controller.analyze_mesh_quality()
    assert first is not None
    assert controller.set_mesh_quality_threshold(0.2)
    assert controller.set_mesh_quality_range("manual", (-0.25, 0.75))
    assert controller.set_mesh_quality_coloring_visible(True)

    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-quality-v1"),
        scene_view_state_from_toggles(),
    )
    assert controller.mesh_quality_analysis is not None
    assert controller.mesh_quality_analysis.mesh_fingerprint == first.mesh_fingerprint
    assert controller.mesh_quality_view_model.threshold == 0.2
    assert controller.mesh_quality_view_model.range_mode == "manual"
    assert controller.mesh_quality_view_model.display_range == (-0.25, 0.75)
    assert MESH_QUALITY_ACTOR_KEY in factory.session.actors
    assert provider.calls == 2

    controller.load_mesh(
        _mesh(changed=True),
        mesh_input_ref("mesh-quality-v1"),
        scene_view_state_from_toggles(),
    )
    assert controller.mesh_quality_status is MeshDiagnosticsStatus.STALE
    assert controller.mesh_quality_analysis is not None
    assert controller.mesh_quality_analysis.status is MeshDiagnosticsStatus.STALE
    assert not any(key.startswith("mesh_quality") for key in factory.session.actors)
    assert "mesh_bad_elements" not in factory.session.actors
    assert controller.mesh_quality_view_model.overlay_actions_enabled is False
    assert controller.select_mesh_quality_bad_cells() is False
    assert factory.session.current_selection is None


def test_request_identity_rejects_late_completion_and_close_cancels() -> None:
    provider = Provider((1.0, -1.0, 0.0))
    controller, factory = _controller(provider)
    request = controller.begin_mesh_quality_analysis()
    assert request is not None
    assert controller.begin_mesh_quality_analysis() is None
    assert controller.mesh_quality_status is MeshDiagnosticsStatus.RUNNING
    late = analyze_mesh_cell_quality(request.mesh, provider=provider)

    controller.load_mesh(
        _mesh(changed=True),
        mesh_input_ref("mesh-quality-v1"),
        scene_view_state_from_toggles(),
    )
    assert controller.complete_mesh_quality_analysis(request, late) is False
    assert controller.mesh_quality_status is MeshDiagnosticsStatus.STALE
    controller.close()
    assert controller.complete_mesh_quality_analysis(request, late) is False
    assert factory.session.close_calls == 1


def test_quality_surface_temporarily_hides_and_restores_result_scalar_layer() -> None:
    controller, factory = _controller(Provider((1.0, -1.0, 0.0)))
    mesh = _mesh()
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None
    dataset = ResultDataset(
        dataset_id="diagnostics-results",
        source="memory",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("value",),
                rows=tuple(
                    ResultRow(index, {"value": float(index)}) for index in range(len(mesh.points))
                ),
                unit="K",
            ),
        ),
    )
    binding = ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-quality-v1",
        result_dataset_id=dataset.dataset_id,
        mesh_identity_schema=fingerprint.schema,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature={
            "node_count": len(mesh.points),
            "cell_count": sum(block.count for block in mesh.cells),
        },
    )
    controller.set_interactive_result_dataset(dataset, binding)
    assert controller.set_scalar_result("temperature", component="value").applied
    assert factory.session.visibility["result:scalar"] is True
    assert factory.session.visibility["result:colorbar"] is True
    assert factory.session.visibility["base_mesh"] is False

    controller.analyze_mesh_quality()
    assert controller.set_mesh_quality_coloring_visible(True)
    assert factory.session.visibility["result:scalar"] is False
    assert factory.session.visibility["result:colorbar"] is False
    assert factory.session.visibility["mesh_quality"] is True
    assert controller.set_mesh_quality_coloring_visible(False)
    assert factory.session.visibility["result:scalar"] is True
    assert factory.session.visibility["result:colorbar"] is True
    assert factory.session.visibility["base_mesh"] is False

    assert controller.set_mesh_quality_coloring_visible(True)
    assert controller.clear_scalar_result()
    assert "result:scalar" not in factory.session.actors
    assert factory.session.visibility["base_mesh"] is False
    assert controller.set_mesh_quality_coloring_visible(False)
    assert factory.session.visibility["base_mesh"] is True
