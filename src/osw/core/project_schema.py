"""Project schema contracts and serialization helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .boundary_curve import BoundaryCurve
from .materials import Material, MaterialDB
from .units import UnitSystem
from .validation import ProjectSchemaError, ValidationReport

CURRENT_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True)
class ProjectMetadata:
    name: str
    description: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "tags": list(self.tags),
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
        )

    def validate(self) -> ValidationReport:
        report = ValidationReport()
        if not self.name:
            report.add_error("metadata.name", "Project metadata name is required.")
        return report


@dataclass(frozen=True)
class GeometryRef:
    ref_id: str
    path: str
    format: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _ref_to_dict(self)

    @classmethod
    def from_dict(cls, data: object) -> GeometryRef:
        return _ref_from_dict(cls, data)


@dataclass(frozen=True)
class MeshRef:
    ref_id: str
    path: str
    format: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _ref_to_dict(self)

    @classmethod
    def from_dict(cls, data: object) -> MeshRef:
        return _ref_from_dict(cls, data)


@dataclass(frozen=True)
class ScriptRef:
    ref_id: str
    path: str
    language: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref_id": self.ref_id,
            "path": self.path,
            "language": self.language,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ScriptRef:
        if not isinstance(data, dict):
            msg = "Script reference must be a mapping."
            raise ValueError(msg)
        return cls(
            ref_id=str(data.get("ref_id", "")),
            path=str(data.get("path", "")),
            language=str(data.get("language", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class BoundaryCondition:
    name: str
    kind: str
    target: str
    values: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "target": self.target,
            "values": dict(self.values),
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryCondition:
        if not isinstance(data, dict):
            msg = "Boundary condition must be a mapping."
            raise ValueError(msg)
        return cls(
            name=str(data.get("name", "")),
            kind=str(data.get("kind", "")),
            target=str(data.get("target", "")),
            values=dict(data.get("values", {})),
        )


@dataclass(frozen=True)
class PhysicsSetup:
    setup_id: str
    name: str
    analysis_type: str
    boundary_conditions: list[BoundaryCondition] = field(default_factory=list)
    material_assignments: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "setup_id": self.setup_id,
            "name": self.name,
            "analysis_type": self.analysis_type,
            "boundary_conditions": [item.to_dict() for item in self.boundary_conditions],
            "material_assignments": dict(self.material_assignments),
        }

    @classmethod
    def from_dict(cls, data: object) -> PhysicsSetup:
        if not isinstance(data, dict):
            msg = "Physics setup must be a mapping."
            raise ValueError(msg)
        return cls(
            setup_id=str(data.get("setup_id", "")),
            name=str(data.get("name", "")),
            analysis_type=str(data.get("analysis_type", "")),
            boundary_conditions=[
                BoundaryCondition.from_dict(item)
                for item in data.get("boundary_conditions", [])
            ],
            material_assignments=dict(data.get("material_assignments", {})),
        )


@dataclass(frozen=True)
class SolverConfig:
    solver_id: str
    name: str
    execution_mode: str = "prepare_only"
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "solver_id": self.solver_id,
            "name": self.name,
            "execution_mode": self.execution_mode,
            "parameters": dict(self.parameters),
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
        )


@dataclass(frozen=True)
class ResultRef:
    ref_id: str
    path: str
    kind: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref_id": self.ref_id,
            "path": self.path,
            "kind": self.kind,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultRef:
        if not isinstance(data, dict):
            msg = "Result reference must be a mapping."
            raise ValueError(msg)
        return cls(
            ref_id=str(data.get("ref_id", "")),
            path=str(data.get("path", "")),
            kind=str(data.get("kind", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class ReportConfig:
    path: str = "reports/report.html"
    title: str = "OSW Report"
    include_validation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "include_validation": self.include_validation,
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
        )


@dataclass(frozen=True)
class Project:
    metadata: ProjectMetadata
    units: UnitSystem = field(default_factory=UnitSystem.si)
    materials: list[Material] = field(default_factory=list)
    geometry: list[GeometryRef] = field(default_factory=list)
    meshes: list[MeshRef] = field(default_factory=list)
    scripts: list[ScriptRef] = field(default_factory=list)
    boundary_curves: list[BoundaryCurve] = field(default_factory=list)
    physics: list[PhysicsSetup] = field(default_factory=list)
    solvers: list[SolverConfig] = field(default_factory=list)
    results: list[ResultRef] = field(default_factory=list)
    report: ReportConfig = field(default_factory=ReportConfig)
    schema_version: str = CURRENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "metadata": self.metadata.to_dict(),
            "units": self.units.to_dict(),
            "materials": [material.to_dict() for material in self.materials],
            "geometry": [item.to_dict() for item in self.geometry],
            "meshes": [item.to_dict() for item in self.meshes],
            "scripts": [item.to_dict() for item in self.scripts],
            "boundary_curves": [item.to_dict() for item in self.boundary_curves],
            "physics": [item.to_dict() for item in self.physics],
            "solvers": [item.to_dict() for item in self.solvers],
            "results": [item.to_dict() for item in self.results],
            "report": self.report.to_dict(),
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

        units_key = "units" if "units" in migrated else "unit_system"
        units_defaulted = units_key not in migrated
        units_data = migrated.get(units_key, UnitSystem.si().to_dict())

        try:
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
                physics=[PhysicsSetup.from_dict(item) for item in migrated.get("physics", [])],
                solvers=[SolverConfig.from_dict(item) for item in migrated.get("solvers", [])],
                results=[ResultRef.from_dict(item) for item in migrated.get("results", [])],
                report=ReportConfig.from_dict(migrated.get("report")),
            )
        except (TypeError, ValueError) as exc:
            raise ProjectSchemaError(f"Invalid OSW project schema: {exc}") from exc

    @property
    def material_db(self) -> MaterialDB:
        return MaterialDB(self.materials)

    def validate(self) -> ValidationReport:
        report = ValidationReport()
        report.extend(self.metadata.validate())
        report.extend(self.units.validate())
        report.extend(self.material_db.validate())
        for index, curve in enumerate(self.boundary_curves):
            report.extend(curve.validate(path=f"boundary_curves[{index}]"))
        return report

    def save(self, path: str | Path) -> None:
        target = Path(path)
        text = _dumps(target, self.to_dict())
        target.write_text(text, encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Project:
        source = Path(path)
        data = _loads(source)
        return cls.from_dict(data)


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
    return migrated


def _ref_to_dict(ref: GeometryRef | MeshRef) -> dict[str, Any]:
    return {
        "ref_id": ref.ref_id,
        "path": ref.path,
        "format": ref.format,
        "metadata": dict(ref.metadata),
    }


def _ref_from_dict(cls: type[GeometryRef] | type[MeshRef], data: object) -> Any:
    if not isinstance(data, dict):
        msg = "Reference must be a mapping."
        raise ValueError(msg)
    return cls(
        ref_id=str(data.get("ref_id", "")),
        path=str(data.get("path", "")),
        format=str(data.get("format", "")),
        metadata=dict(data.get("metadata", {})),
    )


def _loads(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProjectSchemaError(f"Could not read project file {path}: {exc}") from exc

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            data = _loads_yaml(text)
    except Exception as exc:
        raise ProjectSchemaError(f"Could not parse project file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ProjectSchemaError(f"Project file {path} must contain a mapping.")
    return data


def _loads_yaml(text: str) -> Any:
    try:
        import yaml
    except ModuleNotFoundError:
        return json.loads(text)
    return yaml.safe_load(text)


def _dumps(path: Path, data: dict[str, Any]) -> str:
    if path.suffix.lower() == ".json":
        return f"{json.dumps(data, indent=2, sort_keys=True)}\n"

    try:
        import yaml
    except ModuleNotFoundError:
        return f"{json.dumps(data, indent=2, sort_keys=True)}\n"
    return yaml.safe_dump(data, sort_keys=False)
