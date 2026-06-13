"""Experimental no-run FEASpec CalculiX export bundles."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from osw import __version__ as OSW_VERSION

from .calculix_case_plan import (
    FEASpecCalculiXCasePlan,
    plan_calculix_case_from_bridge,
    plan_calculix_case_from_feaspec,
)
from .calculix_export_diagnostics import (
    CalculiXExportDiagnosticCode,
    CalculiXExportSeverity,
    FEASpecCalculiXExportDiagnostic,
)
from .calculix_inp_renderer import CalculiXInpRenderResult, render_calculix_inp
from .models import FEASpecDocument
from .project_bridge import FEASpecProjectBridgePlan

EXPORTER_MODULE = "osw.experimental.feaspec.calculix_exporter"
README_FILENAME = "README_RUN_FIRST.txt"
TARGET_SOLVER = "calculix"

__all__ = [
    "FEASpecCalculiXExportManifest",
    "FEASpecCalculiXExportResult",
    "FEASpecCalculiXExportStatus",
    "FEASpecCalculiXExportedFile",
    "export_calculix_case",
    "export_calculix_case_from_bridge",
    "export_calculix_case_from_feaspec",
    "explain_calculix_export_result",
]


class FEASpecCalculiXExportStatus(str, Enum):
    """Status for no-run FEASpec CalculiX export bundles."""

    BLOCKED = "blocked"
    EXPORTED = "exported"
    EXPORTED_WITH_WARNINGS = "exported-with-warnings"


@dataclass(frozen=True)
class FEASpecCalculiXExportedFile:
    """A file written by the no-run CalculiX exporter."""

    role: str
    filename: str
    path: Path
    sha256: str
    size_bytes: int

    @classmethod
    def from_path(cls, role: str, path: Path) -> FEASpecCalculiXExportedFile:
        payload = path.read_bytes()
        return cls(
            role=role,
            filename=path.name,
            path=path,
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "filename": self.filename,
            "path": str(self.path),
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }

    def to_manifest_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "filename": self.filename,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class FEASpecCalculiXExportManifest:
    """Serializable manifest for a no-run FEASpec CalculiX export bundle."""

    exporter_module: str
    osw_version: str
    release_tag: str
    target_solver: str
    source_feaspec_id: str
    case_id: str
    solver_execution_performed: bool
    ready_for_solver_execution: bool
    files: tuple[FEASpecCalculiXExportedFile, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "exporter_module": self.exporter_module,
            "osw_version": self.osw_version,
            "release_tag": self.release_tag,
            "target_solver": self.target_solver,
            "source_feaspec_id": self.source_feaspec_id,
            "case_id": self.case_id,
            "solver_execution_performed": self.solver_execution_performed,
            "ready_for_solver_execution": self.ready_for_solver_execution,
            "files": [item.to_manifest_dict() for item in self.files],
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class FEASpecCalculiXExportResult:
    """Result of a no-run FEASpec CalculiX export bundle request."""

    status: str
    output_dir: Path
    files: tuple[FEASpecCalculiXExportedFile, ...] = ()
    manifest: FEASpecCalculiXExportManifest | None = None
    diagnostics: tuple[FEASpecCalculiXExportDiagnostic, ...] = ()
    render_result: CalculiXInpRenderResult | None = None
    ready_for_solver_execution: bool = False
    solver_execution_performed: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.status == FEASpecCalculiXExportStatus.BLOCKED.value

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "output_dir": str(self.output_dir),
            "files": [item.to_dict() for item in self.files],
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "render_result": self.render_result.to_dict() if self.render_result else None,
            "ready_for_solver_execution": self.ready_for_solver_execution,
            "solver_execution_performed": self.solver_execution_performed,
        }


def export_calculix_case(
    case_plan: FEASpecCalculiXCasePlan,
    output_dir: str | Path,
    *,
    basename: str = "feaspec_calculix_case",
    overwrite: bool = False,
    create_dir: bool = False,
) -> FEASpecCalculiXExportResult:
    """Write a no-run CalculiX export bundle for a writer-ready case plan."""

    target_dir = Path(output_dir)
    diagnostics = [_solver_run_forbidden_diag()]

    diagnostics.extend(_validate_basename(basename))
    diagnostics.extend(_prepare_output_dir(target_dir, create_dir=create_dir))
    if not _blocks_export(diagnostics):
        target_paths = _target_paths(target_dir, basename)
        diagnostics.extend(
            _validate_target_paths(target_dir, target_paths, overwrite=overwrite)
        )
    else:
        target_paths = {}

    if _blocks_export(diagnostics):
        return _blocked_result(target_dir, diagnostics)

    render_result = render_calculix_inp(case_plan)
    if render_result.is_blocked:
        diagnostics.append(
            _diag(
                CalculiXExportDiagnosticCode.FX_RENDER_BLOCKED,
                CalculiXExportSeverity.BLOCKER,
                "CalculiX INP rendering is blocked; no export files were written.",
                suggested_fix="Resolve renderer diagnostics before exporting.",
            )
        )
        return _blocked_result(target_dir, diagnostics, render_result=render_result)

    write_failure = _write_text(
        target_paths["inp"],
        render_result.text,
        CalculiXExportDiagnosticCode.FX_WRITE_FAILED,
    )
    if write_failure:
        diagnostics.append(write_failure)
        return _blocked_result(target_dir, diagnostics, render_result=render_result)

    diagnostics_payload = _diagnostics_payload(
        diagnostics=diagnostics,
        render_result=render_result,
        status=_export_status(diagnostics, render_result),
    )
    diagnostics_failure = _write_json(
        target_paths["diagnostics"],
        diagnostics_payload,
        CalculiXExportDiagnosticCode.FX_DIAGNOSTICS_WRITE_FAILED,
    )
    if diagnostics_failure:
        diagnostics.append(diagnostics_failure)
        return _blocked_result(target_dir, diagnostics, render_result=render_result)

    readme_failure = _write_text(
        target_paths["readme"],
        _readme_text(case_plan),
        CalculiXExportDiagnosticCode.FX_README_WRITE_FAILED,
    )
    if readme_failure:
        diagnostics.append(readme_failure)
        return _blocked_result(target_dir, diagnostics, render_result=render_result)

    manifest_files = (
        FEASpecCalculiXExportedFile.from_path("inp", target_paths["inp"]),
        FEASpecCalculiXExportedFile.from_path(
            "diagnostics", target_paths["diagnostics"]
        ),
        FEASpecCalculiXExportedFile.from_path("readme", target_paths["readme"]),
    )
    manifest = FEASpecCalculiXExportManifest(
        exporter_module=EXPORTER_MODULE,
        osw_version=OSW_VERSION,
        release_tag=_release_tag(),
        target_solver=TARGET_SOLVER,
        source_feaspec_id=case_plan.source_feaspec_id,
        case_id=case_plan.case_id,
        solver_execution_performed=False,
        ready_for_solver_execution=False,
        files=manifest_files,
        limitations=_limitations(),
    )
    manifest_failure = _write_json(
        target_paths["manifest"],
        manifest.to_dict(),
        CalculiXExportDiagnosticCode.FX_MANIFEST_WRITE_FAILED,
    )
    if manifest_failure:
        diagnostics.append(manifest_failure)
        return _blocked_result(target_dir, diagnostics, render_result=render_result)

    files = (
        manifest_files[0],
        FEASpecCalculiXExportedFile.from_path("manifest", target_paths["manifest"]),
        manifest_files[1],
        manifest_files[2],
    )
    checksum_failure = _verify_file_checksums(files)
    if checksum_failure:
        diagnostics.append(checksum_failure)
        return _blocked_result(target_dir, diagnostics, render_result=render_result)

    return FEASpecCalculiXExportResult(
        status=_export_status(diagnostics, render_result),
        output_dir=target_dir,
        files=files,
        manifest=manifest,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        render_result=render_result,
        ready_for_solver_execution=False,
        solver_execution_performed=False,
    )


def export_calculix_case_from_feaspec(
    spec_or_dict: FEASpecDocument | Mapping[str, Any] | str | Path,
    output_dir: str | Path,
    *,
    basename: str = "feaspec_calculix_case",
    overwrite: bool = False,
    create_dir: bool = False,
) -> FEASpecCalculiXExportResult:
    """Plan and export a no-run CalculiX bundle from approved FEASpec data."""

    return export_calculix_case(
        plan_calculix_case_from_feaspec(spec_or_dict),
        output_dir,
        basename=basename,
        overwrite=overwrite,
        create_dir=create_dir,
    )


def export_calculix_case_from_bridge(
    bridge_plan: FEASpecProjectBridgePlan,
    output_dir: str | Path,
    *,
    basename: str = "feaspec_calculix_case",
    overwrite: bool = False,
    create_dir: bool = False,
) -> FEASpecCalculiXExportResult:
    """Plan and export a no-run CalculiX bundle from a bridge plan."""

    return export_calculix_case(
        plan_calculix_case_from_bridge(bridge_plan),
        output_dir,
        basename=basename,
        overwrite=overwrite,
        create_dir=create_dir,
    )


def explain_calculix_export_result(
    result: FEASpecCalculiXExportResult,
) -> list[str]:
    """Return reviewer-readable no-run export status and diagnostics."""

    lines = [
        f"CalculiX export status: {result.status}.",
        f"Ready for solver execution: {str(result.ready_for_solver_execution).lower()}.",
        (
            "Solver execution performed: "
            f"{str(result.solver_execution_performed).lower()}."
        ),
    ]
    if result.files:
        lines.append(f"Exported {len(result.files)} no-run bundle files.")
        lines.extend(f"- {item.filename} ({item.role})" for item in result.files)
    else:
        lines.append("No export files were written.")
    for diagnostic in result.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    lines.append("No CalculiX solver execution was performed.")
    return lines


def _target_paths(output_dir: Path, basename: str) -> dict[str, Path]:
    return {
        "inp": output_dir / f"{basename}.inp",
        "manifest": output_dir / f"{basename}.manifest.json",
        "diagnostics": output_dir / f"{basename}.diagnostics.json",
        "readme": output_dir / README_FILENAME,
    }


def _validate_basename(basename: str) -> list[FEASpecCalculiXExportDiagnostic]:
    text = str(basename)
    forbidden = set('<>:"/\\|?*')
    unsafe = (
        not text.strip()
        or text in {".", ".."}
        or Path(text).name != text
        or ".." in Path(text).parts
        or any(character in forbidden or ord(character) < 32 for character in text)
    )
    if not unsafe:
        return []
    return [
        _diag(
            CalculiXExportDiagnosticCode.FX_UNSAFE_BASENAME,
            CalculiXExportSeverity.BLOCKER,
            "Export basename is unsafe for a no-run CalculiX bundle.",
            path=text,
            suggested_fix=(
                "Use a simple filename stem without separators, parent traversal, "
                "drive letters, wildcards, or control characters."
            ),
        )
    ]


def _prepare_output_dir(
    output_dir: Path,
    *,
    create_dir: bool,
) -> list[FEASpecCalculiXExportDiagnostic]:
    if output_dir.exists() and not output_dir.is_dir():
        return [
            _diag(
                CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_NOT_DIRECTORY,
                CalculiXExportSeverity.BLOCKER,
                "Export output path exists but is not a directory.",
                path=str(output_dir),
                suggested_fix="Choose or create a directory for the export bundle.",
            )
        ]
    if output_dir.exists():
        return []
    if not create_dir:
        return [
            _diag(
                CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_MISSING,
                CalculiXExportSeverity.BLOCKER,
                "Export output directory does not exist.",
                path=str(output_dir),
                suggested_fix="Create the directory or pass create_dir=True.",
            )
        ]
    try:
        output_dir.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        return [
            _diag(
                CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_MISSING,
                CalculiXExportSeverity.BLOCKER,
                f"Could not create the final output directory: {exc}",
                path=str(output_dir),
                suggested_fix="Create the parent directory and retry.",
            )
        ]
    return []


def _validate_target_paths(
    output_dir: Path,
    target_paths: Mapping[str, Path],
    *,
    overwrite: bool,
) -> list[FEASpecCalculiXExportDiagnostic]:
    diagnostics: list[FEASpecCalculiXExportDiagnostic] = []
    existing_targets = [path for path in target_paths.values() if path.exists()]
    if existing_targets and not overwrite:
        diagnostics.append(
            _diag(
                CalculiXExportDiagnosticCode.FX_OUTPUT_EXISTS,
                CalculiXExportSeverity.BLOCKER,
                "One or more export target files already exist.",
                path=", ".join(str(path) for path in existing_targets),
                suggested_fix="Choose a new output directory or pass overwrite=True.",
            )
        )
    if not overwrite:
        target_names = {path.name for path in target_paths.values()}
        unrelated_entries = [
            item.name for item in output_dir.iterdir() if item.name not in target_names
        ]
        if unrelated_entries:
            diagnostics.append(
                _diag(
                    CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_NOT_EMPTY,
                    CalculiXExportSeverity.BLOCKER,
                    "Export output directory is not empty.",
                    path=str(output_dir),
                    suggested_fix=(
                        "Use an empty directory, choose a new directory, or pass "
                        "overwrite=True after review."
                    ),
                )
            )
    return diagnostics


def _diagnostics_payload(
    *,
    diagnostics: Sequence[FEASpecCalculiXExportDiagnostic],
    render_result: CalculiXInpRenderResult,
    status: str,
) -> dict[str, object]:
    return {
        "status": status,
        "solver_execution_performed": False,
        "ready_for_solver_execution": False,
        "export_diagnostics": [
            diagnostic.to_dict() for diagnostic in _dedupe_diagnostics(diagnostics)
        ],
        "render_diagnostics": [
            diagnostic.to_dict() for diagnostic in render_result.diagnostics
        ],
    }


def _readme_text(case_plan: FEASpecCalculiXCasePlan) -> str:
    return "\n".join(
        [
            "OpenSolver Workbench FEASpec CalculiX no-run export bundle",
            "",
            f"Case plan: {case_plan.case_id}",
            f"Source FEASpec: {case_plan.source_feaspec_id or 'unknown'}",
            f"OSW version: {OSW_VERSION}",
            f"Release tag context: {_release_tag()}",
            "",
            "No solver execution was performed by this exporter.",
            "Inspect the `.inp` text and diagnostics before any manual run.",
            "CalculiX is not bundled with OpenSolver Workbench.",
            "This FEASpec-to-CalculiX path is experimental.",
            "No industrial certification, compliance, production CAE, or accuracy claim is made.",
            "Issue #8 live CalculiX validation remains separate from this export bundle.",
            "External solver execution must use a future reviewed installed-only run gate.",
            "",
        ]
    )


def _write_text(
    path: Path,
    text: str,
    code: CalculiXExportDiagnosticCode,
) -> FEASpecCalculiXExportDiagnostic | None:
    try:
        path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        return _diag(
            code,
            CalculiXExportSeverity.BLOCKER,
            f"Failed to write export file: {exc}",
            path=str(path),
            suggested_fix="Check directory permissions and retry.",
        )
    return None


def _write_json(
    path: Path,
    payload: Mapping[str, object],
    code: CalculiXExportDiagnosticCode,
) -> FEASpecCalculiXExportDiagnostic | None:
    return _write_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        code,
    )


def _verify_file_checksums(
    files: Sequence[FEASpecCalculiXExportedFile],
) -> FEASpecCalculiXExportDiagnostic | None:
    for exported_file in files:
        current = FEASpecCalculiXExportedFile.from_path(
            exported_file.role,
            exported_file.path,
        )
        if (
            current.sha256 != exported_file.sha256
            or current.size_bytes != exported_file.size_bytes
        ):
            return _diag(
                CalculiXExportDiagnosticCode.FX_CHECKSUM_FAILED,
                CalculiXExportSeverity.BLOCKER,
                "Export file checksum changed during verification.",
                path=str(exported_file.path),
                suggested_fix="Discard the bundle and rerun export.",
            )
    return None


def _export_status(
    diagnostics: Sequence[FEASpecCalculiXExportDiagnostic],
    render_result: CalculiXInpRenderResult,
) -> str:
    if _blocks_export(diagnostics):
        return FEASpecCalculiXExportStatus.BLOCKED.value
    if render_result.status.endswith("warnings") or any(
        diagnostic.severity is CalculiXExportSeverity.WARNING
        for diagnostic in diagnostics
    ):
        return FEASpecCalculiXExportStatus.EXPORTED_WITH_WARNINGS.value
    return FEASpecCalculiXExportStatus.EXPORTED.value


def _release_tag() -> str:
    if "rc" in OSW_VERSION:
        prefix, suffix = OSW_VERSION.split("rc", 1)
        return f"v{prefix}-rc{suffix}"
    return f"v{OSW_VERSION}"


def _limitations() -> tuple[str, ...]:
    return (
        "No solver run was performed by this exporter.",
        "No industrial certification, compliance, production CAE, or accuracy claim.",
        "External CalculiX solver binaries are not bundled.",
        "Issue #8 live CalculiX validation remains separate.",
        "FEASpec CalculiX export remains experimental.",
    )


def _solver_run_forbidden_diag() -> FEASpecCalculiXExportDiagnostic:
    return _diag(
        CalculiXExportDiagnosticCode.FX_SOLVER_RUN_FORBIDDEN,
        CalculiXExportSeverity.INFO,
        "Exporter is limited to no-run file bundle creation.",
        suggested_fix="Use a separate installed-only run gate for future solver execution.",
        blocks_export=False,
    )


def _blocked_result(
    output_dir: Path,
    diagnostics: Sequence[FEASpecCalculiXExportDiagnostic],
    *,
    render_result: CalculiXInpRenderResult | None = None,
) -> FEASpecCalculiXExportResult:
    return FEASpecCalculiXExportResult(
        status=FEASpecCalculiXExportStatus.BLOCKED.value,
        output_dir=output_dir,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        render_result=render_result,
        ready_for_solver_execution=False,
        solver_execution_performed=False,
    )


def _diag(
    code: CalculiXExportDiagnosticCode,
    severity: CalculiXExportSeverity,
    message: str,
    *,
    path: str = "",
    suggested_fix: str = "",
    blocks_export: bool | None = None,
) -> FEASpecCalculiXExportDiagnostic:
    return FEASpecCalculiXExportDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        suggested_fix=suggested_fix,
        blocks_export=blocks_export,
    )


def _blocks_export(
    diagnostics: Sequence[FEASpecCalculiXExportDiagnostic],
) -> bool:
    return any(diagnostic.blocks_export for diagnostic in diagnostics)


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXExportDiagnostic],
) -> list[FEASpecCalculiXExportDiagnostic]:
    seen: set[tuple[CalculiXExportDiagnosticCode, str]] = set()
    unique: list[FEASpecCalculiXExportDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.path)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique
