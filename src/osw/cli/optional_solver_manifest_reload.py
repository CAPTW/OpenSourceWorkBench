"""Stdout-first CLI for optional solver plugin manifest reload review."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_reload_file_reader import (
    DEFAULT_MAX_BYTES,
    OptionalSolverPluginManifestReloadFileReader,
    OptionalSolverPluginManifestReloadFileReadRequest,
    OptionalSolverPluginManifestReloadFileReadResult,
)
from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
    OSPMG_RELOAD_DIAGNOSTIC_CODES,
    OSPMG_RELOAD_FUTURE_GATE,
    OSPMG_RELOAD_NO_DISCOVERY_EXECUTION,
    OSPMG_RELOAD_NO_PLUGIN_IMPORT,
    OSPMG_RELOAD_NO_SOLVER_EXECUTION,
    OSPMG_RELOAD_NO_VALIDATION_EXECUTION,
    OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_RELOAD_NOT_TRUST_RESTORE,
    OSPMG_RELOAD_NOT_VALIDATION,
    OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED,
    RELOAD_ACK_EXPIRY_REASONS,
    RELOAD_REQUIRED_ACKS,
    OptionalSolverPluginManifestReloadViewModel,
)

OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND = (
    "optional-solver-plugin-manifest-reload"
)

OSPMG_RELOAD_CLI_REVIEW_ONLY = "OSPMG_RELOAD_CLI_REVIEW_ONLY"
OSPMG_RELOAD_CLI_STDOUT_ONLY = "OSPMG_RELOAD_CLI_STDOUT_ONLY"
OSPMG_RELOAD_CLI_FILE_READER_DISABLED = (
    "OSPMG_RELOAD_CLI_FILE_READER_DISABLED"
)
OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED = (
    "OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED"
)
OSPMG_RELOAD_CLI_DEFAULT_PATH_DISABLED = (
    "OSPMG_RELOAD_CLI_DEFAULT_PATH_DISABLED"
)
OSPMG_RELOAD_CLI_BACKGROUND_RELOAD_DISABLED = (
    "OSPMG_RELOAD_CLI_BACKGROUND_RELOAD_DISABLED"
)
OSPMG_RELOAD_CLI_NOT_VALIDATION = "OSPMG_RELOAD_CLI_NOT_VALIDATION"
OSPMG_RELOAD_CLI_NOT_VALIDATION_FAILURE = (
    "OSPMG_RELOAD_CLI_NOT_VALIDATION_FAILURE"
)
OSPMG_RELOAD_CLI_NOT_TRUST_RESTORE = "OSPMG_RELOAD_CLI_NOT_TRUST_RESTORE"
OSPMG_RELOAD_CLI_NOT_AUTOMATIC_ACTIVATION = (
    "OSPMG_RELOAD_CLI_NOT_AUTOMATIC_ACTIVATION"
)
OSPMG_RELOAD_CLI_NOT_ISSUE_CLOSURE = "OSPMG_RELOAD_CLI_NOT_ISSUE_CLOSURE"
OSPMG_RELOAD_CLI_NOT_RELEASE_MUTATION = (
    "OSPMG_RELOAD_CLI_NOT_RELEASE_MUTATION"
)
OSPMG_RELOAD_CLI_NOT_CERTIFICATION = "OSPMG_RELOAD_CLI_NOT_CERTIFICATION"
OSPMG_RELOAD_CLI_RELOAD_BUNDLE_DISABLED = (
    "OSPMG_RELOAD_CLI_RELOAD_BUNDLE_DISABLED"
)
OSPMG_RELOAD_CLI_EXPORT_FILE_DISABLED = "OSPMG_RELOAD_CLI_EXPORT_FILE_DISABLED"
OSPMG_RELOAD_CLI_REPORT_FILE_DISABLED = "OSPMG_RELOAD_CLI_REPORT_FILE_DISABLED"
OSPMG_RELOAD_CLI_CLIPBOARD_DISABLED = "OSPMG_RELOAD_CLI_CLIPBOARD_DISABLED"
OSPMG_RELOAD_CLI_REPORT_ATTACHMENT_DISABLED = (
    "OSPMG_RELOAD_CLI_REPORT_ATTACHMENT_DISABLED"
)
OSPMG_RELOAD_CLI_OPEN_OUTPUT_FOLDER_DISABLED = (
    "OSPMG_RELOAD_CLI_OPEN_OUTPUT_FOLDER_DISABLED"
)
OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION = (
    "OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION"
)
OSPMG_RELOAD_CLI_NO_PASSIVE_REFRESH = "OSPMG_RELOAD_CLI_NO_PASSIVE_REFRESH"
OSPMG_RELOAD_CLI_NO_PLUGIN_IMPORT = "OSPMG_RELOAD_CLI_NO_PLUGIN_IMPORT"
OSPMG_RELOAD_CLI_NO_DIRECTORY_SCAN = "OSPMG_RELOAD_CLI_NO_DIRECTORY_SCAN"
OSPMG_RELOAD_CLI_NO_NETWORK_FETCH = "OSPMG_RELOAD_CLI_NO_NETWORK_FETCH"
OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION = (
    "OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION"
)
OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION = (
    "OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION"
)
OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED = (
    "OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED"
)
OSPMG_RELOAD_CLI_FUTURE_GATE = "OSPMG_RELOAD_CLI_FUTURE_GATE"
OSPMG_RELOAD_CLI_EXPLICIT_PATH_READER_ENABLED = (
    "OSPMG_RELOAD_CLI_EXPLICIT_PATH_READER_ENABLED"
)
OSPMG_RELOAD_CLI_READER_BLOCKED = "OSPMG_RELOAD_CLI_READER_BLOCKED"
OSPMG_RELOAD_CLI_READY_FOR_VIEWMODEL_PREVIEW = (
    "OSPMG_RELOAD_CLI_READY_FOR_VIEWMODEL_PREVIEW"
)
OSPMG_RELOAD_CLI_READER_DIAGNOSTICS_ONLY = (
    "OSPMG_RELOAD_CLI_READER_DIAGNOSTICS_ONLY"
)
OSPMG_RELOAD_CLI_VIEWMODEL_PREVIEW_ONLY = (
    "OSPMG_RELOAD_CLI_VIEWMODEL_PREVIEW_ONLY"
)

OSPMG_RELOAD_CLI_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_RELOAD_CLI_REVIEW_ONLY,
    OSPMG_RELOAD_CLI_STDOUT_ONLY,
    OSPMG_RELOAD_CLI_FILE_READER_DISABLED,
    OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED,
    OSPMG_RELOAD_CLI_DEFAULT_PATH_DISABLED,
    OSPMG_RELOAD_CLI_BACKGROUND_RELOAD_DISABLED,
    OSPMG_RELOAD_CLI_NOT_VALIDATION,
    OSPMG_RELOAD_CLI_NOT_VALIDATION_FAILURE,
    OSPMG_RELOAD_CLI_NOT_TRUST_RESTORE,
    OSPMG_RELOAD_CLI_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_RELOAD_CLI_NOT_ISSUE_CLOSURE,
    OSPMG_RELOAD_CLI_NOT_RELEASE_MUTATION,
    OSPMG_RELOAD_CLI_NOT_CERTIFICATION,
    OSPMG_RELOAD_CLI_RELOAD_BUNDLE_DISABLED,
    OSPMG_RELOAD_CLI_EXPORT_FILE_DISABLED,
    OSPMG_RELOAD_CLI_REPORT_FILE_DISABLED,
    OSPMG_RELOAD_CLI_CLIPBOARD_DISABLED,
    OSPMG_RELOAD_CLI_REPORT_ATTACHMENT_DISABLED,
    OSPMG_RELOAD_CLI_OPEN_OUTPUT_FOLDER_DISABLED,
    OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION,
    OSPMG_RELOAD_CLI_NO_PASSIVE_REFRESH,
    OSPMG_RELOAD_CLI_NO_PLUGIN_IMPORT,
    OSPMG_RELOAD_CLI_NO_DIRECTORY_SCAN,
    OSPMG_RELOAD_CLI_NO_NETWORK_FETCH,
    OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION,
    OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION,
    OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_RELOAD_CLI_FUTURE_GATE,
    OSPMG_RELOAD_CLI_EXPLICIT_PATH_READER_ENABLED,
    OSPMG_RELOAD_CLI_READER_BLOCKED,
    OSPMG_RELOAD_CLI_READY_FOR_VIEWMODEL_PREVIEW,
    OSPMG_RELOAD_CLI_READER_DIAGNOSTICS_ONLY,
    OSPMG_RELOAD_CLI_VIEWMODEL_PREVIEW_ONLY,
)

_RELOAD_SUBCOMMANDS = (
    "explain",
    "preview",
    "schema",
    "sources",
    "candidates",
    "acknowledgements",
    "diagnostics",
    "redaction",
    "stale-sources",
    "conflicts",
    "unsafe-claims",
    "evidence",
    "actions",
    "load-preview",
)

_STATE_SOURCE_FLAGS = ("sample_state", "empty_state", "unavailable_state")

_NON_ACTION_LINES = (
    "Reloaded manifest UX state is not validation evidence.",
    "Reloaded manifest UX state is not validation failure.",
    "Reloaded manifest UX state is not trust restoration.",
    "Reloaded manifest UX state is not automatic activation.",
    "Reloaded manifest UX state is not solver discovery success.",
    "Reloaded manifest UX state is not dependency installation.",
    "Reloaded manifest UX state is not solver execution.",
    "Reloaded manifest UX state is not issue closure.",
    "Reloaded manifest UX state is not release mutation.",
    "Reloaded manifest UX state is not certification.",
    "A trust label is not certification.",
    "User/plugin manifests remain untrusted by default.",
    "Built-ins are authoritative by default.",
    "No file reader/parser implementation.",
    "No persisted state file reading.",
    "No persisted state file parsing.",
    "No runtime reload behavior.",
    "No default reload path.",
    "No background reload.",
    "No reloadable bundle creation.",
    "No export file creation.",
    "No report file creation.",
    "No clipboard behavior.",
    "No report attachment.",
    "No open-output-folder behavior.",
    "No GUI behavior.",
    "No ProjectSchema mutation.",
    "No live discovery.",
    "No passive refresh.",
    "No plugin package import.",
    "No directory scan.",
    "No network fetch.",
    "No discovery execution.",
    "No validation execution.",
    "No solver execution.",
    "No dependency installation.",
    "No dependency uninstall.",
    "No solver uninstall.",
    "No automatic activation.",
    "No trust restoration.",
    "No issue mutation.",
    "No release mutation.",
    "No tag mutation.",
    "No asset mutation.",
    "No version bump.",
    "No validation-pass claim.",
    "No validation-fail claim.",
    "No issue-closure claim.",
    "No bundled-solver claim.",
    "No certification claim.",
)

_COMMAND_PURPOSE = {
    "explain": "Explain the reload CLI safety boundary.",
    "preview": "Render a stable stdout reload review preview.",
    "schema": "Render payload kind, schema, and migration review state.",
    "sources": "Render redacted source and provenance state.",
    "candidates": "Render candidate lifecycle and future-review state.",
    "acknowledgements": "Render reload acknowledgement and expiry state.",
    "diagnostics": "Render reload view-model and CLI diagnostics.",
    "redaction": "Render redaction and privacy review state.",
    "stale-sources": "Render stale-source and re-preview state.",
    "conflicts": "Render conflict and shared-stack state.",
    "unsafe-claims": "Render unsafe-claim blockers.",
    "evidence": "Render evidence and history retention state.",
    "actions": "Render disabled and future-only action states.",
    "load-preview": "Preview an explicit local reload state file for review.",
}

_LOAD_PREVIEW_NON_ACTION_LINES = (
    "Explicit path preview is review-only.",
    "Explicit path preview is not validation evidence.",
    "Explicit path preview is not validation failure.",
    "Explicit path preview is not trust restoration.",
    "Explicit path preview is not automatic activation.",
    "Explicit path preview is not solver discovery success.",
    "Explicit path preview is not dependency installation.",
    "Explicit path preview is not solver execution.",
    "Explicit path preview is not issue closure.",
    "Explicit path preview is not release mutation.",
    "Explicit path preview is not certification.",
    "User/plugin files remain untrusted by default.",
    "Built-ins are authoritative by default.",
    "A trust label is not certification.",
    "No default reload path.",
    "No background reload.",
    "No directory scan.",
    "No network fetch.",
    "No plugin package import.",
    "No GUI file dialog.",
    "No runtime reload acceptance.",
    "No reloadable bundle creation.",
    "No export file creation.",
    "No report file creation.",
    "No clipboard behavior.",
    "No report attachment.",
    "No open-output-folder behavior.",
    "No ProjectSchema mutation.",
    "No live discovery.",
    "No passive refresh.",
    "No validation execution.",
    "No solver execution.",
    "No dependency installation.",
    "No dependency uninstall.",
    "No solver uninstall.",
    "No automatic activation.",
    "No trust restoration.",
    "No issue mutation.",
    "No release mutation.",
    "No tag mutation.",
    "No asset mutation.",
    "No version bump.",
    "No validation-pass claim.",
    "No validation-fail claim.",
    "No issue-closure claim.",
    "No bundled-solver claim.",
    "No certification claim.",
)


def add_optional_solver_plugin_manifest_reload_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the stdout-only reload review CLI."""

    parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
        help="Review optional solver plugin manifest reload view-model state.",
        description=(
            "Review deterministic optional solver plugin manifest reload "
            "view-model state through stdout only. This command is review-only, "
            "redaction-first, non-reading, non-parsing, non-reloading, "
            "non-discovering, non-validating, non-executing, ProjectSchema-safe, "
            "and issue/release-safe."
        ),
    )
    parser.add_argument(
        "reload_command",
        choices=_RELOAD_SUBCOMMANDS,
        help="Reload review operation to perform.",
    )
    parser.add_argument(
        "--sample-state",
        action="store_true",
        help="Use deterministic in-memory sample state for tests and review.",
    )
    parser.add_argument(
        "--empty-state",
        action="store_true",
        help="Use deterministic empty/no-payload in-memory state.",
    )
    parser.add_argument(
        "--unavailable-state",
        action="store_true",
        help="Use deterministic unavailable state; this is also the default.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit deterministic JSON output.",
    )
    parser.add_argument(
        "--path",
        default="",
        help=(
            "Explicit local state-writer UX state file for load-preview. "
            "No default path is selected."
        ),
    )
    parser.add_argument(
        "--max-bytes",
        type=_positive_int,
        default=None,
        help=(
            "Maximum bytes the explicit-path reader may read. Defaults to the "
            f"reader limit ({DEFAULT_MAX_BYTES})."
        ),
    )
    parser.add_argument(
        "--allow-symlink",
        action="store_true",
        help="Allow symlink target files for explicit load-preview paths.",
    )
    parser.add_argument(
        "--allow-migration",
        action="store_true",
        help="Allow migratable payload schemas to proceed through the reader.",
    )
    parser.add_argument(
        "--allow-unredacted-paths",
        action="store_true",
        help="Allow unredacted paths in payloads; blocked by default.",
    )
    parser.add_argument(
        "--allow-secret-like-values",
        action="store_true",
        help="Allow secret-like payload values; blocked by default.",
    )
    parser.add_argument(
        "--reader-diagnostics-only",
        action="store_true",
        help="Render only the reader diagnostics section for load-preview --path.",
    )
    parser.add_argument(
        "--viewmodel-preview-only",
        action="store_true",
        help="Render view-model preview after reader success for load-preview --path.",
    )
    return parser


