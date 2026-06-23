"""Passive optional solver discovery service.

This module consumes declarative manifests and records passive presence
evidence. It does not execute external commands, import optional solver
packages, perform smoke checks, or install dependencies.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Mapping, Sequence
from importlib import metadata, util
from pathlib import PurePath

from .builtin_manifests import builtin_optional_solver_manifests
from .discovery_models import (
    OptionalSolverDiscoveryDiagnostic,
    OptionalSolverDiscoveryOptions,
    OptionalSolverDiscoveryReport,
    OptionalSolverEnvironmentHintDiscovery,
    OptionalSolverExecutableDiscovery,
    OptionalSolverPathRedactionMode,
    OptionalSolverPythonPackageDiscovery,
    OptionalSolverStackDiscovery,
)
from .manifest_models import (
    OptionalSolverHealthState,
    OptionalSolverManifest,
    OptionalSolverRequirement,
)
from .manifest_validation import (
    OptionalSolverDiagnosticSeverity,
    OptionalSolverManifestDiagnostic,
    validate_optional_solver_manifest,
)

ExecutableResolver = Callable[[str], str | None]
PythonPackageResolver = Callable[[str], object | None]
EnvironmentResolver = Callable[[str], str | None]


def discover_optional_solver_stack(
    manifest: OptionalSolverManifest,
    *,
    options: OptionalSolverDiscoveryOptions | None = None,
    executable_resolver: ExecutableResolver | None = None,
    python_package_resolver: PythonPackageResolver | None = None,
    environment_resolver: EnvironmentResolver | None = None,
) -> OptionalSolverStackDiscovery:
    """Passively discover one optional solver stack from a manifest."""

    active_options = options or OptionalSolverDiscoveryOptions()
    executable_lookup = executable_resolver or _default_executable_resolver
    package_lookup = python_package_resolver or _default_python_package_resolver
    environment_lookup = environment_resolver or _default_environment_resolver

    validation = validate_optional_solver_manifest(manifest)
    diagnostics = [
        _from_manifest_diagnostic(item) for item in validation.diagnostics
    ]
    diagnostics.append(
        _diagnostic(
            "OSD_PASSIVE_ONLY",
            OptionalSolverDiagnosticSeverity.INFO,
            "Passive discovery did not run smoke checks or solver commands.",
            "",
            "Use an explicit validation gate for active smoke execution.",
        )
    )

    executables = tuple(
        _discover_executable_requirement(
            requirement,
            active_options,
            executable_lookup,
            diagnostics,
        )
        for requirement in manifest.executable_requirements
    )
    packages = tuple(
        _discover_python_package_requirement(requirement, package_lookup, diagnostics)
        for requirement in manifest.python_package_requirements
    )
    environment_hints = tuple(
        _discover_environment_hint(name, active_options, environment_lookup, diagnostics)
        for name in manifest.environment_variable_hints
    )

    if not validation.is_valid:
        health_state = OptionalSolverHealthState.UNKNOWN
        confidence = "none"
    else:
        health_state = _health_state(executables, packages)
        confidence = _confidence(health_state)
        if health_state == OptionalSolverHealthState.PARTIALLY_INSTALLED:
            diagnostics.append(
                _diagnostic(
                    "OSD_PARTIAL_STACK",
                    OptionalSolverDiagnosticSeverity.WARNING,
                    "Some required passive requirements were discovered, but not all.",
                    "requirements",
                    "Install or expose the missing optional components before validation.",
                )
            )

    return OptionalSolverStackDiscovery(
        stack_id=manifest.stack_id,
        display_name=manifest.display_name,
        related_issue=manifest.related_issue,
        health_state=health_state,
        executables=executables,
        python_packages=packages,
        environment_hints=environment_hints,
        diagnostics=tuple(diagnostics),
        manifest_valid=validation.is_valid,
        confidence=confidence,
    )


def discover_optional_solver_manifests(
    manifests: Sequence[OptionalSolverManifest],
    *,
    options: OptionalSolverDiscoveryOptions | None = None,
    executable_resolver: ExecutableResolver | None = None,
    python_package_resolver: PythonPackageResolver | None = None,
    environment_resolver: EnvironmentResolver | None = None,
) -> OptionalSolverDiscoveryReport:
    """Passively discover a sequence of optional solver manifests."""

    active_options = options or OptionalSolverDiscoveryOptions()
    stacks = tuple(
        discover_optional_solver_stack(
            manifest,
            options=active_options,
            executable_resolver=executable_resolver,
            python_package_resolver=python_package_resolver,
            environment_resolver=environment_resolver,
        )
        for manifest in manifests
    )
    return OptionalSolverDiscoveryReport(
        generated_at=active_options.generated_at,
        source=active_options.source,
        stacks=stacks,
    )


def discover_builtin_optional_solvers(
    *,
    options: OptionalSolverDiscoveryOptions | None = None,
    executable_resolver: ExecutableResolver | None = None,
    python_package_resolver: PythonPackageResolver | None = None,
    environment_resolver: EnvironmentResolver | None = None,
) -> OptionalSolverDiscoveryReport:
    """Passively discover all built-in optional solver manifests."""

    return discover_optional_solver_manifests(
        builtin_optional_solver_manifests(),
        options=options,
        executable_resolver=executable_resolver,
        python_package_resolver=python_package_resolver,
        environment_resolver=environment_resolver,
    )


def explain_optional_solver_discovery(
    discovery: OptionalSolverDiscoveryReport | OptionalSolverStackDiscovery,
) -> str:
    """Return a short human-readable passive discovery summary."""

    if isinstance(discovery, OptionalSolverDiscoveryReport):
        stack_count = len(discovery.stacks)
        state_counts: dict[str, int] = {}
        for stack in discovery.stacks:
            state_counts[stack.health_state.value] = (
                state_counts.get(stack.health_state.value, 0) + 1
            )
        summary = ", ".join(
            f"{state}={count}" for state, count in sorted(state_counts.items())
        )
        return (
            f"Passive optional solver discovery evaluated {stack_count} stacks "
            f"({summary or 'no states'}). It did not run smoke checks, execute "
            "solver commands, or install dependencies."
        )
    return (
        f"{discovery.display_name} ({discovery.stack_id}) is "
        f"{discovery.health_state.value} from passive discovery. It did not run "
        "smoke checks, execute solver commands, or install dependencies."
    )


def _discover_executable_requirement(
    requirement: OptionalSolverRequirement,
    options: OptionalSolverDiscoveryOptions,
    resolver: ExecutableResolver,
    diagnostics: list[OptionalSolverDiscoveryDiagnostic],
) -> OptionalSolverExecutableDiscovery:
    resolved_path = ""
    try:
        resolved_path = resolver(requirement.identifier) or ""
    except (OSError, PermissionError) as exc:
        diagnostics.append(
            _diagnostic(
                "OSD_PATH_PERMISSION_ISSUE",
                OptionalSolverDiagnosticSeverity.WARNING,
                f"Executable lookup failed for {requirement.identifier}: {exc}",
                f"executable_requirements.{requirement.identifier}",
                "Check PATH permissions or use an injected resolver.",
            )
        )

    found = bool(resolved_path)
    path = (
        resolved_path
        if found and options.path_redaction == OptionalSolverPathRedactionMode.FULL
        else ""
    )
    redacted_path = _redact_path(resolved_path, options.path_redaction) if found else ""
    if found and options.path_redaction != OptionalSolverPathRedactionMode.FULL:
        diagnostics.append(
            _diagnostic(
                "OSD_PATH_REDACTED",
                OptionalSolverDiagnosticSeverity.INFO,
                f"Path for {requirement.identifier} was redacted.",
                f"executable_requirements.{requirement.identifier}",
                "Request full paths only for a local report that may expose user paths.",
            )
        )
    if not found and requirement.required:
        diagnostics.append(
            _diagnostic(
                "OSD_MISSING_EXECUTABLE",
                OptionalSolverDiagnosticSeverity.WARNING,
                f"Required executable was not discovered: {requirement.identifier}",
                f"executable_requirements.{requirement.identifier}",
                "Expose the executable on PATH in a prepared environment.",
            )
        )
    return OptionalSolverExecutableDiscovery(
        identifier=requirement.identifier,
        display_name=requirement.display_name,
        required=requirement.required,
        found=found,
        path=path,
        redacted_path=redacted_path,
        notes=requirement.notes,
    )


def _discover_python_package_requirement(
    requirement: OptionalSolverRequirement,
    resolver: PythonPackageResolver,
    diagnostics: list[OptionalSolverDiscoveryDiagnostic],
) -> OptionalSolverPythonPackageDiscovery:
    package_info: object | None = None
    try:
        package_info = resolver(requirement.identifier)
    except (ImportError, metadata.PackageNotFoundError, ValueError) as exc:
        diagnostics.append(
            _diagnostic(
                "OSD_PYTHON_PACKAGE_LOOKUP_ERROR",
                OptionalSolverDiagnosticSeverity.WARNING,
                f"Python package lookup failed for {requirement.identifier}: {exc}",
                f"python_package_requirements.{requirement.identifier}",
                "Use an injected resolver or inspect the Python environment.",
            )
        )
    found, version = _package_info(package_info)
    if not found and requirement.required:
        diagnostics.append(
            _diagnostic(
                "OSD_MISSING_PYTHON_PACKAGE",
                OptionalSolverDiagnosticSeverity.WARNING,
                f"Required Python package was not discovered: {requirement.identifier}",
                f"python_package_requirements.{requirement.identifier}",
                "Prepare the Python environment before validation.",
            )
        )
    return OptionalSolverPythonPackageDiscovery(
        identifier=requirement.identifier,
        display_name=requirement.display_name,
        required=requirement.required,
        found=found,
        version=version,
        notes=requirement.notes,
    )


def _discover_environment_hint(
    name: str,
    options: OptionalSolverDiscoveryOptions,
    resolver: EnvironmentResolver,
    diagnostics: list[OptionalSolverDiscoveryDiagnostic],
) -> OptionalSolverEnvironmentHintDiscovery:
    value = resolver(name) or ""
    if value and options.include_environment_values:
        return OptionalSolverEnvironmentHintDiscovery(name=name, present=True, value=value)
    if value:
        diagnostics.append(
            _diagnostic(
                "OSD_ENVIRONMENT_VALUE_REDACTED",
                OptionalSolverDiagnosticSeverity.INFO,
                f"Environment value for {name} was redacted.",
                f"environment_variable_hints.{name}",
                "Request environment values only for local reports that may expose paths.",
            )
        )
        return OptionalSolverEnvironmentHintDiscovery(
            name=name,
            present=True,
            redacted_value="<redacted>",
        )
    diagnostics.append(
        _diagnostic(
            "OSD_MISSING_ENVIRONMENT_HINT",
            OptionalSolverDiagnosticSeverity.INFO,
            f"Environment hint is not set: {name}",
            f"environment_variable_hints.{name}",
            "Set the hint only if the optional stack requires it in your environment.",
        )
    )
    return OptionalSolverEnvironmentHintDiscovery(name=name, present=False)


def _health_state(
    executables: tuple[OptionalSolverExecutableDiscovery, ...],
    packages: tuple[OptionalSolverPythonPackageDiscovery, ...],
) -> OptionalSolverHealthState:
    requirements = tuple(
        item for item in (*executables, *packages) if item.required
    ) or (*executables, *packages)
    if not requirements:
        return OptionalSolverHealthState.UNKNOWN
    found_count = sum(1 for item in requirements if item.found)
    if found_count == 0:
        return OptionalSolverHealthState.MISSING
    if found_count == len(requirements):
        return OptionalSolverHealthState.DISCOVERED
    return OptionalSolverHealthState.PARTIALLY_INSTALLED


def _confidence(health_state: OptionalSolverHealthState) -> str:
    if health_state == OptionalSolverHealthState.DISCOVERED:
        return "passive-high"
    if health_state == OptionalSolverHealthState.PARTIALLY_INSTALLED:
        return "passive-partial"
    if health_state == OptionalSolverHealthState.MISSING:
        return "passive-missing"
    return "none"


def _default_executable_resolver(name: str) -> str | None:
    return shutil.which(name)


def _default_python_package_resolver(name: str) -> dict[str, object] | None:
    if util.find_spec(name) is None:
        return None
    version = ""
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        version = ""
    return {"found": True, "version": version}


def _default_environment_resolver(name: str) -> str | None:
    return os.environ.get(name)


def _package_info(info: object | None) -> tuple[bool, str]:
    if info is None or info is False:
        return False, ""
    if info is True:
        return True, ""
    if isinstance(info, str):
        return True, info
    if isinstance(info, Mapping):
        return bool(info.get("found", True)), str(info.get("version", ""))
    return True, str(getattr(info, "version", ""))


def _redact_path(
    path: str,
    mode: OptionalSolverPathRedactionMode,
) -> str:
    if not path:
        return ""
    if mode == OptionalSolverPathRedactionMode.FULL:
        return path
    name = PurePath(path).name or "<path>"
    return f"<redacted:{name}>"


def _from_manifest_diagnostic(
    diagnostic: OptionalSolverManifestDiagnostic,
) -> OptionalSolverDiscoveryDiagnostic:
    return OptionalSolverDiscoveryDiagnostic(
        code="OSD_MANIFEST_ERROR",
        severity=diagnostic.severity,
        message=diagnostic.message,
        path=diagnostic.path,
        suggested_fix=diagnostic.suggested_fix,
    )


def _diagnostic(
    code: str,
    severity: OptionalSolverDiagnosticSeverity,
    message: str,
    path: str,
    suggested_fix: str,
) -> OptionalSolverDiscoveryDiagnostic:
    return OptionalSolverDiscoveryDiagnostic(
        code=code,
        severity=severity,
        message=message,
        path=path,
        suggested_fix=suggested_fix,
    )
