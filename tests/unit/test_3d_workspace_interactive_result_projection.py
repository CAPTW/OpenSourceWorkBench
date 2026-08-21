"""Pure scalar/vector projection and semantic result actor contracts."""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _api() -> tuple[object, object, object]:
    mapping = import_module("osw.post.result_field_mapping")
    try:
        projection = import_module("osw.gui.interactive_results_view_model")
    except ModuleNotFoundError:
        pytest.fail(
            "pure interactive-results projection module is missing",
            pytrace=False,
        )
    binding = import_module("osw.core.result_mesh_binding")
    required_mapping = {
        "ScalarRangeMode",
        "project_interactive_scalar_result",
        "build_result_vector_glyph_spec",
    }
    missing = sorted(name for name in required_mapping if not hasattr(mapping, name))
    if missing or not hasattr(ActiveSceneController, "set_scalar_result"):
        pytest.fail(
            "interactive result projection/lifecycle is missing: "
            + ", ".join(missing or ("ActiveSceneController.set_scalar_result",)),
            pytrace=False,
        )
    return mapping, projection, binding


def _mesh(point_count: int = 6) -> MeshData:
    points = tuple((float(index), 0.0, 0.0) for index in range(point_count))
    cells = (
        MeshCellBlock(
            "line",
            tuple((index, index + 1) for index in range(point_count - 1)),
        ),
    )
    return MeshData(points=points, cells=cells)


def _scalar_field(values: tuple[float, ...]) -> ResultField:
    return ResultField(
        name="temperature",
        location="node",
        components=("value",),
        rows=tuple(ResultRow(index, {"value": value}) for index, value in enumerate(values)),
        unit="K",
    )


def _vector_field(vectors: tuple[tuple[float, float, float], ...]) -> ResultField:
    return ResultField(
        name="displacement",
        location="node",
        components=("ux", "uy", "uz"),
        rows=tuple(
            ResultRow(
                index,
                {"ux": vector[0], "uy": vector[1], "uz": vector[2]},
            )
            for index, vector in enumerate(vectors)
        ),
        unit="mm",
    )


def _dataset(*fields: ResultField) -> ResultDataset:
    return ResultDataset(
        dataset_id="rd-1",
        source="memory",
        solver="fixture",
        analysis_type="static",
        fields=tuple(fields),
    )


def _binding(api: object, mesh: MeshData) -> object:
    fingerprint = compute_mesh_fingerprint(mesh)
    return api.ResultMeshBinding(
        schema=api.RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id="rd-1",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature={
            "node_count": len(mesh.points),
            "cell_count": sum(block.count for block in mesh.cells),
        },
    )


def _resolved(api: object, mesh: MeshData, dataset: ResultDataset) -> object:
    return api.resolve_result_mesh_binding(
        _binding(api, mesh),
        active_mesh=mesh,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )


def test_scalar_auto_and_manual_ranges_are_explicit_and_finite() -> None:
    mapping, _projection, binding = _api()
    mesh = _mesh(3)
    field = _scalar_field((2.0, 4.0, 8.0))
    dataset = _dataset(field)
    resolution = _resolved(binding, mesh, dataset)

    automatic = mapping.project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="temperature",
        component="value",
        range_mode=mapping.ScalarRangeMode.AUTO,
        colormap="viridis",
        colorbar_visible=True,
    )
    manual = mapping.project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="temperature",
        component="value",
        range_mode=mapping.ScalarRangeMode.MANUAL,
        manual_range=(0.0, 10.0),
        colormap="plasma",
        colorbar_visible=False,
    )

    assert automatic.applied is True
    assert automatic.association == "point"
    assert automatic.data_range == (2.0, 8.0)
    assert automatic.display_range == (2.0, 8.0)
    assert automatic.colorbar_title == "temperature / value [K]"
    assert manual.applied is True
    assert manual.data_range == (2.0, 8.0)
    assert manual.display_range == (0.0, 10.0)
    assert manual.colormap == "plasma"
    assert manual.colorbar_visible is False