def run_optional_solver_plugin_manifest_reload_cli(args: argparse.Namespace) -> int:
    """Run a bounded reload CLI review operation."""

    explicit_path_error = _validate_explicit_path_options(args)
    if explicit_path_error:
        _emit(
            {"error": explicit_path_error, "subcommand": args.reload_command},
            [explicit_path_error],
            args,
            error=True,
        )
        return 2

    state_source_error = _validate_state_source_flags(args)
    if state_source_error:
        _emit(
            {"error": state_source_error, "subcommand": args.reload_command},
            [state_source_error],
            args,
            error=True,
        )
        return 2

    if args.reload_command == "load-preview" and args.path:
        return _run_load_preview_path(args)

    view_model, source_label = _view_model_from_args(args)
    payload = _payload(args, view_model, source_label)
    text_lines = _text_lines(args, view_model, source_label)
    blocked = args.reload_command == "load-preview"
    _emit(payload, text_lines, args, error=blocked)
    return 2 if blocked else 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        msg = "--max-bytes must be a positive integer."
        raise argparse.ArgumentTypeError(msg)
    return parsed


def _validate_explicit_path_options(args: argparse.Namespace) -> str:
    path_options_used = any(
        (
            bool(args.path),
            args.max_bytes is not None,
            bool(args.allow_symlink),
            bool(args.allow_migration),
            bool(args.allow_unredacted_paths),
            bool(args.allow_secret_like_values),
            bool(args.reader_diagnostics_only),
            bool(args.viewmodel_preview_only),
        )
    )
    if path_options_used and args.reload_command != "load-preview":
        return "Explicit path options are only supported for load-preview."
    if args.reader_diagnostics_only and args.viewmodel_preview_only:
        return (
            "Select only one explicit-path output mode: "
            "--reader-diagnostics-only or --viewmodel-preview-only."
        )
    return ""


