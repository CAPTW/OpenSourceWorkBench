"""Core project, unit, material, and dataset contracts."""

from __future__ import annotations

from osw.core.boundary_curve import (
    BoundaryCurve,
    BoundaryCurveError,
    BoundaryCurveSourceTrace,
    boundary_curve_from_xy,
    make_source_trace,
)
from osw.core.diagnostics import DiagnosticMessage, DiagnosticReport, DiagnosticSeverity
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
from osw.core.run_manager import ExecutableLookup, ExecutablePathRegistry
from osw.core.units import Quantity, UnitSystem
from osw.core.validation import ProjectSchemaError, ValidationMessage, ValidationReport

__all__ = [
    "BoundaryCondition",
    "BoundaryCurve",
    "BoundaryCurveError",
    "BoundaryCurveSourceTrace",
    "DiagnosticMessage",
    "DiagnosticReport",
    "DiagnosticSeverity",
    "ExecutableLookup",
    "ExecutablePathRegistry",
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
    "boundary_curve_from_xy",
    "load_project",
    "make_source_trace",
]
