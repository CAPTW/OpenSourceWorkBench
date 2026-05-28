"""Safe CalculiX ``ccx`` runner binding.

This module only runs an existing ``.inp`` deck through the shared OSW backend
runner after an explicit request. It does not parse CalculiX result files.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.core.executables import (
    ExecutablePathRegistry,
    ExecutableResolution,
)
from osw.solvers.runner import (
    ExternalCommandRunner,
    RunLog,
    RunRequest,
    RunResult,
    RunStatus,
    TimeoutPolicy,
)


class CalculiXRunStatus(StrEnum):
    """Status values exposed by the CalculiX runner binding."""

    READY = "ready"
    MISSING_EXECUTABLE = "missing_executable"
    MISSING_INPUT_DECK = "missing_input_deck"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


DEFAULT_ARTIFACT_PATTERNS = (
    ".dat",
    ".frd",
    ".sta",
    ".cvg",
    ".12d",
    ".log",
)

ARTIFACT_ROLES = {
    ".inp": ("input_deck", "CalculiX input deck.", "inp"),
    ".dat": ("dat_result", "CalculiX DAT result artifact.", "dat"),
    ".frd": ("frd_result", "CalculiX FRD result artifact.", "frd"),
    ".sta": ("status", "CalculiX status artifact.", "sta"),
    ".cvg": ("convergence", "CalculiX convergence artifact.", "cvg"),
    ".12d": ("unknown", "CalculiX 12d artifact.", "12d"),
    ".log": ("unknown", "CalculiX log artifact.", "log"),
}


@dataclass(frozen=True)
class CalculiXRunPolicy:
    """Execution policy for explicit CalculiX runs."""

    timeout_seconds: float = 60.0
    kill_grace_seconds: float = 1.0
    isolate_case_dir: bool = True
    copy_input_deck: bool = True
    artifact_patterns: tuple[str, ...] = DEFAULT_ARTIFACT_PATTERNS
    env_overrides: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_seconds": self.timeout_seconds,
            "kill_grace_seconds": self.kill_grace_seconds,
            "isolate_case_dir": self.isolate_case_dir,
            "copy_input_deck": self.copy_input_deck,
            "artifact_patterns": list(self.artifact_patterns),
            "env_overrides": dict(self.env_overrides),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXRunPolicy:
        return cls(
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            kill_grace_seconds=float(data.get("kill_grace_seconds", 1.0)),
            isolate_case_dir=bool(data.get("isolate_case_dir", True)),
            copy_input_deck=bool(data.get("copy_input_deck", True)),
            artifact_patterns=tuple(
                str(item) for item in data.get("artifact_patterns", DEFAULT_ARTIFACT_PATTERNS)
            ),
            env_overrides={
                str(key): str(value)
                for key, value in dict(data.get("env_overrides", {}) or {}).items()
            },
            metadata=dict(data.get("metadata", {}) or {}),
        )

    def timeout_policy(self) -> TimeoutPolicy:
        return TimeoutPolicy(
            timeout_seconds=self.timeout_seconds,
            kill_grace_seconds=self.kill_grace_seconds,
        )


@dataclass(frozen=True)
class CalculiXRunRequest:
    """Explicit request to run an existing CalculiX input deck."""

    input_deck_path: Path
    case_dir: Path | None = None
    job_name: str = ""
    run_id: str = ""
    policy: CalculiXRunPolicy = field(default_factory=CalculiXRunPolicy)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        input_deck_path: str | Path,
        *,
        case_dir: str | Path | None = None,
        job_name: str = "",
        run_id: str = "",
        policy: CalculiXRunPolicy | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "input_deck_path", Path(input_deck_path))
        object.__setattr__(self, "case_dir", Path(case_dir) if case_dir else None)
        object.__setattr__(self, "job_name", str(job_name))
        object.__setattr__(self, "run_id", str(run_id))
        object.__setattr__(self, "policy", policy or CalculiXRunPolicy())
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_deck_path": str(self.input_deck_path),
            "case_dir": str(self.case_dir) if self.case_dir else "",
            "job_name": self.job_name,
            "run_id": self.run_id,
            "policy": self.policy.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXRunRequest:
        return cls(
            input_deck_path=Path(str(data.get("input_deck_path", ""))),
            case_dir=Path(str(data["case_dir"])) if data.get("case_dir") else None,
            job_name=str(data.get("job_name", "")),
            run_id=str(data.get("run_id", "")),
            policy=CalculiXRunPolicy.from_dict(data.get("policy", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXRunResult:
    """Structured CalculiX run result with logs, artifacts, and diagnostics."""

    run_id: str
    status: CalculiXRunStatus
    input_deck_path: Path
    case_dir: Path
    job_name: str
    command: tuple[str, ...] = field(default_factory=tuple)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    combined_log: str = ""
    elapsed_seconds: float = 0.0
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    run_result: RunResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "input_deck_path": str(self.input_deck_path),
            "case_dir": str(self.case_dir),
            "job_name": self.job_name,
            "command": list(self.command),
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "combined_log": self.combined_log,
            "elapsed_seconds": self.elapsed_seconds,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": self.diagnostics.to_dict(),
            "run_result": self.run_result.to_dict() if self.run_result else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXRunResult:
        run_result_data = data.get("run_result")
        return cls(
            run_id=str(data.get("run_id", "")),
            status=CalculiXRunStatus(str(data.get("status", CalculiXRunStatus.FAILED.value))),
            input_deck_path=Path(str(data.get("input_deck_path", ""))),
            case_dir=Path(str(data.get("case_dir", "."))),
            job_name=str(data.get("job_name", "")),
            command=tuple(str(item) for item in data.get("command", ()) or ()),
            return_code=(
                int(data["return_code"])
                if data.get("return_code") not in (None, "")
                else None
            ),
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            combined_log=str(data.get("combined_log", "")),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
            artifacts=tuple(
                RunArtifact.from_dict(dict(item))
                for item in data.get("artifacts", ()) or ()
                if isinstance(item, Mapping)
            ),
            diagnostics=DiagnosticReport.from_dict(data.get("diagnostics", {}) or {}),
            run_result=(
                RunResult.from_dict(dict(run_result_data))
                if isinstance(run_result_data, Mapping)
                else None
            ),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def find_ccx_executable(
    registry: ExecutablePathRegistry | None = None,
) -> ExecutableResolution:
    """Resolve CalculiX ``ccx`` without executing it."""

    active_registry = registry or ExecutablePathRegistry()
    names = ("ccx", "ccx.exe") if os.name == "nt" else ("ccx",)
    resolution = active_registry.resolve_any(names)
    if resolution.found:
        return resolution
    diagnostics = DiagnosticReport()
    diagnostics.extend(resolution.diagnostics)
    diagnostics.add_error(
        "ccx-executable-not-found",
        "CalculiX executable `ccx` was not found.",
        hint="Install CalculiX or configure the executable path in Plugin Manager.",
        field="ccx",
    )
    return ExecutableResolution(
        name=resolution.name or "ccx",
        resolved_path=None,
        source=resolution.source,
        diagnostics=diagnostics,
    )


def ccx_available(registry: ExecutablePathRegistry | None = None) -> bool:
    """Return whether ``ccx`` resolves without running it."""

    return find_ccx_executable(registry).found


class CalculiXRunner:
    """Run prepared CalculiX decks through ``ExternalCommandRunner``."""

    def __init__(
        self,
        *,
        executable_registry: ExecutablePathRegistry | None = None,
        command_runner: ExternalCommandRunner | None = None,
    ) -> None:
        self.executable_registry = executable_registry or ExecutablePathRegistry()
        self.command_runner = command_runner or ExternalCommandRunner(
            registry=self.executable_registry
        )

    def validate_request(self, request: CalculiXRunRequest) -> DiagnosticReport:
        diagnostics = DiagnosticReport()
        deck = request.input_deck_path.expanduser()
        if not deck.exists():
            diagnostics.add_error(
                "missing-input-deck",
                f"CalculiX input deck does not exist: {deck}",
                hint="Generate or choose a .inp deck before running ccx.",
                path=deck,
            )
            return diagnostics
        if deck.suffix.lower() != ".inp":
            diagnostics.add_error(
                "invalid-input-deck-extension",
                f"CalculiX runner expects a .inp input deck, got: {deck.name}",
                hint="Choose a CalculiX input deck with the .inp extension.",
                path=deck,
            )
        if (
            request.case_dir is not None
            and request.case_dir.exists()
            and not request.case_dir.is_dir()
        ):
            diagnostics.add_error(
                "invalid-case-directory",
                f"CalculiX case path is not a directory: {request.case_dir}",
                hint="Choose a directory for the isolated CalculiX case.",
                path=request.case_dir,
            )
        diagnostics.extend(request.policy.timeout_policy().diagnostics())
        return diagnostics

    def run_input_deck(
        self,
        path: str | Path,
        *,
        policy: CalculiXRunPolicy | None = None,
        case_dir: str | Path | None = None,
        job_name: str | None = None,
        run_id: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> CalculiXRunResult:
        request = CalculiXRunRequest(
            input_deck_path=path,
            case_dir=case_dir,
            job_name=job_name or "",
            run_id=run_id,
            policy=policy,
            metadata=metadata,
        )
        return self.run(request)

    def run(self, request: CalculiXRunRequest) -> CalculiXRunResult:
        diagnostics = self.validate_request(request)
        run_id = request.run_id or _new_run_id()
        deck = request.input_deck_path.expanduser()
        job_name = _job_name(request.job_name or deck.stem)
        case_dir = request.case_dir or deck.parent
        if diagnostics.has_errors:
            status = (
                CalculiXRunStatus.MISSING_INPUT_DECK
                if any(message.code == "missing-input-deck" for message in diagnostics.messages)
                else CalculiXRunStatus.FAILED
            )
            return _result_from_parts(
                run_id=run_id,
                status=status,
                input_deck_path=deck,
                case_dir=case_dir,
                job_name=job_name,
                command=("ccx", job_name),
                diagnostics=diagnostics,
                metadata=request.metadata,
            )

        resolution = find_ccx_executable(self.executable_registry)
        diagnostics.extend(resolution.diagnostics)
        if not resolution.found or resolution.resolved_path is None:
            return _result_from_parts(
                run_id=run_id,
                status=CalculiXRunStatus.MISSING_EXECUTABLE,
                input_deck_path=deck,
                case_dir=case_dir,
                job_name=job_name,
                command=("ccx", job_name),
                diagnostics=diagnostics,
                metadata=request.metadata,
            )

        try:
            case_dir, copied_deck = self.prepare_case_dir(request, job_name=job_name)
        except OSError as exc:
            diagnostics.add_error(
                "invalid-case-directory",
                f"Could not prepare CalculiX case directory: {exc}",
                hint="Choose a writable run directory.",
                path=request.case_dir or deck.parent,
            )
            return _result_from_parts(
                run_id=run_id,
                status=CalculiXRunStatus.FAILED,
                input_deck_path=deck,
                case_dir=case_dir,
                job_name=job_name,
                command=(str(resolution.resolved_path), job_name),
                diagnostics=diagnostics,
                metadata=request.metadata,
            )

        command = self.build_command(request, case_dir, resolution.resolved_path, job_name)
        runner_request = RunRequest(
            command,
            cwd=case_dir,
            env=request.policy.env_overrides,
            timeout_policy=request.policy.timeout_policy(),
            artifact_patterns=(),
            artifact_dir=case_dir,
            run_id=run_id,
            metadata={
                "solver": "calculix",
                "input_deck_path": str(copied_deck),
                **dict(request.metadata),
            },
        )
        run_result = self.command_runner.run(runner_request)
        diagnostics.extend(run_result.diagnostics)
        status = _status_from_run_result(run_result)
        artifacts = collect_calculix_artifacts(
            case_dir,
            job_name,
            run_result=run_result,
            diagnostics=diagnostics,
            success=status is CalculiXRunStatus.COMPLETED,
            artifact_patterns=request.policy.artifact_patterns,
        )
        if status is CalculiXRunStatus.COMPLETED:
            diagnostics.add_info(
                "ccx-run-completed",
                "CalculiX ccx run completed.",
                command=command,
                return_code=run_result.return_code,
                metadata={"job_name": job_name},
            )
        elif status is CalculiXRunStatus.TIMED_OUT:
            diagnostics.add_error(
                "ccx-run-timed-out",
                "CalculiX ccx run timed out.",
                command=command,
                return_code=run_result.return_code,
            )
        else:
            diagnostics.add_error(
                "ccx-run-failed",
                "CalculiX ccx run failed.",
                command=command,
                return_code=run_result.return_code,
            )
        return CalculiXRunResult(
            run_id=run_id,
            status=status,
            input_deck_path=deck,
            case_dir=case_dir,
            job_name=job_name,
            command=tuple(command),
            return_code=run_result.return_code,
            stdout=_tail_text(run_result.log.stdout),
            stderr=_tail_text(run_result.log.stderr),
            combined_log=_tail_text(run_result.log.combined),
            elapsed_seconds=run_result.elapsed_seconds,
            artifacts=artifacts,
            diagnostics=diagnostics,
            run_result=run_result,
            metadata={
                "copied_input_deck_path": str(copied_deck),
                "isolated_case_dir": request.policy.isolate_case_dir,
                **dict(request.metadata),
            },
        )

    def prepare_case_dir(
        self,
        request: CalculiXRunRequest,
        *,
        job_name: str,
    ) -> tuple[Path, Path]:
        deck = request.input_deck_path.expanduser().resolve()
        if request.policy.isolate_case_dir:
            case_dir = (
                request.case_dir.expanduser()
                if request.case_dir is not None
                else Path(tempfile.mkdtemp(prefix="osw-calculix-"))
            )
        else:
            case_dir = request.case_dir.expanduser() if request.case_dir else deck.parent
        case_dir.mkdir(parents=True, exist_ok=True)
        target_deck = case_dir / f"{job_name}.inp"
        if request.policy.copy_input_deck:
            if deck != target_deck.resolve():
                shutil.copy2(deck, target_deck)
            return case_dir.resolve(), target_deck.resolve()
        if target_deck.resolve() != deck:
            diagnostics_path = case_dir / f"{job_name}.inp"
            msg = (
                "copy_input_deck is false, but the deck is not already located "
                f"at {diagnostics_path}."
            )
            raise OSError(msg)
        return case_dir.resolve(), deck

    def build_command(
        self,
        request: CalculiXRunRequest,
        case_dir: str | Path,
        ccx_path: str | Path,
        job_name: str | None = None,
    ) -> list[str]:
        del request, case_dir
        return [str(ccx_path), _job_name(job_name or "calculix")]


def collect_calculix_artifacts(
    case_dir: str | Path,
    job_name: str,
    *,
    run_result: RunResult | None = None,
    diagnostics: DiagnosticReport | None = None,
    success: bool = False,
    artifact_patterns: Iterable[str] = DEFAULT_ARTIFACT_PATTERNS,
) -> tuple[RunArtifact, ...]:
    """Collect known CalculiX artifacts without parsing result content."""

    root = Path(case_dir).resolve()
    report = diagnostics if diagnostics is not None else DiagnosticReport()
    artifacts: list[RunArtifact] = []
    for path in _known_artifact_paths(root, job_name, artifact_patterns):
        if not _is_under(path, root):
            report.add_warning(
                "artifact-outside-case-directory",
                f"Skipped CalculiX artifact outside case directory: {path}",
                path=path,
            )
            continue
        if path.exists():
            artifact = _artifact_for_path(path)
            artifacts.append(artifact)
            report.add_info(
                "artifact-collected",
                f"Collected CalculiX artifact: {path.name}",
                path=path,
                metadata={"role": artifact.role, "format": artifact.format},
            )
    if run_result is not None:
        artifacts.extend(_standard_runner_artifacts(root, run_result))
    if success:
        _add_success_artifact_warnings(root, job_name, report)
    return _dedupe_artifacts(artifacts)


def _known_artifact_paths(
    case_dir: Path,
    job_name: str,
    artifact_patterns: Iterable[str],
) -> list[Path]:
    paths = [case_dir / f"{job_name}.inp"]
    for pattern in artifact_patterns:
        normalized = str(pattern)
        if normalized.startswith("."):
            paths.append(case_dir / f"{job_name}{normalized}")
        elif "*" in normalized:
            paths.extend(sorted(case_dir.glob(normalized)))
        else:
            paths.append(case_dir / normalized)
    paths.extend(sorted(case_dir.glob("*.log")))
    return sorted(set(paths), key=lambda item: item.name)


def _standard_runner_artifacts(case_dir: Path, run_result: RunResult) -> list[RunArtifact]:
    artifacts: list[RunArtifact] = []
    for path, role, description, fmt in (
        (case_dir / "stdout.txt", "stdout_log", "Captured ccx stdout.", "txt"),
        (case_dir / "stderr.txt", "stderr_log", "Captured ccx stderr.", "txt"),
        (case_dir / "run_summary.json", "run_summary", "Backend runner summary.", "json"),
    ):
        if path.exists():
            artifacts.append(RunArtifact(path, role, description, format=fmt))
    for artifact in run_result.artifacts:
        if artifact.path not in {item.path for item in artifacts} and _is_under(
            artifact.path,
            case_dir,
        ):
            artifacts.append(artifact)
    return artifacts


def _add_success_artifact_warnings(
    case_dir: Path,
    job_name: str,
    diagnostics: DiagnosticReport,
) -> None:
    result_paths = [
        case_dir / f"{job_name}.dat",
        case_dir / f"{job_name}.frd",
        case_dir / f"{job_name}.sta",
        case_dir / f"{job_name}.cvg",
        case_dir / f"{job_name}.12d",
    ]
    for suffix in (".dat", ".frd"):
        path = case_dir / f"{job_name}{suffix}"
        if not path.exists():
            diagnostics.add_warning(
                "artifact-missing",
                f"CalculiX completed but expected artifact is missing: {path.name}",
                hint="Inspect stdout/stderr and the input deck for solver output settings.",
                path=path,
            )
    if not any(path.exists() for path in result_paths):
        diagnostics.add_warning(
            "artifact-missing",
            "CalculiX completed but no result artifacts were found.",
            hint="Inspect stdout/stderr and verify the deck requests solver output.",
            path=case_dir,
        )


def _artifact_for_path(path: Path) -> RunArtifact:
    role, description, fmt = ARTIFACT_ROLES.get(
        path.suffix.lower(),
        ("unknown", "CalculiX artifact.", path.suffix.lstrip(".")),
    )
    return RunArtifact(path, role, description, format=fmt)


def _status_from_run_result(result: RunResult) -> CalculiXRunStatus:
    if result.status is RunStatus.COMPLETED:
        return CalculiXRunStatus.COMPLETED
    if result.status is RunStatus.TIMED_OUT:
        return CalculiXRunStatus.TIMED_OUT
    if result.status is RunStatus.MISSING_EXECUTABLE:
        return CalculiXRunStatus.MISSING_EXECUTABLE
    if result.status is RunStatus.CANCELLED:
        return CalculiXRunStatus.CANCELLED
    return CalculiXRunStatus.FAILED


def _result_from_parts(
    *,
    run_id: str,
    status: CalculiXRunStatus,
    input_deck_path: Path,
    case_dir: Path,
    job_name: str,
    command: Sequence[str],
    diagnostics: DiagnosticReport,
    metadata: Mapping[str, Any],
) -> CalculiXRunResult:
    return CalculiXRunResult(
        run_id=run_id,
        status=status,
        input_deck_path=input_deck_path,
        case_dir=case_dir,
        job_name=job_name,
        command=tuple(command),
        diagnostics=diagnostics,
        metadata=dict(metadata),
        run_result=RunResult(
            run_id=run_id,
            status=RunStatus.MISSING_EXECUTABLE
            if status is CalculiXRunStatus.MISSING_EXECUTABLE
            else RunStatus.FAILED,
            command=tuple(command),
            cwd=case_dir,
            artifact_dir=case_dir,
            log=RunLog(),
            diagnostics=diagnostics,
        ),
    )


def _dedupe_artifacts(artifacts: Iterable[RunArtifact]) -> tuple[RunArtifact, ...]:
    seen: set[tuple[Path, str]] = set()
    unique: list[RunArtifact] = []
    for artifact in artifacts:
        key = (artifact.path, artifact.role)
        if key in seen:
            continue
        seen.add(key)
        unique.append(artifact)
    return tuple(unique)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _job_name(value: str) -> str:
    name = Path(str(value).strip()).stem
    return name or "calculix"


def _new_run_id() -> str:
    return f"ccx_{uuid.uuid4().hex[:12]}"


def _tail_text(value: str, *, max_chars: int = 12000) -> str:
    text = value or ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


__all__ = [
    "CalculiXRunPolicy",
    "CalculiXRunRequest",
    "CalculiXRunResult",
    "CalculiXRunStatus",
    "CalculiXRunner",
    "ccx_available",
    "collect_calculix_artifacts",
    "find_ccx_executable",
]