def _run_load_preview_path(args: argparse.Namespace) -> int:
    request = OptionalSolverPluginManifestReloadFileReadRequest(
        target_path=args.path,
        max_bytes=args.max_bytes or DEFAULT_MAX_BYTES,
        allow_symlink=bool(args.allow_symlink),
        allow_migration=bool(args.allow_migration),
        allow_unredacted_paths=bool(args.allow_unredacted_paths),
        allow_secret_like_values=bool(args.allow_secret_like_values),
        caller_context=(
            "osw.cli optional-solver-plugin-manifest-reload load-preview"
        ),
    )
    try:
        reader_result = OptionalSolverPluginManifestReloadFileReader().read(request)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        payload = _load_preview_internal_error_payload(type(exc).__name__)
        lines = _load_preview_internal_error_lines(type(exc).__name__)
        _emit(payload, lines, args, error=True)
        return 1

    reader_blocked = not (
        reader_result.ready_for_viewmodel and reader_result.safe_mapping is not None
    )
    if reader_blocked:
        payload = _load_preview_payload(args, reader_result, None, status="blocked")
        lines = _load_preview_lines(args, reader_result, None)
        _emit(payload, lines, args, error=True)
        return 2

    if args.reader_diagnostics_only:
        payload = _load_preview_payload(
            args,
            reader_result,
            None,
            status="reader_diagnostics_ready",
        )
        lines = _load_preview_lines(args, reader_result, None)
        _emit(payload, lines, args, error=False)
        return 0

    view_model = OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(
        reader_result.safe_mapping,
        source_label=reader_result.redacted_target_display,
    )
    payload = _load_preview_payload(args, reader_result, view_model, status="ready")
    lines = _load_preview_lines(args, reader_result, view_model)
    _emit(payload, lines, args, error=False)
    return 0


def _validate_state_source_flags(args: argparse.Namespace) -> str:
    selected = [bool(getattr(args, flag, False)) for flag in _STATE_SOURCE_FLAGS]
    if sum(1 for value in selected if value) > 1:
        return (
            "Select only one state source: --sample-state, --empty-state, or "
            "--unavailable-state."
        )
    return ""


