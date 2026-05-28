from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.core.boundary_curve import (
    BoundaryCurveError,
    boundary_curve_from_csv,
    boundary_curve_from_xy,
    export_boundary_curve_csv,
    load_boundary_curve_json,
    save_boundary_curve_json,
)
from osw.scripts.mscript.boundary_curve_bridge import (
    boundary_curve_from_figure_dataset,
    boundary_curve_from_mat_summary,
    boundary_curve_from_workspace_variables,
)
from osw.scripts.mscript.figure_dataset import FigureDataset, WorkspaceVariableSummary
from osw.scripts.mscript.mat_model import MatFileSummary, MatVariableSummary

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "curves"


def test_boundary_curve_from_xy_works() -> None:
    curve = boundary_curve_from_xy(
        [0, 1, 2],
        [10, 20, 30],
        "Load curve",
        curve_id="load-curve",
        x_unit="s",
        y_unit="N",
    )

    assert curve.point_count == 3
    assert curve.x_unit == "s"
    assert curve.y_unit == "N"


def test_boundary_curve_from_csv_works() -> None:
    curve = boundary_curve_from_csv(
        FIXTURES / "time_temperature.csv",
        "time_s",
        "temperature_C",
        x_unit="s",
        y_unit="degC",
        kind="temperature_profile",
    )

    assert curve.y_values == (20.0, 35.0, 50.0, 65.0)
    assert curve.source is not None
    assert curve.source.source_type == "csv"


def test_missing_csv_column_gives_friendly_error() -> None:
    with pytest.raises(BoundaryCurveError, match="Missing CSV column"):
        boundary_curve_from_csv(
            FIXTURES / "time_temperature.csv",
            "missing",
            "temperature_C",
        )


def test_non_numeric_csv_gives_friendly_error() -> None:
    with pytest.raises(BoundaryCurveError, match="non-numeric"):
        boundary_curve_from_csv(
            FIXTURES / "non_numeric_curve.csv",
            "time_s",
            "temperature_C",
        )


def test_workspace_variable_summaries_with_values_create_curve() -> None:
    variables = (
        WorkspaceVariableSummary(
            name="time",
            type_name="numeric",
            metadata={"values": [0, 1, 2]},
        ),
        WorkspaceVariableSummary(
            name="temperature",
            type_name="numeric",
            metadata={"values": [20, 25, 30]},
        ),
    )

    curve = boundary_curve_from_workspace_variables(
        variables,
        "time",
        "temperature",
        x_unit="s",
        y_unit="degC",
    )

    assert curve.point_count == 3


def test_mat_summary_without_values_returns_friendly_diagnostic() -> None:
    summary = MatFileSummary(
        source_path="data.mat",
        variables=(
            MatVariableSummary("x", (3,), "float64", True),
            MatVariableSummary("y", (3,), "float64", True),
        ),
    )

    with pytest.raises(BoundaryCurveError, match="does not include full numeric values"):
        boundary_curve_from_mat_summary(summary, "x", "y")


def test_mat_summary_with_metadata_values_creates_curve() -> None:
    summary = MatFileSummary(
        source_path="data.mat",
        variables=(
            MatVariableSummary("x", (3,), "float64", True, metadata={"values": [0, 1, 2]}),
            MatVariableSummary("y", (3,), "float64", True, metadata={"values": [3, 4, 5]}),
        ),
    )

    curve = boundary_curve_from_mat_summary(summary, "x", "y", x_unit="s", y_unit="Pa")

    assert curve.y_values == (3.0, 4.0, 5.0)


def test_figure_dataset_workspace_values_create_curve() -> None:
    dataset = FigureDataset(
        dataset_id="figures",
        source_file="workspace.json",
        workspace_variables=(
            WorkspaceVariableSummary(name="x", type_name="numeric", metadata={"values": [0, 1]}),
            WorkspaceVariableSummary(name="y", type_name="numeric", metadata={"values": [2, 3]}),
        ),
    )

    curve = boundary_curve_from_figure_dataset(dataset, "x", "y", x_unit="s", y_unit="K")

    assert curve.source is not None
    assert curve.source.source_dataset_id == "figures"


def test_export_boundary_curve_csv_and_json_round_trip(tmp_path: Path) -> None:
    curve = boundary_curve_from_xy(
        [0, 1],
        [10, 20],
        "Export curve",
        curve_id="export-curve",
        x_unit="s",
        y_unit="K",
    )
    json_path = save_boundary_curve_json(curve, tmp_path / "curve.json")
    csv_path = export_boundary_curve_csv(curve, tmp_path / "curve.csv")

    assert load_boundary_curve_json(json_path) == curve
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["curve_id"] == "export-curve"
    assert csv_path.read_text(encoding="utf-8").startswith("x,y")