def test_constant_scalar_uses_documented_nonzero_display_range() -> None:
    mapping, _projection, binding = _api()
    mesh = _mesh(3)
    dataset = _dataset(_scalar_field((5.0, 5.0, 5.0)))

    result = mapping.project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolved(binding, mesh, dataset),
        field_name="temperature",
        component="value",
    )

    assert result.data_range == (5.0, 5.0)
    assert result.display_range == pytest.approx((5.0 - 5e-12, 5.0 + 5e-12))


@pytest.mark.parametrize(
    ("manual_range", "colormap"),
    (
        ((1.0, 1.0), "viridis"),
        ((float("nan"), 2.0), "viridis"),
        ((0.0, 1.0), "backend-code()"),
    ),
)
def test_invalid_range_or_colormap_fails_closed(
    manual_range: tuple[float, float],
    colormap: str,
) -> None:
    mapping, _projection, binding = _api()
    mesh = _mesh(3)
    dataset = _dataset(_scalar_field((1.0, 2.0, 3.0)))

    result = mapping.project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolved(binding, mesh, dataset),
        field_name="temperature",
        component="value",
        range_mode=mapping.ScalarRangeMode.MANUAL,
        manual_range=manual_range,
        colormap=colormap,
    )

    assert result.applied is False
    assert result.status == "INVALID"
    assert result.diagnostics


def test_nonfinite_scalar_values_remain_missing_without_overlay_mutation() -> None:
    mapping, _projection, binding = _api()
    mesh = _mesh(3)
    dataset = _dataset(_scalar_field((1.0, float("nan"), 3.0)))

    result = mapping.project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolved(binding, mesh, dataset),
        field_name="temperature",
        component="value",
    )

    assert result.applied is True
    assert result.status == "RESOLVED"
    assert result.data_range == (1.0, 3.0)
    assert result.statistics.finite_count == 2
    assert result.statistics.nonfinite_count == 1
    assert "temperature" not in mesh.point_data