def _view_model_from_args(
    args: argparse.Namespace,
) -> tuple[OptionalSolverPluginManifestReloadViewModel, str]:
    if args.sample_state:
        return (
            OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review(),
            "deterministic sample in-memory state",
        )
    if args.empty_state:
        return (
            OptionalSolverPluginManifestReloadViewModel.empty(),
            "deterministic empty in-memory state",
        )
    return (
        OptionalSolverPluginManifestReloadViewModel.unavailable(),
        "unavailable in-memory state; live source integration is future-gated",
    )


def _payload(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadViewModel,
    source_label: str,
) -> dict[str, object]:
    return {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
        "subcommand": args.reload_command,
        "purpose": _COMMAND_PURPOSE[args.reload_command],
        "state_source": source_label,
        "state_source_policy": {
            "deterministic_in_memory_only": True,
            "file_reader_performed": False,
            "file_parser_performed": False,
            "default_reload_path_used": False,
            "runtime_reload_performed": False,
            "background_reload_performed": False,
            "live_discovery_performed": False,
            "passive_refresh_performed": False,
            "plugin_package_import_performed": False,
            "directory_scan_performed": False,
            "network_fetch_performed": False,
            "validation_execution_performed": False,
            "solver_execution_performed": False,
        },
        "output_mode": "json" if args.json else "text",
        "stdout_first": True,
        "file_reader_enabled": False,
        "file_parser_enabled": False,
        "load_preview_enabled": False,
        "load_preview_blocked": args.reload_command == "load-preview",
        "view_model": view_model.to_mapping(),
        "selected": _selected_payload(args.reload_command, view_model),
        "cli_diagnostics": list(OSPMG_RELOAD_CLI_DIAGNOSTIC_CODES),
        "model_diagnostics": list(OSPMG_RELOAD_DIAGNOSTIC_CODES),
        "required_acknowledgements": list(RELOAD_REQUIRED_ACKS),
        "acknowledgement_expiry_reasons": list(RELOAD_ACK_EXPIRY_REASONS),
        "non_actions": list(_NON_ACTION_LINES),
    }


def _load_preview_payload(
    args: argparse.Namespace,
    reader_result: OptionalSolverPluginManifestReloadFileReadResult,
    view_model: OptionalSolverPluginManifestReloadViewModel | None,
    *,
    status: str,
) -> dict[str, object]:
    exit_code = 2 if status == "blocked" else 0
    return {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
        "subcommand": "load-preview",
        "purpose": _COMMAND_PURPOSE["load-preview"],
        "status": status,
        "output_mode": "json" if args.json else "text",
        "stdout_first": True,
        "reader": _reader_result_payload(reader_result),
        "viewmodel": view_model.to_mapping() if view_model is not None else None,
        "viewmodel_preview_rendered": view_model is not None,
        "reader_diagnostics_rendered_first": True,
        "reader_diagnostics_only": bool(args.reader_diagnostics_only),
        "viewmodel_preview_only": bool(args.viewmodel_preview_only),
        "state_source_policy": {
            "explicit_path_required": True,
            "explicit_path_reader_performed": True,
            "default_reload_path_used": False,
            "background_reload_performed": False,
            "directory_scan_performed": False,
            "network_fetch_performed": False,
            "plugin_package_import_performed": False,
            "gui_file_dialog_performed": False,
            "runtime_reload_acceptance_performed": False,
            "project_schema_mutation_performed": False,
            "live_discovery_performed": False,
            "passive_refresh_performed": False,
            "validation_execution_performed": False,
            "solver_execution_performed": False,
        },
        "reader_request_policy": {
            "max_bytes": args.max_bytes or DEFAULT_MAX_BYTES,
            "allow_symlink": bool(args.allow_symlink),
            "allow_migration": bool(args.allow_migration),
            "allow_unredacted_paths": bool(args.allow_unredacted_paths),
            "allow_secret_like_values": bool(args.allow_secret_like_values),
        },
        "cli_diagnostics": _load_preview_cli_diagnostics(status, args),
        "model_diagnostics": list(OSPMG_RELOAD_DIAGNOSTIC_CODES),
        "required_acknowledgements": list(RELOAD_REQUIRED_ACKS),
        "acknowledgement_expiry_reasons": list(RELOAD_ACK_EXPIRY_REASONS),
        "non_action_flags": {
            "validation_success_claimed": False,
            "validation_failure_claimed": False,
            "trust_restoration_performed": False,
            "automatic_activation_performed": False,
            "issue_closure_claimed": False,
            "release_mutation_performed": False,
            "certification_claimed": False,
            "project_schema_mutation_performed": False,
            "discovery_execution_performed": False,
            "validation_execution_performed": False,
            "solver_execution_performed": False,
        },
        "non_actions": list(_LOAD_PREVIEW_NON_ACTION_LINES),
        "exit_semantics": {
            "code": exit_code,
            "meaning": (
                "reader diagnostics blocked view-model preview"
                if exit_code == 2
                else "command completion only"
            ),
            "validation_success": False,
            "validation_failure": False,
            "issue_closure": False,
            "release_state": False,
            "activation": False,
            "trust_restoration": False,
            "certification": False,
        },
    }


def _load_preview_internal_error_payload(error_type: str) -> dict[str, object]:
    return {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
        "subcommand": "load-preview",
        "status": "internal_error",
        "error_type": error_type,
        "exit_semantics": {
            "code": 1,
            "validation_success": False,
            "validation_failure": False,
            "issue_closure": False,
            "release_state": False,
            "activation": False,
            "trust_restoration": False,
            "certification": False,
        },
    }


