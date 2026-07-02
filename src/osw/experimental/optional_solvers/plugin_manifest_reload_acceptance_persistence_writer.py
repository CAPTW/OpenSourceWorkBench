"""Explicit reload acceptance persistence review-record writer.

This OSW-EXP-126 module serializes a supplied reload acceptance persistence
view-model into deterministic JSON and writes only to an explicit
caller-supplied target path after dry-run/path/acknowledgement checks pass. It
does not perform runtime reload acceptance, active acceptance mutation,
ProjectSchema mutation, discovery, validation, solver execution, activation,
trust restoration, CLI/GUI behavior, reader invocation, issue/release/tag/asset
mutation, or certification claims.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path

from .plugin_manifest_reload_acceptance_persistence_viewmodel import (
    RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND,
    RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID,
    RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
)

RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_VERSION = "osw-exp-126"
RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_record"
)
RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION = (
    "osw-exp-126-reload-acceptance-persistence-writer-1"
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_ERROR = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_ERROR"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_DIRECTORY_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_DIRECTORY_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_SYMLINK_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_SYMLINK_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_MISSING = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_MISSING"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_NOT_DIRECTORY = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_NOT_DIRECTORY"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CALLER_ACK_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CALLER_ACK_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_SECRET_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_SECRET_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_UNREDACTED_PATH_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SERIALIZATION_ERROR = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SERIALIZATION_ERROR"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED"
)

_WRITABLE_READINESS = {"writer_future_only", "ready_future_only"}
_ALLOWED_FUTURE_ONLY_CODES = {
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY",
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
_ENV_MARKERS = ("%userprofile%", "$env:", "${", "%appdata%")
_SAFETY_GUIDANCE = (
    "Persisted reload acceptance review records are not runtime reload acceptance.",
    "Write success is not validation success.",
    "Write success is not validation failure.",
    "Write success is not ProjectSchema mutation.",
    "Write success is not trust restoration.",
    "Write success is not automatic activation.",
    "Write success is not discovery success.",
    "Write success is not solver execution.",
    "Write success is not issue closure.",
    "Write success is not release mutation.",
    "Write success is not certification.",
    "Persisted review records remain untrusted by default.",
    "Skipped-missing remains skipped-missing.",
    "Issues #6 through #11 remain live optional validation issues.",
)


class ReloadAcceptancePersistenceWriteStatus(str, Enum):
    """Writer result status vocabulary."""

    PLANNED = "planned"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceWriteDiagnostic:
    """Diagnostic returned by the reload acceptance persistence writer."""

    severity: str
    code: str
    message: str
    blocker: bool = False
    target_display: str = ""
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceWritePathPolicy:
    """Path policy enforced by the explicit writer."""

    explicit_target_required: bool = True
    default_path_used: bool = False
    background_write_performed: bool = False
    directory_creation_allowed: bool = False
    directory_targets_allowed: bool = False
    symlink_targets_allowed: bool = False
    missing_parent_allowed: bool = False
    replace_requires_allow_replace: bool = True
    raw_target_display_hidden: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceWriteRequest:
    """Explicit caller request for dry-run planning or writing."""

    persistence_viewmodel: object
    target_path: str | Path | None = None
    dry_run: bool = True
    allow_replace: bool = False
    caller_acknowledged_persistence_write: bool = False
    expected_payload_kind: str | None = None
    expected_schema_version: str | None = None
    allow_symlink: bool = False
    allow_unredacted_paths: bool = False
    allow_secret_like_values: bool = False
    safety_review_id: str = ""
    request_context: str = ""
    encoding: str = "utf-8"
    newline: str = "\n"


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceWritePayload:
    """Deterministic payload wrapper."""

    mapping: Mapping[str, object]

    def to_mapping(self) -> dict[str, object]:
        normalized = _normalize_json_value(self.mapping)
        if not isinstance(normalized, dict):
            raise TypeError("Reload acceptance persistence payload must be a mapping.")
        return normalized


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceWriteResult:
    """Explicit writer result with side-effect and non-action flags."""

    status: ReloadAcceptancePersistenceWriteStatus
    target_display: str
    target_redacted: bool
    dry_run: bool
    planned: bool
    written: bool
    bytes_count: int
    sha256: str
    payload_kind: str
    payload_schema_version: str
    diagnostics: tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    non_action_flags: Mapping[str, bool]
    payload: Mapping[str, object]
    write_performed: bool = False
    persistence_write_performed: bool = False
    runtime_reload_acceptance_performed: bool = False
    project_schema_mutated: bool = False
    cleanup_performed: bool = False
    temp_file_left_behind: bool = False
    temp_file_used: bool = False
    atomic_replace_performed: bool = False

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "target_display": self.target_display,
            "target_redacted": self.target_redacted,
            "dry_run": self.dry_run,
            "planned": self.planned,
            "written": self.written,
            "bytes_count": self.bytes_count,
            "sha256": self.sha256,
            "payload_kind": self.payload_kind,
            "payload_schema_version": self.payload_schema_version,
            "diagnostics": [row.to_mapping() for row in self.diagnostics],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "non_action_flags": dict(self.non_action_flags),
            "payload": _normalize_json_value(self.payload),
            "write_performed": self.write_performed,
            "persistence_write_performed": self.persistence_write_performed,
            "runtime_reload_acceptance_performed": (
                self.runtime_reload_acceptance_performed
            ),
            "project_schema_mutated": self.project_schema_mutated,
            "cleanup_performed": self.cleanup_performed,
            "temp_file_left_behind": self.temp_file_left_behind,
            "temp_file_used": self.temp_file_used,
            "atomic_replace_performed": self.atomic_replace_performed,
        }

    def to_text_lines(self) -> tuple[str, ...]:
        return (
            "Optional Solver Plugin Manifest Reload Acceptance Persistence Writer",
            f"status: {self.status.value}",
            f"target: {self.target_display}",
            f"dry_run: {self.dry_run}",
            f"planned: {self.planned}",
            f"written: {self.written}",
            f"bytes_count: {self.bytes_count}",
            f"sha256: {self.sha256}",
            f"payload_kind: {self.payload_kind}",
            f"payload_schema_version: {self.payload_schema_version}",
            "safety: persisted review record is not runtime acceptance",
            "safety: write success is not validation success",
            "safety: write success is not validation failure",
            "safety: write success is not ProjectSchema mutation",
            "safety: write success is not trust restoration",
            "safety: write success is not automatic activation",
            "safety: write success is not issue closure or release mutation",
            "safety: write success is not certification",
        ) + tuple(
            f"diagnostic: {row.severity} {row.code}" for row in self.diagnostics
        )


class OptionalSolverPluginManifestReloadAcceptancePersistenceWriter:
    """Explicit deterministic writer for reload acceptance review records."""

    payload_kind = RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND
    payload_schema_version = RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION
    writer_version = RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_VERSION

    def build_payload(
        self,
        request: ReloadAcceptancePersistenceWriteRequest,
    ) -> dict[str, object]:
        """Build a deterministic JSON-compatible payload without writing."""

        view_mapping = _mapping_from_viewmodel(request.persistence_viewmodel)
        summary = _mapping(view_mapping.get("summary", {}))
        non_action_flags = _result_non_action_flags(write_completed=False)
        return _normalize_payload_mapping(
            {
                "payload_kind": self.payload_kind,
                "payload_schema_version": self.payload_schema_version,
                "generated_by": (
                    "OSW optional solver plugin manifest reload acceptance "
                    "persistence writer"
                ),
                "writer_version": self.writer_version,
                "source_payload_kind": RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND,
                "source_schema_id": RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID,
                "source_schema_version": RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
                "summary": {
                    "state": str(summary.get("state", "")),
                    "readiness": str(summary.get("readiness", "")),
                    "persistence_requested": bool(
                        summary.get("persistence_requested", False)
                    ),
                    "ready_for_future_write_plan": bool(
                        summary.get("ready_for_future_write_plan", False)
                    ),
                    "accepted_for_session_review": bool(
                        summary.get("accepted_for_session_review", False)
                    ),
                    "persisted_review_record_is_runtime_acceptance": False,
                    "write_success_is_validation_success": False,
                    "write_success_is_validation_failure": False,
                    "write_success_mutates_project_schema": False,
                    "write_success_restores_trust": False,
                    "write_success_activates_candidate": False,
                    "write_success_closes_issue": False,
                    "write_success_mutates_release": False,
                    "write_success_is_certification": False,
                },
                "storage": {
                    "target_display": _safe_display(request.target_path),
                    "target_redacted": bool(str(request.target_path or "")),
                    "explicit_target_path_required": True,
                    "default_path_used": False,
                    "background_write_performed": False,
                    "allow_replace": request.allow_replace,
                    "dry_run": request.dry_run,
                    "request_context": _safe_display(request.request_context),
                    "safety_review_id": _safe_display(request.safety_review_id),
                },
                "write_plan": {
                    "dry_run": request.dry_run,
                    "actual_write_requires_acknowledgement": True,
                    "caller_acknowledged_persistence_write": (
                        request.caller_acknowledged_persistence_write
                    ),
                    "explicit_target_path": bool(str(request.target_path or "").strip()),
                    "atomic_same_directory_temp_replace": True,
                    "parent_directory_creation_performed": False,
                    "directory_scan_performed": False,
                    "write_performed": False,
                    "persistence_write_performed": False,
                    "runtime_reload_acceptance_performed": False,
                    "project_schema_mutated": False,
                    "path_policy": ReloadAcceptancePersistenceWritePathPolicy().to_mapping(),
                },
                "acceptance_persistence": view_mapping,
                "acknowledgements": _list_of_mappings(
                    view_mapping.get("acknowledgements", ())
                ),
                "expiry": _list_of_mappings(
                    view_mapping.get("acknowledgement_expiry", ())
                ),
                "provenance": _list_of_mappings(view_mapping.get("provenance", ())),
                "schema": _list_of_mappings(view_mapping.get("schema", ())),
                "redaction_privacy": (
                    {
                        "raw_absolute_paths_hidden": True,
                        "home_directories_hidden": True,
                        "environment_variables_hidden": True,
                        "secret_like_values_blocked": True,
                        "unredacted_source_paths_blocked": True,
                        "target_display_redacted": bool(str(request.target_path or "")),
                    },
                ),
                "candidate_lifecycle": (
                    "inactive preview remains review-only",
                    "persisted active requires future activation review",
                    "no automatic activation",
                    "no trust restoration",
                    "accepted state does not override built-ins",
                ),
                "stale_sources": (
                    "missing, moved, or changed sources require re-preview",
                    "writer does not inspect referenced source files",
                ),
                "conflicts": (
                    "conflicts remain visible",
                    "built-ins win by default",
                    "writer does not resolve conflicts",
                ),
                "unsafe_claims": (
                    "unsafe validation, issue, release, trust, install, solver, "
                    "or certification claims are blocked"
                ),
                "evidence_history": _list_of_mappings(
                    view_mapping.get("evidence_history", ())
                ),
                "diagnostics": _list_of_mappings(view_mapping.get("diagnostics", ())),
                "non_action_flags": non_action_flags,
                "disabled_future_actions": _list_of_mappings(
                    view_mapping.get("actions", ())
                ),
                "safety_guidance": _SAFETY_GUIDANCE,
                "limitations": (
                    "Local review-record persistence is non-authoritative.",
                    "Persistence does not accept runtime reload state.",
                    "Persistence does not mutate ProjectSchema.",
                    "CLI and GUI invocation remain separately gated.",
                ),
            }
        )

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
        request: ReloadAcceptancePersistenceWriteRequest,
    ) -> ReloadAcceptancePersistenceWriteResult:
        """Plan a write without creating files."""

        payload, payload_bytes, diagnostics = self._build_and_preflight(request)
        if not any(row.blocker for row in diagnostics):
            diagnostics = diagnostics + (
                _diagnostic(
                    "info",
                    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED,
                    (
                        "Reload acceptance persistence writer dry-run planned; "
                        "no file write was performed."
                    ),
                    target_display=_safe_display(request.target_path),
                ),
            )
        status = _status_from_diagnostics(diagnostics, planned=True)
        return _result(
            status=status,
            request=request,
            payload=payload,
            payload_bytes=payload_bytes,
            diagnostics=diagnostics,
        )

    def write(
        self,
        request: ReloadAcceptancePersistenceWriteRequest,
    ) -> ReloadAcceptancePersistenceWriteResult:
        """Plan or write an explicit local review record."""

        payload, payload_bytes, diagnostics = self._build_and_preflight(request)
        target_display = _safe_display(request.target_path)
        if request.dry_run:
            if not any(row.blocker for row in diagnostics):
                diagnostics = diagnostics + (
                    _diagnostic(
                        "info",
                        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED,
                        (
                            "Reload acceptance persistence writer dry-run planned; "
                            "no file write was performed."
                        ),
                        target_display=target_display,
                    ),
                )
            return _result(
                status=_status_from_diagnostics(diagnostics, planned=True),
                request=request,
                payload=payload,
                payload_bytes=payload_bytes,
                diagnostics=diagnostics,
            )
        if any(row.blocker for row in diagnostics):
            return _result(
                status=_status_from_diagnostics(diagnostics, planned=False),
                request=request,
                payload=payload,
                payload_bytes=payload_bytes,
                diagnostics=diagnostics,
            )

        payload = _payload_with_completed_write(payload)
        payload_bytes = self.serialize_payload(
            payload,
            encoding=request.encoding,
            newline=request.newline,
        )
        target = Path(str(request.target_path))
        temp_path: Path | None = None
        cleanup_performed = False
        temp_left = False
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
                cleanup_performed, temp_left = _cleanup_temp_file(temp_path)
            diagnostics = diagnostics + (
                _diagnostic(
                    "error",
                    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED,
                    f"Reload acceptance persistence atomic replace failed: {exc}",
                    blocker=True,
                    target_display=target_display,
                    suggested_fix="Review target permissions and available disk space.",
                ),
            )
            return _result(
                status=ReloadAcceptancePersistenceWriteStatus.ERROR,
                request=request,
                payload=payload,
                payload_bytes=payload_bytes,
                diagnostics=diagnostics,
                cleanup_performed=cleanup_performed,
                temp_file_left_behind=temp_left,
                temp_file_used=temp_path is not None,
            )

        diagnostics = diagnostics + (
            _diagnostic(
                "info",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED,
                "Reload acceptance persistence writer completed an explicit local atomic replace.",
                target_display=target_display,
            ),
        )
        return _result(
            status=ReloadAcceptancePersistenceWriteStatus.COMPLETED,
            request=request,
            payload=payload,
            payload_bytes=payload_bytes,
            diagnostics=diagnostics,
            write_performed=True,
            temp_file_used=True,
            atomic_replace_performed=True,
        )

    def diagnostics_from_preflight(
        self,
        request: ReloadAcceptancePersistenceWriteRequest,
    ) -> tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...]:
        """Return preflight diagnostics without writing."""

        _payload, _payload_bytes, diagnostics = self._build_and_preflight(request)
        return diagnostics

    def _build_and_preflight(
        self,
        request: ReloadAcceptancePersistenceWriteRequest,
    ) -> tuple[
        dict[str, object],
        bytes,
        tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...],
    ]:
        diagnostics: list[ReloadAcceptancePersistenceWriteDiagnostic] = []
        try:
            payload = self.build_payload(request)
            payload_bytes = self.serialize_payload(
                payload,
                encoding=request.encoding,
                newline=request.newline,
            )
        except (TypeError, ValueError, UnicodeError) as exc:
            return {}, b"", (
                _diagnostic(
                    "error",
                    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SERIALIZATION_ERROR,
                    f"Reload acceptance persistence payload could not be serialized: {exc}",
                    blocker=True,
                ),
            )

        diagnostics.extend(_path_diagnostics(request))
        diagnostics.extend(_request_diagnostics(request, payload))
        diagnostics.extend(_payload_safety_diagnostics(request, payload))
        return payload, payload_bytes, tuple(diagnostics)


def build_reload_acceptance_persistence_write_payload(
    request: ReloadAcceptancePersistenceWriteRequest,
) -> dict[str, object]:
    """Build a deterministic payload from a supplied persistence view-model."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceWriter().build_payload(
        request
    )


