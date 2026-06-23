"""Passive optional solver discovery result models.

The discovery model layer records presence evidence only. It does not execute
solver commands, import optional solver packages, or install dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .manifest_models import OptionalSolverHealthState
from .manifest_validation import OptionalSolverDiagnosticSeverity


class OptionalSolverPathRedactionMode(str, Enum):
    """Controls whether discovery reports include full local paths."""

    REDACTED = "redacted"
    FULL = "full"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverPathRedactionMode:
        if isinstance(value, cls):
            return value
        return cls(str(value))


@dataclass(frozen=True, slots=True)
class OptionalSolverDiscoveryOptions:
    """Options for passive optional solver discovery."""

    path_redaction: OptionalSolverPathRedactionMode = (
        OptionalSolverPathRedactionMode.REDACTED
    )
    include_environment_values: bool = False
    generated_at: str = ""
    source: str = "passive_optional_solver_discovery"


@dataclass(frozen=True, slots=True)
class OptionalSolverDiscoveryDiagnostic:
    """Diagnostic emitted by passive optional solver discovery."""

    code: str
    severity: OptionalSolverDiagnosticSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OptionalSolverDiscoveryDiagnostic:
        return cls(
            code=str(data.get("code", "")),
            severity=OptionalSolverDiagnosticSeverity(str(data.get("severity", "info"))),
            message=str(data.get("message", "")),
            path=str(data.get("path", "")),
            suggested_fix=str(data.get("suggested_fix", "")),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverExecutableDiscovery:
    """Presence evidence for one executable requirement."""

    identifier: str
    display_name: str = ""
    required: bool = True
    found: bool = False
    path: str = ""
    redacted_path: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OptionalSolverExecutableDiscovery:
        return cls(
            identifier=str(data.get("identifier", "")),
            display_name=str(data.get("display_name", "")),
            required=bool(data.get("required", True)),
            found=bool(data.get("found", False)),
            path=str(data.get("path", "")),
            redacted_path=str(data.get("redacted_path", "")),
            notes=_tuple(data.get("notes")),
        )

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(
            {
                "identifier": self.identifier,
                "display_name": self.display_name,
                "required": self.required,
                "found": self.found,
                "path": self.path,
                "redacted_path": self.redacted_path,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverPythonPackageDiscovery:
    """Presence evidence for one Python package requirement."""

    identifier: str
    display_name: str = ""
    required: bool = True
    found: bool = False
    version: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> OptionalSolverPythonPackageDiscovery:
        return cls(
            identifier=str(data.get("identifier", "")),
            display_name=str(data.get("display_name", "")),
            required=bool(data.get("required", True)),
            found=bool(data.get("found", False)),
            version=str(data.get("version", "")),
            notes=_tuple(data.get("notes")),
        )

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(
            {
                "identifier": self.identifier,
                "display_name": self.display_name,
                "required": self.required,
                "found": self.found,
                "version": self.version,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverEnvironmentHintDiscovery:
    """Presence evidence for one environment-variable hint."""

    name: str
    present: bool = False
    value: str = ""
    redacted_value: str = ""

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> OptionalSolverEnvironmentHintDiscovery:
        return cls(
            name=str(data.get("name", "")),
            present=bool(data.get("present", False)),
            value=str(data.get("value", "")),
            redacted_value=str(data.get("redacted_value", "")),
        )

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(
            {
                "name": self.name,
                "present": self.present,
                "value": self.value,
                "redacted_value": self.redacted_value,
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverStackDiscovery:
    """Passive discovery report for one optional solver stack."""

    stack_id: str
    display_name: str
    related_issue: int | None
    health_state: OptionalSolverHealthState
    executables: tuple[OptionalSolverExecutableDiscovery, ...] = field(
        default_factory=tuple
    )
    python_packages: tuple[OptionalSolverPythonPackageDiscovery, ...] = field(
        default_factory=tuple
    )
    environment_hints: tuple[OptionalSolverEnvironmentHintDiscovery, ...] = field(
        default_factory=tuple
    )
    diagnostics: tuple[OptionalSolverDiscoveryDiagnostic, ...] = field(
        default_factory=tuple
    )
    manifest_valid: bool = True
    confidence: str = "none"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OptionalSolverStackDiscovery:
        return cls(
            stack_id=str(data.get("stack_id", "")),
            display_name=str(data.get("display_name", "")),
            related_issue=_optional_int(data.get("related_issue")),
            health_state=OptionalSolverHealthState.from_value(
                data.get("health_state", OptionalSolverHealthState.UNKNOWN.value)
            ),
            executables=tuple(
                OptionalSolverExecutableDiscovery.from_dict(item)
                for item in _sequence(data.get("executables"))
            ),
            python_packages=tuple(
                OptionalSolverPythonPackageDiscovery.from_dict(item)
                for item in _sequence(data.get("python_packages"))
            ),
            environment_hints=tuple(
                OptionalSolverEnvironmentHintDiscovery.from_dict(item)
                for item in _sequence(data.get("environment_hints"))
            ),
            diagnostics=tuple(
                OptionalSolverDiscoveryDiagnostic.from_dict(item)
                for item in _sequence(data.get("diagnostics"))
            ),
            manifest_valid=bool(data.get("manifest_valid", True)),
            confidence=str(data.get("confidence", "none")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "stack_id": self.stack_id,
            "display_name": self.display_name,
            "related_issue": self.related_issue,
            "health_state": self.health_state.value,
            "executables": [item.to_dict() for item in self.executables],
            "python_packages": [item.to_dict() for item in self.python_packages],
            "environment_hints": [item.to_dict() for item in self.environment_hints],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "manifest_valid": self.manifest_valid,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverDiscoveryReport:
    """Serializable passive discovery report for one or more stacks."""

    stacks: tuple[OptionalSolverStackDiscovery, ...]
    generated_at: str = ""
    source: str = "passive_optional_solver_discovery"
    diagnostics: tuple[OptionalSolverDiscoveryDiagnostic, ...] = field(
        default_factory=tuple
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OptionalSolverDiscoveryReport:
        return cls(
            generated_at=str(data.get("generated_at", "")),
            source=str(data.get("source", "passive_optional_solver_discovery")),
            stacks=tuple(
                OptionalSolverStackDiscovery.from_dict(item)
                for item in _sequence(data.get("stacks"))
            ),
            diagnostics=tuple(
                OptionalSolverDiscoveryDiagnostic.from_dict(item)
                for item in _sequence(data.get("diagnostics"))
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "source": self.source,
            "stacks": [item.to_dict() for item in self.stacks],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def optional_solver_discovery_report_to_dict(
    report: OptionalSolverDiscoveryReport,
) -> dict[str, object]:
    """Serialize a passive discovery report to a JSON-compatible mapping."""

    return report.to_dict()


def optional_solver_discovery_report_from_dict(
    data: Mapping[str, Any],
) -> OptionalSolverDiscoveryReport:
    """Parse a passive discovery report from a JSON-compatible mapping."""

    return OptionalSolverDiscoveryReport.from_dict(data)


def _tuple(value: object) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    return (str(value),)


def _sequence(value: object) -> tuple[Mapping[str, Any], ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, list | tuple):
        return tuple(item for item in value if isinstance(item, Mapping))
    if isinstance(value, Mapping):
        return (value,)
    return ()


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _drop_empty(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if value not in ("", None, [], (), {})
    }
