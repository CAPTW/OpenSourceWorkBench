"""Backend external command runner for bounded OSW workflows."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact, collect_artifacts
from osw.core.diagnostics import DiagnosticCode, DiagnosticReport
from osw.core.executables import ExecutablePathRegistry


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    MISSING_EXECUTABLE = "missing_executable"


@dataclass(frozen=True, init=False)
class TimeoutPolicy:
    timeout_seconds: float
    kill_grace_seconds: float
    terminate_tree: bool

    def __init__(
        self,
        timeout_seconds: float = 60.0,
        kill_grace_seconds: float = 1.0,
        terminate_tree: bool = True,
        *,
        seconds: float | None = None,
    ) -> None:
        object.__setattr__(
            self,
            "timeout_seconds",
            float(timeout_seconds if seconds is None else seconds),
        )
        object.__setattr__(self, "kill_grace_seconds", float(kill_grace_seconds))
        object.__setattr__(self, "terminate_tree", bool(terminate_tree))

    @property
    def seconds(self) -> float:
        return self.timeout_seconds

    def diagnostics(self) -> DiagnosticReport:
        report = DiagnosticReport()
        if self.timeout_seconds <= 0:
            report.add_error(
                "timeout.invalid",
                "Runner timeout must be greater than zero seconds.",
                hint="Use a positive timeout value.",
            )
        if self.kill_grace_seconds < 0:
            report.add_error(
                "timeout.grace_invalid",
                "Runner kill grace period cannot be negative.",
                hint="Use zero or a positive grace period.",
            )
        return report

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "kill_grace_seconds": self.kill_grace_seconds,
            "terminate_tree": self.terminate_tree,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> TimeoutPolicy:
        return cls(
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            kill_grace_seconds=float(data.get("kill_grace_seconds", 1.0)),
            terminate_tree=bool(data.get("terminate_tree", True)),
        )


@dataclass
class RunLog:
    stdout: str = ""
    stderr: str = ""
    combined: str = ""

    def __post_init__(self) -> None:
        if not self.combined:
            self.combined = self._combine()

    def add_stdout(self, text: str) -> None:
        self.stdout += text
        self.combined = self._combine()

    def add_stderr(self, text: str) -> None:
        self.stderr += text
        self.combined = self._combine()

    def lines(self) -> list[str]:
        return self.combined.splitlines()

    def tail(self, n: int) -> list[str]:
        return self.lines()[-n:]

    def to_dict(self) -> dict[str, str]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "combined": self.combined,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> RunLog:
        return cls(
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            combined=str(data.get("combined", "")),
        )

    def _combine(self) -> str:
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(part.rstrip("\n") for part in parts if part)


@dataclass(frozen=True)
class RunRequest:
    command: tuple[str, ...]
    cwd: Path | None = None
    env: dict[str, str] | None = None
    timeout_policy: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    artifact_patterns: tuple[str, ...] = field(default_factory=tuple)
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    artifact_dir: Path | None = None
    shell: bool = False

    def __init__(
        self,
        command: Sequence[str],
        cwd: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        artifact_patterns: Iterable[str] | None = None,
        run_id: str = "",
        metadata: Mapping[str, Any] | None = None,
        artifact_dir: str | Path | None = None,
        shell: bool = False,
    ) -> None:
        object.__setattr__(self, "command", tuple(str(part) for part in command))
        object.__setattr__(self, "cwd", Path(cwd) if cwd is not None else None)
        object.__setattr__(self, "env", dict(env) if env is not None else None)
        object.__setattr__(self, "timeout_policy", timeout_policy or TimeoutPolicy())
        object.__setattr__(
            self,
            "artifact_patterns",
            tuple(str(pattern) for pattern in artifact_patterns or ()),
        )
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        object.__setattr__(
            self,
            "artifact_dir",
            Path(artifact_dir) if artifact_dir is not None else None,
        )
        object.__setattr__(self, "shell", bool(shell))

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "cwd": str(self.cwd) if self.cwd else "",
            "env": dict(self.env or {}),
            "timeout_policy": self.timeout_policy.to_dict(),
            "artifact_patterns": list(self.artifact_patterns),
            "run_id": self.run_id,
            "metadata": dict(self.metadata),
            "artifact_dir": str(self.artifact_dir) if self.artifact_dir else "",
            "shell": self.shell,
        }


@dataclass(frozen=True, init=False)
class RunResult:
    run_id: str
    status: RunStatus
    command: tuple[str, ...]
    cwd: Path
    return_code: int | None
    started_at: str
    ended_at: str
    elapsed_seconds: float
    log: RunLog
    artifacts: tuple[RunArtifact, ...]
    diagnostics: DiagnosticReport
    metadata: dict[str, Any]
    artifact_dir: Path

    def __init__(
        self,
        *,
        status: RunStatus,
        command: Sequence[str],
        cwd: str | Path,
        artifact_dir: str | Path | None = None,
        return_code: int | None = None,
        returncode: int | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
        elapsed_seconds: float | None = None,
        duration_seconds: float | None = None,
        log: RunLog | None = None,
        artifacts: Iterable[RunArtifact] = (),
        diagnostics: DiagnosticReport | None = None,
        metadata: Mapping[str, Any] | None = None,
        run_id: str = "",
    ) -> None:
        now = _now_iso()
        resolved_return_code = return_code if return_code is not None else returncode
        elapsed = elapsed_seconds if elapsed_seconds is not None else duration_seconds
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "command", tuple(str(part) for part in command))
        object.__setattr__(self, "cwd", Path(cwd))
        object.__setattr__(self, "return_code", resolved_return_code)
        object.__setattr__(self, "started_at", started_at or now)
        object.__setattr__(self, "ended_at", ended_at or now)
        object.__setattr__(self, "elapsed_seconds", float(elapsed or 0.0))
        object.__setattr__(self, "log", log or RunLog())
        object.__setattr__(self, "artifacts", tuple(artifacts))
        object.__setattr__(self, "diagnostics", diagnostics or DiagnosticReport())
        object.__setattr__(self, "metadata", dict(metadata or {}))
        object.__setattr__(
            self,
            "artifact_dir",
            Path(artifact_dir) if artifact_dir is not None else Path(cwd),
        )

    @property
    def returncode(self) -> int | None:
        return self.return_code

    @property
    def duration_seconds(self) -> float:
        return self.elapsed_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "command": list(self.command),
            "cwd": str(self.cwd),
            "return_code": self.return_code,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "elapsed_seconds": self.elapsed_seconds,
            "log": self.log.to_dict(),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
            "artifact_dir": str(self.artifact_dir),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RunResult:
        return cls(
            run_id=str(data.get("run_id", "")),
            status=RunStatus(str(data["status"])),
            command=tuple(str(part) for part in data.get("command", ())),
            cwd=Path(str(data.get("cwd", "."))),
            artifact_dir=Path(str(data.get("artifact_dir") or data.get("cwd", "."))),
            return_code=data.get("return_code"),
            started_at=str(data.get("started_at", "")),
            ended_at=str(data.get("ended_at", "")),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
            log=RunLog.from_dict(data.get("log", {}) or {}),
            artifacts=tuple(
                RunArtifact.from_dict(artifact)
                for artifact in data.get("artifacts", ())
            ),
            diagnostics=DiagnosticReport.from_dict(data.get("diagnostics", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
        )


class ExternalCommandRunner:
    """Run external commands through the backend boundary, never the GUI."""

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
        request_or_executable: RunRequest | str | Path,
        args: Sequence[str] = (),
        *,
        cwd: str | Path | None = None,
        artifact_dir: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        artifact_patterns: Iterable[str] | None = None,
    ) -> RunResult:
        if isinstance(request_or_executable, RunRequest):
            request = request_or_executable
        else:
            request = RunRequest(
                [str(request_or_executable), *[str(arg) for arg in args]],
                cwd=cwd,
                env=env,
                timeout_policy=timeout_policy or self.timeout_policy,
                artifact_patterns=artifact_patterns,
                artifact_dir=artifact_dir,
            )
        return self._run_request(request)

    def run_command(
        self,
        command: Sequence[str],
        cwd: Path | str | None = None,
        timeout_seconds: float | None = None,
        env: Mapping[str, str] | None = None,
        artifact_patterns: Iterable[str] | None = None,
    ) -> RunResult:
        return self.run(
            RunRequest(
                command,
                cwd=cwd,
                env=env,
                timeout_policy=TimeoutPolicy(
                    timeout_seconds if timeout_seconds is not None else self.timeout_policy.seconds
                ),
                artifact_patterns=artifact_patterns,
            )
        )

    def collect_artifacts(
        self,
        run_dir: str | Path,
        patterns: Iterable[str],
    ) -> tuple[RunArtifact, ...]:
        return collect_artifacts(run_dir, patterns)

    def validate_request(self, request: RunRequest) -> DiagnosticReport:
        diagnostics = DiagnosticReport()
        if request.shell:
            diagnostics.add_error(
                DiagnosticCode.UNSAFE_SHELL_COMMAND,
                "Shell command execution is disabled by default.",
                hint="Pass commands as a list of arguments instead of a shell string.",
            )
        if not request.command:
            diagnostics.add_error(
                DiagnosticCode.COMMAND_FAILED,
                "Run request command is empty.",
                hint="Provide an executable and arguments as a list.",
            )
        cwd = request.cwd or Path.cwd()
        if not cwd.exists() or not cwd.is_dir():
            diagnostics.add_error(
                DiagnosticCode.INVALID_WORKING_DIRECTORY,
                f"Working directory does not exist: {cwd}",
                hint="Create the directory or choose an existing project run folder.",
                path=cwd,
            )
        diagnostics.extend(request.timeout_policy.diagnostics())
        return diagnostics

    def _run_request(self, request: RunRequest) -> RunResult:
        started_monotonic = time.monotonic()
        started_at = _now_iso()
        cwd = (request.cwd or Path.cwd()).expanduser()
        artifact_dir = (
            request.artifact_dir.expanduser()
            if request.artifact_dir is not None
            else (cwd if cwd.exists() else Path(tempfile.mkdtemp(prefix="osw-run-invalid-")))
        )
        diagnostics = self.validate_request(request)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        if diagnostics.has_errors:
            return self._result(
                request=request,
                status=RunStatus.FAILED,
                cwd=cwd,
                artifact_dir=artifact_dir,
                started_at=started_at,
                started_monotonic=started_monotonic,
                diagnostics=diagnostics,
            )

        resolution = self.registry.resolve(request.command[0])
        diagnostics.extend(resolution.diagnostics)
        if not resolution.found or resolution.resolved_path is None:
            return self._result(
                request=request,
                status=RunStatus.MISSING_EXECUTABLE,
                cwd=cwd,
                artifact_dir=artifact_dir,
                started_at=started_at,
                started_monotonic=started_monotonic,
                diagnostics=diagnostics,
            )

        command = (str(resolution.resolved_path), *request.command[1:])
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=_merged_env(request.env),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=os.name != "nt",
                creationflags=_process_creationflags(),
            )
        except OSError as exc:
            diagnostics.add_error(
                DiagnosticCode.COMMAND_FAILED,
                f"Could not start command: {exc}",
                command=command,
            )
            return self._result(
                request=request,
                status=RunStatus.FAILED,
                cwd=cwd,
                artifact_dir=artifact_dir,
                started_at=started_at,
                started_monotonic=started_monotonic,
                diagnostics=diagnostics,
                command=command,
            )

        try:
            stdout, stderr = process.communicate(timeout=request.timeout_policy.seconds)
        except subprocess.TimeoutExpired as exc:
            _terminate_process(process, request.timeout_policy)
            stdout, stderr = _communicate_after_timeout(process, request.timeout_policy)
            log = RunLog(_coerce_output(stdout or exc.stdout), _coerce_output(stderr or exc.stderr))
            diagnostics.add_error(
                DiagnosticCode.COMMAND_TIMEOUT,
                (
                    "Command timed out after "
                    f"{request.timeout_policy.seconds:g} seconds: {command[0]}"
                ),
                hint="Increase the timeout or inspect the tool log for a hang.",
                command=command,
            )
            return self._result(
                request=request,
                status=RunStatus.TIMED_OUT,
                cwd=cwd,
                artifact_dir=artifact_dir,
                started_at=started_at,
                started_monotonic=started_monotonic,
                diagnostics=diagnostics,
                command=command,
                log=log,
                artifact_patterns=request.artifact_patterns,
            )

        log = RunLog(stdout, stderr)
        self._add_log_diagnostics(log, diagnostics, command)
        status = RunStatus.COMPLETED if process.returncode == 0 else RunStatus.FAILED
        if status is RunStatus.COMPLETED:
            diagnostics.add_info(
                DiagnosticCode.COMMAND_COMPLETED,
                f"Command completed successfully: {command[0]}",
                command=command,
                return_code=process.returncode,
            )
        else:
            diagnostics.add_error(
                DiagnosticCode.COMMAND_FAILED,
                f"Command exited with status {process.returncode}: {command[0]}",
                hint="Inspect captured stderr/stdout for details.",
                command=command,
                return_code=process.returncode,
            )
        return self._result(
            request=request,
            status=status,
            cwd=cwd,
            artifact_dir=artifact_dir,
            started_at=started_at,
            started_monotonic=started_monotonic,
            diagnostics=diagnostics,
            command=command,
            return_code=process.returncode,
            log=log,
            artifact_patterns=request.artifact_patterns,
        )

    def _result(
        self,
        *,
        request: RunRequest,
        status: RunStatus,
        cwd: Path,
        artifact_dir: Path,
        started_at: str,
        started_monotonic: float,
        diagnostics: DiagnosticReport,
        command: Sequence[str] | None = None,
        return_code: int | None = None,
        log: RunLog | None = None,
        artifact_patterns: Iterable[str] = (),
    ) -> RunResult:
        resolved_command = tuple(command or request.command)
        resolved_log = log or RunLog()
        artifacts = self._write_artifacts(
            artifact_dir,
            resolved_command,
            return_code,
            status,
            resolved_log,
            diagnostics,
            artifact_patterns,
        )
        return RunResult(
            run_id=request.run_id,
            status=status,
            command=resolved_command,
            cwd=cwd,
            artifact_dir=artifact_dir,
            return_code=return_code,
            started_at=started_at,
            ended_at=_now_iso(),
            elapsed_seconds=time.monotonic() - started_monotonic,
            log=resolved_log,
            artifacts=artifacts,
            diagnostics=diagnostics,
            metadata=request.metadata,
        )

    @staticmethod
    def _write_artifacts(
        artifact_dir: Path,
        command: Sequence[str],
        return_code: int | None,
        status: RunStatus,
        log: RunLog,
        diagnostics: DiagnosticReport,
        artifact_patterns: Iterable[str],
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
                    "return_code": return_code,
                    "returncode": return_code,
                    "status": status.value,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        artifacts: list[RunArtifact] = [
            RunArtifact(artifact_dir, "directory", "Run artifact directory."),
            RunArtifact(stdout_path, "stdout", "Captured standard output."),
            RunArtifact(stderr_path, "stderr", "Captured standard error."),
            RunArtifact(summary_path, "summary", "Run status summary.", format="json"),
        ]
        artifacts.extend(
            collect_artifacts(artifact_dir, artifact_patterns, diagnostics=diagnostics)
        )
        return tuple(artifacts)

    @staticmethod
    def _add_log_diagnostics(
        log: RunLog,
        diagnostics: DiagnosticReport,
        command: Sequence[str],
    ) -> None:
        if log.stdout:
            diagnostics.add_info(
                DiagnosticCode.STDOUT_CAPTURED,
                "Captured command stdout.",
                command=command,
                metadata={"bytes": len(log.stdout.encode("utf-8"))},
            )
        if log.stderr:
            diagnostics.add_info(
                DiagnosticCode.STDERR_CAPTURED,
                "Captured command stderr.",
                command=command,
                metadata={"bytes": len(log.stderr.encode("utf-8"))},
            )


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _process_creationflags() -> int:
    if os.name != "nt":
        return 0
    return subprocess.CREATE_NEW_PROCESS_GROUP


def _terminate_process(process: subprocess.Popen[str], policy: TimeoutPolicy) -> None:
    if os.name == "nt" and policy.terminate_tree:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=max(policy.kill_grace_seconds, 1.0),
            check=False,
        )
        return
    if os.name != "nt" and policy.terminate_tree:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    process.terminate()


def _communicate_after_timeout(
    process: subprocess.Popen[str],
    policy: TimeoutPolicy,
) -> tuple[str | bytes | None, str | bytes | None]:
    try:
        return process.communicate(timeout=max(policy.kill_grace_seconds, 0.01))
    except subprocess.TimeoutExpired:
        if os.name != "nt" and policy.terminate_tree:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                process.kill()
        else:
            process.kill()
        return process.communicate()


def _merged_env(env: Mapping[str, str] | None) -> dict[str, str] | None:
    if env is None:
        return None
    merged = os.environ.copy()
    merged.update({str(key): str(value) for key, value in env.items()})
    return merged


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
