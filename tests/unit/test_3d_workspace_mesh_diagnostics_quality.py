"""Focused Scaled Jacobian topology, classification, and failure contracts."""

from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData


class Provider:
    provider_schema = "osw.mesh_quality.provider.unit-fixture.v1"
    provider_version = "1"

    def __init__(self, values: tuple[float, ...]) -> None:
        self.values = values
        self.meshes: list[MeshData] = []

    def evaluate(self, mesh: MeshData) -> tuple[float, ...]:
        self.meshes.append(mesh)
        return self.values


def _mesh(
    cell_type: str,
    points: tuple[tuple[float, float, float], ...],
    connectivity: tuple[int, ...],
) -> MeshData:
    return MeshData(points=points, cells=(MeshCellBlock(cell_type, (connectivity,)),))


@pytest.mark.parametrize(
    ("cell_type", "points", "connectivity"),
    [
        (
            "triangle",
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            (0, 1, 2),
        ),
        (
            "quad",
            (
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (1.0, 1.0, 0.0),
                (0.0, 1.0, 0.0),
            ),
            (0, 1, 2, 3),
        ),
        (
            "tetra",
            (
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            (0, 1, 2, 3),
        ),
    ],
)
def test_v1_coverage_is_exactly_triangle_quad_and_linear_tetra(
    cell_type: str,
    points: tuple[tuple[float, float, float], ...],
    connectivity: tuple[int, ...],
) -> None:
    from osw.mesh.quality import (
        MESH_QUALITY_METRIC_SCHEMA,
        MeshCellQualityStatus,
        analyze_mesh_cell_quality,
    )

    provider = Provider((0.75,))
    analysis = analyze_mesh_cell_quality(
        _mesh(cell_type, points, connectivity),
        provider=provider,
    )

    assert analysis.metric_schema == MESH_QUALITY_METRIC_SCHEMA
    assert analysis.metric_schema == "osw.mesh_quality.scaled_jacobian.v1"
    assert analysis.records[0].status is MeshCellQualityStatus.EVALUATED
    assert analysis.records[0].value == 0.75
    assert provider.meshes[0].cells[0].cell_type == cell_type


@pytest.mark.parametrize(
    "cell_type,node_count",
    [
        ("polygon", 4),
        ("tetra10", 10),
        ("hexahedron", 8),
        ("hexahedron20", 20),
        ("wedge", 6),
        ("pyramid", 5),
        ("unknown", 3),
    ],
)
def test_out_of_scope_topologies_are_named_uncovered_before_provider(
    cell_type: str,
    node_count: int,
) -> None:
    from osw.mesh.quality import (
        MeshCellQualityStatus,
        MeshQualityCategory,
        analyze_mesh_cell_quality,
    )

    points = tuple((float(index), float(index % 2), 0.0) for index in range(node_count))
    provider = Provider(())
    result = analyze_mesh_cell_quality(
        _mesh(cell_type, points, tuple(range(node_count))),
        provider=provider,
    )

    assert provider.meshes == []
    assert result.records[0].status is MeshCellQualityStatus.UNCOVERED
    assert result.records[0].category is MeshQualityCategory.UNCOVERED
    assert "NOT_COVERED" in result.records[0].reason
    assert result.topology_summaries[0].cell_type == cell_type


def test_invalid_supported_arity_and_provider_nan_fail_closed() -> None:
    from osw.mesh.quality import (
        MeshCellQualityStatus,
        MeshQualityCategory,
        analyze_mesh_cell_quality,
    )

    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1), (0, 1, 2))),),
    )
    provider = Provider((math.nan,))
    result = analyze_mesh_cell_quality(mesh, provider=provider)

    assert provider.meshes[0].cells == (MeshCellBlock("triangle", ((0, 1, 2),)),)
    assert tuple(record.status for record in result.records) == (
        MeshCellQualityStatus.INVALID,
        MeshCellQualityStatus.INVALID,
    )
    assert all(record.category is MeshQualityCategory.INVALID for record in result.records)
    assert result.bad_cell_keys == ("0:0", "0:1")


def test_classification_priority_is_inverted_degenerate_threshold_then_acceptable() -> None:
    from osw.mesh.quality import MeshQualityCategory, analyze_mesh_cell_quality

    mesh = MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        cells=(
            MeshCellBlock(
                "tetra",
                ((0, 1, 2, 3), (0, 1, 2, 3), (0, 1, 2, 3), (0, 1, 2, 3)),
            ),
        ),
    )
    result = analyze_mesh_cell_quality(
        mesh,
        threshold=0.2,
        provider=Provider((-0.5, 0.0, 0.1, 0.9)),
    )
    assert tuple(record.category for record in result.records) == (
        MeshQualityCategory.INVERTED,
        MeshQualityCategory.DEGENERATE,
        MeshQualityCategory.THRESHOLD_BAD,
        MeshQualityCategory.ACCEPTABLE,
    )
    assert result.bad_cell_keys == ("0:0", "0:1", "0:2")


def test_bad_membership_obeys_threshold_even_for_inverted_and_degenerate_categories() -> None:
    from osw.mesh.quality import analyze_mesh_cell_quality, reclassify_mesh_quality

    mesh = MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),) * 3),),
    )
    analysis = analyze_mesh_cell_quality(
        mesh,
        threshold=-1.0,
        provider=Provider((-0.5, 0.0, 0.5)),
    )

    assert analysis.bad_cell_keys == ()
    changed = reclassify_mesh_quality(analysis, threshold=0.0)
    assert changed.bad_cell_keys == ("0:0", "0:1")


@pytest.mark.parametrize(
    "threshold",
    [math.inf, -math.inf, math.nan, -1.0000001, 1.0000001],
)
def test_threshold_requires_a_finite_value_within_metric_range(threshold: float) -> None:
    from osw.mesh.quality import analyze_mesh_cell_quality

    with pytest.raises(ValueError, match=r"finite and within \[-1, 1\]"):
        analyze_mesh_cell_quality(
            _mesh(
                "triangle",
                ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
                (0, 1, 2),
            ),
            threshold=threshold,
            provider=Provider((1.0,)),
        )


def test_result_records_are_frozen_and_connectivity_order_changes_fingerprint() -> None:
    from osw.mesh.quality import analyze_mesh_cell_quality

    points = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    first = analyze_mesh_cell_quality(
        _mesh("tetra", points, (0, 1, 2, 3)),
        provider=Provider((1.0,)),
    )
    second = analyze_mesh_cell_quality(
        _mesh("tetra", points, (0, 2, 1, 3)),
        provider=Provider((-1.0,)),
    )
    assert first.mesh_fingerprint.digest != second.mesh_fingerprint.digest
    with pytest.raises(FrozenInstanceError):
        first.records[0].value = 2.0  # type: ignore[misc]


def test_identity_failure_precedes_provider_and_legacy_aggregate_remains_available() -> None:
    from osw.mesh.quality import (
        MeshQualityAnalysisError,
        analyze_mesh_cell_quality,
        analyze_mesh_quality,
    )

    invalid = MeshData(
        points=((0.0, 0.0, 0.0),),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )
    provider = Provider((1.0,))
    with pytest.raises(MeshQualityAnalysisError, match="exact mesh fingerprint"):
        analyze_mesh_cell_quality(invalid, provider=provider)
    assert provider.meshes == []

    legacy = analyze_mesh_quality(
        MeshData(
            points=((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        )
    )
    assert legacy.node_count == 3
    assert legacy.element_count == 1
    assert legacy.max_aspect_ratio == pytest.approx(math.sqrt(5.0))