def plan_reload_acceptance_persistence_write(
    request: ReloadAcceptancePersistenceWriteRequest,
) -> ReloadAcceptancePersistenceWriteResult:
    """Plan an explicit local review-record write without writing."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceWriter().plan_write(
        request
    )


def write_reload_acceptance_persistence_record(
    request: ReloadAcceptancePersistenceWriteRequest,
) -> ReloadAcceptancePersistenceWriteResult:
    """Write a reload acceptance persistence review record to an explicit path."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceWriter().write(
        request
    )


def _path_diagnostics(
    request: ReloadAcceptancePersistenceWriteRequest,
) -> tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...]:
    target_display = _safe_display(request.target_path)
    diagnostics: list[ReloadAcceptancePersistenceWriteDiagnostic] = []
    raw_target = str(request.target_path or "").strip()
    if not raw_target:
        return (
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED,
                "Reload acceptance persistence writer requires an explicit target path.",
                blocker=True,
                suggested_fix="Pass target_path explicitly.",
            ),
        )
    target = Path(raw_target)
    if target.exists() and target.is_symlink():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_SYMLINK_BLOCKED,
                "Reload acceptance persistence writer refuses symlink targets.",
                blocker=True,
                target_display=target_display,
            )
        )
    if target.exists() and target.is_dir():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_DIRECTORY_BLOCKED,
                "Reload acceptance persistence writer refuses directory targets.",
                blocker=True,
                target_display=target_display,
            )
        )
    if not target.parent.exists():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_MISSING,
                (
                    "Reload acceptance persistence writer refuses missing "
                    "parent directories and creates none."
                ),
                blocker=True,
                target_display=target_display,
            )
        )
    elif not target.parent.is_dir():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_NOT_DIRECTORY,
                "Reload acceptance persistence writer target parent is not a directory.",
                blocker=True,
                target_display=target_display,
            )
        )
    if target.exists() and not request.allow_replace and not target.is_dir():
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS,
                (
                    "Reload acceptance persistence writer refuses replacement "
                    "unless allow_replace=True."
                ),
                blocker=True,
                target_display=target_display,
                suggested_fix="Set allow_replace=True for an explicit replacement.",
            )
        )
    return tuple(diagnostics)


