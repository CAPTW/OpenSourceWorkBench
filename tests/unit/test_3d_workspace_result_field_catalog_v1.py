"""Exact-binding interactive ResultDataset field catalog contracts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import (
    RESULT_MESH_BINDING_SCHEMA_V2,
    ResultMeshBinding,
    resolve_result_mesh_binding,
)
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.result_field_catalog import (
    ResultBindingStatus,
    ResultFieldKind,
    build_result_field_catalog,
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
        ResultRow(index, dict(zip(components, row, strict=True)))
        for index, row in enumerate(values)
    )


def _dataset() -> ResultDataset:
    return ResultDataset(
        dataset_id="result-1",
        source="fixture",
        solver="fixture-provider",
        analysis_type="linear_static",
        fields=(
            ResultField(
                name="temperature",
                location="point",
                components=("value",),
                rows=_rows(
                    ((10.0,), (20.0,), (float("nan"),), (40.0,), (50.0,)),
                    ("value",),
                ),
                unit="K",
            ),
            ResultField(
                name="stress",
                location="cell",
                components=("value",),
                rows=_rows(((100.0,), (200.0,)), ("value",)),
                unit="Pa",
            ),
            ResultField(
                name="displacement",
                location="point",
                components=("ux", "uy", "uz"),
                rows=_rows(
                    (
                        (0.0, 0.0, 0.0),
                        (0.1, 0.0, 0.0),
                        (0.0, 0.2, 0.0),
                        (0.0, 0.0, 0.3),
                        (0.1, 0.2, 0.3),
                    ),
                    ("ux", "uy", "uz"),
                ),
                unit="m",
            ),
            ResultField(
                name="cell_flux",
                location="cell",
                components=("x", "y", "z"),
                rows=_rows(((1.0, 0.0, 0.0), (0.0, 2.0, 0.0)), ("x", "y", "z")),
                unit="W/m^2",
            ),
            ResultField(
                name="tensor_like",
                location="cell",
                components=("xx", "yy", "zz", "xy", "yz", "zx"),
                rows=_rows(
                    ((1.0, 1.0, 1.0, 0.0, 0.0, 0.0),) * 2,
                    ("xx", "yy", "zz", "xy", "yz", "zx"),
                ),
            ),
            ResultField(
                name="_osw_transient_point_index",
                location="point",
                components=("value",),
                rows=_rows(((0.0,), (1.0,), (2.0,), (3.0,), (4.0,)), ("value",)),
            ),
        ),
        metadata={
            "title": "Static result fixture",
            "mesh_length_unit": "m",
            "provider_name": "fixture-provider",
            "provider_version": "1.0",
            "field_semantics": {
                "displacement": {
                    "semantic_role": "displacement",
                    "quantity_dimension": "length",
                    "coordinate_system": "global_cartesian",
                }
            },
        },
    )


def _binding(mesh: MeshData) -> ResultMeshBinding:
    fingerprint = compute_mesh_fingerprint(mesh)
    return ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id="result-1",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
        mesh_signature={
            "node_count": len(mesh.points),
            "cell_count": sum(block.count for block in mesh.cells),
        },
    )


def _resolution(mesh: MeshData, dataset: ResultDataset) -> object:
    return resolve_result_mesh_binding(
        _binding(mesh),
        active_mesh=mesh,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )


def test_catalog_is_deterministic_association_safe_and_metadata_complete() -> None:
    mesh = _mesh()
    dataset = _dataset()

    catalog = build_result_field_catalog(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
    )

    assert catalog.binding_status is ResultBindingStatus.READY
    assert catalog.result_id == "result-1"
    assert catalog.display_name == "Static result fixture"
    assert catalog.mesh_fingerprint == compute_mesh_fingerprint(mesh).digest
    assert catalog.point_count == 5
    assert catalog.cell_count == 2
    assert tuple(descriptor.field_id for descriptor in catalog.fields) == (
        "temperature",
        "stress",
        "displacement",
        "cell_flux",
    )
    assert tuple(descriptor.kind for descriptor in catalog.fields) == (
        ResultFieldKind.POINT_SCALAR,
        ResultFieldKind.CELL_SCALAR,
        ResultFieldKind.POINT_VECTOR,
        ResultFieldKind.CELL_VECTOR,
    )

    temperature = catalog.field("temperature")
    assert temperature.component_names == ("value",)
    assert temperature.units == "K"
    assert temperature.tuple_count == 5
    assert temperature.finite_tuple_count == 4
    assert temperature.nonfinite_tuple_count == 1

    displacement = catalog.field("displacement")
    assert displacement.semantic_role == "displacement"
    assert displacement.quantity_dimension == "length"
    assert displacement.coordinate_system == "global_cartesian"
    assert displacement.units == "m"
    assert displacement.deformation_eligible is True

    assert "tensor_like" in catalog.excluded_field_ids
    assert "_osw_transient_point_index" in catalog.excluded_field_ids
    assert any("tensor" in diagnostic.lower() for diagnostic in catalog.diagnostics)


@pytest.mark.parametrize(
    ("field", "expected"),
    (
        (
            ResultField(
                name="bad-point",
                location="point",
                components=("value",),
                rows=(ResultRow(0, {"value": 1.0}),),
            ),
            ResultBindingStatus.INVALID_POINT_COUNT,
        ),
        (
            ResultField(
                name="bad-cell",
                location="cell",
                components=("value",),
                rows=(ResultRow(0, {"value": 1.0}),),
            ),
            ResultBindingStatus.INVALID_CELL_COUNT,
        ),
        (
            ResultField(
                name="bad-association",
                location="face",
                components=("value",),
                rows=(ResultRow(0, {"value": 1.0}),),
            ),
            ResultBindingStatus.UNSUPPORTED_ASSOCIATION,
        ),
        (
            ResultField(
                name="ragged",
                location="point",
                components=("x", "y", "z"),
                rows=tuple(ResultRow(index, {"x": 1.0, "y": 2.0}) for index in range(5)),
            ),
            ResultBindingStatus.INVALID_FIELD_SHAPE,
        ),
    ),
)
def test_catalog_fails_closed_on_count_association_or_shape(
    field: ResultField,
    expected: ResultBindingStatus,
) -> None:
    mesh = _mesh()
    base = _dataset()
    dataset = replace(base, fields=(field,))

    catalog = build_result_field_catalog(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
    )

    assert catalog.binding_status is expected
    assert catalog.fields == ()
    assert catalog.diagnostics


def test_stale_and_legacy_bindings_never_publish_a_ready_catalog() -> None:
    mesh = _mesh()
    dataset = _dataset()
    stale = resolve_result_mesh_binding(
        _binding(mesh),
        active_mesh=_mesh(moved=True),
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )
    legacy = replace(
        _binding(mesh),
        schema="osw.result_mesh_binding.v1",
        mesh_identity_schema="",
        mesh_fingerprint="",
    )
    legacy_resolution = resolve_result_mesh_binding(
        legacy,
        active_mesh=mesh,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )

    stale_catalog = build_result_field_catalog(
        _mesh(moved=True),
        dataset,
        binding_resolution=stale,
    )
    legacy_catalog = build_result_field_catalog(
        mesh,
        dataset,
        binding_resolution=legacy_resolution,
    )

    assert stale_catalog.binding_status is ResultBindingStatus.STALE_MESH
    assert stale_catalog.fields == ()
    assert legacy_catalog.binding_status is ResultBindingStatus.LEGACY_UNRESOLVED
    assert legacy_catalog.fields == ()


def test_duplicate_field_ids_are_rejected_without_silent_normalization() -> None:
    mesh = _mesh()
    base = _dataset()
    duplicate = replace(base, fields=(base.fields[0], base.fields[0]))

    catalog = build_result_field_catalog(
        mesh,
        duplicate,
        binding_resolution=_resolution(mesh, duplicate),
    )

    assert catalog.binding_status is ResultBindingStatus.INVALID_FIELD_SHAPE
    assert catalog.fields == ()
    assert "duplicate" in catalog.diagnostics[0].lower()
