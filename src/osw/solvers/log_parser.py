"""Small log finding parser for backend runner output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LogSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class RunLogFinding:
    severity: LogSeverity
    line_number: int
    message: str


def parse_run_log(text: str) -> list[RunLogFinding]:
    findings: list[RunLogFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if "fatal" in lowered or "error" in lowered:
            findings.append(RunLogFinding(LogSeverity.ERROR, line_number, line))
        elif "warning" in lowered or "warn:" in lowered:
            findings.append(RunLogFinding(LogSeverity.WARNING, line_number, line))
    return findings