def _request_diagnostics(
    request: ReloadAcceptancePersistenceWriteRequest,
    payload: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...]:
    diagnostics: list[ReloadAcceptancePersistenceWriteDiagnostic] = []
    target_display = _safe_display(request.target_path)
    if not request.dry_run and not request.caller_acknowledged_persistence_write:
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CALLER_ACK_REQUIRED,
                "Actual reload acceptance persistence writing requires caller acknowledgement.",
                blocker=True,
                target_display=target_display,
            )
        )
    expected_kind = request.expected_payload_kind
    if expected_kind and expected_kind != payload.get("payload_kind"):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH,
                "Payload kind does not match the request expectation.",
                blocker=True,
                target_display=target_display,
            )
        )
    expected_schema = request.expected_schema_version
    if expected_schema and expected_schema != payload.get("payload_schema_version"):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH,
                "Payload schema version does not match the request expectation.",
                blocker=True,
                target_display=target_display,
            )
        )
    diagnostics.extend(_viewmodel_diagnostics(payload, target_display))
    return tuple(diagnostics)


def _viewmodel_diagnostics(
    payload: Mapping[str, object],
    target_display: str,
) -> tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...]:
    acceptance_persistence = _mapping(payload.get("acceptance_persistence", {}))
    summary = _mapping(acceptance_persistence.get("summary", {}))
    readiness = str(summary.get("readiness", ""))
    ready = bool(summary.get("ready_for_future_write_plan", False))
    blocker_count = int(summary.get("blocker_count", 0) or 0)
    if readiness not in _WRITABLE_READINESS or not ready or blocker_count:
        return (
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED,
                f"Persistence view-model blocks writing: readiness={readiness}.",
                blocker=True,
                target_display=target_display,
                suggested_fix="Resolve persistence view-model blockers first.",
            ),
        )
    diagnostics = _list_of_mappings(acceptance_persistence.get("diagnostics", ()))
    blocked_codes = tuple(
        str(row.get("code", ""))
        for row in diagnostics
        if bool(row.get("blocker", False))
        and str(row.get("code", "")) not in _ALLOWED_FUTURE_ONLY_CODES
    )
    if blocked_codes:
        return tuple(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED,
                f"Persistence view-model carries blocker diagnostic: {code}.",
                blocker=True,
                target_display=target_display,
                suggested_fix="Resolve persistence view-model blockers first.",
            )
            for code in blocked_codes
        )
    return ()


