"""Product contracts for deterministic Scaled Jacobian mesh diagnostics."""

from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData


class RecordingScaledJacobianProvider:
    provider_schema = "osw.mesh_quality.provider.fixture.v1"
    provider_version = "fixture-1"

    def __init__(self, values: tuple[float, ...]) -> None:
        self.values = values
        self.calls: list[MeshData] = []

    def evaluate(self, mesh: MeshData) -> tuple[float, ...]:
        self.calls.append(mesh)
        return self.values


def _mixed_mesh() -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (1.0, 1.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 1.0, 0.0),
            (9.0, 9.0, 9.0),  # deterministic orphan point
        ),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("polygon", ((0, 1, 4, 2),)),
            MeshCellBlock("quad", ((1, 5, 6, 4),)),
            MeshCellBlock(
                "tetra",
                (
                    (0, 1, 2, 3),
                    (0, 2, 1, 3),
                    (0, 1, 2, 4),
                ),
            ),
        ),
        point_data={"temperature": tuple(float(index) for index in range(8))},
    )


def test_mesh_summary_is_deterministic_and_reports_coverage_orphans_and_bounds() -> None:
    from osw.mesh.diagnostics import MESH_DIAGNOSTICS_SCHEMA, build_mesh_summary

    mesh = _mixed_mesh()
    first = build_mesh_summary(mesh)
    second = build_mesh_summary(mesh)

    assert first == second
    assert first.schema == MESH_DIAGNOSTICS_SCHEMA == "osw.mesh_diagnostics.v1"
    assert first.point_count == 8
    assert first.cell_count == 6
    assert first.block_count == 4
    assert first.cell_type_distribution == (
        ("polygon", 1),
        ("quad", 1),
        ("tetra", 3),
        ("triangle", 1),
    )
    assert first.surface_cell_count == 3
    assert first.volume_cell_count == 3
    assert first.quality_supported_count == 5
    assert first.quality_uncovered_count == 1
    assert first.invalid_cell_count == 0
    assert first.referenced_point_count == 7
    assert first.orphan_point_count == 1
    assert first.bounds.minimum == (0.0, 0.0, 0.0)
    assert first.bounds.maximum == (9.0, 9.0, 9.0)
    assert first.extents == (9.0, 9.0, 9.0)
    assert first.diagonal == pytest.approx(15.588457268119896)
    assert first.finite_point_count == 8
    assert first.nonfinite_point_count == 0
    assert first.supported_quality_types == ("quad", "tetra", "triangle")
    assert first.uncovered_quality_types == ("polygon",)
    assert len(first.mesh_fingerprint.digest) == 64


