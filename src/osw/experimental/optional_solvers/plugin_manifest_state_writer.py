"""Explicit local state writer for optional solver plugin manifest UX state.

This OSW-EXP-102 module is intentionally narrow: it serializes supplied
state-writer view-model records to deterministic JSON and writes only to a
caller-supplied target path after preflight and acknowledgement checks pass. It
does not choose default paths, create directories, reload state, mutate
ProjectSchema, integrate with GUI or CLI code, run discovery or validation, or
execute solvers.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .plugin_manifest_state_writer_viewmodel import (
    OptionalSolverPluginManifestStateWriterReadiness,
    OptionalSolverPluginManifestStateWriterViewModel,
)

STATE_WRITER_PAYLOAD_SCHEMA_VERSION = "osw-exp-102-state-writer-1"
STATE_WRITER_IMPLEMENTATION_VERSION = "osw-exp-102"

OSPMG_STATE_WRITER_WRITE_PLANNED = "OSPMG_STATE_WRITER_WRITE_PLANNED"
OSPMG_STATE_WRITER_WRITE_COMPLETED = "OSPMG_STATE_WRITER_WRITE_COMPLETED"
OSPMG_STATE_WRITER_WRITE_BLOCKED = "OSPMG_STATE_WRITER_WRITE_BLOCKED"
OSPMG_STATE_WRITER_WRITE_ERROR = "OSPMG_STATE_WRITER_WRITE_ERROR"
OSPMG_STATE_WRITER_TARGET_REQUIRED = "OSPMG_STATE_WRITER_TARGET_REQUIRED"
OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED = (
    "OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED"
)
OSPMG_STATE_WRITER_PARENT_MISSING = "OSPMG_STATE_WRITER_PARENT_MISSING"
OSPMG_STATE_WRITER_PARENT_NOT_DIRECTORY = (
    "OSPMG_STATE_WRITER_PARENT_NOT_DIRECTORY"
)
OSPMG_STATE_WRITER_TARGET_EXISTS = "OSPMG_STATE_WRITER_TARGET_EXISTS"
OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED = (
    "OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED"
)
OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED = (
    "OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED"
)
OSPMG_STATE_WRITER_SCHEMA_VERSION_MISMATCH = (
    "OSPMG_STATE_WRITER_SCHEMA_VERSION_MISMATCH"
)
OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY = (
    "OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY"
)
OSPMG_STATE_WRITER_PAYLOAD_SECRET_BLOCKED = (
    "OSPMG_STATE_WRITER_PAYLOAD_SECRET_BLOCKED"
)
OSPMG_STATE_WRITER_PAYLOAD_PATH_BLOCKED = (
    "OSPMG_STATE_WRITER_PAYLOAD_PATH_BLOCKED"
)
OSPMG_STATE_WRITER_SERIALIZATION_ERROR = (
    "OSPMG_STATE_WRITER_SERIALIZATION_ERROR"
)
OSPMG_STATE_WRITER_ATOMIC_REPLACE_ERROR = (
    "OSPMG_STATE_WRITER_ATOMIC_REPLACE_ERROR"
)

_SUPPORTED_VIEWMODEL_READYNESS = {
    OptionalSolverPluginManifestStateWriterReadiness.READY_FOR_FUTURE_WRITE.value,
}

_DRY_RUN_ALLOWED_READYNESS = _SUPPORTED_VIEWMODEL_READYNESS | {
    OptionalSolverPluginManifestStateWriterReadiness.DRY_RUN_ONLY.value,
}

_UNAVAILABLE_READYNESS = {
    OptionalSolverPluginManifestStateWriterReadiness.UNAVAILABLE_NO_STATE.value,
    OptionalSolverPluginManifestStateWriterReadiness.UNAVAILABLE_NO_EXPLICIT_REQUEST.value,
}

_SECRET_MARKERS = (
    "token=",
    "secret=",
    "password=",
    "apikey",
    "api_key",
    "bearer ",
    "github_pat",
    "ghp_",
)

_SAFETY_BOUNDARY_NOTES = (
    "Persisted state is local UX state only.",
    "Persisted state is not validation evidence.",
    "Persisted state is not trust restoration.",
    "Persisted state is not automatic activation.",
    "Persisted state is not dependency installation.",
    "Persisted state is not solver execution.",
    "Persisted state is not issue closure.",
    "Persisted state is not release mutation.",
    "A trust label is not certification.",
    "ProjectSchema mutation remains out of scope.",
    "Reload, export, report, clipboard, and GUI/CLI integrations remain future-gated.",
    "Issues #6 through #11 remain live optional validation issues.",
)


class OptionalSolverPluginManifestStateWriterStatus(str, Enum):
    """State writer result vocabulary."""

    DRY_RUN_PLANNED = "dry_run_planned"
    WRITTEN = "written"
    BLOCKED = "blocked"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterDiagnostic:
    """Diagnostic returned by the explicit state writer."""

    severity: str
    code: str
    message: str
    blocker: bool = False
    target_reference_display: str = ""
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "blocker": self.blocker,
            "target_reference_display": self.target_reference_display,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterRequest:
    """Explicit caller request for planning or writing state."""

    target_path: str | Path | None
    allow_replace: bool = False
    dry_run: bool = True
    require_existing_parent: bool = True
    expected_schema_version: str | None = None
    operation_label: str = ""
    caller_acknowledged_write: bool = False
    encoding: str = "utf-8"
    newline: str = "\n"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterResult:
    """Explicit writer result with side-effect and non-action flags."""

    status: OptionalSolverPluginManifestStateWriterStatus
    target_reference_display: str
    target_reference_redacted: bool
    bytes_planned: int
    bytes_written: int
    sha256: str
    payload_key_count: int
    payload_section_count: int
    diagnostics: tuple[OptionalSolverPluginManifestStateWriterDiagnostic, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    write_performed: bool = False
    file_write_performed: bool = False
    runtime_state_file_created: bool = False
    temp_file_used: bool = False
    atomic_replace_performed: bool = False
    settings_file_created: bool = False
    schema_file_created: bool = False
    export_file_created: bool = False
    report_file_created: bool = False
    reloadable_bundle_created: bool = False
    project_schema_mutation_performed: bool = False
    gui_behavior_added: bool = False
    cli_behavior_added: bool = False
    reload_behavior_added: bool = False
    export_behavior_added: bool = False
    clipboard_performed: bool = False
    report_attachment_performed: bool = False
    open_output_folder_performed: bool = False
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    solver_execution_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    tag_mutation_performed: bool = False
    asset_mutation_performed: bool = False
    version_bump_performed: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    issue_closure_claimed: bool = False
    certification_claimed: bool = False

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "target_reference_display": self.target_reference_display,
            "target_reference_redacted": self.target_reference_redacted,
            "bytes_planned": self.bytes_planned,
            "bytes_written": self.bytes_written,
            "sha256": self.sha256,
            "payload_key_count": self.payload_key_count,
            "payload_section_count": self.payload_section_count,
            "diagnostics": [row.to_mapping() for row in self.diagnostics],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "write_performed": self.write_performed,
            "file_write_performed": self.file_write_performed,
            "runtime_state_file_created": self.runtime_state_file_created,
            "temp_file_used": self.temp_file_used,
            "atomic_replace_performed": self.atomic_replace_performed,
            "settings_file_created": self.settings_file_created,
            "schema_file_created": self.schema_file_created,
            "export_file_created": self.export_file_created,
            "report_file_created": self.report_file_created,
            "reloadable_bundle_created": self.reloadable_bundle_created,
            "project_schema_mutation_performed": (
                self.project_schema_mutation_performed
            ),
            "gui_behavior_added": self.gui_behavior_added,
            "cli_behavior_added": self.cli_behavior_added,
            "reload_behavior_added": self.reload_behavior_added,
            "export_behavior_added": self.export_behavior_added,
            "clipboard_performed": self.clipboard_performed,
            "report_attachment_performed": self.report_attachment_performed,
            "open_output_folder_performed": self.open_output_folder_performed,
            "discovery_execution_performed": self.discovery_execution_performed,
            "validation_execution_performed": self.validation_execution_performed,
            "solver_execution_performed": self.solver_execution_performed,
            "issue_mutation_performed": self.issue_mutation_performed,
            "release_mutation_performed": self.release_mutation_performed,
            "tag_mutation_performed": self.tag_mutation_performed,
            "asset_mutation_performed": self.asset_mutation_performed,
            "version_bump_performed": self.version_bump_performed,
            "validation_success_claimed": self.validation_success_claimed,
            "validation_failure_claimed": self.validation_failure_claimed,
            "issue_closure_claimed": self.issue_closure_claimed,
            "certification_claimed": self.certification_claimed,
        }


class OptionalSolverPluginManifestStateWriter:
    """Explicit deterministic local-file state writer."""

    payload_schema_version = STATE_WRITER_PAYLOAD_SCHEMA_VERSION
    writer_version = STATE_WRITER_IMPLEMENTATION_VERSION

    def build_payload(self, view_model: object) -> dict[str, object]:
        """Build a deterministic JSON-compatible payload from supplied state."""

        supplied = _mapping_from_supplied_state(view_model)
        if supplied.get("payload_kind") == "optional_solver_plugin_manifest_state_writer_state":
            return _normalize_payload_mapping(supplied)
        summary = _mapping(supplied.get("summary", {}))
        summary_payload = dict(summary)
        summary_payload.setdefault("not_validation_evidence", True)
        summary_payload.setdefault("not_trust_restoration", True)
        summary_payload.setdefault("not_automatic_activation", True)
        summary_payload.setdefault("trust_label_not_certification", True)
        schema_rows = _list_of_mappings(supplied.get("schema_migration", ()))
        migration_notes = tuple(
            str(row.get("migration_notes", ""))
            for row in schema_rows
            if str(row.get("migration_notes", ""))
        )
        file_boundaries = _list_of_mappings(
            supplied.get("file_format_boundaries", ())
        )
        write_plans = _list_of_mappings(supplied.get("write_plans", ()))
        payload = {
            "payload_kind": "optional_solver_plugin_manifest_state_writer_state",
            "payload_schema_version": self.payload_schema_version,
            "writer_version": self.writer_version,
            "generated_by": str(
                summary.get(
                    "generated_by_display",
                    "OSW optional solver plugin manifest state writer",
                )
            ),
            "state_scope": str(summary.get("state_scope", "session_only")),
            "header": {
                "payload_schema_version": self.payload_schema_version,
                "writer_version": self.writer_version,
                "view_model_schema_version": str(
                    summary.get("schema_version_display", "")
                ),
                "state_scope": str(summary.get("state_scope", "session_only")),
                "readiness": str(summary.get("readiness", "")),
                "operation": "explicit_local_state_write",
                "default_write_path_selected": False,
                "project_schema_state": "not_project_schema",
            },
            "summary": summary_payload,
            "storage_options": _list_of_mappings(
                supplied.get("storage_options", ())
            ),
            "write_plan": write_plans[0] if write_plans else {},
            "write_plans": write_plans,
            "file_format": file_boundaries,
            "schema_boundary": file_boundaries[0] if file_boundaries else {},
            "sources": _list_of_mappings(supplied.get("sources", ())),
            "provenance": _list_of_mappings(supplied.get("sources", ())),
            "candidates": _list_of_mappings(supplied.get("candidates", ())),
            "acknowledgements": _list_of_mappings(
                supplied.get("acknowledgements", ())
            ),
            "redaction_privacy": _list_of_mappings(supplied.get("redaction", ())),
            "schema_migration": schema_rows,
            "stale_sources": _list_of_mappings(supplied.get("stale_sources", ())),
            "conflicts": _list_of_mappings(supplied.get("conflicts", ())),
            "unsafe_claims": _list_of_mappings(supplied.get("unsafe_claims", ())),
            "evidence_history": _list_of_mappings(
                supplied.get("evidence_history", ())
            ),
            "atomicity_error_handling_plan": _list_of_mappings(
                supplied.get("atomicity_plan", ())
            ),
            "diagnostics": _list_of_mappings(supplied.get("diagnostics", ())),
            "limitations": list(
                _text_tuple(supplied.get("guidance_text", ()))
                + _text_tuple(supplied.get("safety_text", ()))
            ),
            "non_action_flags": _mapping(supplied.get("non_action_flags", {})),
            "action_states": _list_of_mappings(supplied.get("actions", ())),
            "migration_notes": list(migration_notes),
            "safety_boundary": list(_SAFETY_BOUNDARY_NOTES),
            "not_validation_evidence": bool(
                supplied.get("not_validation_evidence", True)
            ),
        }
        return _normalize_payload_mapping(payload)

    def serialize_payload(
        self,
        payload: Mapping[str, object],
        *,
        encoding: str = "utf-8",
        newline: str = "\n",
    ) -> bytes:
        """Serialize payload with stable sorted JSON keys and trailing newline."""

        text = json.dumps(
            _normalize_json_value(payload),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        return (text + newline).encode(encoding)

    def plan_write(
        self,
        view_model: object,
        request: OptionalSolverPluginManifestStateWriterRequest,
    ) -> OptionalSolverPluginManifestStateWriterResult:
        """Plan a state write without creating or replacing files."""

        payload, payload_bytes, diagnostics = self._build_and_preflight(
            view_model, request
        )
        target_display, target_redacted = _target_display(request.target_path)
        status = _status_from_diagnostics(diagnostics, request, perform_write=False)
        if status == OptionalSolverPluginManifestStateWriterStatus.SKIPPED:
            diagnostics = diagnostics + (
                _diagnostic(
                    "info",
                    OSPMG_STATE_WRITER_WRITE_PLANNED,
                    "State writer dry-run planned; no file write was performed.",
                ),
            )
            status = OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED
        return _result(
            status=status,
            target_reference_display=target_display,
            target_reference_redacted=target_redacted,
            payload=payload,
            payload_bytes=payload_bytes,
            diagnostics=diagnostics,
        )

    def write_state(
        self,
        view_model: object,
        request: OptionalSolverPluginManifestStateWriterRequest,
    ) -> OptionalSolverPluginManifestStateWriterResult:
        """Write state to the explicit target path when preflight passes."""

        payload, payload_bytes, diagnostics = self._build_and_preflight(
            view_model, request
        )
        target_display, target_redacted = _target_display(request.target_path)
        status = _status_from_diagnostics(diagnostics, request, perform_write=True)
        if status != OptionalSolverPluginManifestStateWriterStatus.SKIPPED:
            return _result(
                status=status,
                target_reference_display=target_display,
                target_reference_redacted=target_redacted,
                payload=payload,
                payload_bytes=payload_bytes,
                diagnostics=diagnostics,
            )
        if request.dry_run:
            diagnostics = diagnostics + (
                _diagnostic(
                    "info",
                    OSPMG_STATE_WRITER_WRITE_PLANNED,
                    "State writer dry-run planned; no file write was performed.",
                ),
            )
            return _result(
                status=OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED,
                target_reference_display=target_display,
                target_reference_redacted=target_redacted,
                payload=payload,
                payload_bytes=payload_bytes,
                diagnostics=diagnostics,
            )

        target = Path(str(request.target_path))
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "wb",
                delete=False,
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
            ) as temp:
                temp_path = Path(temp.name)
                temp.write(payload_bytes)
                temp.flush()
                os.fsync(temp.fileno())
            os.replace(temp_path, target)
        except OSError as exc:
            if temp_path is not None:
                _cleanup_temp_file(temp_path)
            diagnostics = diagnostics + (
                _diagnostic(
                    "error",
                    OSPMG_STATE_WRITER_ATOMIC_REPLACE_ERROR,
                    f"State writer atomic replace failed: {exc}",
                    blocker=True,
                    target_reference_display=target_display,
                    suggested_fix="Review target permissions and available disk space.",
                ),
            )
            return _result(
                status=OptionalSolverPluginManifestStateWriterStatus.ERROR,
                target_reference_display=target_display,
                target_reference_redacted=target_redacted,
                payload=payload,
                payload_bytes=payload_bytes,
                diagnostics=diagnostics,
            )

        diagnostics = diagnostics + (
            _diagnostic(
                "info",
                OSPMG_STATE_WRITER_WRITE_COMPLETED,
                "State writer completed an explicit local atomic replace.",
                target_reference_display=target_display,
            ),
        )
        return _result(
            status=OptionalSolverPluginManifestStateWriterStatus.WRITTEN,
            target_reference_display=target_display,
            target_reference_redacted=target_redacted,
            payload=payload,
            payload_bytes=payload_bytes,
            diagnostics=diagnostics,
            bytes_written=len(payload_bytes),
            write_performed=True,
            file_write_performed=True,
            temp_file_used=True,
            atomic_replace_performed=True,
        )

    def diagnostics_from_preflight(
        self,
        view_model: object,
        request: OptionalSolverPluginManifestStateWriterRequest,
    ) -> tuple[OptionalSolverPluginManifestStateWriterDiagnostic, ...]:
        """Return preflight diagnostics without writing."""

        _payload, _payload_bytes, diagnostics = self._build_and_preflight(
            view_model, request
        )
        return diagnostics

    def _build_and_preflight(
        self,
        view_model: object,
        request: OptionalSolverPluginManifestStateWriterRequest,
    ) -> tuple[
        dict[str, object],
        bytes,
        tuple[OptionalSolverPluginManifestStateWriterDiagnostic, ...],
    ]:
        diagnostics: list[OptionalSolverPluginManifestStateWriterDiagnostic] = []
        try:
            payload = self.build_payload(view_model)
            payload_bytes = self.serialize_payload(
                payload,
                encoding=request.encoding,
                newline=request.newline,
            )
        except (TypeError, ValueError, UnicodeError) as exc:
            return {}, b"", (
                _diagnostic(
                    "error",
                    OSPMG_STATE_WRITER_SERIALIZATION_ERROR,
                    f"State writer could not serialize supplied state: {exc}",
                    blocker=True,
                ),
            )

        diagnostics.extend(_path_diagnostics(request))
        diagnostics.extend(_request_diagnostics(request, payload))
        diagnostics.extend(_payload_safety_diagnostics(payload))
        return payload, payload_bytes, tuple(diagnostics)


def build_optional_solver_plugin_manifest_state_writer_payload(
    view_model: object,
) -> dict[str, object]:
    """Build an OSW-EXP-102 state writer payload from supplied state."""

    return OptionalSolverPluginManifestStateWriter().build_payload(view_model)


def plan_optional_solver_plugin_manifest_state_write(
    view_model: object,
    request: OptionalSolverPluginManifestStateWriterRequest,
) -> OptionalSolverPluginManifestStateWriterResult:
    """Plan an explicit local state write without writing."""

    return OptionalSolverPluginManifestStateWriter().plan_write(view_model, request)


def write_optional_solver_plugin_manifest_state(
    view_model: object,
    request: OptionalSolverPluginManifestStateWriterRequest,
) -> OptionalSolverPluginManifestStateWriterResult:
    """Write optional solver plugin manifest UX state to an explicit path."""

    return OptionalSolverPluginManifestStateWriter().write_state(view_model, request)


def _path_diagnostics(
    request: OptionalSolverPluginManifestStateWriterRequest,
) -> tuple[OptionalSolverPluginManifestStateWriterDiagnostic, ...]:
    target_display, _target_redacted = _target_display(request.target_path)
    diagnostics: list[OptionalSolverPluginManifestStateWriterDiagnostic] = []
    raw_target = str(request.target_path or "").strip()
    if not raw_target:
        return (
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_TARGET_REQUIRED,
                "State writer requires an explicit caller-supplied target path.",
                blocker=True,
                suggested_fix="Pass an explicit target_path in the writer request.",
            ),
        )
    target = Path(raw_target)
    if target.exists() and target.is_symlink():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED,
                "State writer refuses symlink targets.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    if target.exists() and target.is_dir():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED,
                "State writer refuses directory targets.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    if not target.parent.exists():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_PARENT_MISSING,
                "State writer refuses missing parent directories and creates none.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    elif not target.parent.is_dir():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_PARENT_NOT_DIRECTORY,
                "State writer target parent is not a directory.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    if target.exists() and not request.allow_replace and not target.is_dir():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_TARGET_EXISTS,
                "State writer refuses to replace an existing target unless allowed.",
                blocker=True,
                target_reference_display=target_display,
                suggested_fix="Set allow_replace=True for an explicit replacement.",
            )
        )
    return tuple(diagnostics)


def _request_diagnostics(
    request: OptionalSolverPluginManifestStateWriterRequest,
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestStateWriterDiagnostic, ...]:
    diagnostics: list[OptionalSolverPluginManifestStateWriterDiagnostic] = []
    target_display, _target_redacted = _target_display(request.target_path)
    if not request.dry_run and not request.caller_acknowledged_write:
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED,
                "Actual state writing requires caller_acknowledged_write=True.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    if (
        request.expected_schema_version
        and request.expected_schema_version != payload.get("payload_schema_version")
    ):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_SCHEMA_VERSION_MISMATCH,
                "State writer payload schema version does not match request.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    readiness = _payload_readiness(payload)
    allowed = _DRY_RUN_ALLOWED_READYNESS if request.dry_run else _SUPPORTED_VIEWMODEL_READYNESS
    if readiness not in allowed:
        severity = "error" if readiness == "error" else "warning"
        diagnostics.append(
            _diagnostic(
                severity,
                OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
                f"State writer view-model readiness blocks writing: {readiness}.",
                blocker=True,
                target_reference_display=target_display,
                suggested_fix="Resolve view-model blockers before writing.",
            )
        )
    for code in _payload_blocker_codes(payload):
        diagnostics.append(
            _diagnostic(
                "warning",
                OSPMG_STATE_WRITER_WRITE_BLOCKED,
                f"State writer payload carries blocker diagnostic: {code}.",
                blocker=True,
                target_reference_display=target_display,
            )
        )
    return tuple(diagnostics)


def _payload_safety_diagnostics(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestStateWriterDiagnostic, ...]:
    diagnostics: list[OptionalSolverPluginManifestStateWriterDiagnostic] = []
    if _contains_secret_like_content(payload):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_PAYLOAD_SECRET_BLOCKED,
                "State writer refuses payloads containing secret-like content.",
                blocker=True,
            )
        )
    if _contains_unredacted_path_block(payload):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_STATE_WRITER_PAYLOAD_PATH_BLOCKED,
                "State writer refuses payloads with unredacted path blockers.",
                blocker=True,
            )
        )
    return tuple(diagnostics)


def _status_from_diagnostics(
    diagnostics: Sequence[OptionalSolverPluginManifestStateWriterDiagnostic],
    request: OptionalSolverPluginManifestStateWriterRequest,
    *,
    perform_write: bool,
) -> OptionalSolverPluginManifestStateWriterStatus:
    if any(row.code == OSPMG_STATE_WRITER_SERIALIZATION_ERROR for row in diagnostics):
        return OptionalSolverPluginManifestStateWriterStatus.ERROR
    if any(row.code == OSPMG_STATE_WRITER_TARGET_REQUIRED for row in diagnostics):
        return OptionalSolverPluginManifestStateWriterStatus.UNAVAILABLE
    readiness_diagnostic = next(
        (
            row
            for row in diagnostics
            if row.code == OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY
        ),
        None,
    )
    if readiness_diagnostic is not None:
        if "unavailable_" in readiness_diagnostic.message:
            return OptionalSolverPluginManifestStateWriterStatus.UNAVAILABLE
        if " error." in readiness_diagnostic.message:
            return OptionalSolverPluginManifestStateWriterStatus.ERROR
        return OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    if any(row.blocker for row in diagnostics):
        return OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    if not perform_write or request.dry_run:
        return OptionalSolverPluginManifestStateWriterStatus.SKIPPED
    return OptionalSolverPluginManifestStateWriterStatus.SKIPPED


def _result(
    *,
    status: OptionalSolverPluginManifestStateWriterStatus,
    target_reference_display: str,
    target_reference_redacted: bool,
    payload: Mapping[str, object],
    payload_bytes: bytes,
    diagnostics: Sequence[OptionalSolverPluginManifestStateWriterDiagnostic],
    bytes_written: int = 0,
    write_performed: bool = False,
    file_write_performed: bool = False,
    temp_file_used: bool = False,
    atomic_replace_performed: bool = False,
) -> OptionalSolverPluginManifestStateWriterResult:
    blockers = tuple(row.code for row in diagnostics if row.blocker)
    warnings = tuple(row.code for row in diagnostics if row.severity == "warning")
    return OptionalSolverPluginManifestStateWriterResult(
        status=status,
        target_reference_display=target_reference_display,
        target_reference_redacted=target_reference_redacted,
        bytes_planned=len(payload_bytes),
        bytes_written=bytes_written,
        sha256=hashlib.sha256(payload_bytes).hexdigest() if payload_bytes else "",
        payload_key_count=len(payload),
        payload_section_count=_payload_section_count(payload),
        diagnostics=tuple(diagnostics),
        blockers=blockers,
        warnings=warnings,
        write_performed=write_performed,
        file_write_performed=file_write_performed,
        temp_file_used=temp_file_used,
        atomic_replace_performed=atomic_replace_performed,
    )


def _diagnostic(
    severity: str,
    code: str,
    message: str,
    *,
    blocker: bool = False,
    target_reference_display: str = "",
    suggested_fix: str = "",
) -> OptionalSolverPluginManifestStateWriterDiagnostic:
    return OptionalSolverPluginManifestStateWriterDiagnostic(
        severity=severity,
        code=code,
        message=message,
        blocker=blocker,
        target_reference_display=target_reference_display,
        suggested_fix=suggested_fix,
    )


def _mapping_from_supplied_state(value: object) -> Mapping[str, object]:
    if isinstance(value, OptionalSolverPluginManifestStateWriterViewModel):
        return value.to_mapping()
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    raise TypeError("State writer requires a view-model or mapping payload.")


def _normalize_payload_mapping(value: Mapping[str, object]) -> dict[str, object]:
    normalized = _normalize_json_value(value)
    if not isinstance(normalized, dict):
        raise TypeError("State writer payload must normalize to a mapping.")
    return normalized


def _normalize_json_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _normalize_json_value(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if hasattr(value, "to_mapping"):
        mapped = value.to_mapping()
        if isinstance(mapped, Mapping):
            return _normalize_json_value(mapped)
    if hasattr(value, "__slots__"):
        return {
            str(slot): _normalize_json_value(getattr(value, slot))
            for slot in value.__slots__
        }
    raise TypeError(f"Value of type {type(value).__name__} is not JSON-compatible.")


def _mapping(value: object) -> dict[str, object]:
    normalized = _normalize_json_value(value if isinstance(value, Mapping) else {})
    return normalized if isinstance(normalized, dict) else {}


def _list_of_mappings(value: object) -> list[dict[str, object]]:
    normalized = _normalize_json_value(value)
    if isinstance(normalized, list):
        return [item for item in normalized if isinstance(item, dict)]
    if isinstance(normalized, dict):
        return [normalized]
    return []


def _text_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _payload_readiness(payload: Mapping[str, object]) -> str:
    summary = _mapping(payload.get("summary", {}))
    header = _mapping(payload.get("header", {}))
    write_plan = _mapping(payload.get("write_plan", {}))
    return str(
        summary.get(
            "readiness",
            header.get("readiness", write_plan.get("readiness", "")),
        )
    )


def _payload_blocker_codes(payload: Mapping[str, object]) -> tuple[str, ...]:
    diagnostics = _list_of_mappings(payload.get("diagnostics", ()))
    return tuple(
        str(row.get("code", ""))
        for row in diagnostics
        if bool(row.get("blocker", False)) and str(row.get("code", ""))
    )


def _contains_secret_like_content(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_secret_like_content(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_secret_like_content(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in _SECRET_MARKERS)
    return False


def _contains_unredacted_path_block(payload: Mapping[str, object]) -> bool:
    for row in _list_of_mappings(payload.get("redaction_privacy", ())):
        if row.get("unredacted_path_blocked") or row.get("secret_like_content_blocked"):
            return True
    for row in _list_of_mappings(payload.get("sources", ())):
        if row.get("raw_reference_blocked"):
            return True
    return False


def _payload_section_count(payload: Mapping[str, object]) -> int:
    sections = payload.get("sections")
    if isinstance(sections, Sequence) and not isinstance(sections, str):
        return len(sections)
    return sum(
        1
        for key in (
            "storage_options",
            "write_plans",
            "file_format",
            "sources",
            "candidates",
            "acknowledgements",
            "diagnostics",
            "redaction_privacy",
            "schema_migration",
            "stale_sources",
            "conflicts",
            "unsafe_claims",
            "evidence_history",
            "atomicity_error_handling_plan",
        )
        if key in payload
    )


def _target_display(target_path: object) -> tuple[str, bool]:
    raw = str(target_path or "").strip()
    if not raw:
        return "", False
    path = Path(raw)
    display = path.name or "<target>"
    return display, display != raw


def _cleanup_temp_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


__all__ = [
    "OSPMG_STATE_WRITER_ATOMIC_REPLACE_ERROR",
    "OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED",
    "OSPMG_STATE_WRITER_PARENT_MISSING",
    "OSPMG_STATE_WRITER_PARENT_NOT_DIRECTORY",
    "OSPMG_STATE_WRITER_PAYLOAD_PATH_BLOCKED",
    "OSPMG_STATE_WRITER_PAYLOAD_SECRET_BLOCKED",
    "OSPMG_STATE_WRITER_SCHEMA_VERSION_MISMATCH",
    "OSPMG_STATE_WRITER_SERIALIZATION_ERROR",
    "OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED",
    "OSPMG_STATE_WRITER_TARGET_EXISTS",
    "OSPMG_STATE_WRITER_TARGET_REQUIRED",
    "OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED",
    "OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY",
    "OSPMG_STATE_WRITER_WRITE_BLOCKED",
    "OSPMG_STATE_WRITER_WRITE_COMPLETED",
    "OSPMG_STATE_WRITER_WRITE_ERROR",
    "OSPMG_STATE_WRITER_WRITE_PLANNED",
    "STATE_WRITER_IMPLEMENTATION_VERSION",
    "STATE_WRITER_PAYLOAD_SCHEMA_VERSION",
    "OptionalSolverPluginManifestStateWriter",
    "OptionalSolverPluginManifestStateWriterDiagnostic",
    "OptionalSolverPluginManifestStateWriterRequest",
    "OptionalSolverPluginManifestStateWriterResult",
    "OptionalSolverPluginManifestStateWriterStatus",
    "build_optional_solver_plugin_manifest_state_writer_payload",
    "plan_optional_solver_plugin_manifest_state_write",
    "write_optional_solver_plugin_manifest_state",
]
