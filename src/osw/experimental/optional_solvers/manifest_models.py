"""Declarative optional solver manifest models.

This schema layer describes optional solver and science stacks. It does not
discover executables, import optional packages, install dependencies, or run
solver health checks.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OptionalSolverStackId(str, Enum):
    """Known built-in optional solver stack identifiers."""

    GMSH = "gmsh"
    OCTAVE = "octave"
    CALCULIX = "calculix"
    OPENFOAM = "openfoam"
    COOLPROP_CANTERA = "coolprop_cantera"
    PYVISTA_MESHIO = "pyvista_meshio"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverStackId:
        if isinstance(value, cls):
            return value
        return cls(str(value))


class OptionalSolverHealthState(str, Enum):
    """Declarative health states for future optional solver UX."""

    UNKNOWN = "unknown"
    MISSING = "missing"
    PARTIALLY_INSTALLED = "partially_installed"
    DISCOVERED = "discovered"
    SMOKE_PASSED = "smoke_passed"
    SMOKE_FAILED = "smoke_failed"
    BLOCKED_NO_SAFE_CASE = "blocked_no_safe_case"
    UNSUPPORTED_PLATFORM = "unsupported_platform"
    SKIPPED_BY_USER = "skipped_by_user"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverHealthState:
        if isinstance(value, cls):
            return value
        return cls(str(value))


class OptionalSolverSupportStatus(str, Enum):
    """Support status for an optional solver manifest."""

    EXPERIMENTAL = "experimental"
    PLANNED = "planned"
    SUPPORTED_OPTIONAL = "supported_optional"
    DEPRECATED = "deprecated"
    UNSUPPORTED = "unsupported"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverSupportStatus:
        if isinstance(value, cls):
            return value
        return cls(str(value))


@dataclass(frozen=True, slots=True)
class OptionalSolverCapability:
    """Capability declared by an optional solver or science stack."""

    capability_id: str
    description: str

    @classmethod
    def from_dict(cls, data: object) -> OptionalSolverCapability:
        if isinstance(data, str):
            return cls(capability_id=data, description="")
        payload = _mapping(data, "capability")
        return cls(
            capability_id=_string(payload.get("capability_id") or payload.get("id")),
            description=_string(payload.get("description")),
        )

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(
            {
                "capability_id": self.capability_id,
                "description": self.description,
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverRequirement:
    """Executable or Python-package requirement declared by a manifest."""

    identifier: str
    display_name: str = ""
    required: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: object) -> OptionalSolverRequirement:
        if isinstance(data, str):
            return cls(identifier=data)
        payload = _mapping(data, "requirement")
        return cls(
            identifier=_string(payload.get("identifier") or payload.get("id")),
            display_name=_string(payload.get("display_name") or payload.get("name")),
            required=bool(payload.get("required", True)),
            notes=_string_tuple(payload.get("notes")),
        )

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(
            {
                "identifier": self.identifier,
                "display_name": self.display_name,
                "required": self.required,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverProbe:
    """Declarative probe command.

    Probe commands are metadata only. This model never executes them.
    """

    name: str
    command: tuple[str, ...]
    description: str = ""

    @classmethod
    def from_dict(cls, data: object) -> OptionalSolverProbe:
        payload = _mapping(data, "probe")
        return cls(
            name=_string(payload.get("name")),
            command=_string_tuple(payload.get("command")),
            description=_string(payload.get("description")),
        )

    def to_dict(self) -> dict[str, object]:
        return _drop_empty(
            {
                "name": self.name,
                "command": list(self.command),
                "description": self.description,
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverManifest:
    """Declarative manifest for an optional solver or science stack."""

    stack_id: str
    display_name: str
    related_issue: int | None
    capabilities: tuple[OptionalSolverCapability, ...]
    executable_requirements: tuple[OptionalSolverRequirement, ...] = field(
        default_factory=tuple
    )
    python_package_requirements: tuple[OptionalSolverRequirement, ...] = field(
        default_factory=tuple
    )
    environment_variable_hints: tuple[str, ...] = field(default_factory=tuple)
    version_probe: OptionalSolverProbe | None = None
    help_probe: OptionalSolverProbe | None = None
    smoke_test_description: str = ""
    prepared_machine_notes: tuple[str, ...] = field(default_factory=tuple)
    platform_notes: tuple[str, ...] = field(default_factory=tuple)
    documentation_refs: tuple[str, ...] = field(default_factory=tuple)
    support_status: OptionalSolverSupportStatus = OptionalSolverSupportStatus.EXPERIMENTAL
    non_bundled_disclaimer: str = ""
    safety_notes: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OptionalSolverManifest:
        payload = _mapping(data, "optional solver manifest")
        return cls(
            stack_id=_string(payload.get("stack_id")),
            display_name=_string(payload.get("display_name")),
            related_issue=_optional_int(payload.get("related_issue")),
            capabilities=_capabilities(payload.get("capabilities")),
            executable_requirements=_requirements(
                payload.get("executable_requirements")
            ),
            python_package_requirements=_requirements(
                payload.get("python_package_requirements")
            ),
            environment_variable_hints=_string_tuple(
                payload.get("environment_variable_hints")
            ),
            version_probe=_optional_probe(payload.get("version_probe")),
            help_probe=_optional_probe(payload.get("help_probe")),
            smoke_test_description=_string(payload.get("smoke_test_description")),
            prepared_machine_notes=_string_tuple(payload.get("prepared_machine_notes")),
            platform_notes=_string_tuple(payload.get("platform_notes")),
            documentation_refs=_string_tuple(payload.get("documentation_refs")),
            support_status=_support_status(payload.get("support_status")),
            non_bundled_disclaimer=_string(payload.get("non_bundled_disclaimer")),
            safety_notes=_string_tuple(payload.get("safety_notes")),
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "stack_id": self.stack_id,
            "display_name": self.display_name,
            "related_issue": self.related_issue,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "executable_requirements": [
                item.to_dict() for item in self.executable_requirements
            ],
            "python_package_requirements": [
                item.to_dict() for item in self.python_package_requirements
            ],
            "environment_variable_hints": list(self.environment_variable_hints),
            "smoke_test_description": self.smoke_test_description,
            "prepared_machine_notes": list(self.prepared_machine_notes),
            "platform_notes": list(self.platform_notes),
            "documentation_refs": list(self.documentation_refs),
            "support_status": self.support_status.value,
            "non_bundled_disclaimer": self.non_bundled_disclaimer,
            "safety_notes": list(self.safety_notes),
        }
        if self.version_probe is not None:
            payload["version_probe"] = self.version_probe.to_dict()
        if self.help_probe is not None:
            payload["help_probe"] = self.help_probe.to_dict()
        return payload


def parse_optional_solver_manifest_dict(
    data: Mapping[str, Any],
) -> OptionalSolverManifest:
    """Parse a manifest mapping into an optional solver manifest model."""

    return OptionalSolverManifest.from_dict(data)


def explain_optional_solver_manifest(manifest: OptionalSolverManifest) -> str:
    """Return a short human-readable manifest summary."""

    requirement_count = len(manifest.executable_requirements) + len(
        manifest.python_package_requirements
    )
    issue = f"#{manifest.related_issue}" if manifest.related_issue is not None else "none"
    return (
        f"{manifest.display_name} ({manifest.stack_id}) declares "
        f"{len(manifest.capabilities)} capabilities and {requirement_count} "
        f"requirements for issue {issue}. The manifest is declarative only: "
        "it does not install dependencies, bundle solvers, or execute probes."
    )


def _mapping(data: object, name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        msg = f"{name} must be a mapping."
        raise ValueError(msg)
    return data


def _string(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _string_tuple(value: object) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value)
    return (str(value),)


def _capabilities(value: object) -> tuple[OptionalSolverCapability, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(OptionalSolverCapability.from_dict(item) for item in value)
    return (OptionalSolverCapability.from_dict(value),)


def _requirements(value: object) -> tuple[OptionalSolverRequirement, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(OptionalSolverRequirement.from_dict(item) for item in value)
    return (OptionalSolverRequirement.from_dict(value),)


def _optional_probe(value: object) -> OptionalSolverProbe | None:
    if value in (None, ""):
        return None
    return OptionalSolverProbe.from_dict(value)


def _support_status(value: object) -> OptionalSolverSupportStatus:
    if value in (None, ""):
        return OptionalSolverSupportStatus.EXPERIMENTAL
    return OptionalSolverSupportStatus.from_value(value)


def _drop_empty(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if value not in ("", None, [], (), {})
    }