def _reader_result_payload(
    result: OptionalSolverPluginManifestReloadFileReadResult,
) -> dict[str, object]:
    metadata = result.payload_metadata
    summary = result.summary
    return {
        "status": result.status.value,
        "summary": {
            "status": summary.status,
            "target_reference_display": summary.target_reference_display,
            "target_reference_redacted": summary.target_reference_redacted,
            "bytes_read": summary.bytes_read,
            "ready_for_viewmodel": summary.ready_for_viewmodel,
            "blocker_count": summary.blocker_count,
            "warning_count": summary.warning_count,
            "diagnostic_count": summary.diagnostic_count,
            "review_only": summary.review_only,
            "not_validation_evidence": summary.not_validation_evidence,
            "not_trust_restoration": summary.not_trust_restoration,
            "not_automatic_activation": summary.not_automatic_activation,
        },
        "redacted_target_display": result.redacted_target_display,
        "bytes_read": result.bytes_read,
        "payload_hash": result.payload_hash,
        "payload_metadata": {
            "payload_kind": metadata.payload_kind,
            "payload_schema_version": metadata.payload_schema_version,
            "writer_version": metadata.writer_version,
            "view_model_schema_version": metadata.view_model_schema_version,
            "state_scope": metadata.state_scope,
            "generated_by": metadata.generated_by,
            "reader_version": metadata.reader_version,
            "source_count": metadata.source_count,
            "candidate_count": metadata.candidate_count,
            "acknowledgement_count": metadata.acknowledgement_count,
            "diagnostic_count": metadata.diagnostic_count,
            "untrusted_by_default": metadata.untrusted_by_default,
            "trust_label_is_certification": metadata.trust_label_is_certification,
            "fingerprint_is_trust_signal": metadata.fingerprint_is_trust_signal,
        },
        "diagnostics": [row.to_mapping() for row in result.diagnostics],
        "blockers": list(result.blockers),
        "warnings": list(result.warnings),
        "non_action_flags": result.non_action_flags.to_mapping(),
        "action_states": [
            {"action": row.action, "enabled": row.enabled, "reason": row.reason}
            for row in result.action_states
        ],
        "ready_for_viewmodel": result.ready_for_viewmodel,
        "safe_mapping_available": result.safe_mapping is not None,
        "no_validation_claim": result.no_validation_claim,
        "no_validation_failure_claim": result.no_validation_failure_claim,
        "no_trust_restoration": result.no_trust_restoration,
        "no_automatic_activation": result.no_automatic_activation,
        "no_discovery_execution": result.no_discovery_execution,
        "no_solver_execution": result.no_solver_execution,
        "no_issue_closure": result.no_issue_closure,
        "no_release_mutation": result.no_release_mutation,
        "no_certification": result.no_certification,
    }


def _load_preview_cli_diagnostics(
    status: str,
    args: argparse.Namespace,
) -> list[str]:
    diagnostics = [
        OSPMG_RELOAD_CLI_REVIEW_ONLY,
        OSPMG_RELOAD_CLI_STDOUT_ONLY,
        OSPMG_RELOAD_CLI_EXPLICIT_PATH_READER_ENABLED,
        OSPMG_RELOAD_CLI_DEFAULT_PATH_DISABLED,
        OSPMG_RELOAD_CLI_BACKGROUND_RELOAD_DISABLED,
        OSPMG_RELOAD_CLI_NOT_VALIDATION,
        OSPMG_RELOAD_CLI_NOT_VALIDATION_FAILURE,
        OSPMG_RELOAD_CLI_NOT_TRUST_RESTORE,
        OSPMG_RELOAD_CLI_NOT_AUTOMATIC_ACTIVATION,
        OSPMG_RELOAD_CLI_NOT_ISSUE_CLOSURE,
        OSPMG_RELOAD_CLI_NOT_RELEASE_MUTATION,
        OSPMG_RELOAD_CLI_NOT_CERTIFICATION,
        OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION,
        OSPMG_RELOAD_CLI_NO_PASSIVE_REFRESH,
        OSPMG_RELOAD_CLI_NO_PLUGIN_IMPORT,
        OSPMG_RELOAD_CLI_NO_DIRECTORY_SCAN,
        OSPMG_RELOAD_CLI_NO_NETWORK_FETCH,
        OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION,
        OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION,
        OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED,
    ]
    if status == "blocked":
        diagnostics.append(OSPMG_RELOAD_CLI_READER_BLOCKED)
    else:
        diagnostics.append(OSPMG_RELOAD_CLI_READY_FOR_VIEWMODEL_PREVIEW)
    if args.reader_diagnostics_only:
        diagnostics.append(OSPMG_RELOAD_CLI_READER_DIAGNOSTICS_ONLY)
    if args.viewmodel_preview_only:
        diagnostics.append(OSPMG_RELOAD_CLI_VIEWMODEL_PREVIEW_ONLY)
    return diagnostics


