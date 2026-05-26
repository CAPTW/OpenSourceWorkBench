"""Safe GNU Octave runner for explicitly requested M-script execution."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.core.executables import (
    ExecutablePathRegistry,
    ExecutableResolution,
)
from osw.solvers.runner import ExternalCommandRunner, RunLog, RunRequest, RunResult, RunStatus

from .execution_policy import (
    OctaveExecutionPolicy,
    safety_gate_diagnostics,
)
from .importer import preview_mscript
from .script_model import SafetyFinding, ScriptPreview

OCTAVE_EXECUTABLE_NAMES = ("octave-cli", "octave", "octave.exe")


class OctaveExecutionNotConfirmed(RuntimeError):
    """Raised when a compatibility `run_script` call omits explicit approval."""


class OctaveRunStatus(StrEnum):
    READY = "ready"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    MISSING_EXECUTABLE = "missing_executable"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True, init=False)
class OctaveRunRequest:
    script_path: str
    preview: ScriptPreview | None
    working_directory: str
    run_id: str
    policy: OctaveExecutionPolicy
    arguments: tuple[str, ...]
    metadata: dict[str, Any]

    def __init__(
        self,
        script_path: str | Path,
        preview: ScriptPreview | None = None,
        working_directory: str | Path | None = None,
        run_id: str = "",
        policy: OctaveExecutionPolicy | None = None,
        arguments: Iterable[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "script_path", str(script_path))
        object.__setattr__(self, "preview", preview)
        object.__setattr__(
            self,
            "working_directory",
            str(working_directory) if working_directory is not None else "",
        )
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "policy", policy or OctaveExecutionPolicy())
        object.__setattr__(self, "arguments", tuple(str(arg) for arg in arguments or ()))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_path": self.script_path,
            "preview": self.preview.to_dict() if self.preview else None,
            "working_directory": self.working_directory,
            "run_id": self.run_id,
            "policy": self.policy.to_dict(),
            "arguments": list(self.arguments),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OctaveRunRequest:
        preview_payload = data.get("preview")
        return cls(
            script_path=str(data.get("script_path", "")),
            preview=(
                ScriptPreview.from_dict(preview_payload)
                if isinstance(preview_payload, Mapping)
                else None
            ),
            working_directory=str(data.get("working_directory", "")),
            run_id=str(data.get("run_id", "")),
            policy=OctaveExecutionPolicy.from_dict(data.get("policy", {}) or {}),
            arguments=tuple(str(arg) for arg in data.get("arguments", ())),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class OctaveRunResult:
    run_id: str
    status: OctaveRunStatus
    script_path: str
    workspace_dir: str
    command: tuple[str, ...] = field(default_factory=tuple)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    combined_log: str = ""
    elapsed_seconds: float = 0.0
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)
    safety_findings: tuple[SafetyFinding, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.combined_log:
            parts = [part.rstrip("\n") for part in (self.stdout, self.stderr) if part]
            object.__setattr__(self, "combined_log", "\n".join(parts))
        object.__setattr__(self, "command", tuple(str(part) for part in self.command))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "safety_findings", tuple(self.safety_findings))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def artifact_dir(self) -> Path:
        return Path(self.workspace_dir) if self.workspace_dir else Path(".")

    @property
    def returncode(self) -> int | None:
        return self.return_code

    @property
    def log(self) -> RunLog:
        return RunLog(self.stdout, self.stderr, self.combined_log)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "script_path": self.script_path,
            "workspace_dir": self.workspace_dir,
            "command": list(self.command),
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "combined_log": self.combined_log,
            "elapsed_seconds": self.elapsed_seconds,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "safety_findings": [finding.to_dict() for finding in self.safety_findings],
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OctaveRunResult:
        return cls(
            run_id=str(data.get("run_id", "")),
            status=OctaveRunStatus(str(data.get("status", OctaveRunStatus.FAILED.value))),
            script_path=str(data.get("script_path", "")),
            workspace_dir=str(data.get("workspace_dir", "")),
            command=tuple(str(part) for part in data.get("command", ())),
            return_code=data.get("return_code"),
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            combined_log=str(data.get("combined_log", "")),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
            artifacts=tuple(
                RunArtifact.from_dict(artifact)
                for artifact in data.get("artifacts", ())
                if isinstance(artifact, dict)
            ),
            safety_findings=tuple(
                SafetyFinding.from_dict(finding)
                for finding in data.get("safety_findings", ())
                if isinstance(finding, Mapping)
            ),
            diagnostics=DiagnosticReport.from_dict(data.get("diagnostics", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def find_octave_executable(
    registry: ExecutablePathRegistry | None = None,
) -> ExecutableResolution:
    """Resolve GNU Octave without executing it."""

    resolver = registry or ExecutablePathRegistry()
    resolution = resolver.resolve_any(OCTAVE_EXECUTABLE_NAMES)
    if resolution.found:
        return resolution
    report = DiagnosticReport()
    report.extend(resolution.diagnostics)
    report.add_error(
        "octave-executable-not-found",
        "GNU Octave executable was not found.",
        hint="Install GNU Octave or configure the executable path in Plugin Manager.",
        field="octave",
    )
    return ExecutableResolution("octave", None, "missing", report)


def octave_available(registry: ExecutablePathRegistry | None = None) -> bool:
    return find_octave_executable(registry).found


class OctaveRunner:
    """Execute previewed `.m` files through `ExternalCommandRunner` only."""

    def __init__(
        self,
        *,
        executable_registry: ExecutablePathRegistry | None = None,
        command_runner: ExternalCommandRunner | None = None,
        executable: str | Path | None = None,
        registry: ExecutablePathRegistry | None = None,
        timeout_policy: object | None = None,
    ) -> None:
        self.executable_registry = executable_registry or registry or ExecutablePathRegistry()
        self.command_runner = command_runner or ExternalCommandRunner(
            registry=self.executable_registry
        )
        self.executable = str(executable) if executable is not None else ""
        self.default_policy = _policy_from_timeout(timeout_policy)

    def find_executable(self) -> ExecutableResolution:
        if self.executable:
            resolution = self.executable_registry.resolve(self.executable)
            if resolution.found:
                return resolution
            report = DiagnosticReport()
            report.extend(resolution.diagnostics)
            report.add_error(
                "octave-executable-not-found",
                "GNU Octave executable was not found.",
                hint="Install GNU Octave or configure the executable path in Plugin Manager.",
                field=self.executable,
            )
            return ExecutableResolution(str(self.executable), None, "missing", report)
        return find_octave_executable(self.executable_registry)

    def detect_executable(self, executable: str | Path | None = None) -> ExecutableResolution:
        if executable is not None:
            return self.executable_registry.resolve(executable)
        return self.find_executable()

    def validate_request(self, request: OctaveRunRequest) -> DiagnosticReport:
        report = DiagnosticReport()
        report.extend(request.policy.diagnostics())
        script = Path(request.script_path).expanduser()
        if not script.exists():
            report.add_error(
                "mscript-file-missing",
                f"M-script file does not exist: {script}",
                hint="Choose an existing .m file before running Octave.",
                path=script,
            )
            return report
        if script.suffix.lower() != ".m":
            report.add_error(
                "mscript-unsupported-extension",
                "Only .m scripts can be run through the GNU Octave runner.",
                hint="Preview or convert unsupported files before execution.",
                path=script,
            )
        return report

    def run(self, request: OctaveRunRequest) -> OctaveRunResult:
        run_id = request.run_id or _create_run_id()
        policy = request.policy
        diagnostics = self.validate_request(request)
        script = Path(request.script_path).expanduser()
        preview = request.preview
        if not diagnostics.has_errors:
            preview_result = preview_mscript(script)
            diagnostics.extend(preview_result.diagnostics)
            preview = preview or preview_result.preview
        safety_findings = tuple(preview.safety_findings) if preview is not None else ()
        safety_report = safety_gate_diagnostics(safety_findings, policy)
        diagnostics.extend(safety_report)
        workspace = self.prepare_workspace(request, run_id=run_id)

        if diagnostics.has_errors:
            status = (
                OctaveRunStatus.BLOCKED_BY_SAFETY
                if safety_report.has_errors
                else OctaveRunStatus.FAILED
            )
            return _result(
                run_id=run_id,
                status=status,
                script_path=str(script),
                workspace_dir=workspace,
                diagnostics=diagnostics,
                safety_findings=safety_findings,
                metadata=request.metadata,
            )

        resolution = self.find_executable()
        diagnostics.extend(resolution.diagnostics)
        if not resolution.found or resolution.resolved_path is None:
            return _result(
                run_id=run_id,
                status=OctaveRunStatus.MISSING_EXECUTABLE,
                script_path=str(script),
                workspace_dir=workspace,
                diagnostics=diagnostics,
                safety_findings=safety_findings,
                metadata=request.metadata,
            )

        workspace_script = _workspace_script_path(script, workspace, policy)
        if policy.copy_script_to_workspace:
            workspace.mkdir(parents=True, exist_ok=True)
            shutil.copy2(script, workspace_script)

        command = self._build_command(
            executable=resolution.resolved_path,
            script_path=workspace_script,
            arguments=request.arguments,
        )
        run_result = self.command_runner.run(
            RunRequest(
                command,
                cwd=workspace,
                env=policy.env_overrides,
                timeout_policy=policy.timeout_policy(),
                artifact_dir=workspace,
                run_id=run_id,
                metadata={
                    **request.metadata,
                    "script_path": str(script),
                    "workspace_dir": str(workspace),
                },
            )
        )
        diagnostics.extend(run_result.diagnostics)
        artifacts = _octave_artifacts(
            run_result,
            workspace,
            workspace_script,
            policy,
            diagnostics,
        )
        return OctaveRunResult(
            run_id=run_id,
            status=_octave_status_from_run_status(run_result.status),
            script_path=str(script),
            workspace_dir=str(workspace),
            command=run_result.command,
            return_code=run_result.return_code,
            stdout=run_result.log.stdout,
            stderr=run_result.log.stderr,
            combined_log=run_result.log.combined,
            elapsed_seconds=run_result.elapsed_seconds,
            artifacts=artifacts,
            safety_findings=safety_findings,
            diagnostics=diagnostics,
            metadata={
                **request.metadata,
                "run_result": run_result.to_dict(),
                "executable_source": resolution.source,
            },
        )

    def run_script(
        self,
        script_path: str | Path,
        *,
        policy: OctaveExecutionPolicy | None = None,
        working_directory: str | Path | None = None,
        artifact_dir: str | Path | None = None,
        allow_execution: bool = False,
        allow_unsafe: bool = False,
        allow_high_risk: bool | None = None,
        allow_blocked: bool = False,
        arguments: Sequence[str] = (),
        env: Mapping[str, str] | None = None,
        timeout_policy: object | None = None,
    ) -> OctaveRunResult:
        """Compatibility wrapper requiring explicit `allow_execution=True`."""

        if not allow_execution:
            msg = "GNU Octave execution requires explicit execution approval."
            raise OctaveExecutionNotConfirmed(msg)
        resolved_policy = policy or self.default_policy
        if timeout_policy is not None:
            resolved_policy = _policy_from_timeout(timeout_policy, base=resolved_policy)
        if env:
            resolved_policy = OctaveExecutionPolicy.from_dict(
                {**resolved_policy.to_dict(), "env_overrides": dict(env)}
            )
        if allow_unsafe or allow_high_risk is not None or allow_blocked:
            resolved_policy = OctaveExecutionPolicy.from_dict(
                {
                    **resolved_policy.to_dict(),
                    "allow_high_risk": bool(allow_unsafe or allow_high_risk),
                    "allow_blocked": bool(allow_blocked),
                }
            )
        return self.run(
            OctaveRunRequest(
                script_path=script_path,
                working_directory=working_directory or artifact_dir,
                policy=resolved_policy,
                arguments=arguments,
            )
        )

    def build_command(self, request: OctaveRunRequest, workspace_dir: str | Path) -> list[str]:
        resolution = self.find_executable()
        executable = resolution.resolved_path or Path(self.executable or "octave")
        script = _workspace_script_path(
            Path(request.script_path).expanduser(),
            Path(workspace_dir),
            request.policy,
        )
        return self._build_command(
            executable=executable,
            script_path=script,
            arguments=request.arguments,
        )

    def prepare_workspace(self, request: OctaveRunRequest, *, run_id: str | None = None) -> Path:
        policy = request.policy
        if not policy.isolate_workspace:
            if request.working_directory:
                workspace = Path(request.working_directory).expanduser()
            else:
                workspace = Path(request.script_path).expanduser().parent
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace.resolve()

        if request.working_directory:
            root = Path(request.working_directory).expanduser()
            workspace = root / (run_id or request.run_id or _create_run_id())
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace.resolve()

        return Path(tempfile.mkdtemp(prefix=f"osw-octave-{run_id or _create_run_id()}-")).resolve()

    def collect_artifacts(
        self,
        workspace_dir: str | Path,
        patterns: Iterable[str],
    ) -> tuple[RunArtifact, ...]:
        report = DiagnosticReport()
        policy = OctaveExecutionPolicy(artifact_patterns=patterns)
        return _collect_workspace_artifacts(Path(workspace_dir), None, policy, report)

    @staticmethod
    def _build_command(
        *,
        executable: Path,
        script_path: Path,
        arguments: Sequence[str],
    ) -> list[str]:
        return [
            str(executable),
            "--no-gui",
            "--quiet",
            str(script_path.name if not script_path.is_absolute() else script_path),
            *[str(argument) for argument in arguments],
        ]


def _create_run_id() -> str:
    return f"octave_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"


def _policy_from_timeout(
    timeout_policy: object | None,
    *,
    base: OctaveExecutionPolicy | None = None,
) -> OctaveExecutionPolicy:
    policy = base or OctaveExecutionPolicy()
    if timeout_policy is None:
        return policy
    timeout_seconds = getattr(
        timeout_policy,
        "timeout_seconds",
        getattr(timeout_policy, "seconds", None),
    )
    kill_grace_seconds = getattr(timeout_policy, "kill_grace_seconds", policy.kill_grace_seconds)
    return OctaveExecutionPolicy.from_dict(
        {
            **policy.to_dict(),
            "timeout_seconds": float(timeout_seconds or policy.timeout_seconds),
            "kill_grace_seconds": float(kill_grace_seconds),
        }
    )


def _workspace_script_path(script: Path, workspace: Path, policy: OctaveExecutionPolicy) -> Path:
    return workspace / script.name if policy.copy_script_to_workspace else script.resolve()


def _octave_status_from_run_status(status: RunStatus) -> OctaveRunStatus:
    return {
        RunStatus.COMPLETED: OctaveRunStatus.COMPLETED,
        RunStatus.FAILED: OctaveRunStatus.FAILED,
        RunStatus.TIMED_OUT: OctaveRunStatus.TIMED_OUT,
        RunStatus.CANCELLED: OctaveRunStatus.CANCELLED,
        RunStatus.MISSING_EXECUTABLE: OctaveRunStatus.MISSING_EXECUTABLE,
    }.get(status, OctaveRunStatus.FAILED)


def _octave_artifacts(
    run_result: RunResult,
    workspace: Path,
    workspace_script: Path,
    policy: OctaveExecutionPolicy,
    diagnostics: DiagnosticReport,
) -> tuple[RunArtifact, ...]:
    artifacts = list(run_result.artifacts)
    artifacts.append(
        RunArtifact(
            workspace,
            "octave_workspace",
            "Isolated GNU Octave workspace.",
            format="directory",
        )
    )
    if policy.capture_artifacts:
        artifacts.extend(
            _collect_workspace_artifacts(
                workspace,
                workspace_script if policy.copy_script_to_workspace else None,
                policy,
                diagnostics,
            )
        )
    return tuple(_deduplicate_artifacts(artifacts))


def _collect_workspace_artifacts(
    workspace: Path,
    workspace_script: Path | None,
    policy: OctaveExecutionPolicy,
    diagnostics: DiagnosticReport,
) -> tuple[RunArtifact, ...]:
    known_names = {"run_summary.json"}
    artifacts: list[RunArtifact] = []
    for pattern in policy.artifact_patterns:
        matches = sorted(path for path in workspace.glob(pattern) if path.is_file())
        if workspace_script is not None:
            matches = [path for path in matches if path.resolve() != workspace_script.resolve()]
        matches = [path for path in matches if path.name not in known_names]
        if not matches and policy.warn_missing_artifacts:
            diagnostics.add_warning(
                "artifact-missing",
                f"No artifacts matched pattern: {pattern}",
                hint="Check whether the script created the expected output.",
                path=workspace,
                metadata={"pattern": pattern},
            )
            continue
        for path in matches:
            artifacts.append(
                RunArtifact(
                    path,
                    "octave_artifact",
                    "File generated in the Octave workspace.",
                    format=path.suffix.lstrip("."),
                )
            )
    return tuple(artifacts)


def _deduplicate_artifacts(artifacts: Iterable[RunArtifact]) -> tuple[RunArtifact, ...]:
    deduped: dict[tuple[str, str], RunArtifact] = {}
    for artifact in artifacts:
        deduped[(str(artifact.path), artifact.role)] = artifact
    return tuple(deduped.values())


def _result(
    *,
    run_id: str,
    status: OctaveRunStatus,
    script_path: str,
    workspace_dir: Path,
    diagnostics: DiagnosticReport,
    safety_findings: Iterable[SafetyFinding] = (),
    metadata: Mapping[str, Any] | None = None,
    command: Sequence[str] = (),
    return_code: int | None = None,
) -> OctaveRunResult:
    artifacts = (
        RunArtifact(
            workspace_dir,
            "octave_workspace",
            "GNU Octave workspace.",
            format="directory",
            exists=workspace_dir.exists(),
        ),
    )
    return OctaveRunResult(
        run_id=run_id,
        status=status,
        script_path=script_path,
        workspace_dir=str(workspace_dir),
        command=tuple(command),
        return_code=return_code,
        artifacts=artifacts,
        safety_findings=tuple(safety_findings),
        diagnostics=diagnostics,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "OCTAVE_EXECUTABLE_NAMES",
    "OctaveExecutionNotConfirmed",
    "OctaveExecutionPolicy",
    "OctaveRunRequest",
    "OctaveRunResult",
    "OctaveRunStatus",
    "OctaveRunner",
    "find_octave_executable",
    "octave_available",
]
