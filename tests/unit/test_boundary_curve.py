from __future__ import annotations

from pathlib import Path

import pytest

from osw.core.boundary_curve import (
    BoundaryCurve,
    BoundaryCurveError,
    BoundaryCurveKind,
    BoundaryCurveSource,
    BoundaryCurveSourceTrace,
    CurveAxis,
    CurveInterpolation,
    boundary_curve_from_xy,
    curve_preview,
)
from osw.core.project_schema import Project, ProjectMetadata
from osw.scripts.mscript.boundary_curve_bridge import (
    boundary_curve_from_mat_preview,
    boundary_curve_from_workspace_variables,
)
from osw.scripts.mscript.mat_reader import MatFilePreview, MatVariableSummary


def test_workspace_arrays_create_boundary_curve() -> None:
    curve = boundary_curve_from_workspace_variables(
        {"time": [0, 1, 2], "load": [0, 10, 20]},
        x_variable="time",
        y_variable="load",
        curve_id="load-time",
        name="Load history",
        x_unit="s",
        y_unit="N",
        source_file="scripts/load_profile.mat",
        created_at="2026-05-12T00:00:00Z",
    )

    assert curve.curve_id == "load-time"
    assert curve.name == "Load history"
    assert curve.x_values == (0.0, 1.0, 2.0)
    assert curve.y_values == (0.0, 10.0, 20.0)
    assert curve.x_unit == "s"
    assert curve.y_unit == "N"
    assert curve.source == BoundaryCurveSourceTrace(
        source_type="workspace_variable",
        source_file="scripts/load_profile.mat",
        variable_names=("time", "load"),
        created_at="2026-05-12T00:00:00Z",
    )
    assert not curve.validate().has_errors
    assert not curve.validate().has_warnings


def test_missing_units_warn_without_blocking_curve() -> None:
    curve = boundary_curve_from_xy(
        curve_id="unitless",
        name="Unitless preview",
        x_values=(0.0, 1.0),
        y_values=(3.0, 4.0),
        source=BoundaryCurveSourceTrace(
            source_file="workspace",
            variable_names=("x", "y"),
            created_at="2026-05-12T00:00:00Z",
        ),
    )

    report = curve.validate()

    assert not report.has_errors
    assert report.has_warnings
    assert "x unit is missing" in report.friendly_summary()
    assert "y unit is missing" in report.friendly_summary()


def test_boundary_curve_models_serialize_deserialize() -> None:
    source = BoundaryCurveSource(
        source_type="csv",
        source_file="curves.csv",
        x_variable="time",
        y_variable="temperature",
        created_at="2026-05-28T00:00:00Z",
    )
    curve = BoundaryCurve(
        curve_id="time-temperature",
        name="Time Temperature",
        kind=BoundaryCurveKind.TEMPERATURE_PROFILE,
        x_axis=CurveAxis("time", unit="s", role="independent"),
        y_axis=CurveAxis("temperature", unit="degC", role="dependent"),
        x_values=[0, 1, 2],
        y_values=[20, 30, 40],
        interpolation=CurveInterpolation.LINEAR,
        source=source,
    )

    loaded = BoundaryCurve.from_dict(curve.to_dict())

    assert loaded == curve
    assert loaded.source == source
    assert loaded.x_axis.unit == "s"
    assert loaded.y_axis.unit == "degC"


def test_length_mismatch_errors_clearly() -> None:
    with pytest.raises(BoundaryCurveError, match="same length"):
        boundary_curve_from_workspace_variables(
            {"x": [0, 1], "y": [10]},
            x_variable="x",
            y_variable="y",
            curve_id="bad-curve",
            name="Bad curve",
            x_unit="s",
            y_unit="N",
            source_file="workspace",
        )


def test_non_finite_values_error() -> None:
    curve = BoundaryCurve(
        curve_id="bad",
        name="Bad curve",
        x_values=[0, 1],
        y_values=[10, float("nan")],
        x_unit="s",
        y_unit="K",
        source=BoundaryCurveSource(source_file="manual", variable_names=("x", "y")),
    )

    report = curve.validate()

    assert report.has_errors
    assert "finite" in report.friendly_summary()


def test_duplicate_and_non_monotonic_x_warn() -> None:
    duplicate_curve = BoundaryCurve(
        curve_id="duplicate",
        name="Duplicate x",
        kind="time_series",
        x_values=[0, 1, 1],
        y_values=[0, 1, 2],
        x_unit="s",
        y_unit="K",
        source=BoundaryCurveSource(source_file="manual", variable_names=("time", "temperature")),
    )
    non_monotonic_curve = BoundaryCurve(
        curve_id="non-monotonic",
        name="Non monotonic x",
        kind="time_series",
        x_values=[0, 2, 1],
        y_values=[0, 1, 2],
        x_unit="s",
        y_unit="K",
        source=BoundaryCurveSource(source_file="manual", variable_names=("time", "temperature")),
    )

    assert duplicate_curve.validate().has_warnings
    assert "duplicate x values" in duplicate_curve.validate().friendly_summary()
    assert non_monotonic_curve.validate().has_warnings
    assert "monotonic increasing" in non_monotonic_curve.validate().friendly_summary()


def test_curve_preview_truncates_large_curves() -> None:
    curve = boundary_curve_from_xy(
        range(100),
        range(100),
        "Large curve",
        curve_id="large",
        x_unit="s",
        y_unit="K",
        source=BoundaryCurveSource(source_file="manual", variable_names=("x", "y")),
    )

    preview = curve_preview(curve, max_rows=5)

    assert len(preview) == 5
    assert preview[-1] == {"x": 4.0, "y": 4.0}


def test_boundary_curve_round_trips_through_project_schema(tmp_path: Path) -> None:
    curve = boundary_curve_from_workspace_variables(
        {"x": [0, 1], "temperature": [300, 350]},
        x_variable="x",
        y_variable="temperature",
        curve_id="temperature-ramp",
        name="Temperature ramp",
        x_unit="s",
        y_unit="K",
        source_file="scripts/ramp.mat",
        created_at="2026-05-12T00:00:00Z",
    )
    project = Project(
        metadata=ProjectMetadata(name="Boundary curve demo"),
        boundary_curves=[curve],
    )
    path = tmp_path / "project.osw.json"

    project.save(path)
    loaded = Project.load(path)

    assert loaded.boundary_curves == [curve]
    assert loaded.to_dict()["boundary_curves"][0]["curve_id"] == "temperature-ramp"
    assert not loaded.validate().has_errors


def test_mat_preview_bridge_uses_variable_values() -> None:
    preview = MatFilePreview(
        file_path=Path("loads.mat"),
        format_version="v4-v7.2",
        variables=(
            MatVariableSummary("time", (3,), "float64", True),
            MatVariableSummary("pressure", (3,), "float64", True),
        ),
        _values={"time": [0, 1, 2], "pressure": [101000, 102000, 103000]},
    )

    curve = boundary_curve_from_mat_preview(
        preview,
        x_variable="time",
        y_variable="pressure",
        curve_id="pressure-time",
        name="Pressure profile",
        x_unit="s",
        y_unit="Pa",
        created_at="2026-05-12T00:00:00Z",
    )

    assert curve.y_values == (101000.0, 102000.0, 103000.0)
    assert curve.source.source_file.endswith("loads.mat")
    assert curve.source.variable_names == ("time", "pressure")
