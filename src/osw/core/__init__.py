"""Core project, unit, material, and dataset contracts."""

from __future__ import annotations

from osw.core.materials import IsotropicElastic, Material, MaterialDB
from osw.core.project_schema import (
    BoundaryCondition,
    GeometryRef,
    MeshRef,
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ReportConfig,
    ResultRef,
    ScriptRef,
    SolverConfig,
    load_project,
)
from osw.core.units import Quantity, UnitSystem
from osw.core.validation import ProjectSchemaError, ValidationMessage, ValidationReport

__all__ = [
    "BoundaryCondition",
    "GeometryRef",
    "IsotropicElastic",
    "Material",
    "MaterialDB",
    "MeshRef",
    "PhysicsSetup",
    "Project",
    "ProjectMetadata",
    "ProjectSchemaError",
    "Quantity",
    "ReportConfig",
    "ResultRef",
    "ScriptRef",
    "SolverConfig",
    "UnitSystem",
    "ValidationMessage",
    "ValidationReport",
    "load_project",
]