def test_vector_sampler_uses_stable_ranks_and_excludes_zero_vectors() -> None:
    mapping, _projection, binding = _api()
    mesh = _mesh(7)
    vectors = (
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (4.0, 0.0, 0.0),
        (5.0, 0.0, 0.0),
        (6.0, 0.0, 0.0),
    )
    dataset = _dataset(_vector_field(vectors))

    spec = mapping.build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=_resolved(binding, mesh, dataset),
        field_name="displacement",
        components=("ux", "uy", "uz"),
        maximum_glyph_count=3,
        scale=2.0,
    )

    assert spec.applied is True
    assert spec.candidate_count == 6
    assert spec.zero_vector_count == 1
    assert spec.sampled_count == 3
    assert spec.omitted_count == 3
    assert spec.selected_candidate_ranks == (0, 2, 5)
    assert spec.stable_entity_keys == (0, 3, 6)
    assert spec.transient_backend_indices == (0, 3, 6)
    assert spec.positions == ((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (6.0, 0.0, 0.0))


class RecordingResultSession:
    backend_kind = "fake-results"
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
        self.actors: dict[str, object] = {
            "named_selection:keep": object(),
            "setup:force:keep": object(),
            "mesh_quality:bad_cells": object(),
        }
        self.replacements: list[str] = []
        self.visibility: dict[str, bool] = {}
        self.close_calls = 0

    @property
    def hosted_widget(self) -> None:
        return None

    def clear(self) -> None:
        self.actors.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        del generation
        self.actors[semantic_id] = payload
        self.replacements.append(semantic_id)
        return SimpleNamespace(rendered=True, diagnostics=())

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def set_representation(self, _mode: str) -> None:
        return None

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = visible

    def clear_hover(self) -> None:
        return None

    def clear_current_selection(self) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def close(self) -> None:
        self.close_calls += 1
        self.actors.clear()


class RecordingResultFactory:
    backend_kind = RecordingResultSession.backend_kind
    capabilities = RecordingResultSession.capabilities

    def __init__(self) -> None:
        self.session = RecordingResultSession()

    def create_session(self) -> RecordingResultSession:
        return self.session


def test_controller_replaces_semantic_result_resources_and_preserves_other_actors() -> None:
    _mapping, projection, binding = _api()
    mesh = _mesh(3)
    scalar = _scalar_field((1.0, 2.0, 3.0))
    vector = _vector_field(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    dataset = _dataset(scalar, vector)
    factory = RecordingResultFactory()
    controller = ActiveSceneController(factory)
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    controller.set_interactive_result_dataset(dataset, _binding(binding, mesh))

    first_scalar = controller.set_scalar_result(
        "temperature",
        component="value",
    )
    second_scalar = controller.set_scalar_result(
        "temperature",
        component="value",
        colormap="plasma",
    )
    vector_result = controller.set_vector_result(
        "displacement",
        components=("ux", "uy", "uz"),
        maximum_glyph_count=2,
        scale=1.0,
    )

    assert first_scalar.applied and second_scalar.applied and vector_result.applied
    assert projection.RESULT_SCALAR_ACTOR_KEY == "result:scalar"
    assert projection.RESULT_VECTOR_ACTOR_KEY == "result:vector"
    assert projection.RESULT_COLORBAR_ACTOR_KEY == "result:colorbar"
    assert factory.session.replacements.count("result:scalar") == 2
    assert list(factory.session.actors).count("result:scalar") == 1
    assert "result:vector" in factory.session.actors
    assert set(factory.session.actors) >= {
        "named_selection:keep",
        "setup:force:keep",
        "mesh_quality:bad_cells",
    }
    assert controller.actor_records["base_mesh"].visible is False
    assert controller.clear_scalar_result() is True
    assert controller.actor_records["base_mesh"].visible is True
    assert "result:scalar" not in factory.session.actors
    assert "result:vector" in factory.session.actors

    controller.clear_interactive_results()
    controller.clear_interactive_results()
    assert not any(key.startswith("result:") for key in factory.session.actors)
    controller.close()
    controller.close()
    assert factory.session.close_calls == 1


def test_diagnostics_isolation_and_scalar_surface_conflict_fails_closed() -> None:
    _mapping, _projection, binding = _api()
    mesh = _mesh(3)
    dataset = _dataset(_scalar_field((1.0, 2.0, 3.0)))
    factory = RecordingResultFactory()
    controller = ActiveSceneController(factory)
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    controller.set_interactive_result_dataset(dataset, _binding(binding, mesh))
    controller._mesh_quality_visibility_snapshot = {"base_mesh": True}

    blocked = controller.set_scalar_result("temperature", component="value")

    assert blocked.applied is False
    assert "restore diagnostics isolation first" in blocked.diagnostics[0].lower()
    assert "result:scalar" not in factory.session.actors


def test_controller_probe_and_selected_table_share_exact_stable_identity() -> None:
    _mapping, projection, binding = _api()
    probe = import_module("osw.post.result_probe")
    mesh = _mesh(3)
    dataset = _dataset(_scalar_field((1.0, 2.0, 3.0)))
    factory = RecordingResultFactory()
    controller = ActiveSceneController(factory)
    controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    controller.set_interactive_result_dataset(dataset, _binding(binding, mesh))

    result = controller.probe_result(
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_key=1,
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        )
    )
    table = controller.set_selected_result_table(
        field_name="temperature",
        component="value",
        association="point",
        stable_entity_keys=(2, 1),
        limit=500,
    )

    assert result.status is probe.ResultProbeStatus.RESOLVED
    assert result.value == 2.0
    assert projection.RESULT_PROBE_ACTOR_KEY == "result:probe"
    assert "result:probe" in factory.session.actors
    assert table is not None
    assert tuple(row.stable_entity_key for row in table.rows) == (1, 2)
    assert tuple(row.value for row in table.rows) == (2.0, 3.0)
    assert set(factory.session.actors) >= {
        "named_selection:keep",
        "setup:force:keep",
        "mesh_quality:bad_cells",
    }
