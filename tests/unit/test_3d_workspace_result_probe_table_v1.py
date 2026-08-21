"""Canonical scalar/vector result probe and selected-table contracts."""

from __future__ import annotations

from math import isnan

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import (
    RESULT_MESH_BINDING_SCHEMA_V2,
    ResultMeshBinding,
    resolve_result_mesh_binding,
)
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.result_probe import (
    ResultProbeRequest,
    ResultProbeStatus,
    ResultValueStatus,
    build_selected_result_table,
    probe_result_entity,
)


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
        source="fixture",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                "temperature",
                "point",
                ("value",),
                _rows(((10.0,), (float("nan"),), (30.0,), (40.0,), (50.0,)), ("value",)),
                "K",
            ),
            ResultField(
                "velocity",
                "point",
                ("vx", "vy", "vz"),
                _rows(
                    (
                        (3.0, 4.0, 0.0),
                        (1.0, 2.0, 2.0),
                        (0.0, 0.0, 0.0),
                        (1.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                    ),
                    ("vx", "vy", "vz"),
                ),
                "m/s",
            ),
            ResultField(
                "cell_flux",
                "cell",
                ("x", "y", "z"),
                _rows(((1.0, 0.0, 0.0), (0.0, 2.0, 0.0)), ("x", "y", "z")),
                "W/m^2",
            ),
        ),
    )


def _binding(mesh: MeshData) -> ResultMeshBinding:
    return ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id="result-1",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
    )


def _resolution(mesh: MeshData, dataset: ResultDataset) -> object:
    return resolve_result_mesh_binding(
        _binding(mesh),
        active_mesh=mesh,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )


def _request(
    mesh: MeshData,
    *,
    field: str,
    component: str,
    association: str,
    key: int | str,
) -> ResultProbeRequest:
    return ResultProbeRequest(
        dataset_id="result-1",
        field_name=field,
        component=component,
        association=association,
        stable_entity_key=key,
        mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
    )


def test_point_vector_probe_reports_components_magnitude_and_coordinate() -> None:
    mesh = _mesh()
    dataset = _dataset()

    result = probe_result_entity(
        mesh,
        dataset,
        _request(
            mesh,
            field="velocity",
            component="magnitude",
            association="point",
            key=0,
        ),
        binding_resolution=_resolution(mesh, dataset),
    )

    assert result.status is ResultProbeStatus.RESOLVED
    assert result.value_status is ResultValueStatus.FINITE
    assert result.entity_display_id == "point 0"
    assert result.coordinate == (0.0, 0.0, 0.0)
    assert tuple((item.component, item.value) for item in result.component_values) == (
        ("vx", 3.0),
        ("vy", 4.0),
        ("vz", 0.0),
    )
    assert result.magnitude == 5.0
    assert result.value == 5.0
    assert result.unit == "m/s"


def test_cell_vector_probe_reports_canonical_topology_and_centroid() -> None:
    mesh = _mesh()
    dataset = _dataset()

    result = probe_result_entity(
        mesh,
        dataset,
        _request(
            mesh,
            field="cell_flux",
            component="y",
            association="cell",
            key="1:0",
        ),
        binding_resolution=_resolution(mesh, dataset),
    )

    assert result.status is ResultProbeStatus.RESOLVED
    assert result.value == 2.0
    assert result.magnitude == 2.0
    assert result.cell_type == "tetra"
    assert result.connectivity == (1, 2, 3, 4)
    assert result.centroid == pytest.approx((0.5, 0.5, 0.5))
    assert result.stable_entity_key == "1:0"


def test_nonfinite_scalar_probe_is_resolved_as_na_not_rewritten_or_dropped() -> None:
    mesh = _mesh()
    dataset = _dataset()

    result = probe_result_entity(
        mesh,
        dataset,
        _request(
            mesh,
            field="temperature",
            component="scalar",
            association="point",
            key=1,
        ),
        binding_resolution=_resolution(mesh, dataset),
    )

    assert result.status is ResultProbeStatus.RESOLVED
    assert result.value_status is ResultValueStatus.NONFINITE
    assert result.value is None
    assert result.display_value == "N/A"
    assert len(result.component_values) == 1
    assert isnan(result.component_values[0].raw_value)