def _payload_safety_diagnostics(
    request: ReloadAcceptancePersistenceWriteRequest,
    payload: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceWriteDiagnostic, ...]:
    diagnostics: list[ReloadAcceptancePersistenceWriteDiagnostic] = []
    if not request.allow_secret_like_values and _contains_secret_like_content(payload):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_SECRET_BLOCKED,
                "Reload acceptance persistence writer refuses secret-like payload content.",
                blocker=True,
            )
        )
    if not request.allow_unredacted_paths and _contains_unredacted_path_content(payload):
        diagnostics.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_UNREDACTED_PATH_BLOCKED,
                "Reload acceptance persistence writer refuses unredacted path payload content.",
                blocker=True,
            )
        )
    return tuple(diagnostics)


def _status_from_diagnostics(
    diagnostics: Sequence[ReloadAcceptancePersistenceWriteDiagnostic],
    *,
    planned: bool,
) -> ReloadAcceptancePersistenceWriteStatus:
    if any(
        row.code
        in {
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SERIALIZATION_ERROR,
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED,
        }
        for row in diagnostics
    ):
        return ReloadAcceptancePersistenceWriteStatus.ERROR
    if any(row.blocker for row in diagnostics):
        return ReloadAcceptancePersistenceWriteStatus.BLOCKED
    return ReloadAcceptancePersistenceWriteStatus.PLANNED if planned else (
        ReloadAcceptancePersistenceWriteStatus.COMPLETED
    )


