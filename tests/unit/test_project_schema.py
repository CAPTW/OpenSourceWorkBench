"""Project schema serialization and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import (
    BoundaryCondition,
    GeometryRef,
    MeshRef,
    Project,
    ProjectMetadata,
    ProjectSchemaError,
    ReportConfig,
    ResultRef,
    ScriptRef,
    SolverConfig,
    load_project,
)
from osw.core.units import Quantity, UnitSystem
from osw.core.validation import validate_project


def _sample_project() -> Project:
    return Project(
        metadata=ProjectMetadata(
            name="Cantilever demo",
            description="Linear static education fixture",
            author="OSW tests",
            tags=["demo", "validation"],
        ),
        units=UnitSystem.si(),
        materials=[
            Material(
                material_id="steel",
                name="Steel",
                density=Quantity(7850.0, "kg/m^3"),
                elastic=IsotropicElastic(
                    young_modulus=Quantity(210.0, "GPa"),
                    poisson_ratio=0.3,
                ),
            )
        ],
        geometry=[GeometryRef(ref_id="geom-1", path="geometry/cantilever.step", format="STEP")],
        meshes=[MeshRef(ref_id="mesh-1", path="mesh/cantilever.vtu", format="VTU")],
        scripts=[ScriptRef(ref_id="script-1", path="scripts/plot.m", language="m")],
        solvers=[
            SolverConfig(
                solver_id="calculix-linear-static",
                name="CalculiX linear static",
                execution_mode="prepare_only",
            )
        ],
        results=[ResultRef(ref_id="result-1", path="results/cantilever.json", kind="dataset")],
        report=ReportConfig(path="reports/cantilever.html", title="Cantilever report"),
    )


def test_project_json_round_trip(tmp_path: Path) -> None:
    project = _sample_project()
    path = tmp_path / "project.osw.json"

    project.save(path)
    loaded = load_project(path)

    assert loaded == project
    assert loaded.schema_version == "0.1"
    assert not loaded.validate().has_errors


def test_mesh_ref_round_trips_mesh_info_summary(tmp_path: Path) -> None:
    project = Project(
        metadata=ProjectMetadata(name="mesh info"),
        meshes=[
            MeshRef(
                ref_id="mesh-1",
                path="mesh/tiny.vtu",
                format="vtu",
                node_count=3,
                cell_count=1,
                mesh_info={
                    "node_count": 3,
                    "element_count": 1,
                    "cell_types": ["triangle"],
                },
            )
        ],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )
    path = tmp_path / "project.osw.json"

    project.save(path)
    loaded = Project.load(path)

    assert loaded.mesh_refs[0].mesh_info is not None
    assert loaded.mesh_refs[0].mesh_info["cell_types"] == ["triangle"]


def test_project_yaml_round_trip(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    project = _sample_project()
    path = tmp_path / "project.osw.yaml"

    project.save(path)
    loaded = Project.load(path)

    assert loaded == project
    assert "schema_version" in path.read_text(encoding="utf-8")


def test_invalid_yaml_raises_friendly_schema_error(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    path = tmp_path / "broken.osw.yaml"
    path.write_text("metadata: [unterminated\n", encoding="utf-8")

    with pytest.raises(ProjectSchemaError, match="Could not parse project file"):
        Project.load(path)


def test_project_validation_reports_friendly_errors() -> None:
    project = Project.from_dict(
        {
            "schema_version": "0.1",
            "metadata": {"name": ""},
            "units": UnitSystem.si().to_dict(),
            "materials": [{"material_id": "", "name": ""}],
        }
    )

    report = project.validate()

    assert report.has_errors
    assert any("Project metadata name is required." in item.message for item in report.messages)
    assert any("Material id is required." in item.message for item in report.messages)


def test_project_migration_adds_current_schema_version() -> None:
    project = Project.from_dict(
        {
            "metadata": {"name": "legacy"},
            "unit_system": UnitSystem.si().to_dict(),
        }
    )

    assert project.schema_version == "0.1"
    assert project.units == UnitSystem.si()


def test_demo_project_matches_heatsink_flow_visual_data() -> None:
    project = create_heatsink_flow_demo_project()

    assert project.metadata.name == "HeatSink_Flow"
    assert project.schema_version == "0.1"
    assert [item.name for item in project.geometry_refs] == [
        "heatsink.step",
        "enclosure.stp",
        "fluid_domain.csg",
    ]
    assert [item.name for item in project.mesh_refs] == ["mesh.msh", "mesh_stats.txt"]
    assert [item.name for item in project.script_refs] == [
        "preprocess.m",
        "run_case.m",
        "postprocess.m",
    ]
    assert {item.name for item in project.result_refs} >= {
        "run_0001",
        "fields.ex2",
        "residuals.dat",
        "monitor.log",
        "run_0000 (baseline)",
    }
    assert project.report.title == "HeatSink_Flow Simulation Report"
    assert project.report.run_label == "Run 0001"
    assert project.report.sections == ["Overview", "Key Results", "Summary"]


def test_demo_project_boundary_rows_and_solver_settings_match_gui_mock() -> None:
    project = create_heatsink_flow_demo_project()
    assert project.primary_physics is not None

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
    assert project.solver_config is not None
    assert project.solver_config.solver == "chtSolver"
    assert project.solver_config.time_scheme == "Steady-State"
    assert project.solver_config.linear_solver == "GMRES"
    assert project.solver_config.preconditioner == "AMG"
    assert float(project.solver_config.convergence_tolerance) == pytest.approx(1.0e-6)


def test_script_refs_default_to_safe_preview_for_m_files() -> None:
    script = ScriptRef(id="script", path="scripts/run_case.m", language="matlab_octave")

    assert script.safe_preview_required is True


def test_project_validation_warns_for_native_commercial_cad_extension() -> None:
    project = Project(
        metadata=ProjectMetadata(name="native cad warning"),
        geometry=[GeometryRef(id="native", path="geometry/part.sldprt", format="SLDPRT")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any("native commercial CAD direct import" in item.message for item in report.messages)


def test_project_validation_warns_for_native_commercial_mesh_path() -> None:
    project = Project(
        metadata=ProjectMetadata(name="native mesh warning"),
        meshes=[MeshRef(id="native", path="mesh/native_part.sldprt", format="SLDPRT")],
        results=[ResultRef(ref_id="result-1", path="results/preview.json", kind="dataset")],
    )

    report = validate_project(project)

    assert report.has_warnings
    assert any("standard/exported CAD and mesh formats" in item.message for item in report.messages)


def test_boundary_condition_accepts_project_schema_fields() -> None:
    boundary = BoundaryCondition(
        name="inlet",
        type="Velocity Inlet",
        value="3.0 m/s",
        unit="m/s",
        target="inlet",
    )

    assert boundary.kind == "Velocity Inlet"
    assert boundary.to_dict()["value"] == "3.0 m/s"
