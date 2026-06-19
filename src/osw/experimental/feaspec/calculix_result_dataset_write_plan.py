"""In-memory ResultDataset write planning for FEASpec CalculiX results.

This module plans a future persistence operation only. It inspects explicit
output paths and existing artifact references, but it does not create
directories, copy artifacts, write ResultDataset files, execute solvers, or
mutate ProjectSchema records.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path

from osw import __version__ as OSW_VERSION

from .calculix_result_dataset_write_diagnostics import (
    CalculiXResultDatasetWriteDiagnosticCode,
    CalculiXResultDatasetWriteSeverity,
    FEASpecCalculiXResultDatasetWriteDiagnostic,
)

__all__ = [
    "FEASpecCalculiXResultDatasetWritePlan",
    "FEASpecCalculiXResultDatasetWritePlanValidation",
    "FEASpecCalculiXResultDatasetWriteTarget",
    "FEASpecCalculiXResultDatasetPlannedFile",
    "FEASpecCalculiXResultDatasetArtifactReferencePlan",
    "FEASpecCalculiXResultDatasetAtomicWritePlan",
    "FEASpecCalculiXResultDatasetWriteStatus",
    "plan_calculix_result_dataset_write",
    "validate_calculix_result_dataset_write_plan",
    "explain_calculix_result_dataset_write_plan",
]

WRITE_SCHEMA_NAME = "osw.feaspec.calculix.resultdataset"
WRITE_SCHEMA_VERSION = "0.1"
STANDARD_OUTPUT_FILES = (
    "result_dataset.json",
    "result_dataset_manifest.json",
    "diagnostics.json",
    "provenance.json",
    "README_REVIEW_FIRST.txt",
)


class FEASpecCalculiXResultDatasetWriteStatus(str, Enum):
    """Status for in-memory ResultDataset write plans."""

    PLANNED = "planned"
    PLANNED_WITH_WARNINGS = "planned-with-warnings"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    PERSISTENCE_NOT_IMPLEMENTED = "persistence-not-implemented"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetWriteTarget:
    """Explicit output target analysis for a future write operation."""

    mode: str
    output_dir: str = ""
    output_path: str = ""
    parent_path: str = ""
    parent_exists: bool = False
    target_exists: bool = False
    target_is_file: bool = False
    target_is_directory: bool = False
    target_nonempty: bool = False
    create_dir_requested: bool = False
    create_dir_planned: bool = False
    overwrite_requested: bool = False
    unsafe_path: bool = False
    traversal_rejected: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "output_dir": self.output_dir,
            "output_path": self.output_path,
            "parent_path": self.parent_path,
            "parent_exists": self.parent_exists,
            "target_exists": self.target_exists,
            "target_is_file": self.target_is_file,
            "target_is_directory": self.target_is_directory,
            "target_nonempty": self.target_nonempty,
            "create_dir_requested": self.create_dir_requested,
            "create_dir_planned": self.create_dir_planned,
            "overwrite_requested": self.overwrite_requested,
            "unsafe_path": self.unsafe_path,
            "traversal_rejected": self.traversal_rejected,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetPlannedFile:
    """A future ResultDataset output file planned in memory only."""

    role: str
    relative_path: str
    target_path: str
    temp_path: str
    exists: bool = False
    would_overwrite: bool = False
    writes_file: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "relative_path": self.relative_path,
            "target_path": self.target_path,
            "temp_path": self.temp_path,
            "exists": self.exists,
            "would_overwrite": self.would_overwrite,
            "writes_file": self.writes_file,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetArtifactReferencePlan:
    """Original artifact reference retained for a future persisted dataset."""

    source_path: str
    filename: str
    role: str
    suffix: str
    sha256: str
    size_bytes: int
    exists: bool = False
    size_matches: bool | None = None
    copy_requested: bool = False
    copy_planned: bool = False
    copy_supported: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "filename": self.filename,
            "role": self.role,
            "suffix": self.suffix,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "exists": self.exists,
            "size_matches": self.size_matches,
            "copy_requested": self.copy_requested,
            "copy_planned": self.copy_planned,
            "copy_supported": self.copy_supported,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetAtomicWritePlan:
    """Planned temp and target paths for a future atomic write."""

    planned_only: bool
    temp_dir: str
    target_dir: str
    file_pairs: tuple[Mapping[str, str], ...]
    writes_files: bool = False
    atomic_write_implemented: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "planned_only": self.planned_only,
            "temp_dir": self.temp_dir,
            "target_dir": self.target_dir,
            "file_pairs": [dict(item) for item in self.file_pairs],
            "writes_files": self.writes_files,
            "atomic_write_implemented": self.atomic_write_implemented,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetWritePlanValidation:
    """Validation summary for a ResultDataset write plan."""

    status: FEASpecCalculiXResultDatasetWriteStatus
    diagnostics: tuple[FEASpecCalculiXResultDatasetWriteDiagnostic, ...]
    has_blockers: bool
    writes_files: bool = False
    result_dataset_persistence: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "has_blockers": self.has_blockers,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetWritePlan:
    """In-memory plan for a future reviewed ResultDataset write."""

    status: FEASpecCalculiXResultDatasetWriteStatus
    target: FEASpecCalculiXResultDatasetWriteTarget
    planned_files: tuple[FEASpecCalculiXResultDatasetPlannedFile, ...]
    artifact_references: tuple[
        FEASpecCalculiXResultDatasetArtifactReferencePlan,
        ...,
    ]
    atomic_write_plan: FEASpecCalculiXResultDatasetAtomicWritePlan
    diagnostics: tuple[FEASpecCalculiXResultDatasetWriteDiagnostic, ...]
    mapping_status: str = ""
    schema_name: str = WRITE_SCHEMA_NAME
    schema_version: str = WRITE_SCHEMA_VERSION
    producer_version: str = OSW_VERSION
    source_release: str = "v0.1.4-rc1"
    limitations_acknowledged: bool = False
    copy_artifacts_requested: bool = False
    writes_files: bool = False
    result_dataset_persistence: bool = False
    solver_execution_performed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "target": self.target.to_dict(),
            "planned_files": [item.to_dict() for item in self.planned_files],
            "artifact_references": [
                item.to_dict() for item in self.artifact_references
            ],
            "atomic_write_plan": self.atomic_write_plan.to_dict(),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "mapping_status": self.mapping_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "producer_version": self.producer_version,
            "source_release": self.source_release,
            "limitations_acknowledged": self.limitations_acknowledged,
            "copy_artifacts_requested": self.copy_artifacts_requested,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
            "solver_execution_performed": self.solver_execution_performed,
        }


def plan_calculix_result_dataset_write(
    mapping: object,
    *,
    output_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    overwrite: bool = False,
    create_dir: bool = False,
    acknowledge_limitations: bool = False,
    copy_artifacts: bool = False,
) -> FEASpecCalculiXResultDatasetWritePlan:
    """Build an in-memory write plan without performing persistence."""

    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic] = [
        _diag(
            CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_NOT_IMPLEMENTED,
            CalculiXResultDatasetWriteSeverity.INFO,
            "ResultDataset write implementation is not present in this gate.",
            blocks_write=False,
        ),
        _diag(
            CalculiXResultDatasetWriteDiagnosticCode.FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN,
            CalculiXResultDatasetWriteSeverity.INFO,
            "This planner does not persist ResultDataset files.",
            blocks_write=False,
        ),
    ]
    target = _target_from_paths(
        output_dir=output_dir,
        output_path=output_path,
        overwrite=overwrite,
        create_dir=create_dir,
        diagnostics=diagnostics,
    )
    planned_files = _planned_files(target)
    atomic_write_plan = _atomic_write_plan(target, planned_files)
    if planned_files:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_ATOMIC_WRITE_PLANNED_ONLY,
                CalculiXResultDatasetWriteSeverity.INFO,
                "Atomic write temp and target paths are planned only.",
                path=target.output_dir,
                blocks_write=False,
            )
        )
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_ATOMIC_WRITE_NOT_IMPLEMENTED,
                CalculiXResultDatasetWriteSeverity.INFO,
                "Atomic write behavior is not implemented by this model.",
                path=target.output_dir,
                blocks_write=False,
            )
        )

    artifact_references = _artifact_reference_plan(
        mapping,
        copy_artifacts=copy_artifacts,
        diagnostics=diagnostics,
    )
    _append_mapping_diagnostics(
        mapping,
        acknowledge_limitations=acknowledge_limitations,
        diagnostics=diagnostics,
    )
    if copy_artifacts:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_ARTIFACT_COPY_NOT_IMPLEMENTED,
                CalculiXResultDatasetWriteSeverity.WARNING,
                "Artifact copy mode is future-only; artifacts are referenced, not copied.",
                blocks_write=False,
            )
        )

    diagnostics_tuple = tuple(_dedupe_diagnostics(diagnostics))
    status = _status_from_diagnostics(diagnostics_tuple, output_path=output_path)
    return FEASpecCalculiXResultDatasetWritePlan(
        status=status,
        target=target,
        planned_files=planned_files,
        artifact_references=artifact_references,
        atomic_write_plan=atomic_write_plan,
        diagnostics=diagnostics_tuple,
        mapping_status=_mapping_status_text(mapping),
        schema_version=_schema_version(mapping),
        limitations_acknowledged=acknowledge_limitations,
        copy_artifacts_requested=copy_artifacts,
    )


def validate_calculix_result_dataset_write_plan(
    plan: FEASpecCalculiXResultDatasetWritePlan,
) -> FEASpecCalculiXResultDatasetWritePlanValidation:
    """Return blocker status for a write plan."""

    has_blockers = any(item.blocks_write for item in plan.diagnostics)
    status = FEASpecCalculiXResultDatasetWriteStatus.BLOCKED if has_blockers else plan.status
    return FEASpecCalculiXResultDatasetWritePlanValidation(
        status=status,
        diagnostics=plan.diagnostics,
        has_blockers=has_blockers,
        writes_files=plan.writes_files,
        result_dataset_persistence=plan.result_dataset_persistence,
    )


def explain_calculix_result_dataset_write_plan(
    plan: FEASpecCalculiXResultDatasetWritePlan,
) -> list[str]:
    """Return reviewer-readable write-plan notes."""

    validation = validate_calculix_result_dataset_write_plan(plan)
    lines = [
        f"ResultDataset write plan status: {validation.status.value}.",
        "ResultDataset persistence implemented: false.",
        "ResultDataset files written: false.",
        f"Planned output mode: {plan.target.mode}.",
        f"Planned files: {len(plan.planned_files)}.",
        f"Artifact references: {len(plan.artifact_references)}.",
        "Atomic write implementation: false.",
        "Solver execution performed: false.",
    ]
    for diagnostic in plan.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _target_from_paths(
    *,
    output_dir: str | Path | None,
    output_path: str | Path | None,
    overwrite: bool,
    create_dir: bool,
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic],
) -> FEASpecCalculiXResultDatasetWriteTarget:
    if output_dir is None and output_path is None:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_PATH_REQUIRED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "An explicit output directory is required.",
                suggested_fix="Pass output_dir for the planned ResultDataset layout.",
            )
        )
        return FEASpecCalculiXResultDatasetWriteTarget(
            mode="missing",
            overwrite_requested=overwrite,
            create_dir_requested=create_dir,
        )

    if output_path is not None and output_dir is None:
        path = Path(output_path).expanduser()
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_DIRECTORY_REQUIRED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Single-file output_path mode is not supported by this plan model.",
                path=str(path),
                suggested_fix="Pass output_dir to plan the standard directory layout.",
            )
        )
        return _analyze_target_path(
            path,
            mode="single-file-unsupported",
            overwrite=overwrite,
            create_dir=create_dir,
            diagnostics=diagnostics,
            output_path=str(path),
        )

    if output_path is not None:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_DIRECTORY_REQUIRED,
                CalculiXResultDatasetWriteSeverity.WARNING,
                "output_path is ignored when output_dir is provided.",
                path=str(output_path),
                suggested_fix="Use output_dir only for the standard layout.",
                blocks_write=False,
            )
        )
    return _analyze_target_path(
        Path(output_dir).expanduser(),
        mode="directory-layout",
        overwrite=overwrite,
        create_dir=create_dir,
        diagnostics=diagnostics,
    )


def _analyze_target_path(
    path: Path,
    *,
    mode: str,
    overwrite: bool,
    create_dir: bool,
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic],
    output_path: str = "",
) -> FEASpecCalculiXResultDatasetWriteTarget:
    parent = path.parent
    target_exists = path.exists()
    target_is_file = path.is_file()
    target_is_directory = path.is_dir()
    parent_exists = parent.exists()
    traversal = _has_traversal(path)
    unsafe = _is_unsafe_path(path)
    target_nonempty = _is_nonempty_directory(path)
    create_dir_planned = bool(create_dir and not target_exists)

    if traversal:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_PATH_TRAVERSAL_REJECTED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output path contains traversal segments.",
                path=str(path),
                suggested_fix="Use a normalized explicit output directory.",
            )
        )
    if unsafe:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_UNSAFE_PATH,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output path is inside a forbidden location.",
                path=str(path),
                suggested_fix="Use an explicit project or ignored artifact directory.",
            )
        )
    if not target_exists and not parent_exists and not create_dir:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_PARENT_MISSING,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output parent directory does not exist.",
                path=str(parent),
                suggested_fix="Create the parent explicitly or pass create_dir=True.",
            )
        )
    if not target_exists and create_dir:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_CREATE_DIR_REQUIRED,
                CalculiXResultDatasetWriteSeverity.INFO,
                "Output directory creation is planned only.",
                path=str(path),
                blocks_write=False,
            )
        )
    if target_exists and target_is_file and not overwrite:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_EXISTS,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output target already exists as a file.",
                path=str(path),
                suggested_fix="Choose a new directory or pass overwrite=True after review.",
            )
        )
    elif target_exists and target_is_file and overwrite:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_EXISTS,
                CalculiXResultDatasetWriteSeverity.WARNING,
                "Output target exists as a file and would require replacement.",
                path=str(path),
                blocks_write=False,
            )
        )
    if target_nonempty and not overwrite:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_NOT_EMPTY,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output directory exists and is not empty.",
                path=str(path),
                suggested_fix="Choose an empty directory or pass overwrite=True after review.",
            )
        )
    elif target_nonempty and overwrite:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_NOT_EMPTY,
                CalculiXResultDatasetWriteSeverity.WARNING,
                "Output directory exists and is not empty; overwrite is planned only.",
                path=str(path),
                blocks_write=False,
            )
        )

    return FEASpecCalculiXResultDatasetWriteTarget(
        mode=mode,
        output_dir=str(path) if mode == "directory-layout" else "",
        output_path=output_path,
        parent_path=str(parent),
        parent_exists=parent_exists,
        target_exists=target_exists,
        target_is_file=target_is_file,
        target_is_directory=target_is_directory,
        target_nonempty=target_nonempty,
        create_dir_requested=create_dir,
        create_dir_planned=create_dir_planned,
        overwrite_requested=overwrite,
        unsafe_path=unsafe,
        traversal_rejected=traversal,
    )


def _planned_files(
    target: FEASpecCalculiXResultDatasetWriteTarget,
) -> tuple[FEASpecCalculiXResultDatasetPlannedFile, ...]:
    if target.mode != "directory-layout" or not target.output_dir:
        return ()
    root = Path(target.output_dir)
    temp_root = root.parent / f".{root.name}.tmp-osw-resultdataset"
    return tuple(
        FEASpecCalculiXResultDatasetPlannedFile(
            role=_file_role(name),
            relative_path=name,
            target_path=str(root / name),
            temp_path=str(temp_root / name),
            exists=(root / name).exists(),
            would_overwrite=(root / name).exists() and target.overwrite_requested,
        )
        for name in STANDARD_OUTPUT_FILES
    )


def _atomic_write_plan(
    target: FEASpecCalculiXResultDatasetWriteTarget,
    planned_files: Sequence[FEASpecCalculiXResultDatasetPlannedFile],
) -> FEASpecCalculiXResultDatasetAtomicWritePlan:
    target_dir = target.output_dir or target.output_path
    temp_dir = ""
    if target.output_dir:
        root = Path(target.output_dir)
        temp_dir = str(root.parent / f".{root.name}.tmp-osw-resultdataset")
    return FEASpecCalculiXResultDatasetAtomicWritePlan(
        planned_only=True,
        temp_dir=temp_dir,
        target_dir=target_dir,
        file_pairs=tuple(
            {"temp_path": item.temp_path, "target_path": item.target_path}
            for item in planned_files
        ),
    )


def _artifact_reference_plan(
    mapping: object,
    *,
    copy_artifacts: bool,
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic],
) -> tuple[FEASpecCalculiXResultDatasetArtifactReferencePlan, ...]:
    references: list[FEASpecCalculiXResultDatasetArtifactReferencePlan] = []
    for artifact in _mapping_artifacts(mapping):
        source_path = _artifact_value(artifact, "source_path")
        filename = _artifact_value(artifact, "filename") or Path(source_path).name
        sha256 = _artifact_value(artifact, "sha256")
        size_bytes = _int_value(_artifact_value(artifact, "size_bytes"))
        artifact_path = Path(source_path) if source_path else None
        exists = artifact_path.exists() if artifact_path is not None else False
        size_matches: bool | None = None
        digest_matches: bool | None = None
        if exists and artifact_path is not None and artifact_path.is_file():
            size_matches = artifact_path.stat().st_size == size_bytes
            digest_matches = _sha256_file(artifact_path) == sha256
        if not source_path or not sha256 or size_bytes <= 0:
            diagnostics.append(
                _diag(
                    CalculiXResultDatasetWriteDiagnosticCode.FDW_ARTIFACT_REFERENCE_MISSING,
                    CalculiXResultDatasetWriteSeverity.BLOCKER,
                    "Artifact reference must include path, SHA-256, and size.",
                    path=source_path,
                    suggested_fix="Rebuild the draft mapping with complete artifact metadata.",
                )
            )
        elif exists and (size_matches is False or digest_matches is False):
            diagnostics.append(
                _diag(
                    CalculiXResultDatasetWriteDiagnosticCode.FDW_ARTIFACT_HASH_MISMATCH,
                    CalculiXResultDatasetWriteSeverity.BLOCKER,
                    "Artifact hash or size no longer matches the draft reference.",
                    path=source_path,
                    suggested_fix="Re-scan artifacts before planning persistence.",
                )
            )
        elif not exists:
            diagnostics.append(
                _diag(
                    CalculiXResultDatasetWriteDiagnosticCode.FDW_ARTIFACT_REFERENCE_MISSING,
                    CalculiXResultDatasetWriteSeverity.WARNING,
                    "Artifact path is not present on this machine; reference is retained.",
                    path=source_path,
                    blocks_write=False,
                )
            )
        references.append(
            FEASpecCalculiXResultDatasetArtifactReferencePlan(
                source_path=source_path,
                filename=filename,
                role=_artifact_value(artifact, "role"),
                suffix=_artifact_value(artifact, "suffix"),
                sha256=sha256,
                size_bytes=size_bytes,
                exists=exists,
                size_matches=size_matches,
                copy_requested=copy_artifacts,
                copy_planned=False,
                copy_supported=False,
            )
        )
    return tuple(references)


def _append_mapping_diagnostics(
    mapping: object,
    *,
    acknowledge_limitations: bool,
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic],
) -> None:
    mapping_status = _mapping_status_text(mapping)
    if mapping_status in {"blocked", "unsupported"}:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_DRAFT_BLOCKED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "ResultDataset draft mapping is blocked or unsupported.",
                suggested_fix="Resolve result import blockers before planning persistence.",
            )
        )
    schema_version = _schema_version(mapping)
    if not schema_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_SCHEMA_VERSION_MISSING,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Write schema version is missing.",
                suggested_fix="Use a mapping compatible with the write-plan schema.",
            )
        )
    provenance = _mapping_provenance(mapping)
    if not provenance:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_PROVENANCE_INCOMPLETE,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "ResultDataset draft mapping provenance is incomplete.",
                suggested_fix="Preserve run metadata and export manifest evidence.",
            )
        )
    if _mapping_diagnostics(mapping):
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_DIAGNOSTICS_UNREVIEWED,
                CalculiXResultDatasetWriteSeverity.WARNING,
                "Draft mapping diagnostics must be reviewed or carried forward.",
                blocks_write=False,
            )
        )
    if _mapping_limitations(mapping) and not acknowledge_limitations:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_LIMITATIONS_NOT_ACKNOWLEDGED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Draft mapping limitations require explicit acknowledgement.",
                suggested_fix="Pass acknowledge_limitations=True after review.",
            )
        )


def _status_from_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXResultDatasetWriteDiagnostic],
    *,
    output_path: str | Path | None,
) -> FEASpecCalculiXResultDatasetWriteStatus:
    if output_path is not None and any(item.blocks_write for item in diagnostics):
        return FEASpecCalculiXResultDatasetWriteStatus.UNSUPPORTED
    if any(item.blocks_write for item in diagnostics):
        return FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    if any(
        item.severity is CalculiXResultDatasetWriteSeverity.WARNING
        for item in diagnostics
    ):
        return FEASpecCalculiXResultDatasetWriteStatus.PLANNED_WITH_WARNINGS
    return FEASpecCalculiXResultDatasetWriteStatus.PLANNED


def _mapping_artifacts(mapping: object) -> tuple[object, ...]:
    value = _mapping_value(mapping, "artifacts", ())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _mapping_diagnostics(mapping: object) -> tuple[object, ...]:
    value = _mapping_value(mapping, "diagnostics", ())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _mapping_limitations(mapping: object) -> tuple[object, ...]:
    value = _mapping_value(mapping, "limitations", ())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _mapping_provenance(mapping: object) -> object:
    value = _mapping_value(mapping, "provenance", None)
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value if any(bool(item) for item in value.values()) else None
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
        if isinstance(payload, Mapping) and any(bool(item) for item in payload.values()):
            return value
        return None
    return value


def _mapping_status_text(mapping: object) -> str:
    status = _mapping_value(mapping, "status", "")
    return str(getattr(status, "value", status) or "")


def _schema_version(mapping: object) -> str:
    value = _mapping_value(mapping, "schema_version", WRITE_SCHEMA_VERSION)
    return str(value or "")


def _mapping_value(mapping: object, key: str, default: object) -> object:
    if isinstance(mapping, Mapping):
        return mapping.get(key, default)
    return getattr(mapping, key, default)


def _artifact_value(artifact: object, key: str) -> str:
    if isinstance(artifact, Mapping):
        return str(artifact.get(key, "") or "")
    return str(getattr(artifact, key, "") or "")


def _has_traversal(path: Path) -> bool:
    return any(part == ".." for part in path.parts)


def _is_unsafe_path(path: Path) -> bool:
    normalized_parts = {part.lower() for part in path.parts}
    return ".git" in normalized_parts or ".codex" in normalized_parts


def _is_nonempty_directory(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
    except StopIteration:
        return False
    except OSError:
        return True
    return True


def _file_role(filename: str) -> str:
    return {
        "result_dataset.json": "result_dataset",
        "result_dataset_manifest.json": "manifest",
        "diagnostics.json": "diagnostics",
        "provenance.json": "provenance",
        "README_REVIEW_FIRST.txt": "readme",
    }[filename]


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _diag(
    code: CalculiXResultDatasetWriteDiagnosticCode,
    severity: CalculiXResultDatasetWriteSeverity,
    message: str,
    *,
    path: str = "",
    suggested_fix: str = "",
    blocks_write: bool | None = None,
) -> FEASpecCalculiXResultDatasetWriteDiagnostic:
    return FEASpecCalculiXResultDatasetWriteDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        suggested_fix=suggested_fix,
        blocks_write=blocks_write,
    )


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXResultDatasetWriteDiagnostic],
) -> list[FEASpecCalculiXResultDatasetWriteDiagnostic]:
    seen: set[tuple[CalculiXResultDatasetWriteDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXResultDatasetWriteDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.path, diagnostic.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(diagnostic)
    return unique
