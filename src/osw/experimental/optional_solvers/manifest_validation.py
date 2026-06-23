"""Structural validation for optional solver manifests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .manifest_models import (
    OptionalSolverManifest,
    OptionalSolverProbe,
    OptionalSolverStackId,
    parse_optional_solver_manifest_dict,
)


class OptionalSolverDiagnosticSeverity(str, Enum):
    """Severity values emitted by optional solver manifest validation."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


@dataclass(frozen=True, slots=True)
class OptionalSolverManifestDiagnostic:
    """A structural manifest validation diagnostic."""

    code: str
    severity: OptionalSolverDiagnosticSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverManifestValidationReport:
    """Validation report for one optional solver manifest."""

    stack_id: str
    diagnostics: tuple[OptionalSolverManifestDiagnostic, ...] = ()

    @property
    def has_errors(self) -> bool:
        return any(
            item.severity
            in {
                OptionalSolverDiagnosticSeverity.ERROR,
                OptionalSolverDiagnosticSeverity.BLOCKER,
            }
            for item in self.diagnostics
        )

    @property
    def has_blockers(self) -> bool:
        return any(
            item.severity == OptionalSolverDiagnosticSeverity.BLOCKER
            for item in self.diagnostics
        )

    @property
    def is_valid(self) -> bool:
        return not self.has_errors

    def to_dict(self) -> dict[str, object]:
        return {
            "stack_id": self.stack_id,
            "is_valid": self.is_valid,
            "has_errors": self.has_errors,
            "has_blockers": self.has_blockers,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


_BUILTIN_ISSUE_BY_STACK = {
    OptionalSolverStackId.GMSH.value: 6,
    OptionalSolverStackId.OCTAVE.value: 7,
    OptionalSolverStackId.CALCULIX.value: 8,
    OptionalSolverStackId.OPENFOAM.value: 9,
    OptionalSolverStackId.COOLPROP_CANTERA.value: 10,
    OptionalSolverStackId.PYVISTA_MESHIO.value: 11,
}
_REQUIRED_FIELDS = {
    "stack_id",
    "display_name",
    "related_issue",
    "capabilities",
    "smoke_test_description",
    "prepared_machine_notes",
    "documentation_refs",
    "support_status",
    "non_bundled_disclaimer",
    "safety_notes",
}
_INSTALLER_PHRASES = (
    "pip install",
    "conda install",
    "apt install",
    "apt-get install",
    "choco install",
    "winget install",
    "brew install",
    "sudo ",
    "curl ",
    "wget ",
)


def validate_optional_solver_manifest(
    manifest: OptionalSolverManifest | Mapping[str, Any],
) -> OptionalSolverManifestValidationReport:
    """Validate a manifest structurally without running probes."""

    diagnostics: list[OptionalSolverManifestDiagnostic] = []
    raw: Mapping[str, Any] | None = manifest if isinstance(manifest, Mapping) else None
    if raw is not None:
        diagnostics.extend(_validate_raw_mapping(raw))
        stack_id = str(raw.get("stack_id", ""))
        try:
            parsed = parse_optional_solver_manifest_dict(raw)
        except Exception as exc:  # noqa: BLE001 - surface parse shape as diagnostics.
            diagnostics.append(
                _diagnostic(
                    "OSM_PARSE_FAILED",
                    OptionalSolverDiagnosticSeverity.BLOCKER,
                    f"Manifest could not be parsed: {exc}",
                    "",
                    "Provide a JSON object matching the optional solver manifest schema.",
                )
            )
            return OptionalSolverManifestValidationReport(
                stack_id=stack_id,
                diagnostics=tuple(diagnostics),
            )
    else:
        parsed = manifest

    diagnostics.extend(_validate_manifest(parsed))
    return OptionalSolverManifestValidationReport(
        stack_id=parsed.stack_id,
        diagnostics=tuple(diagnostics),
    )


def _validate_raw_mapping(
    raw: Mapping[str, Any],
) -> list[OptionalSolverManifestDiagnostic]:
    diagnostics: list[OptionalSolverManifestDiagnostic] = []
    for field_name in sorted(_REQUIRED_FIELDS):
        if _is_missing(raw.get(field_name)):
            diagnostics.append(
                _diagnostic(
                    "OSM_REQUIRED_FIELD_MISSING",
                    OptionalSolverDiagnosticSeverity.ERROR,
                    f"Required field is missing or empty: {field_name}",
                    field_name,
                    "Populate the required manifest field.",
                )
            )
    refs = raw.get("documentation_refs")
    if isinstance(refs, list):
        for index, ref in enumerate(refs):
            if not isinstance(ref, str):
                diagnostics.append(
                    _diagnostic(
                        "OSM_DOCUMENTATION_REF_NOT_STRING",
                        OptionalSolverDiagnosticSeverity.ERROR,
                        "Documentation references must be strings or paths.",
                        f"documentation_refs[{index}]",
                        "Use an internal documentation path or string reference.",
                    )
                )
    return diagnostics


def _validate_manifest(
    manifest: OptionalSolverManifest,
) -> list[OptionalSolverManifestDiagnostic]:
    diagnostics: list[OptionalSolverManifestDiagnostic] = []
    if not manifest.stack_id.strip():
        diagnostics.append(
            _diagnostic(
                "OSM_STACK_ID_EMPTY",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Manifest stack_id must be stable and nonempty.",
                "stack_id",
                "Use a lowercase stable id such as gmsh.",
            )
        )
    if not manifest.display_name.strip():
        diagnostics.append(
            _diagnostic(
                "OSM_DISPLAY_NAME_EMPTY",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Manifest display_name must be nonempty.",
                "display_name",
                "Add a user-visible stack name.",
            )
        )
    expected_issue = _BUILTIN_ISSUE_BY_STACK.get(manifest.stack_id)
    if expected_issue is not None and manifest.related_issue != expected_issue:
        diagnostics.append(
            _diagnostic(
                "OSM_RELATED_ISSUE_MISMATCH",
                OptionalSolverDiagnosticSeverity.ERROR,
                f"Built-in {manifest.stack_id} must map to issue #{expected_issue}.",
                "related_issue",
                "Use the expected live optional validation issue number.",
            )
        )
    if manifest.related_issue is None:
        diagnostics.append(
            _diagnostic(
                "OSM_RELATED_ISSUE_MISSING",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Manifest related_issue must be present.",
                "related_issue",
                "Link the stack to its validation tracking issue.",
            )
        )
    if not manifest.capabilities:
        diagnostics.append(
            _diagnostic(
                "OSM_CAPABILITIES_EMPTY",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Manifest must declare at least one capability.",
                "capabilities",
                "Add one or more capability declarations.",
            )
        )
    diagnostics.extend(
        _validate_requirement_ids(
            manifest.executable_requirements,
            "executable_requirements",
        )
    )
    diagnostics.extend(
        _validate_requirement_ids(
            manifest.python_package_requirements,
            "python_package_requirements",
        )
    )
    if not manifest.executable_requirements and not manifest.python_package_requirements:
        diagnostics.append(
            _diagnostic(
                "OSM_REQUIREMENTS_EMPTY",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Manifest must declare executable or Python package requirements.",
                "requirements",
                "Declare the optional components needed by the stack.",
            )
        )
    diagnostics.extend(_validate_probe(manifest.version_probe, "version_probe"))
    diagnostics.extend(_validate_probe(manifest.help_probe, "help_probe"))
    if not manifest.non_bundled_disclaimer.strip():
        diagnostics.append(
            _diagnostic(
                "OSM_NON_BUNDLED_DISCLAIMER_MISSING",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Manifest must include a non-bundled solver disclaimer.",
                "non_bundled_disclaimer",
                "State that external solvers are not bundled.",
            )
        )
    safety_text = " ".join(manifest.safety_notes).lower()
    if "no install" not in safety_text and "no dependency install" not in safety_text:
        diagnostics.append(
            _diagnostic(
                "OSM_SAFETY_NO_INSTALL_MISSING",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Safety notes must include a no-install boundary.",
                "safety_notes",
                "State that the manifest does not install dependencies or solvers.",
            )
        )
    if "no bundled" not in safety_text:
        diagnostics.append(
            _diagnostic(
                "OSM_SAFETY_NO_BUNDLED_SOLVER_MISSING",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Safety notes must include a no-bundled-solver boundary.",
                "safety_notes",
                "State that external solvers are not bundled.",
            )
        )
    return diagnostics


def _validate_requirement_ids(
    requirements: object,
    path: str,
) -> list[OptionalSolverManifestDiagnostic]:
    diagnostics: list[OptionalSolverManifestDiagnostic] = []
    for index, requirement in enumerate(requirements):
        if not requirement.identifier.strip():
            diagnostics.append(
                _diagnostic(
                    "OSM_REQUIREMENT_IDENTIFIER_EMPTY",
                    OptionalSolverDiagnosticSeverity.ERROR,
                    "Requirement identifiers must be nonempty.",
                    f"{path}[{index}].identifier",
                    "Use the executable name or Python package import name.",
                )
            )
    return diagnostics


def _validate_probe(
    probe: OptionalSolverProbe | None,
    path: str,
) -> list[OptionalSolverManifestDiagnostic]:
    if probe is None:
        return []
    diagnostics: list[OptionalSolverManifestDiagnostic] = []
    if not probe.name.strip():
        diagnostics.append(
            _diagnostic(
                "OSM_PROBE_NAME_EMPTY",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Probe declarations require a name.",
                f"{path}.name",
                "Name the declarative version/help probe.",
            )
        )
    if not probe.command:
        diagnostics.append(
            _diagnostic(
                "OSM_PROBE_COMMAND_EMPTY",
                OptionalSolverDiagnosticSeverity.ERROR,
                "Probe command declarations must be nonempty.",
                f"{path}.command",
                "Declare the command tokens without executing them.",
            )
        )
    command_text = " ".join(probe.command).lower()
    if any(phrase in command_text for phrase in _INSTALLER_PHRASES):
        diagnostics.append(
            _diagnostic(
                "OSM_PROBE_INSTALLER_COMMAND",
                OptionalSolverDiagnosticSeverity.BLOCKER,
                "Probe declarations must not include installer or download commands.",
                f"{path}.command",
                "Use version/help style probes only.",
            )
        )
    return diagnostics


def _is_missing(value: object) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _diagnostic(
    code: str,
    severity: OptionalSolverDiagnosticSeverity,
    message: str,
    path: str,
    suggested_fix: str,
) -> OptionalSolverManifestDiagnostic:
    return OptionalSolverManifestDiagnostic(
        code=code,
        severity=severity,
        message=message,
        path=path,
        suggested_fix=suggested_fix,
    )
