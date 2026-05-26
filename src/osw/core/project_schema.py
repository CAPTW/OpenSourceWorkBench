"""Project schema contracts and serialization helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .boundary_curve import BoundaryCurve
from .materials import Material, MaterialDB, builtin_materials
from .units import UnitSystem
from .validation import ProjectSchemaError, ValidationReport

CURRENT_SCHEMA_VERSION = "0.1"
NATIVE_COMMERCIAL_CAD_EXTENSIONS = frozenset(
    {".sldprt", ".sldasm", ".catpart", ".catproduct", ".prt", ".asm"}
)


@dataclass(frozen=True)
class ProjectMetadata:
    name: str
    description: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: object) -> ProjectMetadata:
        if not isinstance(data, dict):
            msg = "Project metadata must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            tags=[str(tag) for tag in data.get("tags", [])],
            created_at=str(data.get("created_at", "")),
            modified_at=str(data.get("modified_at", "")),
        )

    def validate(self) -> ValidationReport:
        report = ValidationReport()
        if not self.name:
            report.add_error("metadata.name", "Project metadata name is required.")
        return report


@dataclass(frozen=True, init=False)
class GeometryRef:
    id: str
    name: str
    path: str
    format: str
    role: str
    status: str
    metadata: dict[str, Any]

    def __init__(
        self,
        id: str = "",
        path: str = "",
        format: str = "",
        metadata: Mapping[str, Any] | None = None,
        *,
        ref_id: str | None = None,
        name: str = "",
        role: str = "",
        status: str = "ready",
    ) -> None:
        object.__setattr__(self, "id", str(ref_id or id))
        object.__setattr__(self, "name", str(name or Path(path).name))
        object.__setattr__(self, "path", str(path))
        object.__setattr__(self, "format", str(format))
        object.__setattr__(self, "role", str(role))
        object.__setattr__(self, "status", str(status))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def ref_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ref_id": self.id,
            "name": self.name,
            "path": self.path,
            "format": self.format,
            "role": self.role,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> GeometryRef:
        if not isinstance(data, dict):
            msg = "Geometry reference must be a mapping."
            raise ValueError(msg)
        return cls(
            id=str(data.get("id", data.get("ref_id", ""))),
            name=str(data.get("name", "")),
            path=str(data.get("path", "")),
            format=str(data.get("format", "")),
            role=str(data.get("role", "")),
            status=str(data.get("status", "ready")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, init=False)
class MeshRef:
    id: str
    name: str
    path: str
    format: str
    role: str
    status: str
    cell_count: int | None
    face_count: int | None
    node_count: int | None
    quality_summary: str
    mesh_info: dict[str, Any] | None
    metadata: dict[str, Any]

    def __init__(
        self,
        id: str = "",
        path: str = "",
        format: str = "",
        metadata: Mapping[str, Any] | None = None,
        *,
        ref_id: str | None = None,
        name: str = "",
        role: str = "",
        status: str = "ready",
        cell_count: int | None = None,
        face_count: int | None = None,
        node_count: int | None = None,
        quality_summary: str = "",
        mesh_info: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", str(ref_id or id))
        object.__setattr__(self, "name", str(name or Path(path).name))
        object.__setattr__(self, "path", str(path))
        object.__setattr__(self, "format", str(format))
        object.__setattr__(self, "role", str(role))
        object.__setattr__(self, "status", str(status))
        object.__setattr__(self, "cell_count", _optional_int(cell_count))
        object.__setattr__(self, "face_count", _optional_int(face_count))
        object.__setattr__(self, "node_count", _optional_int(node_count))
        object.__setattr__(self, "quality_summary", str(quality_summary))
        object.__setattr__(self, "mesh_info", dict(mesh_info) if mesh_info else None)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def ref_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ref_id": self.id,
            "name": self.name,
            "path": self.path,
            "format": self.format,
            "role": self.role,
            "status": self.status,
            "cell_count": self.cell_count,
            "face_count": self.face_count,
            "node_count": self.node_count,
            "quality_summary": self.quality_summary,
            "mesh_info": dict(self.mesh_info) if self.mesh_info else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> MeshRef:
        if not isinstance(data, dict):
            msg = "Mesh reference must be a mapping."
            raise ValueError(msg)
        return cls(
            id=str(data.get("id", data.get("ref_id", ""))),
            name=str(data.get("name", "")),
            path=str(data.get("path", "")),
            format=str(data.get("format", "")),
            role=str(data.get("role", "")),
            status=str(data.get("status", "ready")),
            cell_count=data.get("cell_count"),
            face_count=data.get("face_count"),
            node_count=data.get("node_count"),
            quality_summary=str(data.get("quality_summary", "")),
            mesh_info=(
                dict(data.get("mesh_info", {}))
                if isinstance(data.get("mesh_info"), Mapping)
                else None
            ),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, init=False)
class ScriptRef:
    id: str
    name: str
    path: str
    language: str
    role: str
    status: str
    safe_preview_required: bool
    metadata: dict[str, Any]

    def __init__(
        self,
        id: str = "",
        path: str = "",
        language: str = "",
        metadata: Mapping[str, Any] | None = None,
        *,
        ref_id: str | None = None,
        name: str = "",
        role: str = "",
        status: str = "ready",
        safe_preview_required: bool = True,
    ) -> None:
        object.__setattr__(self, "id", str(ref_id or id))
        object.__setattr__(self, "name", str(name or Path(path).name))
        object.__setattr__(self, "path", str(path))
        object.__setattr__(self, "language", str(language))
        object.__setattr__(self, "role", str(role))
        object.__setattr__(self, "status", str(status))
        object.__setattr__(self, "safe_preview_required", bool(safe_preview_required))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def ref_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ref_id": self.id,
            "name": self.name,
            "path": self.path,
            "language": self.language,
            "role": self.role,
            "status": self.status,
            "safe_preview_required": self.safe_preview_required,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ScriptRef:
        if not isinstance(data, dict):
            msg = "Script reference must be a mapping."
            raise ValueError(msg)
        return cls(
            id=str(data.get("id", data.get("ref_id", ""))),
            name=str(data.get("name", "")),
            path=str(data.get("path", "")),
            language=str(data.get("language", "")),
            role=str(data.get("role", "")),
            status=str(data.get("status", "ready")),
            safe_preview_required=bool(data.get("safe_preview_required", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, init=False)
class BoundaryCondition:
    name: str
    type: str
    value: str
    unit: str
    target: str
    metadata: dict[str, Any]
    kind: str
    values: dict[str, Any]

    def __init__(
        self,
        name: str,
        type: str = "",
        value: str = "",
        unit: str = "",
        target: str = "",
        metadata: Mapping[str, Any] | None = None,
        *,
        kind: str = "",
        values: Mapping[str, Any] | None = None,
    ) -> None:
        resolved_type = str(type or kind)
        object.__setattr__(self, "name", str(name))
        object.__setattr__(self, "type", resolved_type)
        object.__setattr__(self, "value", str(value))
        object.__setattr__(self, "unit", str(unit))
        object.__setattr__(self, "target", str(target))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        object.__setattr__(self, "kind", str(kind or resolved_type))
        object.__setattr__(self, "values", dict(values or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "unit": self.unit,
            "target": self.target,
            "metadata": dict(self.metadata),
            "kind": self.kind,
            "values": dict(self.values),
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryCondition:
        if not isinstance(data, dict):
            msg = "Boundary condition must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            type=str(data.get("type", "")),
            value=str(data.get("value", "")),
            unit=str(data.get("unit", "")),
            target=str(data.get("target", "")),
            metadata=dict(data.get("metadata", {})),
            kind=str(data.get("kind", "")),
            values=dict(data.get("values", {})),
        )


@dataclass(frozen=True)
class SolverConfig:
    solver_id: str = ""
    name: str = ""
    execution_mode: str = "prepare_only"
    parameters: dict[str, Any] = field(default_factory=dict)
    solver: str = ""
    time_scheme: str = "Steady-State"
    linear_solver: str = "GMRES"
    preconditioner: str = "AMG"
    convergence_tolerance: float | str = 1.0e-6
    max_iterations: int | None = None
    settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.solver and self.name:
            object.__setattr__(self, "solver", self.name)
        if not self.name and self.solver:
            object.__setattr__(self, "name", self.solver)
        if not self.solver_id and (self.solver or self.name):
            object.__setattr__(self, "solver_id", _slug(self.solver or self.name))

    def to_dict(self) -> dict[str, Any]:
        return {
            "solver_id": self.solver_id,
            "name": self.name,
            "execution_mode": self.execution_mode,
            "parameters": dict(self.parameters),
            "solver": self.solver,
            "time_scheme": self.time_scheme,
            "linear_solver": self.linear_solver,
            "preconditioner": self.preconditioner,
            "convergence_tolerance": self.convergence_tolerance,
            "max_iterations": self.max_iterations,
            "settings": dict(self.settings),
        }

    @classmethod
    def from_dict(cls, data: object) -> SolverConfig:
        if not isinstance(data, dict):
            msg = "Solver config must be a mapping."
            raise ValueError(msg)
        return cls(
            solver_id=str(data.get("solver_id", "")),
            name=str(data.get("name", "")),
            execution_mode=str(data.get("execution_mode", "prepare_only")),
            parameters=dict(data.get("parameters", {})),
            solver=str(data.get("solver", "")),
            time_scheme=str(data.get("time_scheme", "Steady-State")),
            linear_solver=str(data.get("linear_solver", "GMRES")),
            preconditioner=str(data.get("preconditioner", "AMG")),
            convergence_tolerance=data.get("convergence_tolerance", 1.0e-6),
            max_iterations=_optional_int(data.get("max_iterations")),
            settings=dict(data.get("settings", {})),
        )


@dataclass(frozen=True)
class PhysicsSetup:
    setup_id: str = ""
    name: str = ""
    analysis_type: str = ""
    boundary_conditions: list[BoundaryCondition] = field(default_factory=list)
    material_assignments: dict[str, str] = field(default_factory=dict)
    domain: str = "MULTIPHYSICS"
    materials: list[str] = field(default_factory=list)
    boundaries: list[BoundaryCondition] = field(default_factory=list)
    solver_config: SolverConfig | None = None
    files: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.boundaries and self.boundary_conditions:
            object.__setattr__(self, "boundaries", list(self.boundary_conditions))
        if not self.boundary_conditions and self.boundaries:
            object.__setattr__(self, "boundary_conditions", list(self.boundaries))
        if not self.materials and self.material_assignments:
            object.__setattr__(self, "materials", list(self.material_assignments.values()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "setup_id": self.setup_id,
            "name": self.name,
            "domain": self.domain,
            "analysis_type": self.analysis_type,
            "materials": list(self.materials),
            "boundaries": [item.to_dict() for item in self.boundaries],
            "boundary_conditions": [item.to_dict() for item in self.boundary_conditions],
            "material_assignments": dict(self.material_assignments),
            "solver_config": self.solver_config.to_dict() if self.solver_config else None,
            "files": list(self.files),
        }

    @classmethod
    def from_dict(cls, data: object) -> PhysicsSetup:
        if not isinstance(data, dict):
            msg = "Physics setup must be a mapping."
            raise ValueError(msg)
        boundary_payload = data.get("boundary_conditions", data.get("boundaries", []))
        boundaries = [BoundaryCondition.from_dict(item) for item in boundary_payload]
        return cls(
            setup_id=str(data.get("setup_id", "")),
            name=str(data.get("name", "")),
            domain=str(data.get("domain", "MULTIPHYSICS")),
            analysis_type=str(data.get("analysis_type", "")),
            boundary_conditions=boundaries,
            boundaries=boundaries,
            material_assignments={
                str(key): str(value)
                for key, value in dict(data.get("material_assignments", {})).items()
            },
            materials=[str(item) for item in data.get("materials", [])],
            solver_config=(
                SolverConfig.from_dict(data["solver_config"])
                if data.get("solver_config")
                else None
            ),
            files=[str(item) for item in data.get("files", [])],
        )


@dataclass(frozen=True, init=False)
class ResultRef:
    id: str
    name: str
    path: str
    format: str
    run_id: str
    role: str
    kind: str
    metadata: dict[str, Any]

    def __init__(
        self,
        id: str = "",
        path: str = "",
        kind: str = "",
        metadata: Mapping[str, Any] | None = None,
        *,
        ref_id: str | None = None,
        name: str = "",
        format: str = "",
        run_id: str = "",
        role: str = "",
    ) -> None:
        resolved_format = str(format or kind)
        object.__setattr__(self, "id", str(ref_id or id))
        object.__setattr__(self, "name", str(name or Path(path).name or id))
        object.__setattr__(self, "path", str(path))
        object.__setattr__(self, "format", resolved_format)
        object.__setattr__(self, "run_id", str(run_id))
        object.__setattr__(self, "role", str(role))
        object.__setattr__(self, "kind", str(kind or resolved_format))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def ref_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ref_id": self.id,
            "name": self.name,
            "path": self.path,
            "format": self.format,
            "run_id": self.run_id,
            "role": self.role,
            "kind": self.kind,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultRef:
        if not isinstance(data, dict):
            msg = "Result reference must be a mapping."
            raise ValueError(msg)
        return cls(
            id=str(data.get("id", data.get("ref_id", ""))),
            name=str(data.get("name", "")),
            path=str(data.get("path", "")),
            format=str(data.get("format", "")),
            run_id=str(data.get("run_id", "")),
            role=str(data.get("role", "")),
            kind=str(data.get("kind", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class ReportConfig:
    path: str = "reports/report.html"
    title: str = "OSW Report"
    include_validation: bool = True
    run_label: str = ""
    sections: list[str] = field(default_factory=list)
    export_formats: list[str] = field(default_factory=lambda: ["html"])
    include_figures: bool = True
    include_tables: bool = True
    include_warnings: bool = True
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "include_validation": self.include_validation,
            "run_label": self.run_label,
            "sections": list(self.sections),
            "export_formats": list(self.export_formats),
            "include_figures": self.include_figures,
            "include_tables": self.include_tables,
            "include_warnings": self.include_warnings,
            "artifacts": list(self.artifacts),
        }

    @classmethod
    def from_dict(cls, data: object) -> ReportConfig:
        if data is None:
            return cls()
        if not isinstance(data, dict):
            msg = "Report config must be a mapping."
            raise ValueError(msg)
        return cls(
            path=str(data.get("path", "reports/report.html")),
            title=str(data.get("title", "OSW Report")),
            include_validation=bool(data.get("include_validation", True)),
            run_label=str(data.get("run_label", "")),
            sections=[str(item) for item in data.get("sections", [])],
            export_formats=[str(item) for item in data.get("export_formats", ["html"])],
            include_figures=bool(data.get("include_figures", True)),
            include_tables=bool(data.get("include_tables", True)),
            include_warnings=bool(data.get("include_warnings", True)),
            artifacts=[str(item) for item in data.get("artifacts", [])],
        )


@dataclass(frozen=True)
class PluginRef:
    plugin_id: str
    display_name: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> PluginRef:
        if not isinstance(data, dict):
            msg = "Plugin reference must be a mapping."
            raise ValueError(msg)
        return cls(
            plugin_id=str(data.get("plugin_id", data.get("id", ""))),
            display_name=str(data.get("display_name", data.get("name", ""))),
            enabled=bool(data.get("enabled", True)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class ProjectWarning:
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message}

    @classmethod
    def from_dict(cls, data: object) -> ProjectWarning:
        if not isinstance(data, dict):
            msg = "Project warning must be a mapping."
            raise ValueError(msg)
        return cls(path=str(data.get("path", "")), message=str(data.get("message", "")))


@dataclass(frozen=True, init=False)
class Project:
    metadata: ProjectMetadata
    units: UnitSystem
    materials: list[Material]
    geometry: list[GeometryRef]
    meshes: list[MeshRef]
    scripts: list[ScriptRef]
    boundary_curves: list[BoundaryCurve]
    physics: list[PhysicsSetup]
    solvers: list[SolverConfig]
    results: list[ResultRef]
    report: ReportConfig
    schema_version: str
    plugins: list[PluginRef]
    warnings: list[ProjectWarning]

    def __init__(
        self,
        metadata: ProjectMetadata,
        units: UnitSystem | None = None,
        materials: Sequence[Material] | None = None,
        geometry: Sequence[GeometryRef] | None = None,
        meshes: Sequence[MeshRef] | None = None,
        scripts: Sequence[ScriptRef] | None = None,
        boundary_curves: Sequence[BoundaryCurve] | None = None,
        physics: Sequence[PhysicsSetup] | PhysicsSetup | None = None,
        solvers: Sequence[SolverConfig] | None = None,
        results: Sequence[ResultRef] | None = None,
        report: ReportConfig | None = None,
        schema_version: str = CURRENT_SCHEMA_VERSION,
        plugins: Sequence[PluginRef] | None = None,
        warnings: Sequence[ProjectWarning] | None = None,
        *,
        unit_system: UnitSystem | None = None,
        geometry_refs: Sequence[GeometryRef] | None = None,
        mesh_refs: Sequence[MeshRef] | None = None,
        script_refs: Sequence[ScriptRef] | None = None,
        result_refs: Sequence[ResultRef] | None = None,
        report_config: ReportConfig | None = None,
    ) -> None:
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "units", unit_system or units or UnitSystem.si())
        object.__setattr__(self, "materials", list(materials or []))
        object.__setattr__(self, "geometry", list(geometry_refs or geometry or []))
        object.__setattr__(self, "meshes", list(mesh_refs or meshes or []))
        object.__setattr__(self, "scripts", list(script_refs or scripts or []))
        object.__setattr__(self, "boundary_curves", list(boundary_curves or []))
        object.__setattr__(self, "physics", _physics_list(physics))
        object.__setattr__(self, "solvers", list(solvers or []))
        object.__setattr__(self, "results", list(result_refs or results or []))
        object.__setattr__(self, "report", report_config or report or ReportConfig())
        object.__setattr__(self, "schema_version", str(schema_version))
        object.__setattr__(self, "plugins", list(plugins or []))
        object.__setattr__(self, "warnings", list(warnings or []))

    @property
    def unit_system(self) -> UnitSystem:
        return self.units

    @property
    def geometry_refs(self) -> list[GeometryRef]:
        return self.geometry

    @property
    def mesh_refs(self) -> list[MeshRef]:
        return self.meshes

    @property
    def script_refs(self) -> list[ScriptRef]:
        return self.scripts

    @property
    def result_refs(self) -> list[ResultRef]:
        return self.results

    @property
    def primary_physics(self) -> PhysicsSetup | None:
        return self.physics[0] if self.physics else None

    @property
    def solver_config(self) -> SolverConfig | None:
        if self.solvers:
            return self.solvers[0]
        if self.primary_physics is not None:
            return self.primary_physics.solver_config
        return None

    def to_dict(self) -> dict[str, Any]:
        unit_payload = self.units.to_dict()
        geometry_payload = [item.to_dict() for item in self.geometry]
        mesh_payload = [item.to_dict() for item in self.meshes]
        script_payload = [item.to_dict() for item in self.scripts]
        result_payload = [item.to_dict() for item in self.results]
        return {
            "schema_version": self.schema_version,
            "metadata": self.metadata.to_dict(),
            "units": unit_payload,
            "unit_system": unit_payload,
            "materials": [material.to_dict() for material in self.materials],
            "geometry": geometry_payload,
            "geometry_refs": geometry_payload,
            "meshes": mesh_payload,
            "mesh_refs": mesh_payload,
            "scripts": script_payload,
            "script_refs": script_payload,
            "boundary_curves": [item.to_dict() for item in self.boundary_curves],
            "physics": [item.to_dict() for item in self.physics],
            "solvers": [item.to_dict() for item in self.solvers],
            "results": result_payload,
            "result_refs": result_payload,
            "report": self.report.to_dict(),
            "plugins": [item.to_dict() for item in self.plugins],
            "warnings": [item.to_dict() for item in self.warnings],
        }

    @classmethod
    def from_dict(cls, data: object) -> Project:
        if not isinstance(data, dict):
            msg = "Project data must be a mapping."
            raise ProjectSchemaError(msg)
        migrated = migrate_project_data(data)
        schema_version = str(migrated.get("schema_version", CURRENT_SCHEMA_VERSION))
        if schema_version != CURRENT_SCHEMA_VERSION:
            msg = f"Unsupported OSW project schema version: {schema_version}"
            raise ProjectSchemaError(msg)

        units_defaulted = bool(migrated.get("_units_defaulted", False))
        units_data = migrated.get("units", UnitSystem.si().to_dict())

        try:
            solver_payload = migrated.get("solvers", [])
            physics_payload = migrated.get("physics", [])
            return cls(
                schema_version=schema_version,
                metadata=ProjectMetadata.from_dict(migrated.get("metadata", {})),
                units=UnitSystem.from_dict(units_data, defaulted=units_defaulted),
                materials=MaterialDB.from_list(migrated.get("materials", [])).materials,
                geometry=[GeometryRef.from_dict(item) for item in migrated.get("geometry", [])],
                meshes=[MeshRef.from_dict(item) for item in migrated.get("meshes", [])],
                scripts=[ScriptRef.from_dict(item) for item in migrated.get("scripts", [])],
                boundary_curves=[
                    BoundaryCurve.from_dict(item)
                    for item in migrated.get("boundary_curves", [])
                ],
                physics=[PhysicsSetup.from_dict(item) for item in physics_payload],
                solvers=[SolverConfig.from_dict(item) for item in solver_payload],
                results=[ResultRef.from_dict(item) for item in migrated.get("results", [])],
                report=ReportConfig.from_dict(migrated.get("report")),
                plugins=[PluginRef.from_dict(item) for item in migrated.get("plugins", [])],
                warnings=[
                    ProjectWarning.from_dict(item) for item in migrated.get("warnings", [])
                ],
            )
        except (TypeError, ValueError) as exc:
            raise ProjectSchemaError(f"Invalid OSW project schema: {exc}") from exc

    @property
    def material_db(self) -> MaterialDB:
        return MaterialDB(self.materials)

    def validate(self) -> ValidationReport:
        report = ValidationReport()
        if not self.schema_version:
            report.add_error("schema_version", "Project schema_version is required.")
        report.extend(self.metadata.validate())
        report.extend(self.units.validate())
        report.extend(self.material_db.validate())
        for index, curve in enumerate(self.boundary_curves):
            report.extend(curve.validate(path=f"boundary_curves[{index}]"))
        _validate_project_references(self, report)
        return report

    def save(self, path: str | Path) -> None:
        from .project_io import save_project

        save_project(self, path)

    @classmethod
    def load(cls, path: str | Path) -> Project:
        from .project_io import load_project

        return load_project(path)


def load_project(path: str | Path) -> Project:
    return Project.load(path)


def migrate_project_data(data: Mapping[str, Any]) -> dict[str, Any]:
    migrated = dict(data)
    if "schema_version" not in migrated:
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    if migrated.get("schema_version") == "0.0":
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    if "units" not in migrated and "unit_system" in migrated:
        migrated["units"] = migrated["unit_system"]
    if "units" not in migrated:
        migrated["_units_defaulted"] = True
        migrated["units"] = UnitSystem.si().to_dict()
    for old_key, new_key in (
        ("geometry_refs", "geometry"),
        ("mesh_refs", "meshes"),
        ("script_refs", "scripts"),
        ("result_refs", "results"),
    ):
        if new_key not in migrated and old_key in migrated:
            migrated[new_key] = migrated[old_key]
    if isinstance(migrated.get("physics"), dict):
        migrated["physics"] = [migrated["physics"]]
    if "solvers" not in migrated and "solver_config" in migrated:
        migrated["solvers"] = [migrated["solver_config"]]
    return migrated


def project_to_dict(project: Project) -> dict[str, Any]:
    return project.to_dict()


def project_from_dict(data: object) -> Project:
    return Project.from_dict(data)


def _validate_project_references(project: Project, report: ValidationReport) -> None:
    material_ids = {material.material_id for material in project.materials if material.material_id}
    material_names = {material.name for material in project.materials if material.name}
    builtin = builtin_materials()
    builtin_ids = {material.material_id for material in builtin.materials}
    builtin_names = {material.name for material in builtin.materials}

    for index, geometry in enumerate(project.geometry):
        suffix = Path(geometry.path).suffix.lower()
        if suffix in NATIVE_COMMERCIAL_CAD_EXTENSIONS:
            report.add_warning(
                f"geometry[{index}].path",
                (
                    "OSW v0.1 supports standard exported formats; native commercial "
                    "CAD direct import is out of scope."
                ),
            )

    for index, mesh in enumerate(project.meshes):
        suffix = Path(mesh.path).suffix.lower()
        if suffix in NATIVE_COMMERCIAL_CAD_EXTENSIONS:
            report.add_warning(
                f"meshes[{index}].path",
                (
                    "OSW v0.1 supports standard/exported CAD and mesh formats. "
                    "Please export STEP/STL/OBJ or a supported mesh format."
                ),
            )

    if not project.meshes:
        report.add_warning("meshes", "No mesh references are registered.")
    if not project.results:
        report.add_warning("results", "No result references are registered.")

    for physics_index, setup in enumerate(project.physics):
        setup_path = f"physics[{physics_index}]"
        for material_ref in setup.materials:
            if material_ref in material_ids | material_names | builtin_ids | builtin_names:
                continue
            report.add_error(
                f"{setup_path}.materials",
                f"Physics setup references unknown material: {material_ref}",
            )
        for boundary_index, boundary in enumerate(setup.boundary_conditions):
            boundary_path = f"{setup_path}.boundary_conditions[{boundary_index}]"
            if not boundary.name:
                report.add_error(f"{boundary_path}.name", "Boundary condition name is required.")
            if not (boundary.type or boundary.kind):
                report.add_error(f"{boundary_path}.type", "Boundary condition type is required.")
            if not (boundary.value or boundary.values):
                report.add_error(
                    f"{boundary_path}.value",
                    "Boundary condition value is required.",
                )
        if setup.solver_config is not None:
            _validate_solver_config(setup.solver_config, report, path=f"{setup_path}.solver_config")

    for index, solver in enumerate(project.solvers):
        _validate_solver_config(solver, report, path=f"solvers[{index}]")

    for index, script in enumerate(project.scripts):
        if Path(script.path).suffix.lower() == ".m" and not script.safe_preview_required:
            report.add_warning(
                f"scripts[{index}].safe_preview_required",
                "MATLAB/Octave scripts require safe preview before execution.",
            )
        if Path(script.path).suffix.lower() == ".m":
            _validate_mscript_preview_metadata(script, report, path=f"scripts[{index}]")


def _validate_solver_config(
    solver: SolverConfig,
    report: ValidationReport,
    *,
    path: str,
) -> None:
    if not (solver.solver or solver.name):
        report.add_error(f"{path}.solver", "Solver name is required.")
    tolerance = _optional_float(solver.convergence_tolerance)
    if tolerance is None:
        report.add_error(
            f"{path}.convergence_tolerance",
            "Convergence tolerance must be numeric.",
        )
    elif tolerance <= 0:
        report.add_error(
            f"{path}.convergence_tolerance",
            "Convergence tolerance must be positive.",
        )


def _validate_mscript_preview_metadata(
    script: ScriptRef,
    report: ValidationReport,
    *,
    path: str,
) -> None:
    metadata = script.metadata if isinstance(script.metadata, dict) else {}
    preview_payload = metadata.get("preview")
    if not (preview_payload or metadata.get("safety_summary") or metadata.get("kind")):
        report.add_warning(
            f"{path}.metadata",
            "MATLAB/Octave script has not been previewed by the safety scanner yet.",
        )
        return

    findings = []
    if isinstance(preview_payload, dict):
        raw_findings = preview_payload.get("safety_findings", ())
        if isinstance(raw_findings, list | tuple):
            findings.extend(item for item in raw_findings if isinstance(item, dict))
    raw_findings = metadata.get("safety_findings", ())
    if isinstance(raw_findings, list | tuple):
        findings.extend(item for item in raw_findings if isinstance(item, dict))
    for finding in findings:
        severity = str(finding.get("severity", "")).lower()
        if severity in {"high", "blocked"}:
            report.add_warning(
                f"{path}.metadata.safety_findings",
                (
                    "MATLAB/Octave script preview contains high-risk or blocked "
                    f"safety finding: {finding.get('message', finding.get('token', 'script'))}"
                ),
            )


def _physics_list(value: Sequence[PhysicsSetup] | PhysicsSetup | None) -> list[PhysicsSetup]:
    if value is None:
        return []
    if isinstance(value, PhysicsSetup):
        return [value]
    return list(value)


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _slug(value: str) -> str:
    return value.strip().casefold().replace(" ", "-").replace("/", "-") or "solver"


def _loads(path: Path) -> dict[str, Any]:
    from .project_io import _load_mapping_from_path

    return _load_mapping_from_path(path)


def _dumps(path: Path, data: dict[str, Any]) -> str:
    if path.suffix.lower() == ".json":
        return f"{json.dumps(data, indent=2, sort_keys=True)}\n"
    from .project_io import _dump_mapping_for_path

    return _dump_mapping_for_path(path, data)
