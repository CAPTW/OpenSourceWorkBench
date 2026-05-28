"""Serializable OpenFOAM template, run, and residual models."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.solvers.runner import RunResult


class OpenFOAMTemplateKind(StrEnum):
    CAVITY = "cavity"
    DUCT = "duct"
    UNKNOWN = "unknown"


class OpenFOAMSolverKind(StrEnum):
    ICOFOAM = "icoFoam"
    SIMPLEFOAM = "simpleFoam"
    FOAMRUN_PLACEHOLDER = "foamRun_placeholder"


class OpenFOAMBoundaryType(StrEnum):
    FIXED_VALUE = "fixedValue"
    ZERO_GRADIENT = "zeroGradient"
    NO_SLIP = "noSlip"
    MOVING_WALL_VELOCITY = "movingWallVelocity"
    PRESSURE_OUTLET = "pressureOutlet"
    VELOCITY_INLET = "velocityInlet"
    EMPTY = "empty"
    WALL = "wall"
    UNKNOWN = "unknown"


class OpenFOAMRunStatus(StrEnum):
    READY = "ready"
    MISSING_EXECUTABLE = "missing_executable"
    MISSING_CASE = "missing_case"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OpenFOAMBoundaryPatch:
    name: str
    boundary_type: str
    field_values: dict[str, Any] = field(default_factory=dict)
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "boundary_type": self.boundary_type,
            "field_values": dict(self.field_values),
            "role": self.role,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMBoundaryPatch:
        return cls(
            name=str(data.get("name", "")),
            boundary_type=str(data.get("boundary_type", "")),
            field_values=dict(data.get("field_values", {}) or {}),
            role=str(data.get("role", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMTransportProperties:
    nu: float = 1.0e-5
    rho: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"nu": self.nu, "rho": self.rho, "metadata": dict(self.metadata)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMTransportProperties:
        rho = data.get("rho")
        return cls(
            nu=float(data.get("nu", 1.0e-5)),
            rho=float(rho) if rho not in (None, "") else None,
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMControlSettings:
    start_time: float = 0.0
    end_time: float = 1.0
    delta_t: float = 0.005
    write_interval: float = 0.1
    purge_write: int | None = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "delta_t": self.delta_t,
            "write_interval": self.write_interval,
            "purge_write": self.purge_write,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMControlSettings:
        purge_write = data.get("purge_write", 0)
        return cls(
            start_time=float(data.get("start_time", 0.0)),
            end_time=float(data.get("end_time", 1.0)),
            delta_t=float(data.get("delta_t", 0.005)),
            write_interval=float(data.get("write_interval", 0.1)),
            purge_write=int(purge_write) if purge_write not in (None, "") else None,
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMCaseRequest:
    template_kind: str
    solver: str
    case_name: str
    output_dir: Path
    dimensions: dict[str, float] = field(default_factory=dict)
    mesh_settings: dict[str, Any] = field(default_factory=dict)
    boundaries: tuple[OpenFOAMBoundaryPatch, ...] = field(default_factory=tuple)
    transport: OpenFOAMTransportProperties = field(default_factory=OpenFOAMTransportProperties)
    control: OpenFOAMControlSettings = field(default_factory=OpenFOAMControlSettings)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        template_kind: str | OpenFOAMTemplateKind = OpenFOAMTemplateKind.CAVITY,
        solver: str | OpenFOAMSolverKind = OpenFOAMSolverKind.ICOFOAM,
        case_name: str = "cavity",
        output_dir: str | Path = ".",
        dimensions: Mapping[str, float] | None = None,
        mesh_settings: Mapping[str, Any] | None = None,
        boundaries: Iterable[OpenFOAMBoundaryPatch] = (),
        transport: OpenFOAMTransportProperties | None = None,
        control: OpenFOAMControlSettings | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "template_kind", _enum_value(template_kind))
        object.__setattr__(self, "solver", _enum_value(solver))
        object.__setattr__(self, "case_name", str(case_name))
        object.__setattr__(self, "output_dir", Path(output_dir))
        object.__setattr__(self, "dimensions", dict(dimensions or {}))
        object.__setattr__(self, "mesh_settings", dict(mesh_settings or {}))
        object.__setattr__(self, "boundaries", tuple(boundaries))
        object.__setattr__(self, "transport", transport or OpenFOAMTransportProperties())
        object.__setattr__(self, "control", control or OpenFOAMControlSettings())
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_kind": self.template_kind,
            "solver": self.solver,
            "case_name": self.case_name,
            "output_dir": str(self.output_dir),
            "dimensions": dict(self.dimensions),
            "mesh_settings": dict(self.mesh_settings),
            "boundaries": [patch.to_dict() for patch in self.boundaries],
            "transport": self.transport.to_dict(),
            "control": self.control.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMCaseRequest:
        return cls(
            template_kind=str(data.get("template_kind", OpenFOAMTemplateKind.CAVITY.value)),
            solver=str(data.get("solver", OpenFOAMSolverKind.ICOFOAM.value)),
            case_name=str(data.get("case_name", "cavity")),
            output_dir=Path(str(data.get("output_dir", "."))),
            dimensions=dict(data.get("dimensions", {}) or {}),
            mesh_settings=dict(data.get("mesh_settings", {}) or {}),
            boundaries=tuple(
                OpenFOAMBoundaryPatch.from_dict(dict(item))
                for item in data.get("boundaries", ()) or ()
                if isinstance(item, Mapping)
            ),
            transport=OpenFOAMTransportProperties.from_dict(
                dict(data.get("transport", {}) or {})
            ),
            control=OpenFOAMControlSettings.from_dict(dict(data.get("control", {}) or {})),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMCaseResult:
    status: str
    request: OpenFOAMCaseRequest
    case_dir: Path
    generated_files: tuple[Path, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request": self.request.to_dict(),
            "case_dir": str(self.case_dir),
            "generated_files": [str(path) for path in self.generated_files],
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class OpenFOAMRunPolicy:
    timeout_seconds: float = 60.0
    kill_grace_seconds: float = 1.0
    isolate_case_dir: bool = True
    copy_case: bool = True
    artifact_patterns: tuple[str, ...] = (
        "log.*",
        "postProcessing/**",
        "system/*",
        "constant/*",
        "0/*",
        "[1-9]*/*",
    )
    env_overrides: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "kill_grace_seconds": self.kill_grace_seconds,
            "isolate_case_dir": self.isolate_case_dir,
            "copy_case": self.copy_case,
            "artifact_patterns": list(self.artifact_patterns),
            "env_overrides": dict(self.env_overrides),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMRunPolicy:
        return cls(
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            kill_grace_seconds=float(data.get("kill_grace_seconds", 1.0)),
            isolate_case_dir=bool(data.get("isolate_case_dir", True)),
            copy_case=bool(data.get("copy_case", True)),
            artifact_patterns=tuple(
                str(item) for item in data.get("artifact_patterns", cls().artifact_patterns)
            ),
            env_overrides={
                str(key): str(value)
                for key, value in dict(data.get("env_overrides", {}) or {}).items()
            },
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMRunRequest:
    case_dir: Path
    solver: str = OpenFOAMSolverKind.ICOFOAM.value
    run_id: str = ""
    policy: OpenFOAMRunPolicy = field(default_factory=OpenFOAMRunPolicy)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        case_dir: str | Path,
        solver: str | OpenFOAMSolverKind = OpenFOAMSolverKind.ICOFOAM,
        *,
        run_id: str = "",
        policy: OpenFOAMRunPolicy | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "case_dir", Path(case_dir))
        object.__setattr__(self, "solver", _enum_value(solver))
        object.__setattr__(self, "run_id", str(run_id))
        object.__setattr__(self, "policy", policy or OpenFOAMRunPolicy())
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_dir": str(self.case_dir),
            "solver": self.solver,
            "run_id": self.run_id,
            "policy": self.policy.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMRunRequest:
        return cls(
            case_dir=Path(str(data.get("case_dir", "."))),
            solver=str(data.get("solver", OpenFOAMSolverKind.ICOFOAM.value)),
            run_id=str(data.get("run_id", "")),
            policy=OpenFOAMRunPolicy.from_dict(dict(data.get("policy", {}) or {})),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMResidualSeries:
    field: str
    values: tuple[float, ...]
    iterations: tuple[int, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "values": list(self.values),
            "iterations": list(self.iterations),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMResidualSeries:
        return cls(
            field=str(data.get("field", "")),
            values=tuple(float(item) for item in data.get("values", ()) or ()),
            iterations=tuple(int(item) for item in data.get("iterations", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMResidualSummary:
    series: tuple[OpenFOAMResidualSeries, ...] = field(default_factory=tuple)
    final_residuals: dict[str, float] = field(default_factory=dict)
    initial_residuals: dict[str, float] = field(default_factory=dict)
    iteration_count: int = 0
    converged: bool | None = None
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "series": [item.to_dict() for item in self.series],
            "final_residuals": dict(self.final_residuals),
            "initial_residuals": dict(self.initial_residuals),
            "iteration_count": self.iteration_count,
            "converged": self.converged,
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMResidualSummary:
        converged = data.get("converged")
        return cls(
            series=tuple(
                OpenFOAMResidualSeries.from_dict(dict(item))
                for item in data.get("series", ()) or ()
                if isinstance(item, Mapping)
            ),
            final_residuals={
                str(key): float(value)
                for key, value in dict(data.get("final_residuals", {}) or {}).items()
            },
            initial_residuals={
                str(key): float(value)
                for key, value in dict(data.get("initial_residuals", {}) or {}).items()
            },
            iteration_count=int(data.get("iteration_count", 0)),
            converged=bool(converged) if converged is not None else None,
            diagnostics=DiagnosticReport.from_dict(dict(data.get("diagnostics", {}) or {})),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OpenFOAMRunResult:
    run_id: str
    status: OpenFOAMRunStatus
    case_dir: Path
    solver: str
    command: tuple[str, ...] = field(default_factory=tuple)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    elapsed_seconds: float = 0.0
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    run_result: RunResult | None = None
    residual_summary: OpenFOAMResidualSummary | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def combined_log(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr) if part)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "case_dir": str(self.case_dir),
            "solver": self.solver,
            "command": list(self.command),
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "elapsed_seconds": self.elapsed_seconds,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": self.diagnostics.to_dict(),
            "run_result": self.run_result.to_dict() if self.run_result else None,
            "residual_summary": (
                self.residual_summary.to_dict() if self.residual_summary else None
            ),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpenFOAMRunResult:
        run_result_data = data.get("run_result")
        residual_data = data.get("residual_summary")
        return cls(
            run_id=str(data.get("run_id", "")),
            status=OpenFOAMRunStatus(str(data.get("status", OpenFOAMRunStatus.FAILED.value))),
            case_dir=Path(str(data.get("case_dir", "."))),
            solver=str(data.get("solver", "")),
            command=tuple(str(item) for item in data.get("command", ()) or ()),
            return_code=(
                int(data["return_code"])
                if data.get("return_code") not in (None, "")
                else None
            ),
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
            artifacts=tuple(
                RunArtifact.from_dict(dict(item))
                for item in data.get("artifacts", ()) or ()
                if isinstance(item, Mapping)
            ),
            diagnostics=DiagnosticReport.from_dict(dict(data.get("diagnostics", {}) or {})),
            run_result=(
                RunResult.from_dict(dict(run_result_data))
                if isinstance(run_result_data, Mapping)
                else None
            ),
            residual_summary=(
                OpenFOAMResidualSummary.from_dict(dict(residual_data))
                if isinstance(residual_data, Mapping)
                else None
            ),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def _enum_value(value: object) -> str:
    enum_value = getattr(value, "value", None)
    return str(enum_value if enum_value is not None else value)
