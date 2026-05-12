"""Solver adapter package."""

from __future__ import annotations

from osw.solvers.log_parser import LogSeverity, RunLogFinding, parse_run_log
from osw.solvers.runner import (
    ExternalCommandRunner,
    RunArtifact,
    RunLog,
    RunResult,
    RunStatus,
    TimeoutPolicy,
)

__all__ = [
    "ExternalCommandRunner",
    "LogSeverity",
    "RunArtifact",
    "RunLog",
    "RunLogFinding",
    "RunResult",
    "RunStatus",
    "TimeoutPolicy",
    "parse_run_log",
]