def test_scaled_jacobian_result_maps_provider_values_to_canonical_cells() -> None:
    from osw.mesh.quality import (
        MESH_QUALITY_METRIC_LABEL,
        MESH_QUALITY_METRIC_SCHEMA,
        MeshCellQualityStatus,
        MeshDiagnosticsStatus,
        MeshQualityCategory,
        analyze_mesh_cell_quality,
    )

    provider = RecordingScaledJacobianProvider((1.0, 0.25, 0.7, -1.0, 0.0))
    mesh = _mixed_mesh()
    before = (mesh.points, mesh.cells, dict(mesh.point_data), dict(mesh.cell_data))
    result = analyze_mesh_cell_quality(mesh, threshold=0.3, provider=provider)

    assert MESH_QUALITY_METRIC_SCHEMA == "osw.mesh_quality.scaled_jacobian.v1"
    assert MESH_QUALITY_METRIC_LABEL == "Scaled Jacobian"
    assert result.status is MeshDiagnosticsStatus.PARTIAL_COVERAGE
    assert result.metric_schema == MESH_QUALITY_METRIC_SCHEMA
    assert result.metric_direction == "higher_is_better"
    assert "negative values indicate inverted orientation" in result.metric_semantics
    assert result.provider_schema == provider.provider_schema
    assert result.provider_version == provider.provider_version
    assert result.threshold == 0.3
    assert result.covered_count == 5
    assert result.uncovered_count == 1
    assert result.invalid_count == 0
    assert result.bad_count == 3
    assert result.statistics.count == 5
    assert result.statistics.minimum == -1.0
    assert result.statistics.maximum == 1.0
    assert result.statistics.mean == pytest.approx(0.19)
    assert result.statistics.median == 0.25
    assert result.statistics.population_stddev == pytest.approx(0.6887670143089025)
    assert result.statistics.p05 == pytest.approx(-0.8)
    assert result.statistics.p25 == pytest.approx(0.0)
    assert result.statistics.p75 == pytest.approx(0.7)
    assert result.statistics.p95 == pytest.approx(0.94)
    assert result.statistics.percentile_method == "linear"
    assert result.display_range == (-1.0, 1.0)
    assert len(result.digest) == 64
    assert before == (mesh.points, mesh.cells, mesh.point_data, mesh.cell_data)

    assert [record.stable_cell_key for record in result.records] == [
        "0:0",
        "1:0",
        "2:0",
        "3:0",
        "3:1",
        "3:2",
    ]
    assert [record.backend_index for record in result.records] == list(range(6))
    assert result.records[1].status is MeshCellQualityStatus.UNCOVERED
    assert result.records[1].value is None
    assert result.records[1].category is MeshQualityCategory.UNCOVERED
    assert result.records[2].category is MeshQualityCategory.THRESHOLD_BAD
    assert result.records[4].category is MeshQualityCategory.INVERTED
    assert result.records[5].category is MeshQualityCategory.DEGENERATE
    assert provider.calls[0].cells == (
        MeshCellBlock("triangle", ((0, 1, 2),)),
        MeshCellBlock("quad", ((1, 5, 6, 4),)),
        MeshCellBlock(
            "tetra",
            ((0, 1, 2, 3), (0, 2, 1, 3), (0, 1, 2, 4)),
        ),
    )


def test_uncovered_is_classified_before_provider_sentinel_and_reclassify_is_geometry_free() -> None:
    from osw.mesh.quality import (
        MeshQualityCategory,
        analyze_mesh_cell_quality,
        reclassify_mesh_quality,
    )

    provider = RecordingScaledJacobianProvider((1.0, 0.25, 0.7, -1.0, 0.0))
    analysis = analyze_mesh_cell_quality(_mixed_mesh(), threshold=0.3, provider=provider)
    changed = reclassify_mesh_quality(analysis, threshold=0.0)

    assert len(provider.calls) == 1
    assert analysis.records[1].value is None
    assert changed.records[1].category is MeshQualityCategory.UNCOVERED
    assert changed.records[2].category is MeshQualityCategory.ACCEPTABLE
    assert changed.bad_cell_keys == ("3:1", "3:2")
    assert analysis.digest != changed.digest
    assert reclassify_mesh_quality(changed, threshold=0.0) is changed


def test_invalid_connectivity_is_not_sent_to_provider_and_is_bad_not_uncovered() -> None:
    from osw.mesh.quality import MeshQualityCategory, analyze_mesh_cell_quality

    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2), (0, 1))),
            MeshCellBlock("polygon", ((0, 1, 2),)),
        ),
    )
    provider = RecordingScaledJacobianProvider((0.8,))
    result = analyze_mesh_cell_quality(mesh, provider=provider)

    assert provider.calls[0].cells == (MeshCellBlock("triangle", ((0, 1, 2),)),)
    assert result.invalid_count == 1
    assert result.uncovered_count == 1
    assert result.bad_count == 1
    assert result.records[1].category is MeshQualityCategory.INVALID
    assert result.records[2].category is MeshQualityCategory.UNCOVERED


