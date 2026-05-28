from __future__ import annotations

import json
from pathlib import Path

from osw.core.result_dataset import (
    ResultArtifactRef,
    ResultCatalog,
    ResultDataset,
    ResultDatasetKind,
    ResultDatasetSummary,
    ResultField,
    ResultRow,
    ResultScalar,
    ResultSeries,
    ResultSummaryValue,
    ResultTable,
)


def test_existing_result_dataset_round_trips_with_summary_dict() -> None:
    dataset = ResultDataset(
        dataset_id="result-1",
        source="results.json",
        solver="CalculiX",
        analysis_type="linear_static",
        fields=(
            ResultField(
                name="U",
                location="node",
                components=("magnitude",),
                rows=(ResultRow(1, {"magnitude": 0.1}),),
                unit="m",
            ),
        ),
        summaries=(ResultSummaryValue("max_displacement", 0.1, "m", "U"),),
        warnings=("review units",),
    )

    restored = ResultDataset.from_dict(dataset.to_dict())

    assert restored.dataset_id == "result-1"
    assert restored.field("U").rows[0].values["magnitude"] == 0.1
    assert restored.max_summary("max_displacement").unit == "m"
    assert restored.to_report_tables()


def test_result_scalar_series_table_artifact_serialize() -> None:
    scalar = ResultScalar("max", 2.5, "Pa", "stress")
    series = ResultSeries("residual", (1, 2), (1e-3, 1e-6), x_unit="iteration")
    table = ResultTable("table-1", "Preview", ("A",), (("1",),), truncated=True)
    artifact = ResultArtifactRef.from_path(
        Path("tests/fixtures/calculix/results/simple_success.dat"),
        role="dat_result",
    )

    assert ResultScalar.from_dict(scalar.to_dict()) == scalar
    assert ResultSeries.from_dict(series.to_dict()) == series
    assert ResultTable.from_dict(table.to_dict()) == table
    assert ResultArtifactRef.from_dict(artifact.to_dict()).path.endswith("simple_success.dat")
    assert artifact.exists


def test_result_catalog_serializes_with_paths_as_strings() -> None:
    dataset = ResultDataset(
        dataset_id="openfoam",
        source="tests/fixtures/openfoam/residual_simple.log",
        solver="OpenFOAM",
        analysis_type="incompressible_cfd_residuals",
    )
    catalog = ResultCatalog(
        catalog_id="catalog-1",
        project_name="Demo",
        datasets=(dataset,),
    )

    payload = catalog.to_dict()
    restored = ResultCatalog.from_dict(json.loads(json.dumps(payload)))

    assert restored.project_name == "Demo"
    assert restored.selected_dataset_id == "openfoam"
    assert isinstance(restored.datasets[0].source, str)


def test_result_dataset_summary_serializes() -> None:
    summary = ResultDatasetSummary(
        dataset_id="mesh",
        title="Mesh Summary",
        kind=ResultDatasetKind.MESH_SUMMARY,
        source="mesh.msh",
        scalar_count=2,
        diagnostics=("warning: missing artifact",),
    )

    restored = ResultDatasetSummary.from_dict(summary.to_dict())

    assert restored.kind == ResultDatasetKind.MESH_SUMMARY.value
    assert restored.scalar_count == 2
