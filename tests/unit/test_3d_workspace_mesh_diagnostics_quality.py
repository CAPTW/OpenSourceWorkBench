"""Pure contracts for fingerprint-bound preview mesh diagnostics."""

from __future__ import annotations

import math
from importlib import import_module

import pytest

from osw.core.selection_resolution import CELL_ORDINAL_NAMESPACE
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _quality_api() -> object:
    api = import_module("osw.mesh.quality")
    if not hasattr(api, "analyze_mesh_cell_quality"):
        pytest.fail(
            "fingerprint-bound per-cell mesh-quality analysis is missing",
            pytrace=False,
        )
    return api


def _mesh(
    cell_type: str,
    points: tuple[tuple[float, float, float], ...],
    connectivity: tuple[int, ...],
) -> MeshData:
    return MeshData(
        points=points,
        cells=(MeshCellBlock(cell_type, (connectivity,)),),
    )


@pytest.mark.parametrize(
    ("cell_type", "points", "connectivity", "expected"),
    [
        (
            "line",
            ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
            (0, 1),
            1.0,
        ),
        (
            "triangle",
            ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            (0, 1, 2),
            math.sqrt(5.0),
        ),
        (
            "quad",
            (
                (0.0, 0.0, 0.0),
                (2.0, 0.0, 0.0),
                (2.0, 1.0, 0.0),
                (0.0, 1.0, 0.0),
            ),
            (0, 1, 2, 3),
            2.0,
        ),
        (
            "tetra",
            (
                (0.0, 0.0, 0.0),
                (2.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            (0, 1, 2, 3),
            math.sqrt(5.0),
        ),
        (
            "hexahedron",
            (
                (0.0, 0.0, 0.0),
                (2.0, 0.0, 0.0),
                (2.0, 1.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
                (2.0, 0.0, 1.0),
                (2.0, 1.0, 1.0),
                (0.0, 1.0, 1.0),
            ),
            (0, 1, 2, 3, 4, 5, 6, 7),
            2.0,
        ),
        (
            "wedge",
            (
                (0.0, 0.0, 0.0),
                (2.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
                (2.0, 0.0, 1.0),
                (0.0, 1.0, 1.0),
            ),
            (0, 1, 2, 3, 4, 5),
            math.sqrt(5.0),
        ),
        (
            "pyramid",
            (
                (0.0, 0.0, 0.0),
                (2.0, 0.0, 0.0),
                (2.0, 1.0, 0.0),
                (0.0, 1.0, 0.0),
                (1.0, 0.5, 1.0),
            ),
            (0, 1, 2, 3, 4),
            2.0,
        ),
    ],
)
def test_linear_topologies_use_explicit_edges(
    cell_type: str,
    points: tuple[tuple[float, float, float], ...],
    connectivity: tuple[int, ...],
    expected: float,
) -> None:
    api = _quality_api()

    analysis = api.analyze_mesh_cell_quality(
        _mesh(cell_type, points, connectivity)
    )

    assert analysis.metric_schema == "osw.mesh_quality.edge_aspect_ratio.v1"
    assert analysis.metric_label == "Edge aspect ratio preview"
    assert analysis.evaluated_count == 1
    assert analysis.unsupported_count == 0
    assert analysis.invalid_count == 0
    assert analysis.degenerate_count == 0
    assert analysis.records[0].status is api.MeshCellQualityStatus.EVALUATED
    assert analysis.records[0].value == pytest.approx(expected)
    assert analysis.records[0].entity_kind == "cell"
    assert analysis.records[0].id_namespace == CELL_ORDINAL_NAMESPACE
    assert analysis.records[0].stable_cell_key == "0:0"
    assert analysis.records[0].mesh_fingerprint == analysis.mesh_fingerprint.digest


@pytest.mark.parametrize(
    "cell_type",
    [
        "line3",
        "triangle6",
        "quad8",
        "quad9",
        "tetra10",
        "hexahedron20",
    ],
)
def test_high_order_topology_fails_closed_without_corner_guessing(
    cell_type: str,
) -> None:
    api = _quality_api()
    points = tuple((float(index), 0.0, 0.0) for index in range(20))

    analysis = api.analyze_mesh_cell_quality(
        _mesh(cell_type, points, tuple(range(3)))
    )

    record = analysis.records[0]
    assert record.status is api.MeshCellQualityStatus.UNSUPPORTED
    assert record.reason == "UNSUPPORTED_HIGH_ORDER_TOPOLOGY"
    assert record.value is None
    assert analysis.unsupported_count == 1


def test_unknown_and_malformed_linear_cells_are_not_treated_as_good() -> None:
    api = _quality_api()
    points = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    mesh = MeshData(
        points=points,
        cells=(
            MeshCellBlock("polygon", ((0, 1, 2),)),
            MeshCellBlock("triangle", ((0, 1),)),
            MeshCellBlock("line", ((0, 1, 2),)),
        ),
    )

    analysis = api.analyze_mesh_cell_quality(mesh)

    assert [record.stable_cell_key for record in analysis.records] == [
        "0:0",
        "1:0",
        "2:0",
    ]
    assert [record.status for record in analysis.records] == [
        api.MeshCellQualityStatus.UNSUPPORTED,
        api.MeshCellQualityStatus.INVALID,
        api.MeshCellQualityStatus.INVALID,
    ]
    assert [record.reason for record in analysis.records] == [
        "UNSUPPORTED_CELL_TYPE",
        "INSUFFICIENT_CONNECTIVITY",
        "INVALID_CONNECTIVITY",
    ]
    assert analysis.unsupported_count == 1
    assert analysis.invalid_count == 2


def test_degenerate_cells_are_explicit_and_thresholded_with_stable_keys() -> None:
    api = _quality_api()
    mesh = MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("triangle", ((0, 2, 3),)),
        ),
    )

    analysis = api.analyze_mesh_cell_quality(mesh)
    bad = api.derive_bad_cell_records(analysis, threshold=1.0)

    assert analysis.degenerate_count == 1
    assert analysis.records[0].reason == "ZERO_OR_NEAR_ZERO_EDGE"
    assert analysis.records[0].value is None
    assert tuple(record.stable_cell_key for record in bad) == ("0:0", "1:0")
    assert api.derive_bad_cell_records(analysis, threshold=math.sqrt(2.0)) == (
        analysis.records[0],
    )


@pytest.mark.parametrize("threshold", [0.0, -1.0, math.inf, -math.inf, math.nan])
def test_bad_threshold_requires_a_finite_positive_value(threshold: float) -> None:
    api = _quality_api()
    analysis = api.analyze_mesh_cell_quality(
        _mesh(
            "line",
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
            (0, 1),
        )
    )

    with pytest.raises(ValueError, match="finite and positive"):
        api.derive_bad_cell_records(analysis, threshold=threshold)


def test_exact_fingerprint_and_order_change_for_same_count_topology() -> None:
    api = _quality_api()
    baseline = _mesh(
        "triangle",
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        (0, 1, 2),
    )
    rewired = _mesh(
        "triangle",
        baseline.points,
        (0, 2, 1),
    )

    first = api.analyze_mesh_cell_quality(baseline)
    second = api.analyze_mesh_cell_quality(rewired)

    assert first.mesh_fingerprint.cell_count == second.mesh_fingerprint.cell_count
    assert first.mesh_fingerprint.point_count == second.mesh_fingerprint.point_count
    assert first.mesh_fingerprint.digest != second.mesh_fingerprint.digest
    assert first.records[0].stable_cell_key == second.records[0].stable_cell_key
    assert first.records[0].mesh_fingerprint != second.records[0].mesh_fingerprint


def test_nonfinite_geometry_and_out_of_range_connectivity_fail_closed() -> None:
    api = _quality_api()

    with pytest.raises(api.MeshQualityAnalysisError, match="exact mesh fingerprint"):
        api.analyze_mesh_cell_quality(
            _mesh(
                "line",
                ((math.nan, 0.0, 0.0), (1.0, 0.0, 0.0)),
                (0, 1),
            )
        )
    with pytest.raises(api.MeshQualityAnalysisError, match="exact mesh fingerprint"):
        api.analyze_mesh_cell_quality(
            _mesh(
                "line",
                ((0.0, 0.0, 0.0),),
                (0, 2),
            )
        )


def test_legacy_aggregate_contract_remains_block_local_and_unchanged() -> None:
    api = _quality_api()
    mesh = MeshData(
        points=((0.0, 0.0, 0.0),),
        cells=(
            MeshCellBlock("line", ((0, 2),)),
            MeshCellBlock("line", ((0, 3),)),
        ),
    )

    metrics = api.analyze_mesh_quality(mesh)

    assert [warning.element_index for warning in metrics.warnings] == [0, 0]
    assert [warning.code for warning in metrics.warnings] == [
        "invalid_connectivity",
        "invalid_connectivity",
    ]
    assert metrics.to_dict()["warnings"][0]["element_index"] == 0
    assert metrics.report_lines()[0:2] == ("nodes=1", "elements=2")
