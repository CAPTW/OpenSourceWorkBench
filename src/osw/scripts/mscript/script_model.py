"""Preview models for `.m` script imports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MScriptKind(Enum):
    SCRIPT = "script"
    FUNCTION = "function"


@dataclass(frozen=True)
class SafetyFinding:
    function: str
    line: int
    severity: str
    message: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "function": self.function,
            "line": self.line,
            "severity": self.severity,
            "message": self.message,
            "snippet": self.snippet,
        }


@dataclass(frozen=True)
class SafetyScanResult:
    source: str
    findings: tuple[SafetyFinding, ...]

    @property
    def is_safe_for_preview(self) -> bool:
        return not any(finding.severity == "danger" for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "is_safe_for_preview": self.is_safe_for_preview,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class MScriptPreview:
    source: str
    kind: MScriptKind
    name: str
    entrypoint: str | None
    line_count: int
    executable_line_count: int
    comment_line_count: int
    contains_plot_call: bool
    safety: SafetyScanResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind.value,
            "name": self.name,
            "entrypoint": self.entrypoint,
            "line_count": self.line_count,
            "executable_line_count": self.executable_line_count,
            "comment_line_count": self.comment_line_count,
            "contains_plot_call": self.contains_plot_call,
            "safety": self.safety.to_dict(),
        }
