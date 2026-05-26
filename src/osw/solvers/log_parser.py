"""Generic log parsing primitives for backend runner output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class LogSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    RESIDUAL = "residual"
    PROGRESS = "progress"


@dataclass(frozen=True)
class LogEvent:
    severity: LogSeverity
    message: str
    line_no: int
    timestamp: str = ""
    code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def line_number(self) -> int:
        return self.line_no


RunLogFinding = LogEvent


class GenericLogParser:
    """Best-effort generic parser; solver-specific parsers can build on it."""

    WARNING_MARKERS = ("warning", "warn", "non-orthogonal", "skewness")
    ERROR_MARKERS = ("failed", "error", "exception", "fatal")
    RESIDUAL_PATTERN = re.compile(r"\b(residual|res)\b", re.IGNORECASE)
    PROGRESS_PATTERN = re.compile(r"\b(iteration|progress|elapsed|remaining)\b", re.IGNORECASE)

    def parse(self, text: str) -> list[LogEvent]:
        return self.parse_lines(text.splitlines())

    def parse_lines(self, lines: list[str]) -> list[LogEvent]:
        events: list[LogEvent] = []
        for line_no, line in enumerate(lines, start=1):
            try:
                event = self._event_for_line(line, line_no)
            except Exception:
                event = LogEvent(
                    LogSeverity.INFO,
                    str(line),
                    line_no,
                    code="log-line-unparsed",
                )
            if event is not None:
                events.append(event)
        return events

    def detect_warnings(self, text: str) -> list[LogEvent]:
        return [event for event in self.parse(text) if event.severity is LogSeverity.WARNING]

    def detect_errors(self, text: str) -> list[LogEvent]:
        return [event for event in self.parse(text) if event.severity is LogSeverity.ERROR]

    def tail_summary(self, text: str, *, lines: int = 10) -> str:
        return "\n".join(text.splitlines()[-lines:])

    def _event_for_line(self, line: str, line_no: int) -> LogEvent | None:
        lowered = line.lower()
        if any(marker in lowered for marker in self.ERROR_MARKERS):
            return LogEvent(LogSeverity.ERROR, line, line_no, code="log-error-detected")
        if any(marker in lowered for marker in self.WARNING_MARKERS):
            return LogEvent(LogSeverity.WARNING, line, line_no, code="log-warning-detected")
        if self.RESIDUAL_PATTERN.search(line):
            return LogEvent(LogSeverity.RESIDUAL, line, line_no, code="log-residual-detected")
        if self.PROGRESS_PATTERN.search(line):
            return LogEvent(LogSeverity.PROGRESS, line, line_no, code="log-progress-detected")
        return None


def parse_run_log(text: str) -> list[RunLogFinding]:
    return GenericLogParser().parse(text)
