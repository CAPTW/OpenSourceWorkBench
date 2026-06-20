"""Library-only ResultDataset writer for FEASpec CalculiX result imports.

The writer consumes an already reviewed ResultDataset write plan and schema
payload. It writes only the standard ResultDataset JSON/README files requested
by the caller, and it does not execute solvers, copy original result artifacts,
mutate project records, or add command-line/GUI persistence paths.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any

from .calculix_result_dataset_schema import (
    validate_calculix_result_dataset_schema_payload,
)
from .calculix_result_dataset_write_diagnostics import (
    CalculiXResultDatasetWriteDiagnosticCode,
    CalculiXResultDatasetWriteSeverity,
    FEASpecCalculiXResultDatasetWriteDiagnostic,
)
from .calculix_result_dataset_write_plan import (
    STANDARD_OUTPUT_FILES,
    validate_calculix_result_dataset_write_plan,
)

__all__ = [
    "FEASpecCalculiXResultDatasetPreparedWritePayloads",
    "FEASpecCalculiXResultDatasetWrittenFile",
    "FEASpecCalculiXResultDatasetWriteResult",
    "FEASpecCalculiXResultDatasetWriteResultStatus",
    "explain_calculix_result_dataset_write_result",
    "prepare_calculix_result_dataset_write_payloads",
    "write_calculix_result_dataset",
]


class FEASpecCalculiXResultDatasetWriteResultStatus(str, Enum):
    """Status for explicit library-only ResultDataset writes."""

    WRITTEN = "written"
    WRITTEN_WITH_WARNINGS = "written-with-warnings"
    BLOCKED = "blocked"
    FAILED = "failed"
    PARTIAL_CLEANUP_FAILED = "partial-cleanup-failed"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetPreparedWritePayloads:
    """Deterministic text payloads prepared for the standard file layout."""

    target_dir: str
    payloads: tuple[Mapping[str, str], ...]
    diagnostics: tuple[FEASpecCalculiXResultDatasetWriteDiagnostic, ...] = ()
    has_blockers: bool = False
    writes_files: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "target_dir": self.target_dir,
            "payloads": [dict(item) for item in self.payloads],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "has_blockers": self.has_blockers,
            "writes_files": self.writes_files,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetWrittenFile:
    """Metadata for one ResultDataset file written by this library writer."""

    path: str
    relative_path: str
    payload_kind: str
    size_bytes: int
    sha256: str

    @classmethod
    def from_path(
        cls,
        path: Path,
        *,
        relative_path: str,
        payload_kind: str,
    ) -> FEASpecCalculiXResultDatasetWrittenFile:
        data = path.read_bytes()
        return cls(
            path=str(path),
            relative_path=relative_path,
            payload_kind=payload_kind,
            size_bytes=len(data),
            sha256=sha256(data).hexdigest(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "relative_path": self.relative_path,
            "payload_kind": self.payload_kind,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetWriteResult:
    """Result of an explicit library-only ResultDataset write request."""

    status: FEASpecCalculiXResultDatasetWriteResultStatus
    target_dir: str
    written_files: tuple[FEASpecCalculiXResultDatasetWrittenFile, ...] = ()
    diagnostics: tuple[FEASpecCalculiXResultDatasetWriteDiagnostic, ...] = ()
    prepared_payloads: FEASpecCalculiXResultDatasetPreparedWritePayloads | None = None
    solver_execution_performed: bool = False
    artifact_copy_performed: bool = False
    cli_write_command_added: bool = False
    gui_write_command_added: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED

    @property
    def is_failed(self) -> bool:
        return self.status in {
            FEASpecCalculiXResultDatasetWriteResultStatus.FAILED,
            FEASpecCalculiXResultDatasetWriteResultStatus.PARTIAL_CLEANUP_FAILED,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "target_dir": self.target_dir,
            "written_files": [item.to_dict() for item in self.written_files],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "prepared_payloads": (
                self.prepared_payloads.to_dict() if self.prepared_payloads else None
            ),
            "solver_execution_performed": self.solver_execution_performed,
            "artifact_copy_performed": self.artifact_copy_performed,
            "cli_write_command_added": self.cli_write_command_added,
            "gui_write_command_added": self.gui_write_command_added,
        }


def prepare_calculix_result_dataset_write_payloads(
    write_plan: object,
    schema_payload: object,
) -> FEASpecCalculiXResultDatasetPreparedWritePayloads:
    """Prepare deterministic standard-layout payload text without writing files."""

    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic] = []
    target_dir = _target_dir(write_plan)
    if not target_dir:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_PATH_REQUIRED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "An explicit output directory is required before writing.",
            )
        )

    plan_validation = validate_calculix_result_dataset_write_plan(write_plan)
    diagnostics.extend(_write_diagnostics_from(plan_validation.diagnostics))
    if plan_validation.has_blockers:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_DRAFT_BLOCKED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "ResultDataset write plan has blockers.",
                path=target_dir,
                suggested_fix="Resolve write-plan blockers before writing.",
            )
        )

    schema_validation = validate_calculix_result_dataset_schema_payload(schema_payload)
    if schema_validation.has_blockers:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_FAILED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "ResultDataset schema payload has blockers.",
                path=target_dir,
                suggested_fix="Resolve schema payload blockers before writing.",
            )
        )

    payloads = _standard_payloads(schema_payload, diagnostics)
    diagnostics.extend(_planned_file_diagnostics(write_plan, payloads, target_dir))
    diagnostics_tuple = tuple(_dedupe_diagnostics(diagnostics))
    return FEASpecCalculiXResultDatasetPreparedWritePayloads(
        target_dir=target_dir,
        payloads=payloads,
        diagnostics=diagnostics_tuple,
        has_blockers=any(item.blocks_write for item in diagnostics_tuple),
    )


def write_calculix_result_dataset(
    write_plan: object,
    schema_payload: object,
    *,
    overwrite: bool = False,
) -> FEASpecCalculiXResultDatasetWriteResult:
    """Write the standard ResultDataset layout for an explicit reviewed request."""

    prepared = prepare_calculix_result_dataset_write_payloads(
        write_plan,
        schema_payload,
    )
    diagnostics = list(prepared.diagnostics)
    target_dir = Path(prepared.target_dir) if prepared.target_dir else Path()

    if prepared.has_blockers:
        return _result(
            FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED,
            prepared=prepared,
            diagnostics=diagnostics,
        )

    overwrite_allowed = bool(overwrite or _target_overwrite_requested(write_plan))
    diagnostics.extend(
        _prepare_target_directory(
            target_dir,
            write_plan=write_plan,
        )
    )
    if not any(item.blocks_write for item in diagnostics):
        diagnostics.extend(
            _target_collision_diagnostics(
                target_dir,
                overwrite_allowed=overwrite_allowed,
            )
        )
    if any(item.blocks_write for item in diagnostics):
        return _result(
            FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED,
            prepared=prepared,
            diagnostics=diagnostics,
        )

    written_files: list[FEASpecCalculiXResultDatasetWrittenFile] = []
    temp_paths: list[Path] = []
    for payload in prepared.payloads:
        relative_path = payload["relative_path"]
        payload_kind = payload["payload_kind"]
        text = payload["content"]
        target = target_dir / relative_path
        temp_path = _temp_path(target)
        temp_paths.append(temp_path)
        try:
            _write_text_to_temp(temp_path, text)
        except OSError as exc:
            return _write_failure_result(
                prepared=prepared,
                diagnostics=diagnostics,
                written_files=tuple(written_files),
                temp_paths=temp_paths,
                code=CalculiXResultDatasetWriteDiagnosticCode.FDW_TEMP_WRITE_FAILED,
                path=temp_path,
                error=exc,
            )
        try:
            _replace_temp_file(temp_path, target)
        except OSError as exc:
            return _write_failure_result(
                prepared=prepared,
                diagnostics=diagnostics,
                written_files=tuple(written_files),
                temp_paths=temp_paths,
                code=CalculiXResultDatasetWriteDiagnosticCode.FDW_TARGET_REPLACE_FAILED,
                path=target,
                error=exc,
            )
        temp_paths.remove(temp_path)
        written_files.append(
            FEASpecCalculiXResultDatasetWrittenFile.from_path(
                target,
                relative_path=relative_path,
                payload_kind=payload_kind,
            )
        )

    checksum_diagnostic = _verify_written_files(written_files)
    if checksum_diagnostic is not None:
        diagnostics.append(checksum_diagnostic)
        return _result(
            FEASpecCalculiXResultDatasetWriteResultStatus.FAILED,
            prepared=prepared,
            diagnostics=diagnostics,
            written_files=tuple(written_files),
        )

    diagnostics.append(
        _diag(
            CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_COMPLETED,
            CalculiXResultDatasetWriteSeverity.INFO,
            "ResultDataset standard files were written by the library writer.",
            path=str(target_dir),
            blocks_write=False,
        )
    )
    status = (
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN_WITH_WARNINGS
        if any(
            item.severity is CalculiXResultDatasetWriteSeverity.WARNING
            for item in diagnostics
        )
        else FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN
    )
    return _result(
        status,
        prepared=prepared,
        diagnostics=diagnostics,
        written_files=tuple(written_files),
    )


def explain_calculix_result_dataset_write_result(
    result: FEASpecCalculiXResultDatasetWriteResult,
) -> list[str]:
    """Return reviewer-readable ResultDataset write status and diagnostics."""

    lines = [
        f"ResultDataset writer status: {result.status.value}.",
        f"Target directory: {result.target_dir}.",
        f"Files written: {len(result.written_files)}.",
        f"Artifact copy performed: {str(result.artifact_copy_performed).lower()}.",
        (
            "Solver execution performed: "
            f"{str(result.solver_execution_performed).lower()}."
        ),
        f"CLI write command added: {str(result.cli_write_command_added).lower()}.",
        f"GUI write command added: {str(result.gui_write_command_added).lower()}.",
    ]
    for written_file in result.written_files:
        lines.append(
            f"- {written_file.relative_path} ({written_file.payload_kind}, "
            f"{written_file.size_bytes} bytes, sha256={written_file.sha256})"
        )
    for diagnostic in result.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _standard_payloads(
    schema_payload: object,
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic],
) -> tuple[Mapping[str, str], ...]:
    try:
        payload_by_name: dict[str, tuple[str, str]] = {
            "result_dataset.json": (
                "result_dataset",
                _json_text(_object_mapping(schema_payload.dataset)),
            ),
            "result_dataset_manifest.json": (
                "manifest",
                _json_text(_to_mapping(schema_payload.manifest_payload)),
            ),
            "diagnostics.json": (
                "diagnostics",
                _json_text(_to_mapping(schema_payload.diagnostics_payload)),
            ),
            "provenance.json": (
                "provenance",
                _json_text(_to_mapping(schema_payload.provenance_payload)),
            ),
            "README_REVIEW_FIRST.txt": (
                "readme",
                _readme_text(schema_payload.readme_payload),
            ),
        }
    except (AttributeError, TypeError, ValueError) as exc:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_FAILED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                f"ResultDataset schema payload cannot be rendered: {exc}",
            )
        )
        return ()
    return tuple(
        {
            "relative_path": name,
            "payload_kind": payload_by_name[name][0],
            "content": payload_by_name[name][1],
        }
        for name in STANDARD_OUTPUT_FILES
    )


def _planned_file_diagnostics(
    write_plan: object,
    payloads: Sequence[Mapping[str, str]],
    target_dir: str,
) -> list[FEASpecCalculiXResultDatasetWriteDiagnostic]:
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic] = []
    planned_names = {
        str(item.get("relative_path", ""))
        for item in _planned_file_mappings(write_plan)
    }
    payload_names = {item["relative_path"] for item in payloads}
    standard_names = set(STANDARD_OUTPUT_FILES)
    if planned_names != standard_names or payload_names != standard_names:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_FAILED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Write plan and schema payload must cover exactly the standard files.",
                path=target_dir,
                suggested_fix="Rebuild the write plan and schema payload.",
            )
        )
    copy_requested = bool(getattr(write_plan, "copy_artifacts_requested", False))
    if copy_requested:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_ARTIFACT_COPY_FORBIDDEN,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "This writer does not copy original solver artifacts.",
                path=target_dir,
                suggested_fix="Use artifact references only.",
            )
        )
    return diagnostics


def _prepare_target_directory(
    target_dir: Path,
    *,
    write_plan: object,
) -> list[FEASpecCalculiXResultDatasetWriteDiagnostic]:
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic] = []
    if target_dir.exists() and not target_dir.is_dir():
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_DIRECTORY_REQUIRED,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "ResultDataset output target must be a directory.",
                path=str(target_dir),
            )
        )
        return diagnostics
    if target_dir.exists():
        return diagnostics
    parent = target_dir.parent
    create_parent_allowed = bool(
        getattr(getattr(write_plan, "target", None), "create_dir_requested", False)
    )
    if not parent.exists() and not create_parent_allowed:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_PARENT_MISSING,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output parent directory does not exist.",
                path=str(parent),
                suggested_fix="Create the parent or rebuild the plan with create_dir=True.",
            )
        )
        return diagnostics
    try:
        target_dir.mkdir(parents=create_parent_allowed, exist_ok=True)
    except OSError as exc:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_FAILED,
                CalculiXResultDatasetWriteSeverity.ERROR,
                f"Could not create ResultDataset output directory: {exc}",
                path=str(target_dir),
            )
        )
    return diagnostics


def _target_collision_diagnostics(
    target_dir: Path,
    *,
    overwrite_allowed: bool,
) -> list[FEASpecCalculiXResultDatasetWriteDiagnostic]:
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic] = []
    allowed_names = set(STANDARD_OUTPUT_FILES)
    entries = list(target_dir.iterdir()) if target_dir.exists() else []
    unplanned = sorted(item.name for item in entries if item.name not in allowed_names)
    if unplanned:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_UNPLANNED_FILE_COLLISION,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "Output directory contains files outside the standard ResultDataset layout.",
                path=str(target_dir),
                suggested_fix="Choose an empty directory or remove unrelated files manually.",
            )
        )
    standard_existing = [
        target_dir / name
        for name in STANDARD_OUTPUT_FILES
        if (target_dir / name).exists()
    ]
    standard_dirs = [path for path in standard_existing if path.is_dir()]
    if standard_dirs:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_EXISTS,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "A standard ResultDataset target path exists as a directory.",
                path=", ".join(str(path) for path in standard_dirs),
            )
        )
    elif standard_existing and not overwrite_allowed:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_OUTPUT_EXISTS,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
                "One or more ResultDataset output files already exist.",
                path=", ".join(str(path) for path in standard_existing),
                suggested_fix="Pass overwrite=True after review or choose a new output directory.",
            )
        )
    return diagnostics


def _result(
    status: FEASpecCalculiXResultDatasetWriteResultStatus,
    *,
    prepared: FEASpecCalculiXResultDatasetPreparedWritePayloads,
    diagnostics: Sequence[FEASpecCalculiXResultDatasetWriteDiagnostic],
    written_files: tuple[FEASpecCalculiXResultDatasetWrittenFile, ...] = (),
) -> FEASpecCalculiXResultDatasetWriteResult:
    return FEASpecCalculiXResultDatasetWriteResult(
        status=status,
        target_dir=prepared.target_dir,
        written_files=written_files,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        prepared_payloads=prepared,
    )


def _write_failure_result(
    *,
    prepared: FEASpecCalculiXResultDatasetPreparedWritePayloads,
    diagnostics: list[FEASpecCalculiXResultDatasetWriteDiagnostic],
    written_files: tuple[FEASpecCalculiXResultDatasetWrittenFile, ...],
    temp_paths: Sequence[Path],
    code: CalculiXResultDatasetWriteDiagnosticCode,
    path: Path,
    error: OSError,
) -> FEASpecCalculiXResultDatasetWriteResult:
    diagnostics.append(
        _diag(
            code,
            CalculiXResultDatasetWriteSeverity.ERROR,
            f"ResultDataset write failed: {error}",
            path=str(path),
            suggested_fix="Inspect permissions and retry the explicit write.",
        )
    )
    cleanup_ok = _cleanup_temp_paths(temp_paths)
    status = (
        FEASpecCalculiXResultDatasetWriteResultStatus.FAILED
        if cleanup_ok
        else FEASpecCalculiXResultDatasetWriteResultStatus.PARTIAL_CLEANUP_FAILED
    )
    if not cleanup_ok:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITE_FAILED,
                CalculiXResultDatasetWriteSeverity.ERROR,
                "One or more temporary ResultDataset files could not be removed.",
                path=prepared.target_dir,
            )
        )
    return _result(
        status,
        prepared=prepared,
        diagnostics=diagnostics,
        written_files=written_files,
    )


def _verify_written_files(
    written_files: Sequence[FEASpecCalculiXResultDatasetWrittenFile],
) -> FEASpecCalculiXResultDatasetWriteDiagnostic | None:
    for item in written_files:
        path = Path(item.path)
        try:
            current = FEASpecCalculiXResultDatasetWrittenFile.from_path(
                path,
                relative_path=item.relative_path,
                payload_kind=item.payload_kind,
            )
        except OSError as exc:
            return _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITTEN_FILE_HASH_FAILED,
                CalculiXResultDatasetWriteSeverity.ERROR,
                f"Written ResultDataset file could not be verified: {exc}",
                path=str(path),
            )
        if current.sha256 != item.sha256 or current.size_bytes != item.size_bytes:
            return _diag(
                CalculiXResultDatasetWriteDiagnosticCode.FDW_WRITTEN_FILE_HASH_FAILED,
                CalculiXResultDatasetWriteSeverity.ERROR,
                "Written ResultDataset file changed during verification.",
                path=str(path),
            )
    return None


def _target_dir(write_plan: object) -> str:
    target = getattr(write_plan, "target", None)
    return str(getattr(target, "output_dir", "") or "")


def _target_overwrite_requested(write_plan: object) -> bool:
    target = getattr(write_plan, "target", None)
    return bool(getattr(target, "overwrite_requested", False))


def _planned_file_mappings(write_plan: object) -> tuple[Mapping[str, Any], ...]:
    planned_files = getattr(write_plan, "planned_files", ())
    if not isinstance(planned_files, Sequence) or isinstance(planned_files, (str, bytes)):
        return ()
    records: list[Mapping[str, Any]] = []
    for item in planned_files:
        records.append(_to_mapping(item))
    return tuple(records)


def _write_diagnostics_from(
    diagnostics: object,
) -> tuple[FEASpecCalculiXResultDatasetWriteDiagnostic, ...]:
    if not isinstance(diagnostics, Sequence) or isinstance(diagnostics, (str, bytes)):
        return ()
    return tuple(
        item
        for item in diagnostics
        if isinstance(item, FEASpecCalculiXResultDatasetWriteDiagnostic)
        and (
            item.blocks_write
            or item.severity is not CalculiXResultDatasetWriteSeverity.INFO
        )
    )


def _object_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _to_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _json_text(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _readme_text(readme_payload: object) -> str:
    content = str(getattr(readme_payload, "content", "") or "")
    if not content.endswith("\n"):
        content += "\n"
    return content


def _temp_path(target: Path) -> Path:
    return target.with_name(f".osw-{target.name}.{os.getpid()}.tmp")


def _write_text_to_temp(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def _replace_temp_file(temp_path: Path, target_path: Path) -> None:
    os.replace(temp_path, target_path)


def _cleanup_temp_paths(paths: Sequence[Path]) -> bool:
    ok = True
    for path in paths:
        if not path.exists():
            continue
        try:
            path.unlink()
        except OSError:
            ok = False
    return ok


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
