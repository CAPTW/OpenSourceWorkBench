from __future__ import annotations

from osw.core.boundary_curve import BoundaryCurve, BoundaryCurveSource, boundary_curve_from_xy
from osw.core.project_schema import (
    BoundaryCondition,
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ResultRef,
)


def _curve(curve_id: str = "temperature-curve") -> BoundaryCurve:
    return boundary_curve_from_xy(
        [0, 1, 2],
        [20, 30, 40],
        "Temperature curve",
        curve_id=curve_id,
        x_unit="s",
        y_unit="degC",
        kind="temperature_profile",
        source=BoundaryCurveSource(source_file="curves.csv", variable_names=("time", "temp")),
    )


def test_boundary_condition_can_reference_curve_id() -> None:
    boundary = BoundaryCondition(
        name="inlet-temperature",
        type="Temperature",
        target="inlet",
        curve_id="temperature-curve",
        curve_role="temperature",
    )

    assert boundary.to_dict()["curve_id"] == "temperature-curve"
    assert BoundaryCondition.from_dict(boundary.to_dict()).curve_id == "temperature-curve"


def test_project_validation_warns_on_missing_curve_reference() -> None:
    project = Project(
        metadata=ProjectMetadata(name="missing curve"),
        physics=[
            PhysicsSetup(
                boundary_conditions=[
                    BoundaryCondition(
                        name="inlet-temperature",
                        type="Temperature",
                        target="inlet",
                        curve_id="missing",
                    )
                ]
            )
        ],
        results=[ResultRef(ref_id="result", path="results/preview.json", kind="dataset")],
    )

    report = project.validate()

    assert report.has_warnings
    assert "references missing curve_id" in report.friendly_summary()


def test_project_validation_warns_on_curve_kind_boundary_type_mismatch() -> None:
    project = Project(
        metadata=ProjectMetadata(name="mismatch"),
        boundary_curves=[_curve()],
        physics=[
            PhysicsSetup(
                boundary_conditions=[
                    BoundaryCondition(
                        name="pressure",
                        type="Pressure Outlet",
                        target="outlet",
                        curve_id="temperature-curve",
                    )
                ]
            )
        ],
        results=[ResultRef(ref_id="result", path="results/preview.json", kind="dataset")],
    )

    report = project.validate()

    assert report.has_warnings
    assert "may not match curve kind" in report.friendly_summary()


def test_project_schema_json_round_trip_preserves_boundary_curves() -> None:
    project = Project(
        metadata=ProjectMetadata(name="curve project"),
        boundary_curves=[_curve()],
        physics=[
            PhysicsSetup(
                boundary_conditions=[
                    BoundaryCondition(
                        name="inlet-temperature",
                        type="Temperature",
                        target="inlet",
                        curve_id="temperature-curve",
                    )
                ]
            )
        ],
        results=[ResultRef(ref_id="result", path="results/preview.json", kind="dataset")],
    )

    loaded = Project.from_dict(project.to_dict())

    assert loaded.boundary_curves == project.boundary_curves
    assert loaded.primary_physics is not None
    assert loaded.primary_physics.boundary_conditions[0].curve_id == "temperature-curve"


def test_demo_project_still_validates_without_boundary_curves() -> None:
    from osw.core.demo_project import create_heatsink_flow_demo_project

    project = create_heatsink_flow_demo_project()
    rows = [
        (item.name, item.type, item.value)
        for item in project.primary_physics.boundary_conditions
    ]

    assert rows == [
        ("inlet", "Velocity Inlet", "3.0 m/s"),
        ("outlet", "Pressure Outlet", "0 Pa"),
        ("wall_heatsink", "Wall (No Slip)", "—"),
        ("base_bottom", "Heat Flux", "1.0e5 W/m²"),
        ("symmetry", "Symmetry", "—"),
    ]
    assert not project.validate().has_errors
