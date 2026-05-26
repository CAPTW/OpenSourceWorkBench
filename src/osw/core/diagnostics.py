"""Structured diagnostics shared by OSW core, plugins, and runners."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import StrEnum
from pathlib import Path
from typing import Any


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DiagnosticCode(StrEnum):
    EXECUTABLE_NOT_FOUND = "executable-not-found"
    EXECUTABLE_NOT_CONFIGURED = "executable-not-configured"
    COMMAND_TIMEOUT = "command-timeout"
    COMMAND_FAILED = "command-failed"
    COMMAND_COMPLETED = "command-completed"
    STDOUT_CAPTURED = "stdout-captured"
    STDERR_CAPTURED = "stderr-captured"
    ARTIFACT_MISSING = "artifact-missing"
    ARTIFACT_COLLECTED = "artifact-collected"
    INVALID_WORKING_DIRECTORY = "invalid-working-directory"
    UNSAFE_SHELL_COMMAND = "unsafe-shell-command"
    ENVIRONMENT_VARIABLE_MISSING = "environment-variable-missing"
    LOG_WARNING_DETECTED = "log-warning-detected"
    LOG_ERROR_DETECTED = "log-error-detected"
    DEPENDENCY_UNAVAILABLE = "dependency-unavailable"


@dataclass(frozen=True)
class DiagnosticMessage:
    severity: DiagnosticSeverity
    code: str
    message: str
    hint: str = ""
    source: str = ""
    field: str = ""
    path: str = ""
    command: tuple[str, ...] = dataclass_field(default_factory=tuple)
    return_code: int | None = None
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)

    @classmethod
    def info(
        cls,
        code: str | DiagnosticCode,
        message: str,
        *,
        hint: str = "",
        source: str = "",
        field: str = "",
        path: str | Path = "",
        command: Iterable[str] = (),
        return_code: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DiagnosticMessage:
        return cls(
            DiagnosticSeverity.INFO,
            _code_value(code),
            message,
            hint,
            source,
            field,
            str(path) if path else "",
            tuple(str(part) for part in command),
            return_code,
            dict(metadata or {}),
        )

    @classmethod
    def warning(
        cls,
        code: str | DiagnosticCode,
        message: str,
        *,
        hint: str = "",
        source: str = "",
        field: str = "",
        path: str | Path = "",
        command: Iterable[str] = (),
        return_code: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DiagnosticMessage:
        return cls(
            DiagnosticSeverity.WARNING,
            _code_value(code),
            message,
            hint,
            source,
            field,
            str(path) if path else "",
            tuple(str(part) for part in command),
            return_code,
            dict(metadata or {}),
        )

    @classmethod
    def error(
        cls,
        code: str | DiagnosticCode,
        message: str,
        *,
        hint: str = "",
        source: str = "",
        field: str = "",
        path: str | Path = "",
        command: Iterable[str] = (),
        return_code: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DiagnosticMessage:
        return cls(
            DiagnosticSeverity.ERROR,
            _code_value(code),
            message,
            hint,
            source,
            field,
            str(path) if path else "",
            tuple(str(part) for part in command),
            return_code,
            dict(metadata or {}),
        )

    @classmethod
    def critical(
        cls,
        code: str | DiagnosticCode,
        message: str,
        *,
        hint: str = "",
        source: str = "",
        field: str = "",
        path: str | Path = "",
        command: Iterable[str] = (),
        return_code: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DiagnosticMessage:
        return cls(
            DiagnosticSeverity.CRITICAL,
            _code_value(code),
            message,
            hint,
            source,
            field,
            str(path) if path else "",
            tuple(str(part) for part in command),
            return_code,
            dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "source": self.source,
            "field": self.field,
            "path": self.path,
            "command": list(self.command),
            "return_code": self.return_code,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiagnosticMessage:
        return cls(
            severity=DiagnosticSeverity(str(data["severity"])),
            code=str(data["code"]),
            message=str(data["message"]),
            hint=str(data.get("hint", "")),
            source=str(data.get("source", "")),
            field=str(data.get("field", "")),
            path=str(data.get("path", "")),
            command=tuple(str(part) for part in data.get("command", ())),
            return_code=data.get("return_code"),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass
class DiagnosticReport:
    messages: list[DiagnosticMessage] = dataclass_field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(
            message.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL)
            for message in self.messages
        )

    @property
    def has_warnings(self) -> bool:
        return any(message.severity == DiagnosticSeverity.WARNING for message in self.messages)

    def add(self, message: DiagnosticMessage) -> None:
        self.messages.append(message)

    def add_info(
        self,
        code: str | DiagnosticCode,
        message: str,
        **kwargs: Any,
    ) -> None:
        self.add(DiagnosticMessage.info(code, message, **kwargs))

    def add_warning(
        self,
        code: str | DiagnosticCode,
        message: str,
        **kwargs: Any,
    ) -> None:
        self.add(DiagnosticMessage.warning(code, message, **kwargs))

    def add_error(
        self,
        code: str | DiagnosticCode,
        message: str,
        **kwargs: Any,
    ) -> None:
        self.add(DiagnosticMessage.error(code, message, **kwargs))

    def add_critical(
        self,
        code: str | DiagnosticCode,
        message: str,
        **kwargs: Any,
    ) -> None:
        self.add(DiagnosticMessage.critical(code, message, **kwargs))

    def extend(self, other: DiagnosticReport | Iterable[DiagnosticMessage]) -> None:
        if isinstance(other, DiagnosticReport):
            self.messages.extend(other.messages)
            return
        self.messages.extend(other)

    def warnings(self) -> list[DiagnosticMessage]:
        return [
            message
            for message in self.messages
            if message.severity == DiagnosticSeverity.WARNING
        ]

    def errors(self) -> list[DiagnosticMessage]:
        return [
            message
            for message in self.messages
            if message.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL)
        ]

    def to_dict(self) -> dict[str, Any]:
        return {"messages": [message.to_dict() for message in self.messages]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiagnosticReport:
        return cls(
            [
                DiagnosticMessage.from_dict(message)
                for message in data.get("messages", [])
            ]
        )

    def summary(self) -> str:
        if not self.messages:
            return "No diagnostics."
        lines: list[str] = []
        for message in self.messages:
            location = f" {message.path}" if message.path else ""
            hint = f" Hint: {message.hint}" if message.hint else ""
            lines.append(
                f"{message.severity.value.upper()} {message.code}{location}: "
                f"{message.message}{hint}"
            )
        return "\n".join(lines)


def _code_value(code: str | DiagnosticCode) -> str:
    return code.value if isinstance(code, DiagnosticCode) else str(code)