def test_association_mismatch_is_explicit_and_never_interpolated() -> None:
    mesh = _mesh()
    dataset = _dataset()

    result = probe_result_entity(
        mesh,
        dataset,
        _request(
            mesh,
            field="temperature",
            component="scalar",
            association="cell",
            key="0:0",
        ),
        binding_resolution=_resolution(mesh, dataset),
    )

    assert result.status is ResultProbeStatus.ASSOCIATION_MISMATCH
    assert result.value_status is ResultValueStatus.ASSOCIATION_MISMATCH
    assert result.value is None
    assert result.reason_code == "ASSOCIATION_MISMATCH"


def test_selected_table_keeps_duplicates_out_and_includes_vector_metadata() -> None:
    mesh = _mesh()
    dataset = _dataset()

    table = build_selected_result_table(
        mesh,
        dataset,
        field_name="velocity",
        component="magnitude",
        association="point",
        stable_entity_keys=(4, 0, 4, 1),
        binding_resolution=_resolution(mesh, dataset),
        limit=500,
    )

    assert table.status == "RESOLVED"
    assert tuple(row.stable_entity_key for row in table.rows) == (0, 1, 4)
    assert tuple(row.value for row in table.rows) == (5.0, 3.0, 1.0)
    assert tuple(row.magnitude for row in table.rows) == (5.0, 3.0, 1.0)
    assert all(row.entity_kind == "point" for row in table.rows)
    assert all(row.association_status == "MATCH" for row in table.rows)
    assert table.total_count == 3


def test_selected_table_preserves_na_and_emits_association_mismatch_rows() -> None:
    mesh = _mesh()
    dataset = _dataset()
    nonfinite = build_selected_result_table(
        mesh,
        dataset,
        field_name="temperature",
        component="scalar",
        association="point",
        stable_entity_keys=(1,),
        binding_resolution=_resolution(mesh, dataset),
    )
    mismatch = build_selected_result_table(
        mesh,
        dataset,
        field_name="temperature",
        component="scalar",
        association="cell",
        stable_entity_keys=("1:0", "0:0"),
        binding_resolution=_resolution(mesh, dataset),
    )

    assert nonfinite.rows[0].display_value == "N/A"
    assert nonfinite.rows[0].value_status == "NONFINITE"
    assert tuple(row.stable_entity_key for row in mismatch.rows) == ("0:0", "1:0")
    assert all(row.association_status == "ASSOCIATION_MISMATCH" for row in mismatch.rows)
    assert all(row.display_value == "N/A" for row in mismatch.rows)


def test_selected_table_invalid_key_fallback_order_is_deterministic() -> None:
    mesh = _mesh()
    dataset = _dataset()

    table = build_selected_result_table(
        mesh,
        dataset,
        field_name="temperature",
        component="scalar",
        association="point",
        stable_entity_keys=("bad-b", "bad-a", "bad-b"),
        binding_resolution=_resolution(mesh, dataset),
    )

    assert tuple(row.stable_entity_key for row in table.rows) == ("bad-a", "bad-b")
    assert all(row.value_status == "NOT_FOUND" for row in table.rows)


def test_stale_table_is_empty_and_carries_reason_without_rebinding_ids() -> None:
    mesh = _mesh()
    dataset = _dataset()
    stale = resolve_result_mesh_binding(
        _binding(mesh),
        active_mesh=_mesh(moved=True),
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )

    table = build_selected_result_table(
        _mesh(moved=True),
        dataset,
        field_name="temperature",
        component="scalar",
        association="point",
        stable_entity_keys=(0, 1),
        binding_resolution=stale,
    )

    assert table.status == "STALE"
    assert table.rows == ()
    assert table.total_count == 2
    assert "fingerprint" in table.diagnostics[0].lower()
