"""Validation helpers for OSW core data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["error", "warning", "info"]


class ProjectSchemaError(ValueError):
    """Raised when project data cannot be parsed into the OSW schema."""


@dataclass(frozen=True)
class ValidationMessage:
    severity: Severity
    path: str
    message: str

    @classmethod
    def error(cls, path: str, message: str) -> ValidationMessage:
        return cls("error", path, message)

    @classmethod
    def warning(cls, path: str, message: str) -> ValidationMessage:
        return cls("warning", path, message)


@dataclass
class ValidationReport:
    messages: list[ValidationMessage] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(message.severity == "error" for message in self.messages)

    @property
    def has_warnings(self) -> bool:
        return any(message.severity == "warning" for message in self.messages)

    def add_error(self, path: str, message: str) -> None:
        self.messages.append(ValidationMessage.error(path, message))

    def add_warning(self, path: str, message: str) -> None:
        self.messages.append(ValidationMessage.warning(path, message))

    def extend(self, other: ValidationReport) -> None:
        self.messages.extend(other.messages)

    def friendly_summary(self) -> str:
        if not self.messages:
            return "No validation messages."
        return "\n".join(
            f"{message.severity.upper()} {message.path}: {message.message}"
            for message in self.messages
        )