def _selected_payload(
    subcommand: str,
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> object:
    mapping = view_model.to_mapping()
    key_by_command = {
        "schema": "schema",
        "sources": "sources",
        "candidates": "candidates",
        "acknowledgements": "acknowledgements",
        "diagnostics": "diagnostics",
        "redaction": "redaction_privacy",
        "stale-sources": "stale_sources",
        "conflicts": "conflicts",
        "unsafe-claims": "unsafe_claims",
        "evidence": "evidence_history",
        "actions": "actions",
    }
    if subcommand in key_by_command:
        return mapping.get(key_by_command[subcommand], mapping)
    return mapping


def _text_lines(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadViewModel,
    source_label: str,
) -> list[str]:
    lines = _common_header(args, view_model, source_label)
    subcommand = args.reload_command
    if subcommand == "explain":
        lines.extend(_explain_lines())
    elif subcommand == "preview":
        lines.extend(_preview_lines(view_model))
    elif subcommand == "schema":
        lines.extend(_schema_lines(view_model))
    elif subcommand == "sources":
        lines.extend(_source_lines(view_model))
    elif subcommand == "candidates":
        lines.extend(_candidate_lines(view_model))
    elif subcommand == "acknowledgements":
        lines.extend(_acknowledgement_lines(view_model))
    elif subcommand == "diagnostics":
        lines.extend(_diagnostic_lines(view_model))
    elif subcommand == "redaction":
        lines.extend(_redaction_lines(view_model))
    elif subcommand == "stale-sources":
        lines.extend(_stale_source_lines(view_model))
    elif subcommand == "conflicts":
        lines.extend(_conflict_lines(view_model))
    elif subcommand == "unsafe-claims":
        lines.extend(_unsafe_claim_lines(view_model))
    elif subcommand == "evidence":
        lines.extend(_evidence_lines(view_model))
    elif subcommand == "actions":
        lines.extend(_action_lines(view_model))
    elif subcommand == "load-preview":
        lines.extend(_load_preview_disabled_lines())
    lines.extend(_safety_boundary_lines())
    return lines


def _load_preview_lines(
    args: argparse.Namespace,
    reader_result: OptionalSolverPluginManifestReloadFileReadResult,
    view_model: OptionalSolverPluginManifestReloadViewModel | None,
) -> list[str]:
    lines = [
        "Optional Solver Plugin Manifest Reload CLI",
        f"command: {OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND}",
        "subcommand: load-preview",
        f"purpose: {_COMMAND_PURPOSE['load-preview']}",
        "mode: explicit-path reader-first review",
        "output mode: stdout-first review",
        "Reader diagnostics:",
        f"- status: {reader_result.status.value}",
        f"- target: {reader_result.redacted_target_display}",
        f"- target redacted: {reader_result.summary.target_reference_redacted}",
        f"- bytes read: {reader_result.bytes_read}",
        f"- payload hash: {reader_result.payload_hash or '<none>'}",
        (
            "- payload kind: "
            f"{reader_result.payload_metadata.payload_kind or '<none>'}"
        ),
        (
            "- payload schema version: "
            f"{reader_result.payload_metadata.payload_schema_version or '<none>'}"
        ),
        f"- ready for view-model: {reader_result.ready_for_viewmodel}",
        f"- blockers: {len(reader_result.blockers)}",
        f"- warnings: {len(reader_result.warnings)}",
        "- review-only: yes",
        "- not validation evidence: yes",
        "- not validation failure: yes",
        "- not trust restoration: yes",
        "- not automatic activation: yes",
        "- not issue closure: yes",
        "- not release mutation: yes",
        "- not certification: yes",
    ]
    lines.extend(_reader_diagnostic_lines(reader_result))
    lines.extend(_reader_action_lines(reader_result))
    if reader_result.blockers:
        lines.append("Reader blocked view-model preview:")
        lines.extend(f"- {code}" for code in reader_result.blockers)
    elif args.reader_diagnostics_only:
        lines.append("View-model preview: skipped by --reader-diagnostics-only")
    elif view_model is None:
        lines.append("View-model preview: not rendered")
    else:
        lines.extend(_load_preview_viewmodel_lines(view_model))
    lines.extend(_load_preview_safety_lines(args, reader_result))
    lines.extend(_load_preview_exit_lines(reader_result, view_model))
    return lines


def _reader_diagnostic_lines(
    reader_result: OptionalSolverPluginManifestReloadFileReadResult,
) -> list[str]:
    lines = ["- diagnostics:"]
    if not reader_result.diagnostics:
        return [*lines, "  - none"]
    for row in reader_result.diagnostics:
        blocker = "blocker" if row.blocker else "review"
        related = f"; related={row.related}" if row.related else ""
        fix = f"; suggested_fix={row.suggested_fix}" if row.suggested_fix else ""
        lines.append(
            f"  - {row.severity}: {row.code}; {blocker}{related}{fix}; "
            f"{row.message}"
        )
    return lines


def _reader_action_lines(
    reader_result: OptionalSolverPluginManifestReloadFileReadResult,
) -> list[str]:
    lines = ["- reader action states:"]
    for row in reader_result.action_states:
        state = "enabled" if row.enabled else "disabled/future-only"
        lines.append(f"  - {row.action}: {state}; {row.reason}")
    return lines


def _load_preview_viewmodel_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    summary = view_model.summary
    lines = [
        "View-model preview:",
        f"- readiness: {summary.readiness.value}",
        f"- reload state: {summary.state.value}",
        f"- source/provenance rows: {len(view_model.source_rows)}",
        f"- schema/migration rows: {len(view_model.schema_rows)}",
        f"- candidate rows: {len(view_model.candidate_rows)}",
        f"- acknowledgement/expiry rows: {len(view_model.acknowledgement_rows)}",
        f"- redaction/privacy rows: {len(view_model.redaction_rows)}",
        f"- stale-source/re-preview rows: {len(view_model.stale_source_rows)}",
        f"- conflict/shared-stack rows: {len(view_model.conflict_rows)}",
        f"- unsafe-claim rows: {len(view_model.unsafe_claim_rows)}",
        f"- evidence/history rows: {len(view_model.evidence_rows)}",
        f"- diagnostics: {len(view_model.diagnostics)}",
        f"- disabled/future actions: {len(view_model.action_states)}",
        "- reload is validation evidence: "
        f"{summary.reload_is_validation_evidence}",
        "- reload is validation failure: "
        f"{summary.reload_is_validation_failure}",
        f"- reload restores trust: {summary.reload_restores_trust}",
        "- reload automatically activates: "
        f"{summary.reload_automatically_activates}",
        f"- reload runs discovery: {summary.reload_runs_discovery}",
        f"- reload runs validation: {summary.reload_runs_validation}",
        f"- reload executes solver: {summary.reload_executes_solver}",
        "- reload mutates ProjectSchema: "
        f"{summary.reload_mutates_project_schema}",
        f"- reload closes issue: {summary.reload_closes_issue}",
        f"- reload mutates release: {summary.reload_mutates_release}",
        f"- reload certifies manifest: {summary.reload_certifies_manifest}",
        "- view-model text:",
        *[f"  - {line}" for line in view_model.to_text_lines()],
    ]
    return lines


def _load_preview_safety_lines(
    args: argparse.Namespace,
    reader_result: OptionalSolverPluginManifestReloadFileReadResult,
) -> list[str]:
    status = "blocked" if reader_result.blockers else "ready"
    return [
        "Safety boundary:",
        *[f"- {line}" for line in _LOAD_PREVIEW_NON_ACTION_LINES],
        "CLI diagnostics surfaced:",
        *[f"- {code}" for code in _load_preview_cli_diagnostics(status, args)],
    ]


def _load_preview_exit_lines(
    reader_result: OptionalSolverPluginManifestReloadFileReadResult,
    view_model: OptionalSolverPluginManifestReloadViewModel | None,
) -> list[str]:
    blocked = view_model is None and not reader_result.ready_for_viewmodel
    code = 2 if blocked else 0
    meaning = (
        "reader diagnostic blocked view-model preview"
        if blocked
        else "command completion only"
    )
    return [
        "Exit semantics:",
        f"- code: {code}",
        f"- meaning: {meaning}",
        "- no exit code implies validation success.",
        "- no exit code implies validation failure.",
        "- no exit code implies issue closure.",
        "- no exit code implies release state.",
        "- no exit code implies activation, trust restoration, or certification.",
    ]


def _load_preview_internal_error_lines(error_type: str) -> list[str]:
    return [
        "Optional Solver Plugin Manifest Reload CLI",
        "subcommand: load-preview",
        "status: internal_error",
        f"error type: {error_type}",
        "No validation success or validation failure is implied.",
        "No issue closure, release mutation, activation, trust restoration, or "
        "certification is implied.",
    ]


def _common_header(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadViewModel,
    source_label: str,
) -> list[str]:
    summary = view_model.summary
    return [
        "Optional Solver Plugin Manifest Reload CLI",
        f"command: {OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND}",
        f"subcommand: {args.reload_command}",
        f"purpose: {_COMMAND_PURPOSE[args.reload_command]}",
        f"state source: {source_label}",
        "state source policy: deterministic in-memory only; no file reader; "
        "no file parser; no default reload path; no runtime reload; no live "
        "discovery; no passive refresh; no plugin package import; no "
        "directory scan; no network fetch; no validation execution; no solver "
        "execution",
        f"readiness: {summary.readiness.value}",
        f"reload state: {summary.state.value}",
        f"payload kind: {summary.payload_kind or '<none>'}",
        f"payload schema version: {summary.payload_schema_version or '<none>'}",
        "output mode: stdout-only review",
        "file reader: disabled",
        "file parser: disabled",
        "load preview: disabled/future-only",
        "trust/provenance: user/plugin manifests remain untrusted by default; "
        "built-ins are authoritative by default; trust label is not certification",
    ]


def _explain_lines() -> list[str]:
    return [
        "Definition:",
        "- The reload CLI is a stdout-first, review-only surface over supplied "
        "or deterministic in-memory reload view-model state.",
        "- It does not read persisted state files, parse JSON files, choose "
        "default paths, or perform runtime reload.",
        "- It does not run discovery, import plugin packages, validate optional "
        "solvers, execute solvers, install dependencies, close issues, mutate "
        "releases, or certify manifests.",
    ]


def _preview_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    summary = view_model.summary
    return [
        "Preview:",
        f"- sources: {summary.source_count}",
        f"- candidates: {summary.candidate_count}",
        f"- acknowledgements: {summary.acknowledgement_count}",
        f"- diagnostics: {summary.diagnostic_count}",
        f"- blockers: {summary.blocker_count}",
        f"- warnings: {summary.warning_count}",
        f"- redaction rows: {len(view_model.redaction_rows)}",
        f"- stale sources: {len(view_model.stale_source_rows)}",
        f"- conflicts: {len(view_model.conflict_rows)}",
        f"- unsafe claims: {len(view_model.unsafe_claim_rows)}",
        f"- evidence rows: {len(view_model.evidence_rows)}",
        *[f"- model line: {line}" for line in view_model.to_text_lines()],
    ]


def _schema_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Schema/migration:",
        "- Schema mismatch is not validation failure.",
        "- Reload schema is separate from ProjectSchema.",
    ]
    if not view_model.schema_rows:
        return [*lines, "- none"]
    for row in view_model.schema_rows:
        lines.append(
            "- "
            f"payload_kind={row.payload_kind or '<none>'}; "
            f"payload_schema_version={row.payload_schema_version or '<none>'}; "
            f"supported={row.supported_schema}; "
            f"migration_required={row.migration_required}; "
            f"blocker={row.blocker}"
        )
    return lines


