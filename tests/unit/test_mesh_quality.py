from __future__ import annotations

from math import sqrt

from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.mesh.quality import analyze_mesh_quality


def test_good_mesh_quality_summary_computes_counts_bounds_edges_and_serializes() -> None:
    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("line", ((0, 1),)),
        ),
    )

    metrics = analyze_mesh_quality(mesh)

    assert metrics.node_count == 3
    assert metrics.element_count == 2
    assert metrics.cell_type_distribution == {"triangle": 1, "line": 1}
    assert metrics.bounding_box.minimum == (0.0, 0.0, 0.0)
    assert metrics.bounding_box.maximum == (1.0, 1.0, 0.0)
    assert metrics.min_edge_length == 1.0
    assert metrics.max_edge_length == sqrt(2.0)
    assert metrics.max_aspect_ratio == sqrt(2.0)
    assert metrics.has_warnings is False

    payload = metrics.to_dict()

    assert payload["node_count"] == 3
    assert payload["element_count"] == 2
    assert payload["cell_type_distribution"] == {"triangle": 1, "line": 1}
    assert payload["min_edge_length"] == 1.0
    assert payload["warnings"] == []


def test_bad_synthetic_mesh_triggers_aspect_ratio_warning() -> None:
    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (0.01, 0.0, 0.0), (10.0, 0.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )

    metrics = analyze_mesh_quality(mesh, bad_aspect_ratio_threshold=20.0)

    assert metrics.has_warnings is True
    assert metrics.max_aspect_ratio == 1000.0
    assert any(warning.code == "high_aspect_ratio" for warning in metrics.warnings)
    assert any("exceeds threshold" in warning.message for warning in metrics.warnings)


def test_degenerate_mesh_triggers_zero_edge_warning() -> None:
    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )

    metrics = analyze_mesh_quality(mesh)

    assert metrics.min_edge_length == 0.0
    assert any(warning.code == "degenerate_edge" for warning in metrics.warnings)


def test_invalid_connectivity_is_reported_without_crashing() -> None:
    mesh = MeshData(
        points=((0.0, 0.0, 0.0),),
        cells=(MeshCellBlock("line", ((0, 2),)),),
    )

    metrics = analyze_mesh_quality(mesh)

    assert metrics.element_count == 1
    assert metrics.min_edge_length is None
    assert any(warning.code == "invalid_connectivity" for warning in metrics.warnings)


def test_empty_mesh_quality_is_report_friendly() -> None:
    metrics = analyze_mesh_quality(MeshData(points=(), cells=()))

    assert metrics.node_count == 0
    assert metrics.element_count == 0
    assert metrics.min_edge_length is None
    assert metrics.max_edge_length is None
    assert metrics.max_aspect_ratio is None
    assert metrics.to_dict()["bounding_box"]["minimum"] == [0.0, 0.0, 0.0]
    assert any("nodes=0" in line for line in metrics.report_lines())
