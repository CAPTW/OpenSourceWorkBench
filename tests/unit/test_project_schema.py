"""Project schema serialization and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import (
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


def test_project_yaml_round_trip(tmp_path: Path) -> None:
    project = _sample_project()
    path = tmp_path / "project.osw.yaml"

    project.save(path)
    loaded = Project.load(path)

    assert loaded == project
    assert "schema_version" in path.read_text(encoding="utf-8")


def test_invalid_yaml_raises_friendly_schema_error(tmp_path: Path) -> None:
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
