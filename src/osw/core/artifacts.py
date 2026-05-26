"""Runtime artifact models and collection helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticCode, DiagnosticReport


@dataclass(frozen=True)
class RunArtifact:
    path: Path
    role: str
    description: str = ""
    format: str = ""
    exists: bool | None = None
    size_bytes: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        resolved_exists = self.path.exists() if self.exists is None else self.exists
        resolved_size = self.size_bytes
        if resolved_size is None and resolved_exists and self.path.is_file():
            resolved_size = self.path.stat().st_size
        object.__setattr__(self, "exists", resolved_exists)
        object.__setattr__(self, "size_bytes", resolved_size)

    @property
    def kind(self) -> str:
        return self.role

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "role": self.role,
            "description": self.description,
            "format": self.format,
            "exists": bool(self.exists),
            "size_bytes": self.size_bytes,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunArtifact:
        return cls(
            path=Path(str(data["path"])),
            role=str(data["role"]),
            description=str(data.get("description", "")),
            format=str(data.get("format", "")),
            exists=bool(data.get("exists", False)),
            size_bytes=data.get("size_bytes"),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def collect_artifacts(
    run_dir: str | Path,
    patterns: Iterable[str],
    *,
    diagnostics: DiagnosticReport | None = None,
) -> tuple[RunArtifact, ...]:
    root = Path(run_dir)
    report = diagnostics if diagnostics is not None else DiagnosticReport()
    artifacts: list[RunArtifact] = []
    for pattern in patterns:
        matches = sorted(root.glob(pattern))
        if not matches:
            report.add_warning(
                DiagnosticCode.ARTIFACT_MISSING,
                f"No artifacts matched pattern: {pattern}",
                hint="Check whether the tool produced the expected output file.",
                path=root,
                metadata={"pattern": pattern},
            )
            continue
        for path in matches:
            artifact = RunArtifact(
                path=path,
                role=_role_from_pattern(pattern),
                format=path.suffix.lstrip("."),
            )
            artifacts.append(artifact)
            report.add_info(
                DiagnosticCode.ARTIFACT_COLLECTED,
                f"Collected artifact: {path.name}",
                path=path,
                metadata={"pattern": pattern, "role": artifact.role},
            )
    return tuple(artifacts)


def _role_from_pattern(pattern: str) -> str:
    suffix = Path(pattern.replace("*", "artifact")).suffix.lstrip(".")
    return f"{suffix}_artifact" if suffix else "artifact"
