"""Scalar-component, magnitude, range, and vector-glyph result contracts."""

from __future__ import annotations

from copy import deepcopy
from math import isnan, sqrt

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.core.result_mesh_binding import (
    RESULT_MESH_BINDING_SCHEMA_V2,
    ResultMeshBinding,
    resolve_result_mesh_binding,
)
from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.result_field_mapping import (
    ScalarComponentMode,
    ScalarRangeMode,
    VectorScaleMode,
    build_result_vector_glyph_spec,
    project_interactive_scalar_result,
)


def _mesh() -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (0.0, 2.0, 0.0),
            (0.0, 0.0, 2.0),
            (2.0, 2.0, 2.0),
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
                name="temperature",
                location="point",
                components=("value",),
                rows=_rows(
                    ((1.0,), (2.0,), (float("nan"),), (4.0,), (5.0,)),
                    ("value",),
                ),
                unit="K",
            ),
            ResultField(
                name="stress",
                location="cell",
                components=("value",),
                rows=_rows(((10.0,), (20.0,)), ("value",)),
                unit="Pa",
            ),
            ResultField(
                name="velocity",
                location="point",
                components=("vx", "vy", "vz"),
                rows=_rows(
                    (
                        (3.0, 4.0, 0.0),
                        (0.0, 0.0, 0.0),
                        (float("nan"), 1.0, 0.0),
                        (0.0, 0.0, 2.0),
                        (6.0, 8.0, 0.0),
                    ),
                    ("vx", "vy", "vz"),
                ),
                unit="m/s",
            ),
            ResultField(
                name="cell_flux",
                location="cell",
                components=("x", "y", "z"),
                rows=_rows(((1.0, 0.0, 0.0), (0.0, 2.0, 0.0)), ("x", "y", "z")),
                unit="W/m^2",
            ),
        ),
    )


def _resolution(mesh: MeshData, dataset: ResultDataset) -> object:
    fingerprint = compute_mesh_fingerprint(mesh)
    binding = ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref="mesh-1",
        result_dataset_id=dataset.dataset_id,
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=fingerprint.digest,
    )
    return resolve_result_mesh_binding(
        binding,
        active_mesh=mesh,
        active_mesh_ref="mesh-1",
        result_dataset=dataset,
    )


def test_scalar_contour_preserves_nonfinite_values_and_uses_finite_statistics() -> None:
    mesh = _mesh()
    dataset = _dataset()
    before = deepcopy(dataset.to_dict())

    result = project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="temperature",
        component="scalar",
        range_mode=ScalarRangeMode.AUTO,
    )

    assert result.applied is True
    assert result.scalar_mode is ScalarComponentMode.SCALAR
    assert result.source_components == ("value",)
    assert result.association == "point"
    assert isnan(result.values[2])
    assert result.data_range == (1.0, 5.0)
    assert result.statistics.finite_count == 4
    assert result.statistics.nonfinite_count == 1
    assert result.statistics.mean == pytest.approx(3.0)
    assert result.statistics.median == pytest.approx(3.0)
    assert result.diagnostics == (
        "Result scalar view excludes 1 nonfinite tuple from its range and statistics.",
    )
    assert dataset.to_dict() == before
    assert mesh.point_data == {}


@pytest.mark.parametrize(
    ("mode", "expected", "source"),
    (
        ("x", (3.0, 0.0, float("nan"), 0.0, 6.0), ("vx",)),
        ("y", (4.0, 0.0, 1.0, 0.0, 8.0), ("vy",)),
        ("z", (0.0, 0.0, 0.0, 2.0, 0.0), ("vz",)),
        ("magnitude", (5.0, 0.0, float("nan"), 2.0, 10.0), ("vx", "vy", "vz")),
    ),
)
def test_vector_components_and_derived_magnitude_are_explicit(
    mode: str,
    expected: tuple[float, ...],
    source: tuple[str, ...],
) -> None:
    mesh = _mesh()
    dataset = _dataset()

    result = project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="velocity",
        component=mode,
        colormap="coolwarm",
    )

    assert result.applied is True
    assert result.scalar_mode.value == mode
    assert result.source_components == source
    assert result.derived is (mode == "magnitude")
    assert result.unit == "m/s"
    derived_label = " (derived)" if mode == "magnitude" else ""
    assert result.colorbar_title == f"velocity / {mode}{derived_label} [m/s]"
    for actual, wanted in zip(result.values, expected, strict=True):
        assert isnan(actual) if isnan(wanted) else actual == wanted


