"""Explicit local file reader for optional solver plugin manifest reload state.

This OSW-EXP-113 module is the library-level reader designed in OSW-EXP-112. It
reads and parses only an explicit caller-provided local file path, validates the
bounded OSW-EXP-102 state-writer payload family, and returns diagnostics plus a
sanitized in-memory mapping suitable for OSW-EXP-107 reload view-model review.

It is intentionally narrow. It never chooses a default path, scans directories,
fetches URLs, imports plugin packages, runs discovery/validation/solver
execution, mutates ProjectSchema, activates candidates, restores trust, accepts a
reload at runtime, writes/creates/deletes files, or wires itself into the CLI or
GUI. Reading a file is never validation, trust restoration, automatic activation,
issue closure, release mutation, or certification.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .plugin_manifest_reload_viewmodel import (
    STATE_WRITER_PAYLOAD_KIND,
    STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
)

#: Conservative default maximum readable file size (bytes).
DEFAULT_MAX_BYTES = 1_000_000

#: Schema versions the reader recognizes as needing a future migration gate.
MIGRATABLE_PAYLOAD_SCHEMA_VERSIONS: tuple[str, ...] = (
    "osw-exp-102-state-writer-0",
    "osw-exp-102-preview",
)

READER_VERSION = "osw-exp-113"

# --- Diagnostics vocabulary (design-only reservation from OSW-EXP-112) --------
OSPMG_RELOAD_READER_FILE_MISSING = "OSPMG_RELOAD_READER_FILE_MISSING"
OSPMG_RELOAD_READER_NOT_REGULAR_FILE = "OSPMG_RELOAD_READER_NOT_REGULAR_FILE"
OSPMG_RELOAD_READER_SYMLINK_BLOCKED = "OSPMG_RELOAD_READER_SYMLINK_BLOCKED"
OSPMG_RELOAD_READER_FILE_TOO_LARGE = "OSPMG_RELOAD_READER_FILE_TOO_LARGE"
OSPMG_RELOAD_READER_EMPTY_FILE = "OSPMG_RELOAD_READER_EMPTY_FILE"
OSPMG_RELOAD_READER_ENCODING_ERROR = "OSPMG_RELOAD_READER_ENCODING_ERROR"
OSPMG_RELOAD_READER_JSON_PARSE_ERROR = "OSPMG_RELOAD_READER_JSON_PARSE_ERROR"
OSPMG_RELOAD_READER_ROOT_NOT_OBJECT = "OSPMG_RELOAD_READER_ROOT_NOT_OBJECT"
OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED = "OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED"
OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH = "OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH"
OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED = "OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED"
OSPMG_RELOAD_READER_MIGRATION_REQUIRED = "OSPMG_RELOAD_READER_MIGRATION_REQUIRED"
OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED"
)
OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED = (
    "OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED"
)
OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED = "OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED"
OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED = (
    "OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED"
)
OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED"
)
OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY = (
    "OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY"
)
OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY = (
    "OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY"
)
OSPMG_RELOAD_READER_REVIEW_ONLY = "OSPMG_RELOAD_READER_REVIEW_ONLY"
OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL = "OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL"
OSPMG_RELOAD_READER_READ_COMPLETED = "OSPMG_RELOAD_READER_READ_COMPLETED"

OSPMG_RELOAD_READER_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_RELOAD_READER_FILE_MISSING,
    OSPMG_RELOAD_READER_NOT_REGULAR_FILE,
    OSPMG_RELOAD_READER_SYMLINK_BLOCKED,
    OSPMG_RELOAD_READER_FILE_TOO_LARGE,
    OSPMG_RELOAD_READER_EMPTY_FILE,
    OSPMG_RELOAD_READER_ENCODING_ERROR,
    OSPMG_RELOAD_READER_JSON_PARSE_ERROR,
    OSPMG_RELOAD_READER_ROOT_NOT_OBJECT,
    OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED,
    OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH,
    OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_READER_MIGRATION_REQUIRED,
    OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED,
    OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED,
    OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED,
    OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED,
    OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY,
    OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY,
    OSPMG_RELOAD_READER_REVIEW_ONLY,
    OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL,
    OSPMG_RELOAD_READER_READ_COMPLETED,
)

# Secret-like substrings that block a payload outright.
_SECRET_MARKERS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "access_token",
    "secret",
    "password",
    "passwd",
    "bearer ",
    "private_key",
    "client_secret",
    "token=",
    "ghp_",
    "github_pat",
    "aws_secret",
)

# Raw absolute path markers that indicate an unredacted local path leak.
_UNREDACTED_PATH_PATTERN = re.compile(
    r"(?:^[A-Za-z]:[\\/])"  # Windows drive path: C:\ or C:/
    r"|(?:/home/)"
    r"|(?:/users/)"
    r"|(?:\\users\\)"
    r"|(?:%userprofile%)"
    r"|(?:\$home\b)"
    r"|(?:\$userprofile\b)",
    re.IGNORECASE,
)

# Disabled/future-only actions surfaced by the reader.
_DISABLED_FUTURE_ACTIONS: tuple[tuple[str, str], ...] = (
    ("accept_reload_as_trusted", "Reload acceptance is future-gated."),
    ("activate_reloaded_candidate", "Activation requires future activation review."),
    ("refresh_discovery", "Discovery refresh is future-gated."),
    ("validate_solver", "Validation is future-gated and out of scope."),
    ("execute_solver", "Solver execution is out of scope."),
    ("install_dependency", "Dependency installation is out of scope."),
    ("uninstall_dependency", "Dependency uninstall is out of scope."),
    ("uninstall_solver", "Solver uninstall is out of scope."),
    ("mutate_project_schema", "ProjectSchema mutation is out of scope."),
    ("create_export_summary", "Export summary creation is future-gated."),
    ("create_report_file", "Report file creation is future-gated."),
    ("create_reloadable_bundle", "Reloadable bundle creation is future-gated."),
    ("copy_to_clipboard", "Clipboard behavior is out of scope."),
    ("attach_to_report", "Report attachment is out of scope."),
    ("open_output_folder", "Open-output-folder behavior is out of scope."),
    ("close_issue", "Issue closure is out of scope."),
    ("mutate_release", "Release mutation is out of scope."),
    ("push_tag", "Tag mutation is out of scope."),
    ("upload_asset", "Asset mutation is out of scope."),
    ("claim_validation_success_failure", "Validation claims are out of scope."),
    ("claim_certification", "Certification claims are out of scope."),
)


class OptionalSolverPluginManifestReloadFileReaderStatus(str, Enum):
    """Reader result status vocabulary."""

    READY_FOR_VIEWMODEL = "ready_for_viewmodel"
    BLOCKED = "blocked"
    UNREADABLE = "unreadable"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReadRequest:
    """Explicit caller request describing one local file to read."""

    target_path: str | Path | None
    max_bytes: int = DEFAULT_MAX_BYTES
    allow_symlink: bool = False
    expected_payload_kind: str = STATE_WRITER_PAYLOAD_KIND
    expected_schema_version: str = STATE_WRITER_PAYLOAD_SCHEMA_VERSION
    allow_migration: bool = False
    allow_unredacted_paths: bool = False
    allow_secret_like_values: bool = False
    caller_context: str = ""
    acknowledgements: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReaderDiagnostic:
    """One diagnostic row produced by the reader (redacted context only)."""

    severity: str
    code: str
    message: str
    blocker: bool = False
    related: str = ""
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "blocker": self.blocker,
            "related": self.related,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReaderPayloadMetadata:
    """Metadata describing a parsed payload (provenance, not trust)."""

    payload_kind: str = ""
    payload_schema_version: str = ""
    writer_version: str = ""
    view_model_schema_version: str = ""
    state_scope: str = ""
    generated_by: str = ""
    reader_version: str = READER_VERSION
    source_count: int = 0
    candidate_count: int = 0
    acknowledgement_count: int = 0
    diagnostic_count: int = 0
    untrusted_by_default: bool = True
    trust_label_is_certification: bool = False
    fingerprint_is_trust_signal: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReaderNonActionFlags:
    """Reader honesty flags; every flag is and stays false."""

    file_write_performed: bool = False
    directory_created: bool = False
    directory_scan_performed: bool = False
    default_path_lookup_performed: bool = False
    background_reload_performed: bool = False
    network_fetch_performed: bool = False
    plugin_package_import_performed: bool = False
    cli_wiring_performed: bool = False
    gui_file_dialog_performed: bool = False
    runtime_reload_acceptance_performed: bool = False
    reloadable_bundle_created: bool = False
    export_file_created: bool = False
    report_file_created: bool = False
    clipboard_performed: bool = False
    report_attachment_performed: bool = False
    open_output_folder_performed: bool = False
    project_schema_mutation_performed: bool = False
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    solver_execution_performed: bool = False
    dependency_install_performed: bool = False
    dependency_uninstall_performed: bool = False
    solver_uninstall_performed: bool = False
    automatic_activation_performed: bool = False
    trust_restoration_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    tag_mutation_performed: bool = False
    asset_mutation_performed: bool = False
    version_bump_performed: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    issue_closure_claimed: bool = False
    certification_claimed: bool = False

    def to_mapping(self) -> dict[str, bool]:
        return {slot: getattr(self, slot) for slot in self.__slots__}


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReaderActionState:
    """One disabled/future-only action surfaced by the reader."""

    action: str
    enabled: bool
    reason: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReaderSummary:
    """Deterministic summary of one read attempt (redacted display only)."""

    status: str
    target_reference_display: str
    target_reference_redacted: bool
    bytes_read: int
    ready_for_viewmodel: bool
    blocker_count: int
    warning_count: int
    diagnostic_count: int
    review_only: bool = True
    not_validation_evidence: bool = True
    not_trust_restoration: bool = True
    not_automatic_activation: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadFileReadResult:
    """Explicit reader result. ``safe_mapping`` is set only when ready."""

    status: OptionalSolverPluginManifestReloadFileReaderStatus
    summary: OptionalSolverPluginManifestReloadFileReaderSummary
    payload_metadata: OptionalSolverPluginManifestReloadFileReaderPayloadMetadata
    diagnostics: tuple[OptionalSolverPluginManifestReloadFileReaderDiagnostic, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    redacted_target_display: str
    bytes_read: int
    payload_hash: str
    non_action_flags: OptionalSolverPluginManifestReloadFileReaderNonActionFlags
    action_states: tuple[OptionalSolverPluginManifestReloadFileReaderActionState, ...]
    safe_mapping: dict[str, object] | None = None
    no_validation_claim: bool = True
    no_validation_failure_claim: bool = True
    no_trust_restoration: bool = True
    no_automatic_activation: bool = True
    no_discovery_execution: bool = True
    no_solver_execution: bool = True
    no_issue_closure: bool = True
    no_release_mutation: bool = True
    no_certification: bool = True

    @property
    def ready_for_viewmodel(self) -> bool:
        return (
            self.status
            == OptionalSolverPluginManifestReloadFileReaderStatus.READY_FOR_VIEWMODEL
        )

    def codes(self) -> tuple[str, ...]:
        return tuple(diag.code for diag in self.diagnostics)

    def to_text_lines(self) -> tuple[str, ...]:
        """Render redacted, review-only plain-text lines (never raw paths)."""

        lines = [
            "Optional solver plugin manifest reload file reader",
            f"status: {self.summary.status}",
            f"target: {self.redacted_target_display}",
            f"bytes_read: {self.bytes_read}",
            f"ready_for_viewmodel: {self.ready_for_viewmodel}",
            "review-only: reading is not validation, trust restoration, or activation",
        ]
        for diag in self.diagnostics:
            lines.append(f"[{diag.severity}] {diag.code}: {diag.message}")
        return tuple(lines)


class OptionalSolverPluginManifestReloadFileReader:
    """Explicit-path, review-only reader for state-writer UX state files."""

    reader_version = READER_VERSION

    def read(
        self,
        request: OptionalSolverPluginManifestReloadFileReadRequest,
    ) -> OptionalSolverPluginManifestReloadFileReadResult:
        """Read and validate one explicit local file. Writes nothing."""

        redacted = _redact_path(request.target_path)
        target_redacted = redacted != str(request.target_path or "").strip()

        file_diag, raw = _read_file_bytes(request, redacted)
        if file_diag is not None:
            return _unreadable_result(redacted, target_redacted, (file_diag,), 0, "")

        parse_diag, payload, payload_hash = _parse_payload(raw, redacted)
        bytes_read = len(raw)
        if parse_diag is not None:
            return _unreadable_result(
                redacted, target_redacted, (parse_diag,), bytes_read, payload_hash
            )

        assert payload is not None
        diagnostics = _validate_payload(payload, request, redacted)
        blockers = tuple(d.code for d in diagnostics if d.blocker)
        warnings = tuple(d.code for d in diagnostics if d.severity == "warning")
        metadata = _payload_metadata(payload)

        if blockers:
            status = OptionalSolverPluginManifestReloadFileReaderStatus.BLOCKED
            safe_mapping: dict[str, object] | None = None
        else:
            status = (
                OptionalSolverPluginManifestReloadFileReaderStatus.READY_FOR_VIEWMODEL
            )
            diagnostics = diagnostics + (
                _diag(
                    "info",
                    OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL,
                    "Payload validated; a safe review mapping is available.",
                ),
                _diag(
                    "info",
                    OSPMG_RELOAD_READER_READ_COMPLETED,
                    "Read completed; reading is review-only and not acceptance.",
                ),
            )
            safe_mapping = payload

        summary = OptionalSolverPluginManifestReloadFileReaderSummary(
            status=status.value,
            target_reference_display=redacted,
            target_reference_redacted=target_redacted,
            bytes_read=bytes_read,
            ready_for_viewmodel=safe_mapping is not None,
            blocker_count=len(blockers),
            warning_count=len(warnings),
            diagnostic_count=len(diagnostics),
        )
        return OptionalSolverPluginManifestReloadFileReadResult(
            status=status,
            summary=summary,
            payload_metadata=metadata,
            diagnostics=diagnostics,
            blockers=blockers,
            warnings=warnings,
            redacted_target_display=redacted,
            bytes_read=bytes_read,
            payload_hash=payload_hash,
            non_action_flags=(
                OptionalSolverPluginManifestReloadFileReaderNonActionFlags()
            ),
            action_states=_action_states(),
            safe_mapping=safe_mapping,
        )


def read_optional_solver_plugin_manifest_reload_file(
    target_path: str | Path | None,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    allow_symlink: bool = False,
    expected_payload_kind: str = STATE_WRITER_PAYLOAD_KIND,
    expected_schema_version: str = STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
    allow_migration: bool = False,
    allow_unredacted_paths: bool = False,
    allow_secret_like_values: bool = False,
    caller_context: str = "",
) -> OptionalSolverPluginManifestReloadFileReadResult:
    """Read one explicit local reload state file and return a reader result."""

    request = OptionalSolverPluginManifestReloadFileReadRequest(
        target_path=target_path,
        max_bytes=max_bytes,
        allow_symlink=allow_symlink,
        expected_payload_kind=expected_payload_kind,
        expected_schema_version=expected_schema_version,
        allow_migration=allow_migration,
        allow_unredacted_paths=allow_unredacted_paths,
        allow_secret_like_values=allow_secret_like_values,
        caller_context=caller_context,
    )
    return OptionalSolverPluginManifestReloadFileReader().read(request)


# ---------------------------------------------------------------------------
# Internal helpers (pure; no writes, no scans, no network, no imports of state).
# ---------------------------------------------------------------------------
def _read_file_bytes(
    request: OptionalSolverPluginManifestReloadFileReadRequest,
    redacted: str,
) -> tuple[OptionalSolverPluginManifestReloadFileReaderDiagnostic | None, bytes]:
    raw_target = str(request.target_path or "").strip()
    if not raw_target:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_FILE_MISSING,
                "Reader requires an explicit caller-supplied local file path.",
                blocker=True,
                suggested_fix="Pass an explicit target_path.",
            ),
            b"",
        )
    target = Path(raw_target)
    try:
        is_symlink = target.is_symlink()
        exists = target.exists()
    except OSError:
        return (_diag_missing(redacted), b"")

    if is_symlink and not request.allow_symlink:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_SYMLINK_BLOCKED,
                "Reader refuses symlink targets by default.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    if not exists:
        return (_diag_missing(redacted), b"")
    if target.is_dir():
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_NOT_REGULAR_FILE,
                "Reader refuses directory targets; a regular file is required.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    if not target.is_file():
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_NOT_REGULAR_FILE,
                "Reader refuses special files; a regular file is required.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    try:
        size = target.stat().st_size
    except OSError:
        return (_diag_missing(redacted), b"")
    if size == 0:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_EMPTY_FILE,
                "Reader refuses empty files.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    if size > request.max_bytes:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_FILE_TOO_LARGE,
                f"Reader refuses files larger than {request.max_bytes} bytes.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    try:
        with target.open("rb") as handle:
            raw = handle.read(request.max_bytes + 1)
    except OSError:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_ENCODING_ERROR,
                "Reader could not read the target file.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    if len(raw) > request.max_bytes:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_FILE_TOO_LARGE,
                f"Reader refuses files larger than {request.max_bytes} bytes.",
                blocker=True,
                related=redacted,
            ),
            b"",
        )
    return (None, raw)


def _parse_payload(
    raw: bytes,
    redacted: str,
) -> tuple[
    OptionalSolverPluginManifestReloadFileReaderDiagnostic | None,
    dict[str, object] | None,
    str,
]:
    body = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
    payload_hash = hashlib.sha256(body).hexdigest()
    if b"\x00" in body:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_ENCODING_ERROR,
                "Reader refuses binary-looking content (NUL byte present).",
                blocker=True,
                related=redacted,
            ),
            None,
            payload_hash,
        )
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_ENCODING_ERROR,
                "Reader requires UTF-8 encoded text.",
                blocker=True,
                related=redacted,
            ),
            None,
            payload_hash,
        )
    tracker = _DuplicateKeyTracker()
    try:
        data = json.loads(text, object_pairs_hook=tracker)
    except (json.JSONDecodeError, ValueError, RecursionError):
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_JSON_PARSE_ERROR,
                "Reader could not parse the file as JSON.",
                blocker=True,
                related=redacted,
            ),
            None,
            payload_hash,
        )
    if tracker.duplicates:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED,
                "Reader refuses payloads containing duplicate JSON keys.",
                blocker=True,
                related=redacted,
            ),
            None,
            payload_hash,
        )
    if not isinstance(data, dict):
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_ROOT_NOT_OBJECT,
                "Reader requires a JSON object root.",
                blocker=True,
                related=redacted,
            ),
            None,
            payload_hash,
        )
    return (None, data, payload_hash)


def _validate_payload(
    payload: Mapping[str, object],
    request: OptionalSolverPluginManifestReloadFileReadRequest,
    redacted: str,
) -> tuple[OptionalSolverPluginManifestReloadFileReaderDiagnostic, ...]:
    diagnostics: list[OptionalSolverPluginManifestReloadFileReaderDiagnostic] = []

    kind = str(payload.get("payload_kind", ""))
    if kind != request.expected_payload_kind:
        diagnostics.append(
            _diag(
                "error",
                OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH,
                "Payload kind does not match the expected state-writer family.",
                blocker=True,
                related=redacted,
            )
        )

    diagnostics.extend(_schema_diagnostics(payload, request, redacted))

    if not request.allow_secret_like_values and _contains_secret_like(payload):
        diagnostics.append(
            _diag(
                "error",
                OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED,
                "Payload contains secret-like values and is blocked.",
                blocker=True,
                related=redacted,
            )
        )
    if not request.allow_unredacted_paths and _contains_unredacted_path(payload):
        diagnostics.append(
            _diag(
                "error",
                OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED,
                "Payload contains an unredacted absolute path and is blocked.",
                blocker=True,
                related=redacted,
                suggested_fix="Redact raw paths to basenames before reload review.",
            )
        )
    if _contains_unsafe_claim(payload):
        diagnostics.append(
            _diag(
                "error",
                OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED,
                "Payload asserts an unsafe action/claim; blocked and not trusted.",
                blocker=True,
                related=redacted,
            )
        )
    if _has_stale_source(payload):
        diagnostics.append(
            _diag(
                "warning",
                OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED,
                "A stale source requires re-preview; not validation failure.",
                blocker=True,
                related=redacted,
            )
        )
    if _has_conflict(payload):
        diagnostics.append(
            _diag(
                "warning",
                OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED,
                "A conflict/shared stack requires review; built-ins win by default.",
                blocker=True,
                related=redacted,
            )
        )
    if _has_expired_acknowledgement(payload):
        diagnostics.append(
            _diag(
                "warning",
                OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED,
                "A persisted acknowledgement is expired and must be re-shown.",
                related=redacted,
            )
        )
    if _truthy_sequence(payload.get("evidence_history")):
        diagnostics.append(
            _diag(
                "info",
                OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY,
                "Evidence/history retained as reference only; not fresh evidence.",
                related=redacted,
            )
        )
    diagnostics.append(
        _diag(
            "info",
            OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY,
            "Loaded state is not ProjectSchema state; no ProjectSchema mutation.",
        )
    )
    diagnostics.append(
        _diag(
            "info",
            OSPMG_RELOAD_READER_REVIEW_ONLY,
            "Reader output is review-only; user/plugin files remain untrusted.",
        )
    )
    return tuple(diagnostics)


def _schema_diagnostics(
    payload: Mapping[str, object],
    request: OptionalSolverPluginManifestReloadFileReadRequest,
    redacted: str,
) -> tuple[OptionalSolverPluginManifestReloadFileReaderDiagnostic, ...]:
    version = str(payload.get("payload_schema_version", ""))
    self_declares_migration = any(
        bool(row.get("migration_required"))
        for row in _rows(payload.get("schema_migration"))
    )
    if not version:
        return (
            _diag(
                "error",
                OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED,
                "Payload is missing a schema version and is unsupported.",
                blocker=True,
                related=redacted,
            ),
        )
    if version == request.expected_schema_version:
        if self_declares_migration:
            return (
                _diag(
                    "warning",
                    OSPMG_RELOAD_READER_MIGRATION_REQUIRED,
                    "Payload requires migration before reuse; migration is future-gated.",
                    blocker=True,
                    related=redacted,
                ),
            )
        return ()
    if version in MIGRATABLE_PAYLOAD_SCHEMA_VERSIONS:
        return (
            _diag(
                "warning",
                OSPMG_RELOAD_READER_MIGRATION_REQUIRED,
                "Payload schema requires a future migration gate.",
                blocker=True,
                related=redacted,
            ),
        )
    return (
        _diag(
            "error",
            OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED,
            "Payload schema version is unsupported.",
            blocker=True,
            related=redacted,
        ),
    )


def _payload_metadata(
    payload: Mapping[str, object],
) -> OptionalSolverPluginManifestReloadFileReaderPayloadMetadata:
    header = payload.get("header")
    header_map = header if isinstance(header, Mapping) else {}
    return OptionalSolverPluginManifestReloadFileReaderPayloadMetadata(
        payload_kind=str(payload.get("payload_kind", "")),
        payload_schema_version=str(payload.get("payload_schema_version", "")),
        writer_version=str(payload.get("writer_version", "")),
        view_model_schema_version=str(
            header_map.get("view_model_schema_version", "")
        ),
        state_scope=str(payload.get("state_scope", "")),
        generated_by=str(payload.get("generated_by", "")),
        source_count=len(_rows(payload.get("sources"))),
        candidate_count=len(_rows(payload.get("candidates"))),
        acknowledgement_count=len(_rows(payload.get("acknowledgements"))),
        diagnostic_count=len(_rows(payload.get("diagnostics"))),
    )


def _action_states() -> tuple[
    OptionalSolverPluginManifestReloadFileReaderActionState, ...
]:
    return tuple(
        OptionalSolverPluginManifestReloadFileReaderActionState(
            action=action, enabled=False, reason=reason
        )
        for action, reason in _DISABLED_FUTURE_ACTIONS
    )


class _DuplicateKeyTracker:
    """object_pairs_hook that records duplicate keys without mutating input."""

    __slots__ = ("duplicates",)

    def __init__(self) -> None:
        self.duplicates: list[str] = []

    def __call__(self, pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
        seen: dict[str, object] = {}
        for key, value in pairs:
            if key in seen:
                self.duplicates.append(key)
            seen[key] = value
        return seen


def _redact_path(target_path: object) -> str:
    raw = str(target_path or "").strip()
    if not raw:
        return "<no target>"
    name = Path(raw).name
    return name or "<target>"


def _diag_missing(
    redacted: str,
) -> OptionalSolverPluginManifestReloadFileReaderDiagnostic:
    return _diag(
        "error",
        OSPMG_RELOAD_READER_FILE_MISSING,
        "Reader could not find the explicit target file.",
        blocker=True,
        related=redacted,
    )


def _diag(
    severity: str,
    code: str,
    message: str,
    *,
    blocker: bool = False,
    related: str = "",
    suggested_fix: str = "",
) -> OptionalSolverPluginManifestReloadFileReaderDiagnostic:
    return OptionalSolverPluginManifestReloadFileReaderDiagnostic(
        severity=severity,
        code=code,
        message=message,
        blocker=blocker,
        related=related,
        suggested_fix=suggested_fix,
    )


def _unreadable_result(
    redacted: str,
    target_redacted: bool,
    diagnostics: tuple[OptionalSolverPluginManifestReloadFileReaderDiagnostic, ...],
    bytes_read: int,
    payload_hash: str,
) -> OptionalSolverPluginManifestReloadFileReadResult:
    blockers = tuple(d.code for d in diagnostics if d.blocker)
    warnings = tuple(d.code for d in diagnostics if d.severity == "warning")
    summary = OptionalSolverPluginManifestReloadFileReaderSummary(
        status=OptionalSolverPluginManifestReloadFileReaderStatus.UNREADABLE.value,
        target_reference_display=redacted,
        target_reference_redacted=target_redacted,
        bytes_read=bytes_read,
        ready_for_viewmodel=False,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        diagnostic_count=len(diagnostics),
    )
    return OptionalSolverPluginManifestReloadFileReadResult(
        status=OptionalSolverPluginManifestReloadFileReaderStatus.UNREADABLE,
        summary=summary,
        payload_metadata=(
            OptionalSolverPluginManifestReloadFileReaderPayloadMetadata()
        ),
        diagnostics=diagnostics,
        blockers=blockers,
        warnings=warnings,
        redacted_target_display=redacted,
        bytes_read=bytes_read,
        payload_hash=payload_hash,
        non_action_flags=(
            OptionalSolverPluginManifestReloadFileReaderNonActionFlags()
        ),
        action_states=_action_states(),
        safe_mapping=None,
    )


def _rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [item for item in value if isinstance(item, Mapping)]
    if isinstance(value, Mapping):
        return [value]
    return []


def _truthy_sequence(value: object) -> bool:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return len(value) > 0
    return bool(value) if isinstance(value, Mapping) else False


def _iter_strings(value: object):
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, str):
        yield value


def _contains_secret_like(payload: Mapping[str, object]) -> bool:
    for text in _iter_strings(payload):
        lowered = text.lower()
        if any(marker in lowered for marker in _SECRET_MARKERS):
            return True
    return False


def _contains_unredacted_path(payload: Mapping[str, object]) -> bool:
    for row in _rows(payload.get("redaction_privacy")):
        if row.get("unredacted_path_blocked") or row.get("secret_like_content_blocked"):
            return True
    for row in _rows(payload.get("sources")):
        if row.get("raw_reference_blocked"):
            return True
    for text in _iter_strings(payload):
        if _UNREDACTED_PATH_PATTERN.search(text):
            return True
    return False


def _contains_unsafe_claim(payload: Mapping[str, object]) -> bool:
    if _truthy_sequence(payload.get("unsafe_claims")):
        return True
    flags = payload.get("non_action_flags")
    if isinstance(flags, Mapping) and any(bool(value) for value in flags.values()):
        return True
    for key in (
        "validation_success_claimed",
        "validation_failure_claimed",
        "issue_closure_claimed",
        "certification_claimed",
    ):
        if bool(payload.get(key)):
            return True
    return False


def _has_stale_source(payload: Mapping[str, object]) -> bool:
    if _truthy_sequence(payload.get("stale_sources")):
        return True
    for row in _rows(payload.get("sources")):
        if row.get("repreview_required") or str(row.get("stale_source_state", "")):
            return True
    return False


def _has_conflict(payload: Mapping[str, object]) -> bool:
    return _truthy_sequence(payload.get("conflicts"))


def _has_expired_acknowledgement(payload: Mapping[str, object]) -> bool:
    for row in _rows(payload.get("acknowledgements")):
        if row.get("expired") or row.get("acknowledgement_expired"):
            return True
    return False


__all__ = [
    "DEFAULT_MAX_BYTES",
    "MIGRATABLE_PAYLOAD_SCHEMA_VERSIONS",
    "OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED",
    "OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED",
    "OSPMG_RELOAD_READER_DIAGNOSTIC_CODES",
    "OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED",
    "OSPMG_RELOAD_READER_EMPTY_FILE",
    "OSPMG_RELOAD_READER_ENCODING_ERROR",
    "OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY",
    "OSPMG_RELOAD_READER_FILE_MISSING",
    "OSPMG_RELOAD_READER_FILE_TOO_LARGE",
    "OSPMG_RELOAD_READER_JSON_PARSE_ERROR",
    "OSPMG_RELOAD_READER_MIGRATION_REQUIRED",
    "OSPMG_RELOAD_READER_NOT_REGULAR_FILE",
    "OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH",
    "OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY",
    "OSPMG_RELOAD_READER_READ_COMPLETED",
    "OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL",
    "OSPMG_RELOAD_READER_REVIEW_ONLY",
    "OSPMG_RELOAD_READER_ROOT_NOT_OBJECT",
    "OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED",
    "OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED",
    "OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_RELOAD_READER_SYMLINK_BLOCKED",
    "OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED",
    "OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED",
    "READER_VERSION",
    "OptionalSolverPluginManifestReloadFileReadRequest",
    "OptionalSolverPluginManifestReloadFileReadResult",
    "OptionalSolverPluginManifestReloadFileReader",
    "OptionalSolverPluginManifestReloadFileReaderActionState",
    "OptionalSolverPluginManifestReloadFileReaderDiagnostic",
    "OptionalSolverPluginManifestReloadFileReaderNonActionFlags",
    "OptionalSolverPluginManifestReloadFileReaderPayloadMetadata",
    "OptionalSolverPluginManifestReloadFileReaderStatus",
    "OptionalSolverPluginManifestReloadFileReaderSummary",
    "read_optional_solver_plugin_manifest_reload_file",
]