def test_manual_range_constant_auto_range_statistics_and_validation() -> None:
    from osw.mesh.quality import (
        analyze_mesh_cell_quality,
        reclassify_mesh_quality,
    )

    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2), (0, 2, 1))),),
    )
    result = analyze_mesh_cell_quality(
        mesh,
        provider=RecordingScaledJacobianProvider((0.5, 0.5)),
    )
    assert result.display_range[0] < 0.5 < result.display_range[1]
    assert result.statistics.population_stddev == 0.0
    assert result.statistics.p05 == result.statistics.p95 == 0.5

    range_only = reclassify_mesh_quality(
        result,
        threshold=0.0,
        range_mode="manual",
        manual_range=(-0.25, 0.75),
    )
    assert range_only.digest == result.digest

    manual = reclassify_mesh_quality(
        result,
        threshold=0.1,
        range_mode="manual",
        manual_range=(-0.25, 0.75),
    )
    assert manual.range_mode == "manual"
    assert manual.display_range == (-0.25, 0.75)
    with pytest.raises(ValueError, match="minimum must be less"):
        reclassify_mesh_quality(result, threshold=0.0, manual_range=(1.0, 1.0))
    with pytest.raises(ValueError, match="finite"):
        reclassify_mesh_quality(result, threshold=float("nan"))


def test_report_summary_json_and_csv_are_stable_and_actor_free() -> None:
    from osw.mesh.diagnostics_export import (
        MESH_DIAGNOSTICS_REPORT_SCHEMA,
        build_mesh_diagnostics_report_summary,
        render_mesh_diagnostics_csv,
        render_mesh_diagnostics_json,
    )
    from osw.mesh.quality import MeshDiagnosticsStatus, analyze_mesh_cell_quality

    analysis = analyze_mesh_cell_quality(
        _mixed_mesh(),
        threshold=0.3,
        provider=RecordingScaledJacobianProvider((1.0, 0.25, 0.7, -1.0, 0.0)),
    )
    summary = build_mesh_diagnostics_report_summary(analysis)
    first_json = render_mesh_diagnostics_json(summary)
    second_json = render_mesh_diagnostics_json(summary)
    csv_text = render_mesh_diagnostics_csv(summary)

    assert summary.schema == MESH_DIAGNOSTICS_REPORT_SCHEMA
    assert first_json == second_json
    assert first_json.endswith("\n") and "\r" not in first_json
    assert csv_text.endswith("\n") and "\r" not in csv_text
    decoded = json.loads(first_json)
    assert decoded["schema"] == "osw.mesh_diagnostics_report.v1"
    assert decoded["claim"] == (
        "Mesh diagnostics are advisory and do not certify solver suitability."
    )
    assert decoded["quality"]["metric_schema"] == "osw.mesh_quality.scaled_jacobian.v1"
    assert decoded["quality"]["coverage_ratio"] == pytest.approx(5 / 6)
    assert decoded["quality"]["inverted_count"] == 1
    assert decoded["quality"]["degenerate_count"] == 1
    assert csv_text.splitlines()[0].split(",")[:10] == [
        "canonical_cell_id",
        "mesh_fingerprint",
        "block_index",
        "local_cell_index",
        "global_cell_index",
        "cell_type",
        "metric_id",
        "quality_status",
        "quality_value",
        "threshold_classification",
    ]
    assert "0:0" in csv_text
    stale_csv = render_mesh_diagnostics_csv(
        build_mesh_diagnostics_report_summary(replace(analysis, status=MeshDiagnosticsStatus.STALE))
    )
    stale_rows = [line.split(",") for line in stale_csv.splitlines()]
    analysis_status_index = stale_rows[0].index("analysis_status")
    assert all(row[analysis_status_index] == "stale" for row in stale_rows[1:])
    assert "actor" not in first_json.casefold()
    assert "object at 0x" not in first_json.casefold()
    assert replace(summary) == summary