def _source_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Sources/provenance:",
        "- User/plugin manifests remain untrusted by default.",
        "- Built-ins are authoritative by default.",
        "- A trust label is not certification.",
        "- Fingerprints are not trust signals.",
    ]
    if not view_model.source_rows:
        return [*lines, "- none"]
    for row in view_model.source_rows:
        lines.append(
            "- "
            f"{row.source_id}: type={row.source_type}; trust={row.trust_label}; "
            f"display={row.source_display or '<none>'}; "
            f"redacted={row.source_reference_redacted}; "
            f"provenance={row.provenance_label}; "
            f"built_in_authoritative={row.built_ins_authoritative_by_default}"
        )
    return lines


def _candidate_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Candidates:",
        "- Candidate rows do not imply automatic activation or trust restoration.",
        "- Future activation review remains separate from reload preview.",
        "- Future discovery refresh remains separate from reload preview.",
    ]
    if not view_model.candidate_rows:
        return [*lines, "- none"]
    for row in view_model.candidate_rows:
        lines.append(
            "- "
            f"{row.candidate_id}: {row.display_name}; "
            f"lifecycle={row.lifecycle_state}; review={row.reload_review_state}; "
            f"future_activation_review={row.requires_future_activation_review}; "
            f"future_discovery_refresh={row.requires_future_discovery_refresh}; "
            f"no_automatic_activation={row.no_automatic_activation}; "
            f"no_trust_restoration={row.no_trust_restoration}; "
            f"skipped_missing_remains_skipped_missing="
            f"{row.skipped_missing_remains_skipped_missing}"
        )
    return lines


def _acknowledgement_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Acknowledgements:",
        "- Missing or satisfied acknowledgements do not validate, reload, trust, "
        "activate, close issues, mutate releases, or certify anything.",
        f"- required acknowledgements: {', '.join(RELOAD_REQUIRED_ACKS)}",
        f"- expiry reasons: {', '.join(RELOAD_ACK_EXPIRY_REASONS)}",
    ]
    if not view_model.acknowledgement_rows:
        return [*lines, "- none"]
    for row in view_model.acknowledgement_rows:
        lines.append(
            "- "
            f"{row.acknowledgement_id}: required={row.required}; "
            f"satisfied={row.satisfied}; expired={row.expired}; "
            f"blocker={row.blocker}; "
            f"expires_on={', '.join(row.expiry_reasons)}"
        )
    return lines


def _diagnostic_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Diagnostics:",
        "- Diagnostics are review state, not validation success or validation failure.",
        "- CLI diagnostic codes:",
        *[f"  - {code}" for code in OSPMG_RELOAD_CLI_DIAGNOSTIC_CODES],
        "- View-model reserved diagnostic codes:",
        *[f"  - {code}" for code in OSPMG_RELOAD_DIAGNOSTIC_CODES],
        "- View-model diagnostic rows:",
    ]
    if not view_model.diagnostics:
        return [*lines, "  - none"]
    for row in view_model.diagnostics:
        lines.append(
            "  - "
            f"{row.severity}: {row.code}; blocker={row.blocker}; {row.message}"
        )
    return lines


def _redaction_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Redaction/privacy:",
        "- Raw absolute paths are hidden by default.",
        "- Secrets, tokens, credentials, environment variables, and API keys are "
        "blocked or redacted.",
        "- Fingerprints are not trust signals.",
        "- Redaction review precedes any future activation review.",
    ]
    if not view_model.redaction_rows:
        return [*lines, "- none"]
    for row in view_model.redaction_rows:
        lines.append(
            "- "
            f"redaction_required={row.redaction_required}; "
            f"review_required={row.redaction_review_required}; "
            f"raw_paths_hidden_by_default={row.raw_paths_hidden_by_default}; "
            f"unredacted_path_blocked={row.unredacted_path_blocked}; "
            f"secret_like_content_blocked={row.secret_like_content_blocked}"
        )
    return lines


def _stale_source_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Stale sources / re-preview:",
        "- Stale sources are not silently trusted.",
        "- No source file IO is performed.",
        "- Stale state is not validation failure.",
    ]
    if not view_model.stale_source_rows:
        return [*lines, "- none"]
    for row in view_model.stale_source_rows:
        lines.append(
            "- "
            f"{row.source_id}: state={row.stale_source_state}; "
            f"repreview_required={row.repreview_required}; "
            f"old_preview_not_silently_trusted="
            f"{row.old_preview_not_silently_trusted}; "
            f"no_source_file_io={row.no_source_file_io}"
        )
    return lines


