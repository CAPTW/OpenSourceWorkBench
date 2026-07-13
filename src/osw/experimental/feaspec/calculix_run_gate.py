"""Installed-only CalculiX run gate for FEASpec export bundles."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from osw import __version__ as OSW_VERSION

from .calculix_exporter import README_FILENAME
from .calculix_run_diagnostics import (
    CalculiXRunDiagnosticCode,
    CalculiXRunSeverity,
    FEASpecCalculiXRunDiagnostic,
)

DEFAULT_TIMEOUT_SECONDS = 10.0
RUN_METADATA_FILENAME = "run_metadata.json"
STDOUT_FILENAME = "stdout.txt"
STDERR_FILENAME = "stderr.txt"

__all__ = [
    "CalculiXExportBundleInspection",
    "CalculiXRuntimeDiscovery",
    "FEASpecCalculiXRunMetadata",
    "FEASpecCalculiXRunPlan",
    "FEASpecCalculiXRunResult",
    "FEASpecCalculiXRunStatus",
    "discover_calculix_executable",
    "explain_calculix_run_result",
    "inspect_calculix_export_bundle",
    "plan_calculix_installed_run",
    "run_calculix_installed_only",
]


class FEASpecCalculiXRunStatus(str, Enum):
    """Status for the FEASpec installed-only CalculiX run gate."""

    BLOCKED = "blocked"
    DRY_RUN_READY = "dry-run-ready"
    SKIPPED_MISSING = "skipped-missing"
    RAN = "ran"
    RAN_WITH_WARNINGS = "ran-with-warnings"
    FAILED = "failed"
    TIMED_OUT = "timed-out"


@dataclass(frozen=True, slots=True)
class CalculiXRuntimeDiscovery:
    """Installed CalculiX executable discovery result."""

    ccx_path: str = ""
    discovered: bool = False
    executable: bool = False
    source: str = ""
    diagnostics: tuple[FEASpecCalculiXRunDiagnostic, ...] = ()

    @property
    def ready(self) -> bool:
        return self.discovered and self.executable and bool(self.ccx_path)

    def to_dict(self) -> dict[str, object]:
        return {
            "ccx_path": self.ccx_path,
            "discovered": self.discovered,
            "executable": self.executable,
            "source": self.source,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class CalculiXExportBundleInspection:
    """Inspection result for a no-run FEASpec CalculiX export bundle."""

    export_dir: Path
    manifest_path: Path | None = None
    inp_path: Path | None = None
    readme_path: Path | None = None
    diagnostics_path: Path | None = None
    manifest: Mapping[str, Any] | None = None
    diagnostics: tuple[FEASpecCalculiXRunDiagnostic, ...] = ()
    solver_execution_performed: bool = False

    @property
    def is_valid(self) -> bool:
        return (
            self.manifest_path is not None
            and self.inp_path is not None
            and self.readme_path is not None
            and not _has_blockers(self.diagnostics)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "export_dir": str(self.export_dir),
            "manifest_path": str(self.manifest_path) if self.manifest_path else "",
            "inp_path": str(self.inp_path) if self.inp_path else "",
            "readme_path": str(self.readme_path) if self.readme_path else "",
            "diagnostics_path": (
                str(self.diagnostics_path) if self.diagnostics_path else ""
            ),
            "solver_execution_performed": self.solver_execution_performed,
            "is_valid": self.is_valid,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXRunPlan:
    """Plan for a dry-run or installed-only CalculiX execution request."""

    status: FEASpecCalculiXRunStatus
    export_dir: Path
    run_dir: Path
    timeout_seconds: float
    execute_requested: bool
    confirm_run: bool
    acknowledge_readme: bool
    inspection: CalculiXExportBundleInspection
    runtime: CalculiXRuntimeDiscovery
    command: tuple[str, ...] = ()
    diagnostics: tuple[FEASpecCalculiXRunDiagnostic, ...] = ()

    @property
    def is_blocked(self) -> bool:
        return self.status is FEASpecCalculiXRunStatus.BLOCKED or _has_blockers(
            self.diagnostics
        )

    @property
    def can_execute(self) -> bool:
        return (
            self.execute_requested
            and self.status is FEASpecCalculiXRunStatus.DRY_RUN_READY
            and self.inspection.is_valid
            and self.runtime.ready
            and not _has_blockers(self.diagnostics)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "export_dir": str(self.export_dir),
            "run_dir": str(self.run_dir),
            "timeout_seconds": self.timeout_seconds,
            "execute_requested": self.execute_requested,
            "confirm_run": self.confirm_run,
            "acknowledge_readme": self.acknowledge_readme,
            "command": list(self.command),
            "inspection": self.inspection.to_dict(),
            "runtime": self.runtime.to_dict(),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXRunMetadata:
    """Serializable run metadata written after a process is started."""

    command: tuple[str, ...]
    status: FEASpecCalculiXRunStatus
    export_dir: Path
    run_dir: Path
    ccx_path: str
    ccx_discovered: bool
    execute_requested: bool
    solver_execution_performed: bool
    exit_code: int | None
    timed_out: bool
    stdout_path: Path | None
    stderr_path: Path | None
    run_metadata_path: Path | None
    diagnostics: tuple[FEASpecCalculiXRunDiagnostic, ...]
    started_at: str = ""
    finished_at: str = ""
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "command": list(self.command),
            "status": self.status.value,
            "export_dir": str(self.export_dir),
            "run_dir": str(self.run_dir),
            "ccx_path": self.ccx_path,
            "ccx_discovered": self.ccx_discovered,
            "execute_requested": self.execute_requested,
            "solver_execution_performed": self.solver_execution_performed,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "stdout_path": str(self.stdout_path) if self.stdout_path else "",
            "stderr_path": str(self.stderr_path) if self.stderr_path else "",
            "run_metadata_path": (
                str(self.run_metadata_path) if self.run_metadata_path else ""
            ),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "limitations": list(self.limitations),
            "osw_version": OSW_VERSION,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXRunResult:
    """Result from the FEASpec installed-only CalculiX run gate."""

    status: FEASpecCalculiXRunStatus
    plan: FEASpecCalculiXRunPlan
    metadata: FEASpecCalculiXRunMetadata
    diagnostics: tuple[FEASpecCalculiXRunDiagnostic, ...] = ()

    @property
    def exit_code(self) -> int | None:
        return self.metadata.exit_code

    @property
    def timed_out(self) -> bool:
        return self.metadata.timed_out

    @property
    def solver_execution_performed(self) -> bool:
        return self.metadata.solver_execution_performed

    def to_dict(self) -> dict[str, object]:
        payload = self.metadata.to_dict()
        payload["status"] = self.status.value
        payload["plan"] = self.plan.to_dict()
        payload["diagnostics"] = [item.to_dict() for item in self.diagnostics]
        return payload


def discover_calculix_executable(
    candidate: str | Path | None = None,
) -> CalculiXRuntimeDiscovery:
    """Discover an installed ``ccx`` executable without installing anything."""

    if candidate is not None:
        candidate_path = Path(candidate).expanduser()
        if not candidate_path.is_file():
            return CalculiXRuntimeDiscovery(
                ccx_path=str(candidate_path),
                source="candidate",
                diagnostics=(
                    _diag(
                        CalculiXRunDiagnosticCode.FR_CCX_MISSING,
                        CalculiXRunSeverity.BLOCKER,
                        "Explicit CalculiX ccx path was not found.",
                        path=str(candidate_path),
                        suggested_fix=(
                            "Install CalculiX separately or provide an existing "
                            "ccx path."
                        ),
                    ),
                ),
            )
        resolved = candidate_path.resolve()
        if not _path_is_executable(resolved):
            return CalculiXRuntimeDiscovery(
                ccx_path=str(resolved),
                discovered=True,
                source="candidate",
                diagnostics=(
                    _diag(
                        CalculiXRunDiagnosticCode.FR_CCX_NOT_EXECUTABLE,
                        CalculiXRunSeverity.BLOCKER,
                        "Explicit CalculiX ccx path exists but is not executable.",
                        path=str(resolved),
                        suggested_fix="Provide an executable ccx path.",
                    ),
                ),
            )
        return CalculiXRuntimeDiscovery(
            ccx_path=str(resolved),
            discovered=True,
            executable=True,
            source="candidate",
        )

    for command_name in ("ccx", "ccx.exe"):
        found = shutil.which(command_name)
        if found:
            resolved = Path(found).resolve()
            if _path_is_executable(resolved):
                return CalculiXRuntimeDiscovery(
                    ccx_path=str(resolved),
                    discovered=True,
                    executable=True,
                    source="PATH",
                )
            return CalculiXRuntimeDiscovery(
                ccx_path=str(resolved),
                discovered=True,
                source="PATH",
                diagnostics=(
                    _diag(
                        CalculiXRunDiagnosticCode.FR_CCX_NOT_EXECUTABLE,
                        CalculiXRunSeverity.BLOCKER,
                        "Discovered ccx path is not executable.",
                        path=str(resolved),
                        suggested_fix="Fix the executable permission or provide --ccx.",
                    ),
                ),
            )

    return CalculiXRuntimeDiscovery(
        source="PATH",
        diagnostics=(
            _diag(
                CalculiXRunDiagnosticCode.FR_CCX_MISSING,
                CalculiXRunSeverity.WARNING,
                "CalculiX ccx was not discovered on PATH.",
                suggested_fix=(
                    "Install CalculiX separately on a prepared validation machine "
                    "or pass --ccx to an existing executable."
                ),
                blocks_execution=True,
            ),
        ),
    )


def inspect_calculix_export_bundle(
    export_dir: str | Path,
) -> CalculiXExportBundleInspection:
    """Inspect a no-run export bundle without writing or executing anything."""

    root = Path(export_dir).expanduser()
    diagnostics: list[FEASpecCalculiXRunDiagnostic] = []
    manifest_path: Path | None = None
    inp_path: Path | None = None
    readme_path: Path | None = None
    diagnostics_path: Path | None = None
    manifest: Mapping[str, Any] | None = None
    solver_execution_performed = False

    if not root.exists() or not root.is_dir():
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_EXPORT_BUNDLE_INVALID,
                CalculiXRunSeverity.BLOCKER,
                "Export bundle path is not a readable directory.",
                path=str(root),
                suggested_fix="Pass --export-dir pointing to a FEASpec no-run export bundle.",
            )
        )
        return CalculiXExportBundleInspection(root, diagnostics=tuple(diagnostics))

    manifest_candidates = sorted(root.glob("*.manifest.json"))
    if len(manifest_candidates) != 1:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_MANIFEST_MISSING,
                CalculiXRunSeverity.BLOCKER,
                "Export bundle must contain exactly one manifest JSON file.",
                path=str(root),
                suggested_fix="Use a bundle written by feaspec-calculix-export-write.",
            )
        )
    else:
        manifest_path = manifest_candidates[0]
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            diagnostics.append(
                _diag(
                    CalculiXRunDiagnosticCode.FR_EXPORT_BUNDLE_INVALID,
                    CalculiXRunSeverity.BLOCKER,
                    f"Export manifest could not be read as JSON: {exc}",
                    path=str(manifest_path),
                    suggested_fix="Recreate the no-run export bundle.",
                )
            )
        else:
            if not isinstance(loaded, Mapping):
                diagnostics.append(
                    _diag(
                        CalculiXRunDiagnosticCode.FR_EXPORT_BUNDLE_INVALID,
                        CalculiXRunSeverity.BLOCKER,
                        "Export manifest must contain a JSON object.",
                        path=str(manifest_path),
                        suggested_fix="Recreate the no-run export bundle.",
                    )
                )
            else:
                manifest = loaded
                solver_execution_performed = bool(
                    loaded.get("solver_execution_performed", False)
                )
                if loaded.get("solver_execution_performed") is not False:
                    diagnostics.append(
                        _diag(
                            CalculiXRunDiagnosticCode.FR_EXPORT_BUNDLE_INVALID,
                            CalculiXRunSeverity.BLOCKER,
                            (
                                "Export manifest must record "
                                "solver_execution_performed=false before a run gate."
                            ),
                            path=str(manifest_path),
                            suggested_fix="Use a fresh no-run export bundle.",
                        )
                    )

    inp_path = _select_bundle_file(
        root,
        manifest,
        role="inp",
        fallback_pattern="*.inp",
        missing_code=CalculiXRunDiagnosticCode.FR_INP_MISSING,
        diagnostics=diagnostics,
    )
    readme_path = _select_bundle_file(
        root,
        manifest,
        role="readme",
        fallback_pattern=README_FILENAME,
        missing_code=CalculiXRunDiagnosticCode.FR_README_MISSING,
        diagnostics=diagnostics,
    )
    diagnostics_path = _select_optional_bundle_file(root, manifest, "diagnostics")

    return CalculiXExportBundleInspection(
        export_dir=root,
        manifest_path=manifest_path,
        inp_path=inp_path,
        readme_path=readme_path,
        diagnostics_path=diagnostics_path,
        manifest=manifest,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        solver_execution_performed=solver_execution_performed,
    )


def plan_calculix_installed_run(
    export_dir: str | Path,
    *,
    ccx_path: str | Path | None = None,
    run_dir: str | Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    execute: bool = False,
    confirm_run: bool = False,
    acknowledge_readme: bool = False,
) -> FEASpecCalculiXRunPlan:
    """Plan a FEASpec installed-only CalculiX run or dry-run."""

    inspection = inspect_calculix_export_bundle(export_dir)
    runtime = discover_calculix_executable(ccx_path)
    diagnostics = [*inspection.diagnostics, *runtime.diagnostics]
    export_root = inspection.export_dir
    resolved_run_dir = _resolve_run_dir(export_root, run_dir)

    timeout_value = _normalize_timeout(timeout_seconds, diagnostics)
    diagnostics.extend(_run_dir_diagnostics(resolved_run_dir, export_root))

    if execute and not confirm_run:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_CONFIRMATION_REQUIRED,
                CalculiXRunSeverity.BLOCKER,
                "Execute mode requires explicit run confirmation.",
                suggested_fix="Pass --confirm-run after reviewing the export bundle.",
            )
        )
    if execute and not acknowledge_readme:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_README_NOT_ACKNOWLEDGED,
                CalculiXRunSeverity.BLOCKER,
                "Execute mode requires README_RUN_FIRST acknowledgement.",
                suggested_fix="Review README_RUN_FIRST.txt and pass --acknowledge-readme.",
            )
        )
    if (confirm_run or acknowledge_readme) and not execute:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_EXECUTE_FLAG_REQUIRED,
                CalculiXRunSeverity.INFO,
                (
                    "Run confirmation flags were supplied without execute mode; "
                    "dry-run remains active."
                ),
                suggested_fix="Pass --execute only after review if a run is intended.",
                blocks_execution=False,
            )
        )
    if not execute:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_NOT_AUTHORIZED,
                CalculiXRunSeverity.INFO,
                "Dry-run mode is active; no CalculiX process will be started.",
                suggested_fix=(
                    "Use --execute --confirm-run --acknowledge-readme for a "
                    "reviewed run."
                ),
                blocks_execution=False,
            )
        )

    command = _planned_command(runtime, inspection)
    status = _plan_status(
        diagnostics,
        inspection=inspection,
        runtime=runtime,
        execute=execute,
    )
    return FEASpecCalculiXRunPlan(
        status=status,
        export_dir=export_root,
        run_dir=resolved_run_dir,
        timeout_seconds=timeout_value,
        execute_requested=execute,
        confirm_run=confirm_run,
        acknowledge_readme=acknowledge_readme,
        inspection=inspection,
        runtime=runtime,
        command=command,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def run_calculix_installed_only(
    export_dir: str | Path,
    *,
    ccx_path: str | Path | None = None,
    run_dir: str | Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    execute: bool = False,
    confirm_run: bool = False,
    acknowledge_readme: bool = False,
) -> FEASpecCalculiXRunResult:
    """Run or dry-run the installed-only CalculiX gate for a no-run bundle."""

    plan = plan_calculix_installed_run(
        export_dir,
        ccx_path=ccx_path,
        run_dir=run_dir,
        timeout_seconds=timeout_seconds,
        execute=execute,
        confirm_run=confirm_run,
        acknowledge_readme=acknowledge_readme,
    )
    if not execute or not plan.can_execute:
        return _result_without_execution(plan)

    return _execute_plan(plan)


def explain_calculix_run_result(result: FEASpecCalculiXRunResult) -> list[str]:
    """Return reviewer-readable run gate status and diagnostics."""

    lines = [
        f"FEASpec CalculiX installed-only run gate status: {result.status.value}.",
        "Installed-only: true.",
        "No solver install was performed.",
        "No release mutation was performed.",
        "No issue closure was performed.",
        "Result import is a separate future gate.",
        (
            "GitHub state verified 2026-07-14: Issue #8 is closed after bounded "
            "WSL CalculiX evidence; this workflow does not broaden that closure."
        ),
        f"Solver execution performed: {str(result.solver_execution_performed).lower()}.",
    ]
    if result.metadata.ccx_path:
        lines.append(f"ccx: {result.metadata.ccx_path}")
    else:
        lines.append("ccx: not discovered")
    if result.metadata.run_dir:
        lines.append(f"Run directory: {result.metadata.run_dir}")
    if result.metadata.exit_code is not None:
        lines.append(f"Exit code: {result.metadata.exit_code}")
    if result.metadata.timed_out:
        lines.append("Timed out: true")
    if result.metadata.stdout_path:
        lines.append(f"stdout: {result.metadata.stdout_path}")
    if result.metadata.stderr_path:
        lines.append(f"stderr: {result.metadata.stderr_path}")
    for diagnostic in result.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _execute_plan(plan: FEASpecCalculiXRunPlan) -> FEASpecCalculiXRunResult:
    diagnostics = list(plan.diagnostics)
    started_at = _utc_now()
    stdout_text = ""
    stderr_text = ""
    exit_code: int | None = None
    timed_out = False
    process_started = False
    status = FEASpecCalculiXRunStatus.FAILED
    run_metadata_path = plan.run_dir / RUN_METADATA_FILENAME
    stdout_path = plan.run_dir / STDOUT_FILENAME
    stderr_path = plan.run_dir / STDERR_FILENAME

    try:
        if not plan.run_dir.exists():
            plan.run_dir.mkdir(parents=False, exist_ok=False)
        if plan.inspection.inp_path is None:
            msg = "Internal run-gate error: missing input deck after planning."
            raise FileNotFoundError(msg)
        deck_path = plan.run_dir / plan.inspection.inp_path.name
        shutil.copy2(plan.inspection.inp_path, deck_path)
        command = (plan.runtime.ccx_path, deck_path.stem)
        completed = subprocess.run(
            command,
            cwd=plan.run_dir,
            capture_output=True,
            text=True,
            timeout=plan.timeout_seconds,
            check=False,
        )
        process_started = True
        stdout_text = completed.stdout or ""
        stderr_text = completed.stderr or ""
        exit_code = completed.returncode
        if completed.returncode == 0:
            status = FEASpecCalculiXRunStatus.RAN
        else:
            status = FEASpecCalculiXRunStatus.FAILED
            diagnostics.append(
                _diag(
                    CalculiXRunDiagnosticCode.FR_NONZERO_EXIT,
                    CalculiXRunSeverity.ERROR,
                    "CalculiX ccx exited with a nonzero status.",
                    path=str(plan.run_dir),
                    suggested_fix="Inspect stdout.txt, stderr.txt, and CalculiX artifacts.",
                )
            )
    except subprocess.TimeoutExpired as exc:
        process_started = True
        timed_out = True
        stdout_text = _timeout_output(exc.stdout)
        stderr_text = _timeout_output(exc.stderr)
        status = FEASpecCalculiXRunStatus.TIMED_OUT
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_TIMEOUT,
                CalculiXRunSeverity.ERROR,
                "CalculiX ccx exceeded the run gate timeout and was terminated.",
                path=str(plan.run_dir),
                suggested_fix="Inspect partial logs and rerun only with a reviewed timeout.",
            )
        )
    except OSError as exc:
        status = FEASpecCalculiXRunStatus.FAILED
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_PROCESS_START_FAILED,
                CalculiXRunSeverity.BLOCKER,
                f"CalculiX ccx process could not be started: {exc}",
                path=plan.runtime.ccx_path,
                suggested_fix="Check the executable path and run directory permissions.",
            )
        )

    stdout_write = _write_runtime_text(stdout_path, stdout_text)
    stderr_write = _write_runtime_text(stderr_path, stderr_text)
    if stdout_write:
        diagnostics.append(stdout_write)
    if stderr_write:
        diagnostics.append(stderr_write)

    finished_at = _utc_now()
    metadata = FEASpecCalculiXRunMetadata(
        command=plan.command,
        status=status,
        export_dir=plan.export_dir,
        run_dir=plan.run_dir,
        ccx_path=plan.runtime.ccx_path,
        ccx_discovered=plan.runtime.discovered,
        execute_requested=True,
        solver_execution_performed=process_started,
        exit_code=exit_code,
        timed_out=timed_out,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        run_metadata_path=run_metadata_path,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        started_at=started_at,
        finished_at=finished_at,
        limitations=_limitations(),
    )
    metadata_failure = _write_metadata(run_metadata_path, metadata)
    if metadata_failure:
        diagnostics.append(metadata_failure)
        status = FEASpecCalculiXRunStatus.FAILED
        metadata = FEASpecCalculiXRunMetadata(
            command=metadata.command,
            status=status,
            export_dir=metadata.export_dir,
            run_dir=metadata.run_dir,
            ccx_path=metadata.ccx_path,
            ccx_discovered=metadata.ccx_discovered,
            execute_requested=metadata.execute_requested,
            solver_execution_performed=metadata.solver_execution_performed,
            exit_code=metadata.exit_code,
            timed_out=metadata.timed_out,
            stdout_path=metadata.stdout_path,
            stderr_path=metadata.stderr_path,
            run_metadata_path=None,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
            started_at=metadata.started_at,
            finished_at=metadata.finished_at,
            limitations=metadata.limitations,
        )
    return FEASpecCalculiXRunResult(
        status=status,
        plan=plan,
        metadata=metadata,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def _result_without_execution(
    plan: FEASpecCalculiXRunPlan,
) -> FEASpecCalculiXRunResult:
    metadata = FEASpecCalculiXRunMetadata(
        command=plan.command,
        status=plan.status,
        export_dir=plan.export_dir,
        run_dir=plan.run_dir,
        ccx_path=plan.runtime.ccx_path,
        ccx_discovered=plan.runtime.discovered,
        execute_requested=plan.execute_requested,
        solver_execution_performed=False,
        exit_code=None,
        timed_out=False,
        stdout_path=None,
        stderr_path=None,
        run_metadata_path=None,
        diagnostics=plan.diagnostics,
        limitations=_limitations(),
    )
    return FEASpecCalculiXRunResult(
        status=plan.status,
        plan=plan,
        metadata=metadata,
        diagnostics=plan.diagnostics,
    )


def _select_bundle_file(
    root: Path,
    manifest: Mapping[str, Any] | None,
    *,
    role: str,
    fallback_pattern: str,
    missing_code: CalculiXRunDiagnosticCode,
    diagnostics: list[FEASpecCalculiXRunDiagnostic],
) -> Path | None:
    manifest_path = _manifest_file_for_role(root, manifest, role)
    if manifest_path is not None:
        if manifest_path.is_file():
            return manifest_path
        diagnostics.append(
            _diag(
                missing_code,
                CalculiXRunSeverity.BLOCKER,
                f"Manifest references a missing {role} file.",
                path=str(manifest_path),
                suggested_fix="Recreate the no-run export bundle.",
            )
        )
        return None

    matches = (
        [root / fallback_pattern]
        if fallback_pattern == README_FILENAME
        else sorted(root.glob(fallback_pattern))
    )
    existing = [path for path in matches if path.is_file()]
    if len(existing) == 1:
        return existing[0]
    diagnostics.append(
        _diag(
            missing_code,
            CalculiXRunSeverity.BLOCKER,
            f"Export bundle must contain exactly one {role} file.",
            path=str(root),
            suggested_fix="Use a bundle written by feaspec-calculix-export-write.",
        )
    )
    return None


def _select_optional_bundle_file(
    root: Path,
    manifest: Mapping[str, Any] | None,
    role: str,
) -> Path | None:
    manifest_path = _manifest_file_for_role(root, manifest, role)
    if manifest_path is not None and manifest_path.is_file():
        return manifest_path
    matches = sorted(root.glob("*.diagnostics.json"))
    return matches[0] if len(matches) == 1 and matches[0].is_file() else None


def _manifest_file_for_role(
    root: Path,
    manifest: Mapping[str, Any] | None,
    role: str,
) -> Path | None:
    if manifest is None:
        return None
    files = manifest.get("files", ())
    if not isinstance(files, Sequence) or isinstance(files, (str, bytes)):
        return None
    role_matches = [
        item
        for item in files
        if isinstance(item, Mapping) and str(item.get("role", "")) == role
    ]
    if len(role_matches) != 1:
        return None
    filename = str(role_matches[0].get("filename", ""))
    if not filename or Path(filename).name != filename:
        return None
    return root / filename


def _normalize_timeout(
    timeout_seconds: float,
    diagnostics: list[FEASpecCalculiXRunDiagnostic],
) -> float:
    try:
        timeout_value = float(timeout_seconds)
    except (TypeError, ValueError):
        timeout_value = DEFAULT_TIMEOUT_SECONDS
    if timeout_value <= 0:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_NOT_AUTHORIZED,
                CalculiXRunSeverity.BLOCKER,
                "Timeout must be greater than zero seconds.",
                suggested_fix="Use a short positive timeout such as 10 seconds.",
            )
        )
        return DEFAULT_TIMEOUT_SECONDS
    if timeout_value > 300:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_NOT_AUTHORIZED,
                CalculiXRunSeverity.BLOCKER,
                "Timeout is too large for this installed-only gate.",
                suggested_fix="Use a bounded timeout of 300 seconds or less.",
            )
        )
    return timeout_value


def _resolve_run_dir(export_dir: Path, run_dir: str | Path | None) -> Path:
    if run_dir is None:
        return export_dir / "feaspec_calculix_run"
    return Path(run_dir).expanduser()


def _run_dir_diagnostics(
    run_dir: Path,
    export_dir: Path,
) -> list[FEASpecCalculiXRunDiagnostic]:
    diagnostics: list[FEASpecCalculiXRunDiagnostic] = []
    try:
        resolved_run = run_dir.resolve(strict=False)
        resolved_export = export_dir.resolve(strict=False)
    except OSError:
        resolved_run = run_dir
        resolved_export = export_dir

    if resolved_run == resolved_export:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_DIR_UNSAFE,
                CalculiXRunSeverity.BLOCKER,
                "Run directory must be separate from the export bundle directory.",
                path=str(run_dir),
                suggested_fix="Choose an empty child or sibling runtime directory.",
            )
        )
    if _is_root_path(resolved_run):
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_DIR_UNSAFE,
                CalculiXRunSeverity.BLOCKER,
                "Run directory cannot be a filesystem root.",
                path=str(run_dir),
                suggested_fix="Choose an isolated empty runtime directory.",
            )
        )
    if ".git" in resolved_run.parts:
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_FORBIDDEN_PATH,
                CalculiXRunSeverity.BLOCKER,
                "Run directory cannot be inside a Git metadata directory.",
                path=str(run_dir),
                suggested_fix="Choose an ignored artifacts or temporary directory.",
            )
        )
    if run_dir.exists() and not run_dir.is_dir():
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_DIR_UNSAFE,
                CalculiXRunSeverity.BLOCKER,
                "Run directory path exists but is not a directory.",
                path=str(run_dir),
                suggested_fix="Choose an empty directory path.",
            )
        )
    elif run_dir.exists() and any(run_dir.iterdir()):
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_DIR_NOT_EMPTY,
                CalculiXRunSeverity.BLOCKER,
                "Run directory must be empty before execution.",
                path=str(run_dir),
                suggested_fix="Choose a new empty runtime directory.",
            )
        )
    elif not run_dir.exists() and not run_dir.parent.is_dir():
        diagnostics.append(
            _diag(
                CalculiXRunDiagnosticCode.FR_RUN_DIR_UNSAFE,
                CalculiXRunSeverity.BLOCKER,
                "Run directory parent does not exist.",
                path=str(run_dir),
                suggested_fix="Create the parent directory explicitly or choose another path.",
            )
        )
    return diagnostics


def _plan_status(
    diagnostics: Sequence[FEASpecCalculiXRunDiagnostic],
    *,
    inspection: CalculiXExportBundleInspection,
    runtime: CalculiXRuntimeDiscovery,
    execute: bool,
) -> FEASpecCalculiXRunStatus:
    if _has_blockers(diagnostics) or not inspection.is_valid:
        if _only_missing_ccx_blocks(diagnostics, inspection=inspection):
            return FEASpecCalculiXRunStatus.SKIPPED_MISSING
        return FEASpecCalculiXRunStatus.BLOCKED
    if not runtime.ready:
        return FEASpecCalculiXRunStatus.SKIPPED_MISSING
    if not execute:
        return FEASpecCalculiXRunStatus.DRY_RUN_READY
    return FEASpecCalculiXRunStatus.DRY_RUN_READY


def _only_missing_ccx_blocks(
    diagnostics: Sequence[FEASpecCalculiXRunDiagnostic],
    *,
    inspection: CalculiXExportBundleInspection,
) -> bool:
    if not inspection.is_valid:
        return False
    blockers = [item for item in diagnostics if item.blocks_execution]
    return bool(blockers) and all(
        item.code is CalculiXRunDiagnosticCode.FR_CCX_MISSING for item in blockers
    )


def _planned_command(
    runtime: CalculiXRuntimeDiscovery,
    inspection: CalculiXExportBundleInspection,
) -> tuple[str, ...]:
    if not runtime.ccx_path or inspection.inp_path is None:
        return ()
    return (runtime.ccx_path, inspection.inp_path.stem)


def _write_runtime_text(
    path: Path,
    text: str,
) -> FEASpecCalculiXRunDiagnostic | None:
    try:
        path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        return _diag(
            CalculiXRunDiagnosticCode.FR_METADATA_WRITE_FAILED,
            CalculiXRunSeverity.ERROR,
            f"Could not write run artifact: {exc}",
            path=str(path),
            suggested_fix="Check run directory permissions.",
        )
    return None


def _write_metadata(
    path: Path,
    metadata: FEASpecCalculiXRunMetadata,
) -> FEASpecCalculiXRunDiagnostic | None:
    try:
        path.write_text(
            json.dumps(metadata.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        return _diag(
            CalculiXRunDiagnosticCode.FR_METADATA_WRITE_FAILED,
            CalculiXRunSeverity.ERROR,
            f"Could not write run metadata: {exc}",
            path=str(path),
            suggested_fix="Check run directory permissions.",
        )
    return None


def _timeout_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _path_is_executable(path: Path) -> bool:
    if os.name == "nt":
        return path.is_file()
    return path.is_file() and os.access(path, os.X_OK)


def _is_root_path(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    return resolved.parent == resolved


def _has_blockers(
    diagnostics: Sequence[FEASpecCalculiXRunDiagnostic],
) -> bool:
    return any(item.blocks_execution for item in diagnostics)


def _diag(
    code: CalculiXRunDiagnosticCode,
    severity: CalculiXRunSeverity,
    message: str,
    *,
    path: str = "",
    suggested_fix: str = "",
    blocks_execution: bool | None = None,
) -> FEASpecCalculiXRunDiagnostic:
    return FEASpecCalculiXRunDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        suggested_fix=suggested_fix,
        blocks_execution=blocks_execution,
    )


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXRunDiagnostic],
) -> list[FEASpecCalculiXRunDiagnostic]:
    seen: set[tuple[CalculiXRunDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXRunDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.path, diagnostic.message)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique


def _limitations() -> tuple[str, ...]:
    return (
        "Installed-only run gate; no CalculiX install was attempted.",
        "No result import or .frd/.dat parser is implemented by this gate.",
        "No release, tag, issue, or asset mutation is performed.",
        "External solvers remain optional and are not bundled.",
        (
            "GitHub state verified 2026-07-14: Issue #8 is closed after bounded "
            "WSL CalculiX evidence; this workflow does not broaden that closure."
        ),
        "No industrial certification, compliance, production CAE, or accuracy claim.",
    )


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