def _result(
    *,
    status: ReloadAcceptancePersistenceWriteStatus,
    request: ReloadAcceptancePersistenceWriteRequest,
    payload: Mapping[str, object],
    payload_bytes: bytes,
    diagnostics: Sequence[ReloadAcceptancePersistenceWriteDiagnostic],
    write_performed: bool = False,
    cleanup_performed: bool = False,
    temp_file_left_behind: bool = False,
    temp_file_used: bool = False,
    atomic_replace_performed: bool = False,
) -> ReloadAcceptancePersistenceWriteResult:
    completed = status == ReloadAcceptancePersistenceWriteStatus.COMPLETED
    blockers = tuple(row.code for row in diagnostics if row.blocker)
    warnings = tuple(row.code for row in diagnostics if row.severity == "warning")
    target_display = _safe_display(request.target_path)
    non_action_flags = _result_non_action_flags(write_completed=completed)
    payload_kind = str(payload.get("payload_kind", ""))
    payload_schema_version = str(payload.get("payload_schema_version", ""))
    return ReloadAcceptancePersistenceWriteResult(
        status=status,
        target_display=target_display,
        target_redacted=bool(str(request.target_path or "")),
        dry_run=request.dry_run,
        planned=status == ReloadAcceptancePersistenceWriteStatus.PLANNED,
        written=completed,
        bytes_count=len(payload_bytes),
        sha256=hashlib.sha256(payload_bytes).hexdigest() if payload_bytes else "",
        payload_kind=payload_kind,
        payload_schema_version=payload_schema_version,
        diagnostics=tuple(diagnostics),
        blockers=blockers,
        warnings=warnings,
        non_action_flags=non_action_flags,
        payload=_payload_with_result_flags(payload, non_action_flags),
        write_performed=write_performed,
        persistence_write_performed=completed,
        temp_file_used=temp_file_used,
        atomic_replace_performed=atomic_replace_performed,
        cleanup_performed=cleanup_performed,
        temp_file_left_behind=temp_file_left_behind,
    )


