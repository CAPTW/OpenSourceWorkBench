"""Typed displacement eligibility and derived-shape projection contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from math import sqrt

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import (
    RESULT_MESH_BINDING_SCHEMA_V2,
    ResultMeshBinding,
    resolve_result_mesh_binding,
)
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.result_deformation import (
    DeformationMode,
    DeformationScaleMode,
    DeformationStatus,
    build_deformed_shape_spec,
    evaluate_displacement_eligibility,
)


def _mesh(*, moved: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (2.0 if moved else 1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
        point_data={"source_point": (1.0, 2.0, 3.0, 4.0)},
        cell_data={"source_cell": (5.0,)},
    )


def _field(
    *,
    name: str = "u",
    location: str = "point",
    unit: str = "m",
    nonfinite: bool = False,
) -> ResultField:
    values = (
        (0.0, 0.0, 0.0),
        (0.1, 0.0, 0.0),
        (0.0, float("nan") if nonfinite else 0.2, 0.0),
        (0.0, 0.0, 0.3),
    )
    return ResultField(
        name=name,
        location=location,
        components=("ux", "uy", "uz"),
        rows=tuple(
            ResultRow(index, dict(zip(("ux", "uy", "uz"), value, strict=True)))
            for index, value in enumerate(values)
        ),
        unit=unit,
    )


def _dataset(
    field: ResultField | None = None,
    *,
    semantic: bool = True,
    mesh_unit: str = "m",
) -> ResultDataset:
    active = field or _field()
    semantics = (
        {
            active.name: {
                "semantic_role": "displacement",
                "quantity_dimension": "length",
                "coordinate_system": "global_cartesian",
            }
        }
        if semantic
        else {}
    )
    return ResultDataset(
        dataset_id="result-1",
        source="fixture",
        solver="fixture",
        analysis_type="static",
        fields=(active,),
        metadata={
            "mesh_length_unit": mesh_unit,
            "field_semantics": semantics,
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


def _resolution(mesh: MeshData, dataset: ResultDataset) -> object:
    return resolve_result_mesh_binding(
        _binding(mesh),
        active_mesh=mesh,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )


def test_typed_exact_point_displacement_is_eligible_but_name_only_is_not() -> None:
    mesh = _mesh()
    typed = _dataset()
    name_only = _dataset(_field(name="displacement"), semantic=False)

    eligible = evaluate_displacement_eligibility(
        mesh,
        typed,
        binding_resolution=_resolution(mesh, typed),
        field_name="u",
    )
    rejected = evaluate_displacement_eligibility(
        mesh,
        name_only,
        binding_resolution=_resolution(mesh, name_only),
        field_name="displacement",
    )

    assert eligible.eligible is True
    assert eligible.status is DeformationStatus.READY
    assert eligible.components == ("ux", "uy", "uz")
    assert eligible.unit == eligible.mesh_length_unit == "m"
    assert rejected.eligible is False
    assert rejected.status is DeformationStatus.INELIGIBLE
    assert "semantic" in rejected.diagnostics[0].lower()


@pytest.mark.parametrize(
    ("dataset", "reason"),
    (
        (_dataset(_field(location="cell")), "point"),
        (_dataset(_field(unit="mm"), mesh_unit="m"), "unit"),
        (_dataset(_field(nonfinite=True)), "nonfinite"),
        (
            _dataset(replace(_field(), components=("ux", "uy"))),
            "three",
        ),
    ),
)
def test_ineligible_shape_association_units_or_values_fail_closed(
    dataset: ResultDataset,
    reason: str,
) -> None:
    mesh = _mesh()

    eligibility = evaluate_displacement_eligibility(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name=dataset.fields[0].name,
    )

    assert eligibility.eligible is False
    assert eligibility.status is DeformationStatus.INELIGIBLE
    assert reason in eligibility.diagnostics[0].lower()


def test_auto_deformation_uses_documented_scene_relative_scale_without_mutation() -> None:
    mesh = _mesh()
    dataset = _dataset()
    mesh_before = deepcopy(mesh)
    dataset_before = deepcopy(dataset.to_dict())

    spec = build_deformed_shape_spec(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="u",
        mode=DeformationMode.DEFORMED,
        scale_mode=DeformationScaleMode.AUTO,
    )

    assert spec.applied is True
    assert spec.mode is DeformationMode.DEFORMED
    assert spec.maximum_displacement == pytest.approx(0.3)
    assert spec.bounds_diagonal == pytest.approx(sqrt(3.0))
    assert spec.scale == pytest.approx(0.1 * sqrt(3.0) / 0.3)
    assert spec.mesh_data is not None
    assert spec.mesh_data.points[1] == pytest.approx((1.0 + 0.1 * spec.scale, 0.0, 0.0))
    assert spec.mesh_data.points[2] == pytest.approx((0.0, 1.0 + 0.2 * spec.scale, 0.0))
    assert spec.mesh_data.cells == mesh.cells
    assert spec.mesh_data.point_data == mesh.point_data
    assert spec.mesh_data.cell_data == mesh.cell_data
    assert spec.canonical_point_ids == (0, 1, 2, 3)
    assert spec.canonical_cell_ids == ("0:0",)
    assert mesh == mesh_before
    assert dataset.to_dict() == dataset_before


def test_original_deformed_overlay_and_manual_zero_are_explicit() -> None:
    mesh = _mesh()
    dataset = _dataset()
    resolution = _resolution(mesh, dataset)

    original = build_deformed_shape_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="u",
        mode="ORIGINAL",
        scale_mode="MANUAL",
        manual_scale=1.0,
    )
    deformed_zero = build_deformed_shape_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="u",
        mode="DEFORMED",
        scale_mode="MANUAL",
        manual_scale=0.0,
    )
    overlay = build_deformed_shape_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="u",
        mode="OVERLAY",
        scale_mode="MANUAL",
        manual_scale=2.0,
    )
    invalid = build_deformed_shape_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="u",
        mode="DEFORMED",
        scale_mode="MANUAL",
        manual_scale=-1.0,
    )

    assert original.applied is True and original.mesh_data is None
    assert deformed_zero.mesh_data is not None
    assert deformed_zero.mesh_data.points == mesh.points
    assert overlay.applied is True and overlay.mesh_data is not None
    assert invalid.applied is False
    assert "nonnegative" in invalid.diagnostics[0].lower()


def test_different_mesh_fingerprint_is_stale_and_never_rebinds_displacements() -> None:
    mesh = _mesh()
    moved = _mesh(moved=True)
    dataset = _dataset()
    stale = resolve_result_mesh_binding(
        _binding(mesh),
        active_mesh=moved,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )

    spec = build_deformed_shape_spec(
        moved,
        dataset,
        binding_resolution=stale,
        field_name="u",
        mode="DEFORMED",
    )

    assert spec.applied is False
    assert spec.status is DeformationStatus.STALE
    assert spec.mesh_data is None
    assert "fingerprint" in spec.diagnostics[0].lower()
