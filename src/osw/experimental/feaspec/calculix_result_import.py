"""Safe FEASpec CalculiX result import planning.

This module inspects already-existing CalculiX result directories. It does not
start solvers, parse numerical result contents, write ResultDataset files, or
mutate ProjectSchema records.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .calculix_result_dat_parser import parse_calculix_dat_minimal
from .calculix_result_dat_section_scanner import scan_calculix_dat_sections
from .calculix_result_dataset_draft_mapping import (
    build_calculix_result_dataset_draft_mapping,
)
from .calculix_result_diagnostics import (
    CalculiXResultImportDiagnosticCode,
    CalculiXResultImportSeverity,
    FEASpecCalculiXResultImportDiagnostic,
)
from .calculix_result_frd_block_scanner import scan_calculix_frd_blocks
from .calculix_result_metadata_scanner import scan_calculix_result_file_metadata
from .calculix_result_status_scanner import scan_calculix_status_file

RUN_METADATA_FILENAME = "run_metadata.json"
EXPORT_DIAGNOSTICS_SUFFIX = ".diagnostics.json"
EXPORT_MANIFEST_SUFFIX = ".manifest.json"
STDOUT_FILENAME = "stdout.txt"
STDERR_FILENAME = "stderr.txt"
README_FILENAME = "README_RUN_FIRST.txt"

__all__ = [
    "CalculiXResultArtifact",
    "CalculiXResultArtifactKind",
    "FEASpecCalculiXResultDatasetDraft",
    "FEASpecCalculiXResultDirectoryInspection",
    "FEASpecCalculiXResultImportPlan",
    "FEASpecCalculiXResultImportStatus",
    "FEASpecCalculiXResultProvenance",
    "build_calculix_result_dataset_draft",
    "explain_calculix_result_import_plan",
    "inspect_calculix_result_directory",
    "plan_calculix_result_import",
]


class CalculiXResultArtifactKind(str, Enum):
    """Artifact kinds recognized by the FEASpec CalculiX result import model."""

    INP = "inp"
    EXPORT_MANIFEST = "export_manifest"
    EXPORT_DIAGNOSTICS = "export_diagnostics"
    README = "readme"
    RUN_METADATA = "run_metadata"
    STDOUT = "stdout"
    STDERR = "stderr"
    DAT = "dat"
    FRD = "frd"
    STA = "sta"
    CVG = "cvg"
    OTHER = "other"


class FEASpecCalculiXResultImportStatus(str, Enum):
    """Status for a safe FEASpec CalculiX result import plan."""

    BLOCKED = "blocked"
    IMPORT_READY = "import-ready"
    IMPORT_READY_WITH_WARNINGS = "import-ready-with-warnings"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    PARSE_NOT_IMPLEMENTED = "parse-not-implemented"


@dataclass(frozen=True, slots=True)
class CalculiXResultArtifact:
    """A file artifact discovered in a CalculiX result directory."""

    kind: CalculiXResultArtifactKind
    path: Path
    filename: str
    suffix: str
    size_bytes: int
    sha256: str
    role: str = ""
    source: str = "directory"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(
        cls,
        path: Path,
        *,
        kind: CalculiXResultArtifactKind,
        role: str = "",
        source: str = "directory",
        metadata: Mapping[str, Any] | None = None,
    ) -> CalculiXResultArtifact:
        metadata_payload = dict(metadata or {})
        parser_payload = metadata_payload.get("result_parser")
        if isinstance(parser_payload, Mapping):
            size_bytes = parser_payload.get("byte_size")
            sha256 = parser_payload.get("sha256")
        else:
            size_bytes = metadata_payload.get("byte_size")
            sha256 = metadata_payload.get("sha256")

        if isinstance(size_bytes, int) and isinstance(sha256, str):
            resolved_size = size_bytes
            resolved_sha256 = sha256
        else:
            resolved_size = path.stat().st_size
            resolved_sha256 = _sha256(path)
        return cls(
            kind=kind,
            path=path,
            filename=path.name,
            suffix=path.suffix.lower(),
            size_bytes=resolved_size,
            sha256=resolved_sha256,
            role=role or kind.value,
            source=source,
            metadata=metadata_payload,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "path": str(self.path),
            "filename": self.filename,
            "suffix": self.suffix,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "role": self.role,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDirectoryInspection:
    """Inspection record for an explicit CalculiX result directory."""

    result_dir: Path
    exists: bool
    is_directory: bool
    artifacts: tuple[CalculiXResultArtifact, ...] = ()
    run_metadata_path: Path | None = None
    export_manifest_path: Path | None = None
    export_diagnostics_path: Path | None = None
    run_metadata: Mapping[str, Any] | None = None
    export_manifest: Mapping[str, Any] | None = None
    export_diagnostics: Mapping[str, Any] | None = None
    diagnostics: tuple[FEASpecCalculiXResultImportDiagnostic, ...] = ()

    @property
    def primary_artifacts(self) -> tuple[CalculiXResultArtifact, ...]:
        return tuple(
            artifact
            for artifact in self.artifacts
            if artifact.kind
            in {
                CalculiXResultArtifactKind.DAT,
                CalculiXResultArtifactKind.FRD,
                CalculiXResultArtifactKind.STA,
                CalculiXResultArtifactKind.CVG,
            }
        )

    @property
    def has_blockers(self) -> bool:
        return _has_blockers(self.diagnostics)

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": str(self.result_dir),
            "exists": self.exists,
            "is_directory": self.is_directory,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "run_metadata_path": (
                str(self.run_metadata_path) if self.run_metadata_path else ""
            ),
            "export_manifest_path": (
                str(self.export_manifest_path) if self.export_manifest_path else ""
            ),
            "export_diagnostics_path": (
                str(self.export_diagnostics_path)
                if self.export_diagnostics_path
                else ""
            ),
            "run_metadata": dict(self.run_metadata or {}),
            "export_manifest": dict(self.export_manifest or {}),
            "export_diagnostics": dict(self.export_diagnostics or {}),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultProvenance:
    """Provenance collected from run metadata and export manifest files."""

    result_dir: Path
    run_metadata_path: Path | None = None
    export_manifest_path: Path | None = None
    source_feaspec_id: str = ""
    case_id: str = ""
    osw_version: str = ""
    release_tag: str = ""
    run_status: str = ""
    solver_execution_performed: bool = False
    exit_code: int | None = None
    timed_out: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": str(self.result_dir),
            "run_metadata_path": (
                str(self.run_metadata_path) if self.run_metadata_path else ""
            ),
            "export_manifest_path": (
                str(self.export_manifest_path) if self.export_manifest_path else ""
            ),
            "source_feaspec_id": self.source_feaspec_id,
            "case_id": self.case_id,
            "osw_version": self.osw_version,
            "release_tag": self.release_tag,
            "run_status": self.run_status,
            "solver_execution_performed": self.solver_execution_performed,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultImportPlan:
    """Result-import plan for already-existing CalculiX artifacts."""

    status: FEASpecCalculiXResultImportStatus
    result_dir: Path
    inspection: FEASpecCalculiXResultDirectoryInspection
    provenance: FEASpecCalculiXResultProvenance
    diagnostics: tuple[FEASpecCalculiXResultImportDiagnostic, ...] = ()
    limitations: tuple[str, ...] = ()
    parser_available: bool = False
    result_dataset_write_allowed: bool = False

    @property
    def artifacts(self) -> tuple[CalculiXResultArtifact, ...]:
        return self.inspection.artifacts

    @property
    def is_blocked(self) -> bool:
        return self.status is FEASpecCalculiXResultImportStatus.BLOCKED

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "result_dir": str(self.result_dir),
            "inspection": self.inspection.to_dict(),
            "provenance": self.provenance.to_dict(),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "limitations": list(self.limitations),
            "parser_available": self.parser_available,
            "result_dataset_write_allowed": self.result_dataset_write_allowed,
        }

    @property
    def primary_artifacts(self) -> tuple[CalculiXResultArtifact, ...]:
        return self.inspection.primary_artifacts


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetDraft:
    """Pure in-memory ResultDataset mapping draft for CalculiX artifacts."""

    dataset_id: str
    source: str
    solver: str
    analysis_type: str
    status: FEASpecCalculiXResultImportStatus
    scalar_summaries: Mapping[str, Any] = field(default_factory=dict)
    tables: tuple[Mapping[str, Any], ...] = ()
    artifacts: tuple[CalculiXResultArtifact, ...] = ()
    field_references: tuple[Mapping[str, Any], ...] = ()
    draft_mapping: Mapping[str, Any] = field(default_factory=dict)
    provenance: FEASpecCalculiXResultProvenance | None = None
    limitations: tuple[str, ...] = ()
    diagnostics: tuple[FEASpecCalculiXResultImportDiagnostic, ...] = ()
    writes_files: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "solver": self.solver,
            "analysis_type": self.analysis_type,
            "status": self.status.value,
            "scalar_summaries": dict(self.scalar_summaries),
            "tables": [dict(table) for table in self.tables],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "field_references": [dict(item) for item in self.field_references],
            "draft_mapping": dict(self.draft_mapping),
            "provenance": (
                self.provenance.to_dict() if self.provenance is not None else {}
            ),
            "limitations": list(self.limitations),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "writes_files": self.writes_files,
        }


def inspect_calculix_result_directory(
    result_dir: str | Path,
) -> FEASpecCalculiXResultDirectoryInspection:
    """Inspect a result directory without parsing numerical solver content."""

    root = Path(result_dir).expanduser()
    diagnostics: list[FEASpecCalculiXResultImportDiagnostic] = []

    if not root.exists():
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_RESULT_DIR_MISSING,
                CalculiXResultImportSeverity.BLOCKER,
                "Result directory does not exist.",
                path=str(root),
                suggested_fix="Pass an existing explicit CalculiX result directory.",
            )
        )
        return FEASpecCalculiXResultDirectoryInspection(
            result_dir=root,
            exists=False,
            is_directory=False,
            diagnostics=tuple(diagnostics),
        )
    if not root.is_dir():
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_RESULT_DIR_NOT_DIRECTORY,
                CalculiXResultImportSeverity.BLOCKER,
                "Result path exists but is not a directory.",
                path=str(root),
                suggested_fix="Pass a directory containing run metadata and artifacts.",
            )
        )
        return FEASpecCalculiXResultDirectoryInspection(
            result_dir=root,
            exists=True,
            is_directory=False,
            diagnostics=tuple(diagnostics),
        )
    if _path_is_forbidden(root):
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_FORBIDDEN_PATH,
                CalculiXResultImportSeverity.BLOCKER,
                "Result directory cannot be inside Git metadata.",
                path=str(root),
                suggested_fix="Use an explicit ignored artifacts or temporary directory.",
            )
        )

    artifacts = _classify_artifacts(root, diagnostics)
    run_metadata_path = _artifact_path(artifacts, CalculiXResultArtifactKind.RUN_METADATA)
    export_manifest_path = _artifact_path(
        artifacts, CalculiXResultArtifactKind.EXPORT_MANIFEST
    )
    export_diagnostics_path = _artifact_path(
        artifacts, CalculiXResultArtifactKind.EXPORT_DIAGNOSTICS
    )

    run_metadata = _load_json_mapping(run_metadata_path, diagnostics)
    export_manifest = _load_json_mapping(export_manifest_path, diagnostics)
    export_diagnostics = _load_json_mapping(export_diagnostics_path, diagnostics)

    if run_metadata_path is None:
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_RUN_METADATA_MISSING,
                CalculiXResultImportSeverity.WARNING,
                "run_metadata.json was not found.",
                path=str(root),
                suggested_fix="Import from a directory produced by the installed-only run gate.",
                blocks_import=False,
            )
        )
    if export_manifest_path is None:
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_EXPORT_MANIFEST_MISSING,
                CalculiXResultImportSeverity.WARNING,
                "No FEASpec CalculiX export manifest was found.",
                path=str(root),
                suggested_fix="Keep the no-run export manifest with runtime outputs.",
                blocks_import=False,
            )
        )
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_MANIFEST_MISSING,
                CalculiXResultImportSeverity.INFO,
                "Result import provenance manifest is incomplete.",
                path=str(root),
                suggested_fix="Preserve export manifest metadata for traceability.",
                blocks_import=False,
            )
        )

    _append_metadata_diagnostics(run_metadata, root, diagnostics)
    _append_primary_result_diagnostics(artifacts, root, diagnostics)

    return FEASpecCalculiXResultDirectoryInspection(
        result_dir=root,
        exists=True,
        is_directory=True,
        artifacts=tuple(artifacts),
        run_metadata_path=run_metadata_path,
        export_manifest_path=export_manifest_path,
        export_diagnostics_path=export_diagnostics_path,
        run_metadata=run_metadata,
        export_manifest=export_manifest,
        export_diagnostics=export_diagnostics,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def plan_calculix_result_import(
    result_dir: str | Path,
) -> FEASpecCalculiXResultImportPlan:
    """Build a safe import plan for existing CalculiX runtime artifacts."""

    inspection = inspect_calculix_result_directory(result_dir)
    diagnostics = tuple(_dedupe_diagnostics(inspection.diagnostics))
    provenance = _provenance_from_inspection(inspection)
    return FEASpecCalculiXResultImportPlan(
        status=_status_from_inspection(inspection, diagnostics),
        result_dir=inspection.result_dir,
        inspection=inspection,
        provenance=provenance,
        diagnostics=diagnostics,
        limitations=_limitations(),
        parser_available=_has_dat_minimal_parse(inspection.artifacts),
        result_dataset_write_allowed=False,
    )


def build_calculix_result_dataset_draft(
    plan: FEASpecCalculiXResultImportPlan,
) -> FEASpecCalculiXResultDatasetDraft:
    """Build a pure in-memory ResultDataset draft without writing files."""

    dataset_id = plan.provenance.case_id or plan.provenance.source_feaspec_id
    if not dataset_id:
        dataset_id = "feaspec-calculix-result-draft"
    draft_mapping = build_calculix_result_dataset_draft_mapping(plan)
    return FEASpecCalculiXResultDatasetDraft(
        dataset_id=dataset_id,
        source=str(plan.result_dir),
        solver="CalculiX",
        analysis_type="linear_static",
        status=plan.status,
        scalar_summaries=_result_scalar_summaries(plan),
        tables=_result_tables(plan.artifacts),
        artifacts=plan.artifacts,
        field_references=_field_references(plan.artifacts),
        draft_mapping=draft_mapping.to_dict(),
        provenance=plan.provenance,
        limitations=plan.limitations,
        diagnostics=plan.diagnostics,
        writes_files=False,
    )


def explain_calculix_result_import_plan(
    plan: FEASpecCalculiXResultImportPlan,
) -> list[str]:
    """Return reviewer-readable result import plan status and diagnostics."""

    lines = [
        f"FEASpec CalculiX result import status: {plan.status.value}.",
        "Result import model only: true.",
        "Broad numerical result parser implemented: false.",
        f"Minimal .dat parser available: {str(plan.parser_available).lower()}.",
        "ResultDataset write allowed: false.",
        "Solver execution performed by this import model: false.",
        f"Artifacts inspected: {len(plan.artifacts)}.",
    ]
    if plan.provenance.case_id:
        lines.append(f"Case ID: {plan.provenance.case_id}")
    if plan.provenance.source_feaspec_id:
        lines.append(f"Source FEASpec: {plan.provenance.source_feaspec_id}")
    status_artifacts = [
        artifact for artifact in plan.artifacts if "status_summary" in artifact.metadata
    ]
    if status_artifacts:
        lines.append(f"Status summaries scanned: {len(status_artifacts)}.")
    for diagnostic in plan.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _classify_artifacts(
    root: Path,
    diagnostics: list[FEASpecCalculiXResultImportDiagnostic],
) -> list[CalculiXResultArtifact]:
    artifacts: list[CalculiXResultArtifact] = []
    for path in sorted(item for item in root.iterdir() if item.is_file()):
        kind = _artifact_kind(path)
        parser_scan = scan_calculix_result_file_metadata(path)
        metadata_payload: dict[str, Any] = {"result_parser": parser_scan.to_dict()}
        if kind is CalculiXResultArtifactKind.DAT:
            dat_section_scan = scan_calculix_dat_sections(path, metadata=parser_scan)
            dat_minimal_parse = parse_calculix_dat_minimal(
                path,
                section_scan=dat_section_scan,
            )
            metadata_payload["dat_section_scan"] = dat_section_scan.to_dict()
            metadata_payload["dat_section_summary"] = dat_section_scan.summary.to_dict()
            metadata_payload["dat_minimal_parse"] = dat_minimal_parse.to_dict()
            metadata_payload["dat_minimal_parse_summary"] = (
                dat_minimal_parse.summary_dict()
            )
        if kind in {CalculiXResultArtifactKind.STA, CalculiXResultArtifactKind.CVG}:
            status_scan = scan_calculix_status_file(path, metadata=parser_scan)
            metadata_payload["status_scan"] = status_scan.to_dict()
            metadata_payload["status_summary"] = status_scan.summary.to_dict()
        if kind is CalculiXResultArtifactKind.FRD:
            frd_block_scan = scan_calculix_frd_blocks(path, metadata=parser_scan)
            metadata_payload["frd_block_scan"] = frd_block_scan.to_dict()
            metadata_payload["frd_block_summary"] = frd_block_scan.summary.to_dict()
        artifact = CalculiXResultArtifact.from_path(
            path,
            kind=kind,
            metadata=metadata_payload,
        )
        artifacts.append(artifact)
        if kind is CalculiXResultArtifactKind.OTHER:
            diagnostics.append(
                _diag(
                    CalculiXResultImportDiagnosticCode.FI_UNSUPPORTED_FILE,
                    CalculiXResultImportSeverity.WARNING,
                    "Unsupported file was left as an artifact reference.",
                    path=str(path),
                    suggested_fix="Keep only reviewed CalculiX runtime artifacts.",
                    blocks_import=False,
                )
            )
        if kind in {
            CalculiXResultArtifactKind.FRD,
            CalculiXResultArtifactKind.STA,
            CalculiXResultArtifactKind.CVG,
        }:
            diagnostics.append(
                _diag(
                    CalculiXResultImportDiagnosticCode.FI_PARSE_NOT_IMPLEMENTED,
                    CalculiXResultImportSeverity.WARNING,
                    (
                        f"{path.suffix.lower()} artifact was classified, but "
                        "numerical parsing is not implemented."
                    ),
                    path=str(path),
                    suggested_fix="Use a future parser gate for numerical fields.",
                    blocks_import=False,
                )
            )
    return artifacts


def _artifact_kind(path: Path) -> CalculiXResultArtifactKind:
    name = path.name
    suffix = path.suffix.lower()
    if name == RUN_METADATA_FILENAME:
        return CalculiXResultArtifactKind.RUN_METADATA
    if name == STDOUT_FILENAME:
        return CalculiXResultArtifactKind.STDOUT
    if name == STDERR_FILENAME:
        return CalculiXResultArtifactKind.STDERR
    if name == README_FILENAME:
        return CalculiXResultArtifactKind.README
    if name.endswith(EXPORT_MANIFEST_SUFFIX):
        return CalculiXResultArtifactKind.EXPORT_MANIFEST
    if name.endswith(EXPORT_DIAGNOSTICS_SUFFIX):
        return CalculiXResultArtifactKind.EXPORT_DIAGNOSTICS
    if suffix == ".inp":
        return CalculiXResultArtifactKind.INP
    if suffix == ".dat":
        return CalculiXResultArtifactKind.DAT
    if suffix == ".frd":
        return CalculiXResultArtifactKind.FRD
    if suffix == ".sta":
        return CalculiXResultArtifactKind.STA
    if suffix == ".cvg":
        return CalculiXResultArtifactKind.CVG
    return CalculiXResultArtifactKind.OTHER


def _append_metadata_diagnostics(
    run_metadata: Mapping[str, Any] | None,
    root: Path,
    diagnostics: list[FEASpecCalculiXResultImportDiagnostic],
) -> None:
    if run_metadata is None:
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_PROVENANCE_INCOMPLETE,
                CalculiXResultImportSeverity.WARNING,
                "Run metadata is unavailable, so provenance is incomplete.",
                path=str(root),
                suggested_fix="Preserve run_metadata.json with result artifacts.",
                blocks_import=False,
            )
        )
        return
    if run_metadata.get("solver_execution_performed") is False:
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_SOLVER_NOT_EXECUTED,
                CalculiXResultImportSeverity.WARNING,
                "Run metadata records solver_execution_performed=false.",
                path=str(root),
                suggested_fix="Import runtime outputs only after an explicit run gate.",
                blocks_import=False,
            )
        )
    if bool(run_metadata.get("timed_out", False)):
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_RUN_TIMED_OUT,
                CalculiXResultImportSeverity.WARNING,
                "Run metadata records a timeout.",
                path=str(root),
                suggested_fix="Inspect partial logs before interpreting artifacts.",
                blocks_import=False,
            )
        )
    exit_code = _optional_int(run_metadata.get("exit_code"))
    if exit_code is not None and exit_code != 0:
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_RUN_FAILED,
                CalculiXResultImportSeverity.WARNING,
                "Run metadata records a nonzero exit code.",
                path=str(root),
                suggested_fix="Inspect stdout.txt, stderr.txt, and partial artifacts.",
                blocks_import=False,
            )
        )


def _append_primary_result_diagnostics(
    artifacts: Sequence[CalculiXResultArtifact],
    root: Path,
    diagnostics: list[FEASpecCalculiXResultImportDiagnostic],
) -> None:
    if any(
        artifact.kind
        in {
            CalculiXResultArtifactKind.DAT,
            CalculiXResultArtifactKind.FRD,
            CalculiXResultArtifactKind.STA,
            CalculiXResultArtifactKind.CVG,
        }
        for artifact in artifacts
    ):
        return
    diagnostics.append(
        _diag(
            CalculiXResultImportDiagnosticCode.FI_NO_PRIMARY_RESULT,
            CalculiXResultImportSeverity.WARNING,
            "No .dat, .frd, .sta, or .cvg primary result artifact was found.",
            path=str(root),
            suggested_fix="Keep CalculiX result artifacts with run metadata.",
            blocks_import=False,
        )
    )


def _status_from_inspection(
    inspection: FEASpecCalculiXResultDirectoryInspection,
    diagnostics: Sequence[FEASpecCalculiXResultImportDiagnostic],
) -> FEASpecCalculiXResultImportStatus:
    if _has_blockers(diagnostics):
        return FEASpecCalculiXResultImportStatus.BLOCKED
    if not inspection.artifacts:
        return FEASpecCalculiXResultImportStatus.UNSUPPORTED
    if any(artifact.kind is CalculiXResultArtifactKind.OTHER for artifact in inspection.artifacts):
        if not inspection.primary_artifacts:
            return FEASpecCalculiXResultImportStatus.UNSUPPORTED
    if not inspection.primary_artifacts:
        return FEASpecCalculiXResultImportStatus.PARTIAL
    if _has_code(diagnostics, CalculiXResultImportDiagnosticCode.FI_RUN_FAILED) or _has_code(
        diagnostics, CalculiXResultImportDiagnosticCode.FI_RUN_TIMED_OUT
    ):
        return FEASpecCalculiXResultImportStatus.PARTIAL
    if _has_code(
        diagnostics,
        CalculiXResultImportDiagnosticCode.FI_RUN_METADATA_MISSING,
        CalculiXResultImportDiagnosticCode.FI_EXPORT_MANIFEST_MISSING,
        CalculiXResultImportDiagnosticCode.FI_SOLVER_NOT_EXECUTED,
    ):
        return FEASpecCalculiXResultImportStatus.PARTIAL
    if _has_code(diagnostics, CalculiXResultImportDiagnosticCode.FI_PARSE_NOT_IMPLEMENTED):
        return FEASpecCalculiXResultImportStatus.IMPORT_READY_WITH_WARNINGS
    return FEASpecCalculiXResultImportStatus.IMPORT_READY


def _provenance_from_inspection(
    inspection: FEASpecCalculiXResultDirectoryInspection,
) -> FEASpecCalculiXResultProvenance:
    run_metadata = inspection.run_metadata or {}
    export_manifest = inspection.export_manifest or {}
    return FEASpecCalculiXResultProvenance(
        result_dir=inspection.result_dir,
        run_metadata_path=inspection.run_metadata_path,
        export_manifest_path=inspection.export_manifest_path,
        source_feaspec_id=str(
            export_manifest.get("source_feaspec_id")
            or run_metadata.get("source_feaspec_id")
            or ""
        ),
        case_id=str(export_manifest.get("case_id") or run_metadata.get("case_id") or ""),
        osw_version=str(
            export_manifest.get("osw_version") or run_metadata.get("osw_version") or ""
        ),
        release_tag=str(
            export_manifest.get("release_tag") or run_metadata.get("release_tag") or ""
        ),
        run_status=str(run_metadata.get("status", "")),
        solver_execution_performed=bool(
            run_metadata.get("solver_execution_performed", False)
        ),
        exit_code=_optional_int(run_metadata.get("exit_code")),
        timed_out=bool(run_metadata.get("timed_out", False)),
    )


def _metadata_scalar_summaries(
    run_metadata: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if run_metadata is None:
        return {}
    for key in ("scalar_summaries", "result_scalars"):
        payload = run_metadata.get(key)
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _result_scalar_summaries(
    plan: FEASpecCalculiXResultImportPlan,
) -> Mapping[str, Any]:
    scalars = dict(_metadata_scalar_summaries(plan.inspection.run_metadata))
    candidates: list[Mapping[str, Any]] = []
    for artifact in plan.artifacts:
        payload = artifact.metadata.get("dat_minimal_parse")
        if not isinstance(payload, Mapping):
            continue
        scalar_candidates = payload.get("scalar_candidates", ())
        if isinstance(scalar_candidates, Sequence) and not isinstance(
            scalar_candidates,
            (str, bytes),
        ):
            candidates.extend(
                dict(item) for item in scalar_candidates if isinstance(item, Mapping)
            )
    if candidates:
        scalars["dat_minimal_candidates"] = candidates
    return scalars


def _result_tables(
    artifacts: Sequence[CalculiXResultArtifact],
) -> tuple[Mapping[str, Any], ...]:
    tables: list[Mapping[str, Any]] = []
    for artifact in artifacts:
        payload = artifact.metadata.get("dat_minimal_parse")
        if not isinstance(payload, Mapping):
            continue
        table_candidates = payload.get("table_candidates", ())
        if isinstance(table_candidates, Sequence) and not isinstance(
            table_candidates,
            (str, bytes),
        ):
            tables.extend(
                dict(item) for item in table_candidates if isinstance(item, Mapping)
            )
    return tuple(tables)


def _has_dat_minimal_parse(
    artifacts: Sequence[CalculiXResultArtifact],
) -> bool:
    return any("dat_minimal_parse_summary" in artifact.metadata for artifact in artifacts)


def _field_references(
    artifacts: Sequence[CalculiXResultArtifact],
) -> tuple[Mapping[str, Any], ...]:
    references: list[Mapping[str, Any]] = []
    for artifact in artifacts:
        if artifact.kind is CalculiXResultArtifactKind.FRD:
            payload = artifact.metadata.get("frd_block_scan")
            if isinstance(payload, Mapping):
                candidates = payload.get("reference_candidates", ())
                if isinstance(candidates, Sequence) and not isinstance(
                    candidates,
                    (str, bytes),
                ):
                    candidate_references = [
                        {
                            **dict(item),
                            "artifact": artifact.filename,
                            "format": "frd",
                            "status": "candidate-not-parsed",
                        }
                        for item in candidates
                        if isinstance(item, Mapping)
                    ]
                    if candidate_references:
                        references.extend(candidate_references)
                        continue
            references.append(
                {
                    "artifact": artifact.filename,
                    "format": "frd",
                    "status": "referenced-not-parsed",
                }
            )
    return tuple(references)


def _load_json_mapping(
    path: Path | None,
    diagnostics: list[FEASpecCalculiXResultImportDiagnostic],
) -> Mapping[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_PROVENANCE_INCOMPLETE,
                CalculiXResultImportSeverity.WARNING,
                f"JSON metadata could not be read: {exc}",
                path=str(path),
                suggested_fix="Regenerate or repair metadata JSON.",
                blocks_import=False,
            )
        )
        return None
    if not isinstance(payload, Mapping):
        diagnostics.append(
            _diag(
                CalculiXResultImportDiagnosticCode.FI_PROVENANCE_INCOMPLETE,
                CalculiXResultImportSeverity.WARNING,
                "JSON metadata must contain an object.",
                path=str(path),
                suggested_fix="Use object-shaped metadata JSON.",
                blocks_import=False,
            )
        )
        return None
    return payload


def _artifact_path(
    artifacts: Sequence[CalculiXResultArtifact],
    kind: CalculiXResultArtifactKind,
) -> Path | None:
    matches = [artifact.path for artifact in artifacts if artifact.kind is kind]
    return matches[0] if len(matches) == 1 else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _path_is_forbidden(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        resolved = path
    return ".git" in resolved.parts


def _has_blockers(
    diagnostics: Sequence[FEASpecCalculiXResultImportDiagnostic],
) -> bool:
    return any(diagnostic.blocks_import for diagnostic in diagnostics)


def _has_code(
    diagnostics: Sequence[FEASpecCalculiXResultImportDiagnostic],
    *codes: CalculiXResultImportDiagnosticCode,
) -> bool:
    return any(diagnostic.code in codes for diagnostic in diagnostics)


def _diag(
    code: CalculiXResultImportDiagnosticCode,
    severity: CalculiXResultImportSeverity,
    message: str,
    *,
    path: str = "",
    suggested_fix: str = "",
    blocks_import: bool | None = None,
) -> FEASpecCalculiXResultImportDiagnostic:
    return FEASpecCalculiXResultImportDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        suggested_fix=suggested_fix,
        blocks_import=blocks_import,
    )


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXResultImportDiagnostic],
) -> list[FEASpecCalculiXResultImportDiagnostic]:
    seen: set[tuple[CalculiXResultImportDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXResultImportDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.path, diagnostic.message)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique


def _limitations() -> tuple[str, ...]:
    return (
        "Result import model only; .dat parsing is bounded to explicit scalar/table candidates.",
        ".frd scanning is block metadata only; field values and mesh are not parsed.",
        "No free-form .dat parser, .frd numerical field parser, "
        ".sta numerical parser, or .cvg numerical parser is implemented.",
        "No ResultDataset file is written by this model.",
        "No solver execution, solver adapter call, runner call, or external command is performed.",
        "Issue #8 live CalculiX validation remains separate and open.",
        "External CalculiX solvers are optional and not bundled.",
        "No industrial certification, compliance, production CAE, or accuracy claim.",
    )