def _diagnostic(
    severity: str,
    code: str,
    message: str,
    *,
    blocker: bool = False,
    target_display: str = "",
    suggested_fix: str = "",
) -> ReloadAcceptancePersistenceWriteDiagnostic:
    return ReloadAcceptancePersistenceWriteDiagnostic(
        severity=severity,
        code=code,
        message=message,
        blocker=blocker,
        target_display=target_display,
        suggested_fix=suggested_fix,
    )


def _payload_with_completed_write(
    payload: Mapping[str, object],
) -> dict[str, object]:
    updated = _normalize_payload_mapping(payload)
    write_plan = _mapping(updated.get("write_plan", {}))
    write_plan["write_performed"] = True
    write_plan["persistence_write_performed"] = True
    updated["write_plan"] = write_plan
    updated["non_action_flags"] = _result_non_action_flags(write_completed=True)
    return updated


def _payload_with_result_flags(
    payload: Mapping[str, object],
    non_action_flags: Mapping[str, bool],
) -> dict[str, object]:
    updated = _redact_unsafe_strings(_normalize_payload_mapping(payload))
    if not isinstance(updated, dict):
        raise TypeError("Reload acceptance persistence result payload must be a mapping.")
    updated["non_action_flags"] = dict(non_action_flags)
    return updated


