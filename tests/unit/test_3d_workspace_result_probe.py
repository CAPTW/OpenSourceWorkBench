"""Exact point/cell probe and bounded selected-result table contracts."""

from __future__ import annotations

from importlib import import_module

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _api() -> tuple[object, object]:
    try:
        probe = import_module("osw.post.result_probe")
    except ModuleNotFoundError:
        pytest.fail("pure result probe module is missing", pytrace=False)
    binding = import_module("osw.core.result_mesh_binding")
    required = {
        "ResultProbeRequest",
        "ResultProbeStatus",
        "probe_result_entity",
        "build_selected_result_table",
    }
    missing = sorted(name for name in required if not hasattr(probe, name))
    if missing:
        pytest.fail(
            "result probe/table contract is missing: " + ", ".join(missing),
            pytrace=False,
        )
    return probe, binding


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


def _dataset(*, nonfinite: bool = False) -> ResultDataset:
    node_values = (10.0, float("nan"), 30.0) if nonfinite else (10.0, 20.0, 30.0)
    return ResultDataset(
        dataset_id="rd-1",
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
                    for index, value in enumerate(node_values)
                ),
                unit="K",
            ),
            ResultField(
                name="stress",
                location="cell",
                components=("sxx",),
                rows=(ResultRow(0, {"sxx": 42.0}),),
                unit="MPa",
            ),
        ),
    )


def _binding(api: object, mesh: MeshData | None = None) -> object:
    active = mesh or _mesh()
    fingerprint = compute_mesh_fingerprint(active)
    return api.ResultMeshBinding(
        schema=api.RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id="rd-1",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
    )


def _resolved(api: object, dataset: ResultDataset | None = None) -> object:
    return api.resolve_result_mesh_binding(
        _binding(api),
        active_mesh=_mesh(),
        active_mesh_ref="mesh-1",
        result_dataset=dataset or _dataset(),
    )


def test_exact_point_and_cell_probe_return_stored_values_only() -> None:
    probe, binding = _api()
    mesh = _mesh()
    dataset = _dataset()
    resolution = _resolved(binding, dataset)

    point = probe.probe_result_entity(
        mesh,
        dataset,
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_key=1,
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        ),
        binding_resolution=resolution,
    )
    cell = probe.probe_result_entity(
        mesh,
        dataset,
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="stress",
            component="sxx",
            association="cell",
            stable_entity_key="0:0",
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        ),
        binding_resolution=resolution,
    )

    assert point.status is probe.ResultProbeStatus.RESOLVED
    assert point.value == 20.0
    assert point.entity_display_id == "point 1"
    assert point.unit == "K"
    assert cell.status is probe.ResultProbeStatus.RESOLVED
    assert cell.value == 42.0
    assert cell.entity_display_id == "cell 0:0"
    assert cell.unit == "MPa"


def test_probe_wrong_association_missing_row_stale_and_nonfinite_fail_closed() -> None:
    probe, binding = _api()
    mesh = _mesh()
    dataset = _dataset()
    resolution = _resolved(binding, dataset)

    mismatch = probe.probe_result_entity(
        mesh,
        dataset,
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="temperature",
            component="value",
            association="cell",
            stable_entity_key="0:0",
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        ),
        binding_resolution=resolution,
    )
    missing = probe.probe_result_entity(
        mesh,
        dataset,
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_key=99,
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        ),
        binding_resolution=resolution,
    )
    stale_resolution = binding.resolve_result_mesh_binding(
        _binding(binding),
        active_mesh=MeshData(
            points=((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        ),
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )
    stale = probe.probe_result_entity(
        mesh,
        dataset,
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_key=0,
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        ),
        binding_resolution=stale_resolution,
    )
    invalid = probe.probe_result_entity(
        mesh,
        _dataset(nonfinite=True),
        probe.ResultProbeRequest(
            dataset_id="rd-1",
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_key=1,
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        ),
        binding_resolution=resolution,
    )

    assert mismatch.status is probe.ResultProbeStatus.ASSOCIATION_MISMATCH
    assert missing.status is probe.ResultProbeStatus.NOT_FOUND
    assert stale.status is probe.ResultProbeStatus.STALE
    assert invalid.status is probe.ResultProbeStatus.INVALID


def test_selected_result_table_is_deterministic_bounded_and_shares_lookup() -> None:
    probe, binding = _api()
    mesh = _mesh()
    dataset = _dataset()

    table = probe.build_selected_result_table(
        mesh,
        dataset,
        field_name="temperature",
        component="value",
        association="point",
        stable_entity_keys=(2, 0, 1),
        binding_resolution=_resolved(binding, dataset),
        limit=2,
    )

    assert tuple(row.stable_entity_key for row in table.rows) == (0, 1)
    assert tuple(row.value for row in table.rows) == (10.0, 20.0)
    assert tuple(row.unit for row in table.rows) == ("K", "K")
    assert table.total_count == 3
    assert table.truncated_count == 1
    assert table.limit == 2


@pytest.mark.parametrize("limit", (0, -1, 501))
def test_selected_result_table_limit_is_fail_closed(limit: int) -> None:
    probe, binding = _api()

    with pytest.raises(ValueError, match="between 1 and 500"):
        probe.build_selected_result_table(
            _mesh(),
            _dataset(),
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_keys=(0,),
            binding_resolution=_resolved(binding),
            limit=limit,
        )