def test_cell_scalar_keeps_canonical_block_then_local_order() -> None:
    mesh = _mesh()
    dataset = _dataset()

    result = project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="stress",
        component="scalar",
        range_mode="MANUAL",
        manual_range=(0.0, 25.0),
        colormap="gray",
        colorbar_visible=False,
    )

    assert result.applied is True
    assert result.association == "cell"
    assert result.values == (10.0, 20.0)
    assert result.display_range == (0.0, 25.0)
    assert result.colorbar_visible is False


def test_all_nonfinite_scalar_fails_without_a_fake_range() -> None:
    mesh = _mesh()
    field = ResultField(
        name="invalid",
        location="point",
        components=("value",),
        rows=_rows(((float("nan"),),) * 5, ("value",)),
    )
    dataset = ResultDataset("result-1", "fixture", "fixture", "static", (field,))

    result = project_interactive_scalar_result(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="invalid",
        component="scalar",
    )

    assert result.applied is False
    assert result.data_range is None
    assert result.display_range is None
    assert "finite" in result.diagnostics[0].lower()


def test_point_vector_glyphs_exclude_nonfinite_and_zero_tuples_deterministically() -> None:
    mesh = _mesh()
    dataset = _dataset()
    before = deepcopy(dataset.to_dict())

    spec = build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="velocity",
        maximum_glyph_count=1,
        scale_mode=VectorScaleMode.MANUAL,
        scale=2.0,
    )

    assert spec.applied is True
    assert spec.total_tuple_count == 5
    assert spec.nonfinite_vector_count == 1
    assert spec.zero_vector_count == 1
    assert spec.candidate_count == 3
    assert spec.sampled_count == 1
    assert spec.selected_candidate_ranks == (1,)
    assert spec.stable_entity_keys == (3,)
    assert spec.positions == ((0.0, 0.0, 2.0),)
    assert spec.vectors == ((0.0, 0.0, 2.0),)
    assert spec.magnitudes == (2.0,)
    assert spec.scale == 2.0
    assert dataset.to_dict() == before


def test_cell_vector_origins_and_auto_scale_are_scene_relative() -> None:
    mesh = _mesh()
    dataset = _dataset()

    spec = build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="cell_flux",
        maximum_glyph_count=10,
        scale_mode="AUTO",
    )

    assert spec.applied is True
    assert spec.association == "cell"
    assert spec.stable_entity_keys == ("0:0", "1:0")
    assert spec.positions == (
        (2.0 / 3.0, 2.0 / 3.0, 0.0),
        (1.0, 1.0, 1.0),
    )
    assert spec.reference_magnitude == 2.0
    assert spec.bounds_diagonal == pytest.approx(sqrt(12.0))
    assert spec.scale == pytest.approx(0.1 * sqrt(12.0) / 2.0)


def test_cell_vector_rejects_missing_connectivity_instead_of_fabricating_origins() -> None:
    mesh = MeshData(
        points=((0.0, 0.0, 0.0),),
        cells=(MeshCellBlock("polygon", ((),)),),
    )
    dataset = ResultDataset(
        dataset_id="result-1",
        source="fixture",
        solver="fixture",
        analysis_type="steady",
        fields=(
            ResultField(
                "cell_flux",
                "cell",
                ("x", "y", "z"),
                _rows(((1.0, 0.0, 0.0),), ("x", "y", "z")),
                "W/m^2",
            ),
        ),
    )

    spec = build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=_resolution(mesh, dataset),
        field_name="cell_flux",
        scale_mode="AUTO",
    )

    assert spec.applied is False
    assert "connectivity" in spec.diagnostics[0].lower()


def test_vector_scale_validation_and_sampling_membership_are_independent() -> None:
    mesh = _mesh()
    dataset = _dataset()
    resolution = _resolution(mesh, dataset)
    automatic = build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="velocity",
        maximum_glyph_count=2,
        scale_mode="AUTO",
    )
    manual = build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="velocity",
        maximum_glyph_count=2,
        scale_mode="MANUAL",
        scale=7.5,
    )
    invalid = build_result_vector_glyph_spec(
        mesh,
        dataset,
        binding_resolution=resolution,
        field_name="velocity",
        maximum_glyph_count=2,
        scale_mode="MANUAL",
        scale=0.0,
    )

    assert automatic.stable_entity_keys == manual.stable_entity_keys == (0, 4)
    assert automatic.vectors == manual.vectors
    assert automatic.scale != manual.scale
    assert invalid.applied is False
    assert "positive" in invalid.diagnostics[0].lower()