@pytest.mark.optional_dependency
def test_retained_pyvista_provider_distinguishes_well_shaped_and_distorted_surfaces() -> None:
    pytest.importorskip("pyvista")
    from osw.mesh.quality import analyze_mesh_cell_quality

    mesh = MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.5, math.sqrt(3.0) / 2.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (2.001, 0.01, 0.0),
            (0.0, 2.0, 0.0),
            (1.0, 2.0, 0.0),
            (1.0, 3.0, 0.0),
            (0.0, 3.0, 0.0),
            (2.0, 2.0, 0.0),
            (3.0, 2.0, 0.0),
            (2.2, 2.1, 0.0),
            (2.0, 3.0, 0.0),
        ),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2), (3, 4, 5))),
            MeshCellBlock("quad", ((6, 7, 8, 9), (10, 11, 12, 13))),
        ),
    )
    before = (mesh.points, mesh.cells, dict(mesh.point_data), dict(mesh.cell_data))
    analysis = analyze_mesh_cell_quality(mesh)

    assert tuple(record.value for record in analysis.records) == pytest.approx(
        (1.0, 0.011557984905465167, 1.0, -0.9417419115948372),
        abs=1.0e-12,
    )
    assert analysis.records[0].value > analysis.records[1].value
    assert analysis.records[2].value > analysis.records[3].value
    assert before == (mesh.points, mesh.cells, mesh.point_data, mesh.cell_data)


@pytest.mark.optional_dependency
def test_retained_pyvista_provider_evaluates_regular_inverted_and_degenerate_tetra() -> None:
    pytest.importorskip("pyvista")
    from osw.mesh.quality import MeshQualityCategory, analyze_mesh_cell_quality

    height = math.sqrt(2.0 / 3.0)
    mesh = MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.5, math.sqrt(3.0) / 2.0, 0.0),
            (0.5, math.sqrt(3.0) / 6.0, height),
            (0.5, 0.25, 0.0),
        ),
        cells=(
            MeshCellBlock(
                "tetra",
                ((0, 1, 2, 3), (0, 2, 1, 3), (0, 1, 2, 4)),
            ),
        ),
    )
    analysis = analyze_mesh_cell_quality(mesh)

    assert tuple(record.value for record in analysis.records) == pytest.approx(
        (1.0, -1.0, 0.0),
        abs=1.0e-12,
    )
    assert tuple(record.category for record in analysis.records) == (
        MeshQualityCategory.ACCEPTABLE,
        MeshQualityCategory.INVERTED,
        MeshQualityCategory.DEGENERATE,
    )
    assert analysis.provider_schema == "osw.mesh_quality.provider.pyvista_vtk.v1"
    assert "pyvista-" in analysis.provider_version


def test_optional_provider_absence_is_an_explicit_result_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from osw.mesh import quality_pyvista
    from osw.mesh.quality import (
        MeshDiagnosticsStatus,
        MeshQualityProviderUnavailableError,
        analyze_mesh_cell_quality,
    )

    def missing(name: str) -> object:
        if name == "pyvista":
            raise ModuleNotFoundError(name)
        raise AssertionError(name)

    monkeypatch.setattr(quality_pyvista, "import_module", missing)
    result = analyze_mesh_cell_quality(
        MeshData(
            points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        ),
        provider=quality_pyvista.PyVistaScaledJacobianProvider(),
    )

    assert result.status is MeshDiagnosticsStatus.UNAVAILABLE_OPTIONAL_DEPENDENCY
    assert result.unavailable_count == 1
    assert "optional PyVista/VTK" in result.diagnostics[0]
    with pytest.raises(MeshQualityProviderUnavailableError):
        quality_pyvista.PyVistaScaledJacobianProvider().evaluate(_mixed_mesh())


def test_uncovered_only_summary_does_not_import_the_optional_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from osw.mesh import quality

    def unexpected_provider() -> object:
        raise AssertionError("provider must stay lazy")

    monkeypatch.setattr(
        quality,
        "_default_scaled_jacobian_provider",
        unexpected_provider,
    )
    analysis = quality.analyze_mesh_cell_quality(
        MeshData(
            points=(
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (1.0, 1.0, 0.0),
                (0.0, 1.0, 0.0),
            ),
            cells=(MeshCellBlock("polygon", ((0, 1, 2, 3),)),),
        )
    )

    assert analysis.status.value == "partial_coverage"
    assert analysis.provider_version == "not_evaluated_no_covered_cells"
