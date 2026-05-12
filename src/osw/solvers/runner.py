"""Backend external command runner for bounded OSW solver workflows."""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from osw.core.diagnostics import DiagnosticReport
from osw.core.run_manager import ExecutablePathRegistry


class RunStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    MISSING_EXECUTABLE = "missing_executable"


@dataclass(frozen=True)
class TimeoutPolicy:
    seconds: float = 60.0

    def diagnostics(self) -> DiagnosticReport:
        report = DiagnosticReport()
        if self.seconds <= 0:
            report.add_error("timeout.invalid", "Runner timeout must be greater than zero seconds.")
        return report


@dataclass(frozen=True)
class RunLog:
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class RunArtifact:
    path: Path
    kind: str
    description: str = ""


@dataclass(frozen=True)
class RunResult:
    status: RunStatus
    command: tuple[str, ...]
    cwd: Path
    artifact_dir: Path
    returncode: int | None
    duration_seconds: float
    log: RunLog = field(default_factory=RunLog)
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)


class ExternalCommandRunner:
    """Run a configured external command outside the GUI layer."""

    def __init__(
        self,
        *,
        registry: ExecutablePathRegistry | None = None,
        timeout_policy: TimeoutPolicy | None = None,
    ) -> None:
        self.registry = registry or ExecutablePathRegistry()
        self.timeout_policy = timeout_policy or TimeoutPolicy()

    def run(
        self,
        executable: str | Path,
        args: Sequence[str] = (),
        *,
        cwd: str | Path,
        artifact_dir: str | Path,
        env: Mapping[str, str] | None = None,
        timeout_policy: TimeoutPolicy | None = None,
    ) -> RunResult:
        started = time.monotonic()
        cwd_path = Path(cwd).expanduser().resolve()
        artifact_path = Path(artifact_dir).expanduser().resolve()
        artifact_path.mkdir(parents=True, exist_ok=True)

        diagnostics = DiagnosticReport()
        effective_timeout = timeout_policy or self.timeout_policy
        diagnostics.extend(effective_timeout.diagnostics())
        if diagnostics.has_errors:
            return self._result(
                status=RunStatus.FAILED,
                executable=executable,
                args=args,
                cwd=cwd_path,
                artifact_dir=artifact_path,
                started=started,
                diagnostics=diagnostics,
            )

        lookup = self.registry.resolve(executable)
        diagnostics.extend(lookup.diagnostics)
        if not lookup.found or lookup.path is None:
            return self._result(
                status=RunStatus.MISSING_EXECUTABLE,
                executable=executable,
                args=args,
                cwd=cwd_path,
                artifact_dir=artifact_path,
                started=started,
                diagnostics=diagnostics,
            )

        command = (str(lookup.path), *[str(arg) for arg in args])
        try:
            completed = subprocess.run(
                command,
                cwd=cwd_path,
                env=dict(env) if env is not None else None,
                capture_output=True,
                text=True,
                timeout=effective_timeout.seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            log = RunLog(_coerce_output(exc.stdout), _coerce_output(exc.stderr))
            diagnostics.add_error(
                "runner.timeout",
                f"Command timed out after {effective_timeout.seconds:g} seconds: {command[0]}",
            )
            artifacts = self._write_artifacts(
                artifact_path,
                command,
                None,
                RunStatus.TIMED_OUT,
                log,
            )
            return RunResult(
                status=RunStatus.TIMED_OUT,
                command=command,
                cwd=cwd_path,
                artifact_dir=artifact_path,
                returncode=None,
                duration_seconds=time.monotonic() - started,
                log=log,
                artifacts=artifacts,
                diagnostics=diagnostics,
            )
        except OSError as exc:
            diagnostics.add_error("runner.os_error", f"Could not start command: {exc}")
            return self._result(
                status=RunStatus.FAILED,
                executable=executable,
                args=args,
                cwd=cwd_path,
                artifact_dir=artifact_path,
                started=started,
                diagnostics=diagnostics,
            )

        log = RunLog(completed.stdout, completed.stderr)
        status = RunStatus.COMPLETED if completed.returncode == 0 else RunStatus.FAILED
        if status == RunStatus.FAILED:
            diagnostics.add_error(
                "runner.nonzero_exit",
                f"Command exited with status {completed.returncode}: {command[0]}",
            )
        artifacts = self._write_artifacts(
            artifact_path,
            command,
            completed.returncode,
            status,
            log,
        )
        return RunResult(
            status=status,
            command=command,
            cwd=cwd_path,
            artifact_dir=artifact_path,
            returncode=completed.returncode,
            duration_seconds=time.monotonic() - started,
            log=log,
            artifacts=artifacts,
            diagnostics=diagnostics,
        )

    def _result(
        self,
        *,
        status: RunStatus,
        executable: str | Path,
        args: Sequence[str],
        cwd: Path,
        artifact_dir: Path,
        started: float,
        diagnostics: DiagnosticReport,
    ) -> RunResult:
        command = (str(executable), *[str(arg) for arg in args])
        artifacts = self._write_artifacts(artifact_dir, command, None, status, RunLog())
        return RunResult(
            status=status,
            command=command,
            cwd=cwd,
            artifact_dir=artifact_dir,
            returncode=None,
            duration_seconds=time.monotonic() - started,
            artifacts=artifacts,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _write_artifacts(
        artifact_dir: Path,
        command: tuple[str, ...],
        returncode: int | None,
        status: RunStatus,
        log: RunLog,
    ) -> tuple[RunArtifact, ...]:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = artifact_dir / "stdout.txt"
        stderr_path = artifact_dir / "stderr.txt"
        summary_path = artifact_dir / "run_summary.json"

        stdout_path.write_text(log.stdout, encoding="utf-8")
        stderr_path.write_text(log.stderr, encoding="utf-8")
        summary_path.write_text(
            json.dumps(
                {
                    "command": list(command),
                    "returncode": returncode,
                    "status": status.value,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        return (
            RunArtifact(artifact_dir, "directory", "Run artifact directory."),
            RunArtifact(stdout_path, "stdout", "Captured standard output."),
            RunArtifact(stderr_path, "stderr", "Captured standard error."),
            RunArtifact(summary_path, "summary", "Run status summary."),
        )


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value
