"""Generic run directory and run summary management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from osw.core.executables import (
    ExecutableLookup,
    ExecutablePathRegistry,
    ExecutableResolution,
)

if TYPE_CHECKING:
    from osw.solvers.runner import ExternalCommandRunner, RunRequest, RunResult


@dataclass
class RunManager:
    """Small manager for run IDs, directories, and result summaries."""

    command_runner: ExternalCommandRunner | None = None
    runs_directory_name: str = "runs"
    _sequence: int = field(default=0, init=False)

    def create_run_id(self, prefix: str = "run") -> str:
        self._sequence += 1
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"{prefix}_{timestamp}_{self._sequence:04d}"

    def create_run_dir(self, project_dir: Path, run_id: str | None = None) -> Path:
        resolved_run_id = run_id or self.create_run_id()
        run_dir = Path(project_dir) / self.runs_directory_name / resolved_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def run(self, request: RunRequest) -> RunResult:
        runner = self.command_runner
        if runner is None:
            from osw.solvers.runner import ExternalCommandRunner

            runner = ExternalCommandRunner()
            self.command_runner = runner
        return runner.run(request)

    def save_result_summary(self, result: RunResult, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def load_result_summary(self, path: Path) -> RunResult:
        from osw.solvers.runner import RunResult

        data = json.loads(path.read_text(encoding="utf-8"))
        return RunResult.from_dict(data)


__all__ = [
    "ExecutableLookup",
    "ExecutablePathRegistry",
    "ExecutableResolution",
    "RunManager",
]
