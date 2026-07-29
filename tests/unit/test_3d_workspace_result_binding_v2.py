"""Exact fingerprint-backed ResultDataset-to-mesh binding contracts."""

from __future__ import annotations

from importlib import import_module

import pytest

from osw.core.project_schema import Project, ProjectMetadata, ResultRef
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _api() -> object:
    api = import_module("osw.core.result_mesh_binding")
    required = {
        "RESULT_MESH_BINDING_SCHEMA_V1",
        "RESULT_MESH_BINDING_SCHEMA_V2",
        "ResultMeshBindingResolutionState",
        "resolve_result_mesh_binding",
    }
    missing = sorted(name for name in required if not hasattr(api, name))
    if missing:
        pytest.fail(
            "Result binding v2 contract is missing: " + ", ".join(missing),
            pytrace=False,
        )
    return api


def _mesh(*, moved: bool = False, rewired: bool = False) -> MeshData:
    points = (
        (0.0, 0.0, 0.0),
        (2.0 if moved else 1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    )
    connectivity = (0, 2, 1) if rewired else (0, 1, 2)
    return MeshData(
        points=points,
        cells=(MeshCellBlock("triangle", (connectivity,)),),
    )


def _dataset(dataset_id: str = "rd-1") -> ResultDataset:
    return ResultDataset(
        dataset_id=dataset_id,
        source="memory",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("value",),
                rows=tuple(
                    ResultRow(index, {"value": float(index + 1)})
                    for index in range(3)
                ),
                unit="K",
            ),
        ),
    )


def _v2_binding(api: object, mesh: MeshData | None = None) -> object:
    active = mesh or _mesh()
    fingerprint = compute_mesh_fingerprint(active)
    return api.ResultMeshBinding(
        schema=api.RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id="rd-1",
        field_id="temperature",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature={"node_count": 3, "cell_count": 1},
    )


def test_v2_payload_round_trips_exact_identity_without_schema_bump() -> None:
    api = _api()
    binding = _v2_binding(api)

    payload = binding.to_dict()

    assert payload["schema"] == "osw.result_mesh_binding.v2"
    assert payload["mesh_identity_schema"] == "osw.mesh_identity.v1"
    assert payload["mesh_fingerprint"] == compute_mesh_fingerprint(_mesh()).digest
    assert payload["mesh_signature"] == {"node_count": 3, "cell_count": 1}
    assert api.ResultMeshBinding.from_dict(payload) == binding

    ref = ResultRef(id="result-1", metadata={"mesh_binding": payload})
    project = Project(
        metadata=ProjectMetadata(name="Binding v2"),
        results=[ref],
        schema_version="0.3",
    )
    restored = Project.from_dict(project.to_dict())
    assert restored.schema_version == project.schema_version == "0.3"
    assert restored.results[0].metadata["mesh_binding"] == payload


def test_only_exact_v2_fingerprint_match_resolves() -> None:
    api = _api()
    binding = _v2_binding(api)

    result = api.resolve_result_mesh_binding(
        binding,
        active_mesh=_mesh(),
        active_mesh_ref="mesh-1",
        result_dataset=_dataset(),
        field_name="temperature",
        association="point",
    )

    assert result.state is api.ResultMeshBindingResolutionState.RESOLVED
    assert result.reason_code == "EXACT_MESH_FINGERPRINT_MATCH"
    assert result.binding == binding


@pytest.mark.parametrize(
    ("active_mesh", "reason"),
    (
        (_mesh(moved=True), "MESH_FINGERPRINT_MISMATCH"),
        (_mesh(rewired=True), "MESH_FINGERPRINT_MISMATCH"),
    ),
)
def test_same_counts_changed_geometry_or_topology_is_stale(
    active_mesh: MeshData,
    reason: str,
) -> None:
    api = _api()

    result = api.resolve_result_mesh_binding(
        _v2_binding(api),
        active_mesh=active_mesh,
        active_mesh_ref="mesh-1",
        result_dataset=_dataset(),
        field_name="temperature",
        association="point",
    )

    assert result.state is api.ResultMeshBindingResolutionState.STALE
    assert result.reason_code == reason
    assert result.transient_field is None


def test_v1_remains_readable_but_never_auto_applies() -> None:
    api = _api()
    legacy = api.ResultMeshBinding(
        schema=api.RESULT_MESH_BINDING_SCHEMA_V1,
        mesh_ref="mesh-1",
        result_dataset_id="rd-1",
        field_id="temperature",
        mesh_signature={"node_count": 3, "cell_count": 1},
    )

    restored = api.ResultMeshBinding.from_dict(legacy.to_dict())
    result = api.resolve_result_mesh_binding(
        restored,
        active_mesh=_mesh(),
        active_mesh_ref="mesh-1",
        result_dataset=_dataset(),
        field_name="temperature",
    )

    assert restored.schema == "osw.result_mesh_binding.v1"
    assert result.state is api.ResultMeshBindingResolutionState.STALE
    assert result.reason_code == "LEGACY_BINDING_FINGERPRINT_UNVERIFIED"
    assert result.transient_field is None


def test_absent_mesh_or_dataset_is_unresolved_with_exact_reason() -> None:
    api = _api()
    binding = _v2_binding(api)

    no_mesh = api.resolve_result_mesh_binding(
        binding,
        active_mesh=None,
        active_mesh_ref="mesh-1",
        result_dataset=_dataset(),
    )
    no_dataset = api.resolve_result_mesh_binding(
        binding,
        active_mesh=_mesh(),
        active_mesh_ref="mesh-1",
        result_dataset=None,
    )

    assert no_mesh.state is api.ResultMeshBindingResolutionState.UNRESOLVED
    assert no_mesh.reason_code == "ACTIVE_MESH_NOT_LOADED"
    assert no_dataset.state is api.ResultMeshBindingResolutionState.UNRESOLVED
    assert no_dataset.reason_code == "RESULT_DATASET_NOT_AVAILABLE"


def test_malformed_or_future_schema_fails_closed() -> None:
    api = _api()

    malformed = api.resolve_result_mesh_binding(
        {
            "schema": "osw.result_mesh_binding.v99",
            "mesh_ref": "mesh-1",
            "result_dataset_id": "rd-1",
        },
        active_mesh=_mesh(),
        active_mesh_ref="mesh-1",
        result_dataset=_dataset(),
    )
    missing_fingerprint = api.resolve_result_mesh_binding(
        {
            "schema": api.RESULT_MESH_BINDING_SCHEMA_V2,
            "mesh_ref": "mesh-1",
            "result_dataset_id": "rd-1",
            "mesh_identity_schema": MESH_IDENTITY_SCHEMA,
        },
        active_mesh=_mesh(),
        active_mesh_ref="mesh-1",
        result_dataset=_dataset(),
    )

    assert malformed.state is api.ResultMeshBindingResolutionState.INVALID
    assert malformed.reason_code == "MALFORMED_BINDING_SCHEMA"
    assert missing_fingerprint.state is api.ResultMeshBindingResolutionState.INVALID
    assert missing_fingerprint.reason_code == "MISSING_MESH_FINGERPRINT"
