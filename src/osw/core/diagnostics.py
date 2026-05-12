"""Friendly diagnostic messages for OSW runtime services."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class DiagnosticMessage:
    severity: DiagnosticSeverity
    code: str
    message: str
    path: str = ""

    @classmethod
    def info(cls, code: str, message: str, *, path: str = "") -> DiagnosticMessage:
        return cls(DiagnosticSeverity.INFO, code, message, path)

    @classmethod
    def warning(cls, code: str, message: str, *, path: str = "") -> DiagnosticMessage:
        return cls(DiagnosticSeverity.WARNING, code, message, path)

    @classmethod
    def error(cls, code: str, message: str, *, path: str = "") -> DiagnosticMessage:
        return cls(DiagnosticSeverity.ERROR, code, message, path)


@dataclass
class DiagnosticReport:
    messages: list[DiagnosticMessage] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(message.severity == DiagnosticSeverity.ERROR for message in self.messages)

    @property
    def has_warnings(self) -> bool:
        return any(message.severity == DiagnosticSeverity.WARNING for message in self.messages)

    def add_info(self, code: str, message: str, *, path: str = "") -> None:
        self.messages.append(DiagnosticMessage.info(code, message, path=path))

    def add_warning(self, code: str, message: str, *, path: str = "") -> None:
        self.messages.append(DiagnosticMessage.warning(code, message, path=path))

    def add_error(self, code: str, message: str, *, path: str = "") -> None:
        self.messages.append(DiagnosticMessage.error(code, message, path=path))

    def extend(self, other: DiagnosticReport) -> None:
        self.messages.extend(other.messages)

    def summary(self) -> str:
        if not self.messages:
            return "No diagnostics."
        lines: list[str] = []
        for message in self.messages:
            location = f" {message.path}" if message.path else ""
            lines.append(
                f"{message.severity.value.upper()} {message.code}{location}: "
                f"{message.message}"
            )
        return "\n".join(lines)

