"""Structured plugin diagnostics and errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PluginDiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class PluginDiagnostic:
    severity: PluginDiagnosticSeverity
    code: str
    message: str
    hint: str = ""
    field: str = ""
    source: str = ""

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        *,
        hint: str = "",
        field: str = "",
        source: str = "",
    ) -> PluginDiagnostic:
        return cls(PluginDiagnosticSeverity.ERROR, code, message, hint, field, source)

    @classmethod
    def warning(
        cls,
        code: str,
        message: str,
        *,
        hint: str = "",
        field: str = "",
        source: str = "",
    ) -> PluginDiagnostic:
        return cls(PluginDiagnosticSeverity.WARNING, code, message, hint, field, source)

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "field": self.field,
            "source": self.source,
        }


class PluginError(RuntimeError):
    """Base plugin-layer error."""


class PluginValidationError(ValueError):
    """Raised when plugin data cannot be validated."""

    def __init__(
        self,
        message: str,
        diagnostics: tuple[PluginDiagnostic, ...] = (),
    ) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics
