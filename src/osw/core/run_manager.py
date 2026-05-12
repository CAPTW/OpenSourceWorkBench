"""Executable registry used by backend runner services."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from osw.core.diagnostics import DiagnosticReport


@dataclass(frozen=True)
class ExecutableLookup:
    name: str
    path: Path | None
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)

    @property
    def found(self) -> bool:
        return self.path is not None and not self.diagnostics.has_errors


@dataclass
class ExecutablePathRegistry:
    """Local-only executable path registry.

    The registry does not install tools or edit environment variables. It only
    resolves configured paths and PATH entries for backend runner code.
    """

    _paths: dict[str, Path] = field(default_factory=dict)

    def register(self, name: str, path: str | Path) -> Self:
        normalized_name = self._normalize_name(name)
        self._paths[normalized_name] = Path(path).expanduser()
        return self

    def configured_path(self, name: str) -> Path | None:
        return self._paths.get(self._normalize_name(name))

    def resolve(self, name: str | Path) -> ExecutableLookup:
        raw_name = str(name)
        configured = self.configured_path(raw_name)
        if configured is not None:
            return self._resolve_configured(raw_name, configured)

        direct_path = Path(raw_name).expanduser()
        if _looks_like_path(raw_name):
            return self._resolve_direct_path(raw_name, direct_path)

        path_from_env = shutil.which(raw_name)
        if path_from_env:
            return ExecutableLookup(raw_name, Path(path_from_env))

        report = DiagnosticReport()
        report.add_error(
            "executable.not_found",
            (
                f"Executable not found: {raw_name}. Configure it in "
                "ExecutablePathRegistry or install it on PATH."
            ),
        )
        return ExecutableLookup(raw_name, None, report)

    def _resolve_configured(self, name: str, path: Path) -> ExecutableLookup:
        report = DiagnosticReport()
        if path.exists():
            return ExecutableLookup(name, path.resolve(), report)
        report.add_error(
            "executable.configured_missing",
            f"Configured executable path does not exist: {path}",
            path=str(path),
        )
        return ExecutableLookup(name, None, report)

    def _resolve_direct_path(self, name: str, path: Path) -> ExecutableLookup:
        report = DiagnosticReport()
        if path.exists():
            return ExecutableLookup(name, path.resolve(), report)
        report.add_error(
            "executable.path_missing",
            f"Executable path does not exist: {path}",
            path=str(path),
        )
        return ExecutableLookup(name, None, report)

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

