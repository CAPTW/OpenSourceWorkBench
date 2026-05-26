"""Executable path resolution for backend runner services."""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from osw.core.diagnostics import DiagnosticCode, DiagnosticReport


@dataclass(frozen=True)
class ExecutableResolution:
    name: str
    resolved_path: Path | None = None
    source: str = "missing"
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)

    @property
    def found(self) -> bool:
        return self.resolved_path is not None and not self.diagnostics.has_errors

    @property
    def path(self) -> Path | None:
        return self.resolved_path

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "resolved_path": str(self.resolved_path) if self.resolved_path else "",
            "source": self.source,
            "diagnostics": self.diagnostics.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ExecutableResolution:
        resolved = str(data.get("resolved_path", ""))
        diagnostics_data = data.get("diagnostics", {})
        diagnostics = (
            DiagnosticReport.from_dict(diagnostics_data)
            if isinstance(diagnostics_data, dict)
            else DiagnosticReport()
        )
        return cls(
            name=str(data["name"]),
            resolved_path=Path(resolved) if resolved else None,
            source=str(data.get("source", "missing")),
            diagnostics=diagnostics,
        )


ExecutableLookup = ExecutableResolution


@dataclass
class ExecutablePathRegistry:
    """Resolve external executables without executing them."""

    _paths: dict[str, Path] = field(default_factory=dict)
    _aliases: dict[str, str] = field(default_factory=dict)
    _env_vars: dict[str, str] = field(default_factory=dict)

    def register(
        self,
        name: str,
        path: str | Path | None = None,
        aliases: Iterable[str] | None = None,
        env_var: str | None = None,
    ) -> Self:
        normalized = self._normalize_name(name)
        if path is not None:
            self._paths[normalized] = Path(path).expanduser()
        if env_var:
            self._env_vars[normalized] = env_var
        for alias in aliases or ():
            self._aliases[self._normalize_name(alias)] = normalized
        return self

    def set_path(self, name: str, path: str | Path) -> Self:
        self._paths[self._canonical_name(name)] = Path(path).expanduser()
        return self

    def get_configured_path(self, name: str) -> str | None:
        configured = self._paths.get(self._canonical_name(name))
        return str(configured) if configured is not None else None

    def configured_path(self, name: str) -> Path | None:
        return self._paths.get(self._canonical_name(name))

    def resolve(self, name: str | Path) -> ExecutableResolution:
        raw_name = str(name)
        canonical = self._canonical_name(raw_name)
        configured = self._paths.get(canonical)
        if configured is not None:
            return self._resolve_configured(raw_name, configured)

        env_var = self._env_vars.get(canonical)
        if env_var:
            env_value = os.environ.get(env_var, "")
            if env_value:
                return self._resolve_configured(raw_name, Path(env_value).expanduser())
            report = DiagnosticReport()
            report.add_warning(
                DiagnosticCode.ENVIRONMENT_VARIABLE_MISSING,
                f"Environment variable is not set for executable {raw_name}: {env_var}",
                hint=f"Set {env_var} or configure {raw_name} directly.",
                field=env_var,
            )
            return ExecutableResolution(raw_name, None, "missing", report)

        direct_path = Path(raw_name).expanduser()
        if _looks_like_path(raw_name):
            return self._resolve_direct_path(raw_name, direct_path)

        path_from_env = shutil.which(raw_name)
        if path_from_env:
            return ExecutableResolution(raw_name, Path(path_from_env).resolve(), "PATH")

        report = DiagnosticReport()
        report.add_error(
            DiagnosticCode.EXECUTABLE_NOT_FOUND,
            (
                f"Executable not found: {raw_name}. Configure it in "
                "ExecutablePathRegistry or install it on PATH."
            ),
            hint=f"Install {raw_name} or configure an explicit path before running.",
            field=raw_name,
        )
        return ExecutableResolution(raw_name, None, "missing", report)

    def resolve_any(self, names: Iterable[str]) -> ExecutableResolution:
        last: ExecutableResolution | None = None
        combined = DiagnosticReport()
        for name in names:
            resolution = self.resolve(name)
            if resolution.found:
                return resolution
            combined.extend(resolution.diagnostics)
            last = resolution
        if last is None:
            combined.add_error(
                DiagnosticCode.EXECUTABLE_NOT_CONFIGURED,
                "No executable names were provided for resolution.",
                hint="Pass at least one executable name.",
            )
            return ExecutableResolution("", None, "missing", combined)
        return ExecutableResolution(last.name, None, "missing", combined)

    def check(self, name: str) -> DiagnosticReport:
        return self.resolve(name).diagnostics

    def to_dict(self) -> dict[str, object]:
        return {
            "paths": {key: str(path) for key, path in self._paths.items()},
            "aliases": dict(self._aliases),
            "env_vars": dict(self._env_vars),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ExecutablePathRegistry:
        registry = cls()
        paths = data.get("paths", {})
        if isinstance(paths, Mapping):
            registry._paths = {
                str(key): Path(str(value)).expanduser() for key, value in paths.items()
            }
        aliases = data.get("aliases", {})
        if isinstance(aliases, Mapping):
            registry._aliases = {str(key): str(value) for key, value in aliases.items()}
        env_vars = data.get("env_vars", {})
        if isinstance(env_vars, Mapping):
            registry._env_vars = {str(key): str(value) for key, value in env_vars.items()}
        return registry

    def _resolve_configured(self, name: str, path: Path) -> ExecutableResolution:
        report = DiagnosticReport()
        expanded = path.expanduser()
        if expanded.exists():
            return ExecutableResolution(name, expanded.resolve(), "configured", report)
        report.add_error(
            DiagnosticCode.EXECUTABLE_NOT_CONFIGURED,
            f"Configured executable path does not exist: {expanded}",
            hint="Update the configured executable path.",
            path=expanded,
        )
        return ExecutableResolution(name, None, "configured", report)

    def _resolve_direct_path(self, name: str, path: Path) -> ExecutableResolution:
        report = DiagnosticReport()
        expanded = path.expanduser()
        if expanded.exists():
            return ExecutableResolution(name, expanded.resolve(), "configured", report)
        report.add_error(
            DiagnosticCode.EXECUTABLE_NOT_FOUND,
            f"Executable path does not exist: {expanded}",
            hint="Verify the path or configure the executable by name.",
            path=expanded,
        )
        return ExecutableResolution(name, None, "missing", report)

    def _canonical_name(self, name: str | Path) -> str:
        normalized = self._normalize_name(name)
        return self._aliases.get(normalized, normalized)

    @staticmethod
    def _normalize_name(name: str | Path) -> str:
        return str(name).strip().lower()


def _looks_like_path(value: str) -> bool:
    return (
        "/" in value
        or "\\" in value
        or value.startswith(".")
        or bool(Path(value).drive)
    )