def _result_non_action_flags(*, write_completed: bool) -> dict[str, bool]:
    return {
        "runtime_reload_acceptance_performed": False,
        "persistence_write_performed": write_completed,
        "project_schema_mutated": False,
        "default_reload_path_used": False,
        "background_reload_performed": False,
        "directory_scan_performed": False,
        "network_fetch_performed": False,
        "plugin_package_imported": False,
        "cli_subprocess_used": False,
        "gui_subprocess_used": False,
        "reloadable_bundle_created": False,
        "export_file_created": False,
        "report_file_created": False,
        "clipboard_used": False,
        "report_attached": False,
        "output_folder_opened": False,
        "live_discovery_executed": False,
        "passive_refresh_executed": False,
        "validation_executed": False,
        "solver_executed": False,
        "dependency_installed": False,
        "dependency_uninstalled": False,
        "solver_uninstalled": False,
        "candidate_activated": False,
        "trust_restored": False,
        "issue_mutated": False,
        "release_mutated": False,
        "tag_mutated": False,
        "asset_mutated": False,
        "version_bumped": False,
        "validation_pass_claimed": False,
        "validation_fail_claimed": False,
        "issue_closure_claimed": False,
        "bundled_solver_claimed": False,
        "certification_claimed": False,
    }


def _mapping_from_viewmodel(value: object) -> Mapping[str, object]:
    if isinstance(value, OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel):
        return value.to_mapping()
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    raise TypeError("Reload acceptance persistence writer requires a view-model or mapping.")


def _normalize_payload_mapping(value: Mapping[str, object]) -> dict[str, object]:
    normalized = _normalize_json_value(value)
    if not isinstance(normalized, dict):
        raise TypeError("Reload acceptance persistence payload must normalize to a mapping.")
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


def _contains_secret_like_content(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            _key_secret_like(str(key)) or _contains_secret_like_content(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_secret_like_content(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in _SECRET_MARKERS)
    return False


def _key_secret_like(key: str) -> bool:
    lowered = key.lower()
    return lowered in {"token", "secret", "password", "api_key", "apikey"} or (
        lowered.endswith("_token")
        or lowered.endswith("_secret")
        or lowered.endswith("_password")
    )


def _contains_unredacted_path_content(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_unredacted_path_content(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_unredacted_path_content(item) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    normalized = value.replace("\\", "/")
    if any(marker in lowered for marker in _ENV_MARKERS):
        return True
    if normalized.startswith(("C:/Users/", "/home/", "/Users/")):
        return True
    if len(normalized) > 3 and normalized[1:3] == ":/":
        return True
    return False


def _redact_unsafe_strings(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _redact_unsafe_strings(item)
            for key, item in value.items()
            if not _key_secret_like(str(key))
        }
    if isinstance(value, list):
        return [_redact_unsafe_strings(item) for item in value]
    if isinstance(value, str):
        if _secret_string(value):
            return "<redacted-secret-like-value>"
        if _contains_unredacted_path_content(value):
            return _safe_display(value)
    return value


def _safe_display(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if _secret_string(text):
        return "<redacted-secret-like-value>"
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        return normalized.rsplit("/", 1)[-1] or "redacted-reference"
    return text


def _secret_string(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _SECRET_MARKERS)


def _cleanup_temp_file(path: Path) -> tuple[bool, bool]:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return True, path.exists()
    return True, path.exists()


def _record_to_mapping(record: object) -> dict[str, object]:
    return {
        field.name: _normalize_json_value(getattr(record, field.name))
        for field in fields(record)
    }


__all__ = [
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CALLER_ACK_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_MISSING",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_NOT_DIRECTORY",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_SECRET_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_UNREDACTED_PATH_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SERIALIZATION_ERROR",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_DIRECTORY_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_SYMLINK_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_ERROR",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED",
    "RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND",
    "RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION",
    "RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_VERSION",
    "OptionalSolverPluginManifestReloadAcceptancePersistenceWriter",
    "ReloadAcceptancePersistenceWriteDiagnostic",
    "ReloadAcceptancePersistenceWritePathPolicy",
    "ReloadAcceptancePersistenceWritePayload",
    "ReloadAcceptancePersistenceWriteRequest",
    "ReloadAcceptancePersistenceWriteResult",
    "ReloadAcceptancePersistenceWriteStatus",
    "build_reload_acceptance_persistence_write_payload",
    "plan_reload_acceptance_persistence_write",
    "write_reload_acceptance_persistence_record",
]
