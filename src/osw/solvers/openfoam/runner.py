"""Safe OpenFOAM solver runner binding for generated template cases."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.core.executables import ExecutablePathRegistry, ExecutableResolution
from osw.solvers.openfoam.model import (
    OpenFOAMRunPolicy,
    OpenFOAMRunRequest,
    OpenFOAMRunResult,
    OpenFOAMRunStatus,
)
from osw.solvers.openfoam.residual_parser import parse_openfoam_case_logs
from osw.solvers.runner import (
    ExternalCommandRunner,
    RunLog,
    RunRequest,
    RunResult,
    RunStatus,
    TimeoutPolicy,
)

OPENFOAM_EXECUTABLES = ("blockMesh", "icoFoam", "simpleFoam")

ARTIFACT_ROLES = {
    "stdout.txt": ("stdout_log", "Captured OpenFOAM stdout.", "txt"),
    "stderr.txt": ("stderr_log", "Captured OpenFOAM stderr.", "txt"),
    "run_summary.json": ("run_summary", "Backend runner summary.", "json"),
}


def find_openfoam_executable(
    name: str,
    registry: ExecutablePathRegistry | None = None,
) -> ExecutableResolution:
    """Resolve an OpenFOAM executable without executing it."""

    active_registry = registry or ExecutablePathRegistry()
    names = (name, f"{name}.exe") if os.name == "nt" and not name.endswith(".exe") else (name,)
    resolution = active_registry.resolve_any(names)
    if resolution.found:
        return resolution
    diagnostics = DiagnosticReport()
    diagnostics.extend(resolution.diagnostics)
    diagnostics.add_error(
        "openfoam-executable-not-found",
        f"OpenFOAM executable `{name}` was not found.",
        hint="Install OpenFOAM or configure the executable path in Plugin Manager.",
        field=name,
    )
    return ExecutableResolution(
        name=resolution.name or name,
        resolved_path=None,
        source=resolution.source,
        diagnostics=diagnostics,
    )


def openfoam_solver_available(
    solver: str,
    registry: ExecutablePathRegistry | None = None,
) -> bool:
    return find_openfoam_executable(solver, registry).found


def blockmesh_available(registry: ExecutablePathRegistry | None = None) -> bool:
    return find_openfoam_executable("blockMesh", registry).found


class OpenFOAMRunner:
    """Run explicit OpenFOAM template cases through ExternalCommandRunner."""

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

    def validate_request(self, request: OpenFOAMRunRequest) -> DiagnosticReport:
        diagnostics = DiagnosticReport()
        case_dir = request.case_dir.expanduser()
        if not case_dir.exists() or not case_dir.is_dir():
            diagnostics.add_error(
                "openfoam-case-missing",
                f"OpenFOAM case directory does not exist: {case_dir}",
                hint="Generate a template case or choose an existing OpenFOAM case directory.",
                path=case_dir,
            )
            return diagnostics
        for relative_path in ("0", "constant", "system"):
            if not (case_dir / relative_path).exists():
                diagnostics.add_warning(
                    "openfoam-case-incomplete",
                    f"OpenFOAM case directory is missing {relative_path}/.",
                    hint="Generated cavity/duct cases should include 0, constant, and system.",
                    path=case_dir / relative_path,
                )
        diagnostics.extend(
            TimeoutPolicy(
                request.policy.timeout_seconds,
                kill_grace_seconds=request.policy.kill_grace_seconds,
            ).diagnostics()
        )
        return diagnostics

    def run_block_mesh(
        self,
        case_dir: str | Path,
        policy: OpenFOAMRunPolicy | None = None,
    ) -> OpenFOAMRunResult:
        return self.run_solver(
            OpenFOAMRunRequest(case_dir, "blockMesh", policy=policy or OpenFOAMRunPolicy())
        )

    def run_case(
        self,
        case_dir: str | Path,
        solver: str,
        policy: OpenFOAMRunPolicy | None = None,
        *,
        run_block_mesh_first: bool = False,
    ) -> OpenFOAMRunResult:
        active_policy = policy or OpenFOAMRunPolicy()
        if run_block_mesh_first:
            block_result = self.run_block_mesh(case_dir, active_policy)
            if block_result.status is not OpenFOAMRunStatus.COMPLETED:
                return block_result
            return self.run_solver(
                OpenFOAMRunRequest(block_result.case_dir, solver, policy=active_policy)
            )
        return self.run_solver(OpenFOAMRunRequest(case_dir, solver, policy=active_policy))

    def run_solver(self, request: OpenFOAMRunRequest) -> OpenFOAMRunResult:
        diagnostics = self.validate_request(request)
        run_id = request.run_id or _new_run_id()
        source_case_dir = request.case_dir.expanduser()
        if diagnostics.has_errors:
            return _result_from_parts(
                run_id=run_id,
                status=OpenFOAMRunStatus.MISSING_CASE,
                case_dir=source_case_dir,
                solver=request.solver,
                command=(request.solver,),
                diagnostics=diagnostics,
                metadata=request.metadata,
            )

        resolution = find_openfoam_executable(request.solver, self.executable_registry)
        diagnostics.extend(resolution.diagnostics)
        if not resolution.found or resolution.resolved_path is None:
            return _result_from_parts(
                run_id=run_id,
                status=OpenFOAMRunStatus.MISSING_EXECUTABLE,
                case_dir=source_case_dir,
                solver=request.solver,
                command=(request.solver,),
                diagnostics=diagnostics,
                metadata=request.metadata,
            )

        try:
            case_dir = self.prepare_case_dir(request)
        except OSError as exc:
            diagnostics.add_error(
                "invalid-case-directory",
                f"Could not prepare OpenFOAM case directory: {exc}",
                hint="Choose a writable run directory.",
                path=source_case_dir,
            )
            return _result_from_parts(
                run_id=run_id,
                status=OpenFOAMRunStatus.FAILED,
                case_dir=source_case_dir,
                solver=request.solver,
                command=(str(resolution.resolved_path),),
                diagnostics=diagnostics,
                metadata=request.metadata,
            )

        command = self.build_solver_command(request, resolution.resolved_path)
        runner_request = RunRequest(
            command,
            cwd=case_dir,
            env=request.policy.env_overrides,
            timeout_policy=TimeoutPolicy(
                request.policy.timeout_seconds,
                kill_grace_seconds=request.policy.kill_grace_seconds,
            ),
            artifact_patterns=(),
            artifact_dir=case_dir,
            run_id=run_id,
            metadata={
                "solver": "openfoam",
                "openfoam_solver": request.solver,
                "source_case_dir": str(source_case_dir),
                **dict(request.metadata),
            },
        )
        run_result = self.command_runner.run(runner_request)
        diagnostics.extend(run_result.diagnostics)
        status = _status_from_run_result(run_result)
        artifacts = collect_openfoam_artifacts(
            case_dir,
            run_result=run_result,
            diagnostics=diagnostics,
            artifact_patterns=request.policy.artifact_patterns,
        )
        residual_summary = parse_openfoam_case_logs(case_dir)
        diagnostics.extend(residual_summary.diagnostics)
        if status is OpenFOAMRunStatus.COMPLETED:
            diagnostics.add_info(
                "openfoam-run-completed",
                "OpenFOAM solver run completed.",
                command=command,
                return_code=run_result.return_code,
                metadata={"solver": request.solver},
            )
        elif status is OpenFOAMRunStatus.TIMED_OUT:
            diagnostics.add_error(
                "openfoam-run-timed-out",
                "OpenFOAM solver run timed out.",
                command=command,
                return_code=run_result.return_code,
            )
        else:
            diagnostics.add_error(
                "openfoam-run-failed",
                "OpenFOAM solver run failed.",
                command=command,
                return_code=run_result.return_code,
            )
        return OpenFOAMRunResult(
            run_id=run_id,
            status=status,
            case_dir=case_dir,
            solver=request.solver,
            command=tuple(command),
            return_code=run_result.return_code,
            stdout=_tail_text(run_result.log.stdout),
            stderr=_tail_text(run_result.log.stderr),
            elapsed_seconds=run_result.elapsed_seconds,
            artifacts=artifacts,
            diagnostics=diagnostics,
            run_result=run_result,
            residual_summary=residual_summary,
            metadata={
                "source_case_dir": str(source_case_dir),
                "isolated_case_dir": request.policy.isolate_case_dir,
                **dict(request.metadata),
            },
        )

    def prepare_case_dir(self, request: OpenFOAMRunRequest) -> Path:
        source = request.case_dir.expanduser().resolve()
        if not request.policy.isolate_case_dir:
            return source
        if not request.policy.copy_case:
            case_dir = Path(tempfile.mkdtemp(prefix="osw-openfoam-")) / source.name
            case_dir.mkdir(parents=True, exist_ok=True)
            return case_dir.resolve()
        target = Path(tempfile.mkdtemp(prefix="osw-openfoam-")) / source.name
        shutil.copytree(source, target)
        return target.resolve()

    def build_solver_command(
        self,
        request: OpenFOAMRunRequest,
        solver_path: str | Path,
    ) -> list[str]:
        del request
        return [str(solver_path)]


def collect_openfoam_artifacts(
    case_dir: str | Path,
    *,
    run_result: RunResult | None = None,
    diagnostics: DiagnosticReport | None = None,
    artifact_patterns: Iterable[str] = (),
) -> tuple[RunArtifact, ...]:
    root = Path(case_dir).resolve()
    report = diagnostics if diagnostics is not None else DiagnosticReport()
    artifacts: list[RunArtifact] = []
    for path in _known_artifact_paths(root, artifact_patterns):
        if not _is_under(path, root):
            report.add_warning(
                "artifact-outside-case-directory",
                f"Skipped OpenFOAM artifact outside case directory: {path}",
                path=path,
            )
            continue
        if not path.exists():
            continue
        artifact = _artifact_for_path(path, root)
        artifacts.append(artifact)
        report.add_info(
            "artifact-collected",
            f"Collected OpenFOAM artifact: {path.name}",
            path=path,
            metadata={"role": artifact.role, "format": artifact.format},
        )
    if run_result is not None:
        artifacts.extend(_standard_runner_artifacts(root, run_result))
    if not any(artifact.role == "solver_log" for artifact in artifacts):
        report.add_warning(
            "artifact-missing",
            "OpenFOAM run completed without a log.* artifact.",
            hint="Inspect captured stdout/stderr for solver output.",
            path=root,
        )
    return _dedupe_artifacts(artifacts)


def _known_artifact_paths(case_dir: Path, artifact_patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in artifact_patterns:
        paths.extend(sorted(case_dir.glob(str(pattern))))
    for name in ("stdout.txt", "stderr.txt", "run_summary.json"):
        paths.append(case_dir / name)
    paths.extend(sorted(case_dir.glob("log.*")))
    return sorted(set(paths), key=lambda item: str(item))


def _standard_runner_artifacts(case_dir: Path, run_result: RunResult) -> list[RunArtifact]:
    artifacts: list[RunArtifact] = []
    for path, role, description, fmt in (
        (case_dir / "stdout.txt", "stdout_log", "Captured OpenFOAM stdout.", "txt"),
        (case_dir / "stderr.txt", "stderr_log", "Captured OpenFOAM stderr.", "txt"),
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


def _artifact_for_path(path: Path, root: Path) -> RunArtifact:
    if path.name.startswith("log."):
        return RunArtifact(path, "solver_log", "OpenFOAM solver log.", format="log")
    if path.name in ARTIFACT_ROLES:
        role, description, fmt = ARTIFACT_ROLES[path.name]
        return RunArtifact(path, role, description, format=fmt)
    if path.is_dir():
        role = "case_directory" if path == root else "case_subdirectory"
        return RunArtifact(path, role, "OpenFOAM case directory.")
    suffix = path.suffix.lstrip(".")
    if "postProcessing" in path.parts:
        return RunArtifact(
            path,
            "post_processing",
            "OpenFOAM postProcessing artifact.",
            format=suffix,
        )
    return RunArtifact(path, "case_file", "OpenFOAM case file.", format=suffix)


def _status_from_run_result(result: RunResult) -> OpenFOAMRunStatus:
    if result.status is RunStatus.COMPLETED:
        return OpenFOAMRunStatus.COMPLETED
    if result.status is RunStatus.TIMED_OUT:
        return OpenFOAMRunStatus.TIMED_OUT
    if result.status is RunStatus.MISSING_EXECUTABLE:
        return OpenFOAMRunStatus.MISSING_EXECUTABLE
    if result.status is RunStatus.CANCELLED:
        return OpenFOAMRunStatus.CANCELLED
    return OpenFOAMRunStatus.FAILED


def _result_from_parts(
    *,
    run_id: str,
    status: OpenFOAMRunStatus,
    case_dir: Path,
    solver: str,
    command: Sequence[str],
    diagnostics: DiagnosticReport,
    metadata: Mapping[str, object],
) -> OpenFOAMRunResult:
    return OpenFOAMRunResult(
        run_id=run_id,
        status=status,
        case_dir=case_dir,
        solver=solver,
        command=tuple(command),
        diagnostics=diagnostics,
        run_result=RunResult(
            run_id=run_id,
            status=RunStatus.MISSING_EXECUTABLE
            if status is OpenFOAMRunStatus.MISSING_EXECUTABLE
            else RunStatus.FAILED,
            command=tuple(command),
            cwd=case_dir,
            artifact_dir=case_dir,
            log=RunLog(),
            diagnostics=diagnostics,
        ),
        metadata=dict(metadata),
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


def _new_run_id() -> str:
    return f"openfoam_{uuid.uuid4().hex[:12]}"


def _tail_text(value: str, *, max_chars: int = 12000) -> str:
    text = value or ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]