def _conflict_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Conflicts/shared stacks:",
        "- Conflicts are visible.",
        "- Built-ins win by default.",
        "- Reload preview does not resolve conflicts or override built-ins.",
    ]
    if not view_model.conflict_rows:
        return [*lines, "- none"]
    for row in view_model.conflict_rows:
        lines.append(
            "- "
            f"{row.conflict_id}: candidate={row.candidate_id or '<none>'}; "
            f"type={row.conflict_type}; "
            f"built_ins_win_by_default={row.built_ins_win_by_default}; "
            f"shared_stack_warning_visible={row.shared_stack_warning_visible}; "
            f"reload_resolves_conflict={row.reload_resolves_conflict}; "
            f"blocker={row.blocker}"
        )
    return lines


def _unsafe_claim_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Unsafe claims:",
        "- Unsafe claims are visible and blocked.",
        "- Unsafe claims are not reloaded as truth.",
        "- Unsafe claims include validation success/failure, issue closure, "
        "release mutation, bundled solvers, solver execution, and certification.",
    ]
    if not view_model.unsafe_claim_rows:
        return [*lines, "- none"]
    for row in view_model.unsafe_claim_rows:
        lines.append(
            "- "
            f"{row.claim_id}: type={row.claim_type}; blocked={row.blocked}; "
            f"not_reloaded_as_truth={row.not_reloaded_as_truth}; "
            f"text={row.claim_text}"
        )
    return lines


def _evidence_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = [
        "Evidence/history:",
        "- Deactivation and reactivation history are retained.",
        "- Historical evidence is retained as reference only.",
        "- Skipped-missing remains skipped-missing.",
        "- Reload preview is not validation evidence.",
    ]
    if not view_model.evidence_rows:
        return [*lines, "- none"]
    for row in view_model.evidence_rows:
        lines.append(
            "- "
            f"{row.evidence_id}: candidate={row.candidate_id or '<none>'}; "
            f"type={row.evidence_type}; "
            f"deactivation_history_retained={row.deactivation_history_retained}; "
            f"reactivation_history_retained={row.reactivation_history_retained}; "
            f"historical_evidence_reference_only="
            f"{row.historical_evidence_reference_only}; "
            f"skipped_missing_remains_skipped_missing="
            f"{row.skipped_missing_remains_skipped_missing}; "
            f"issue_closure_implied={row.issue_closure_implied}"
        )
    return lines


def _action_lines(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> list[str]:
    lines = ["Actions:"]
    for row in view_model.action_states:
        state = "enabled" if row.enabled else "disabled/future-only"
        label = row.action.value.replace("_", " ")
        lines.append(
            "- "
            f"{label}: {state}; future_only={row.future_only}; reason={row.reason}"
        )
    lines.extend(
        (
            "- read reload file: disabled/future-only",
            "- parse reload file: disabled/future-only",
            "- runtime reload: disabled/future-only",
            "- restore trust: disabled/future-only",
            "- automatically activate candidates: disabled/future-only",
            "- create reloadable bundle: disabled/future-only",
            "- create export file: disabled/future-only",
            "- create report file: disabled/future-only",
            "- copy to clipboard: disabled/future-only",
            "- attach to report: disabled/future-only",
            "- open output folder: disabled/future-only",
            "- run discovery: disabled/future-only",
            "- run validation: disabled/future-only",
            "- execute solver: disabled/future-only",
            "- close issue: disabled/future-only",
            "- mutate release: disabled/future-only",
            "- claim validation success/failure: disabled/future-only",
            "- claim certification: disabled/future-only",
        )
    )
    return lines


def _load_preview_disabled_lines() -> list[str]:
    return [
        "load-preview: blocked",
        f"- {OSPMG_RELOAD_CLI_FILE_READER_DISABLED}",
        f"- {OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED}",
        f"- {OSPMG_RELOAD_CLI_DEFAULT_PATH_DISABLED}",
        f"- {OSPMG_RELOAD_CLI_FUTURE_GATE}",
        "- load-preview is future-only and reads no files, parses no files, "
        "chooses no default paths, performs no runtime reload, and returns 2 "
        "without implying validation failure.",
    ]


def _safety_boundary_lines() -> list[str]:
    return [
        "Safety boundary:",
        *[f"- {line}" for line in _NON_ACTION_LINES],
        "Diagnostics surfaced:",
        f"- {OSPMG_RELOAD_CLI_REVIEW_ONLY}",
        f"- {OSPMG_RELOAD_CLI_STDOUT_ONLY}",
        f"- {OSPMG_RELOAD_CLI_FILE_READER_DISABLED}",
        f"- {OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED}",
        f"- {OSPMG_RELOAD_CLI_NOT_VALIDATION}",
        f"- {OSPMG_RELOAD_CLI_NOT_VALIDATION_FAILURE}",
        f"- {OSPMG_RELOAD_CLI_NOT_TRUST_RESTORE}",
        f"- {OSPMG_RELOAD_CLI_NOT_AUTOMATIC_ACTIVATION}",
        f"- {OSPMG_RELOAD_CLI_NOT_ISSUE_CLOSURE}",
        f"- {OSPMG_RELOAD_CLI_NOT_RELEASE_MUTATION}",
        f"- {OSPMG_RELOAD_CLI_NOT_CERTIFICATION}",
        f"- {OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION}",
        f"- {OSPMG_RELOAD_CLI_NO_PLUGIN_IMPORT}",
        f"- {OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION}",
        f"- {OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION}",
        f"- {OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED}",
        "View-model diagnostics preserved:",
        f"- {OSPMG_RELOAD_NOT_VALIDATION}",
        f"- {OSPMG_RELOAD_NOT_TRUST_RESTORE}",
        f"- {OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION}",
        f"- {OSPMG_RELOAD_NO_DISCOVERY_EXECUTION}",
        f"- {OSPMG_RELOAD_NO_PLUGIN_IMPORT}",
        f"- {OSPMG_RELOAD_NO_VALIDATION_EXECUTION}",
        f"- {OSPMG_RELOAD_NO_SOLVER_EXECUTION}",
        f"- {OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED}",
        f"- {OSPMG_RELOAD_FUTURE_GATE}",
    ]


def _emit(
    payload: Mapping[str, object],
    text_lines: Sequence[str],
    args: argparse.Namespace,
    *,
    error: bool,
) -> None:
    stream = sys.stderr if error else sys.stdout
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
        return
    print("\n".join(text_lines), file=stream)


__all__ = [
    "OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND",
    "OSPMG_RELOAD_CLI_DIAGNOSTIC_CODES",
    "add_optional_solver_plugin_manifest_reload_parser",
    "run_optional_solver_plugin_manifest_reload_cli",
]
