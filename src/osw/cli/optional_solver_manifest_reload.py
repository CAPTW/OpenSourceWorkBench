"""Stdout-first CLI for optional solver plugin manifest reload review."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

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
    "load-preview": "Blocked future file reader/parser preview action.",
}


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
    return parser


def run_optional_solver_plugin_manifest_reload_cli(args: argparse.Namespace) -> int:
    """Run a bounded reload CLI review operation."""

    state_source_error = _validate_state_source_flags(args)
    if state_source_error:
        _emit(
            {"error": state_source_error, "subcommand": args.reload_command},
            [state_source_error],
            args,
            error=True,
        )
        return 2

    view_model, source_label = _view_model_from_args(args)
    payload = _payload(args, view_model, source_label)
    text_lines = _text_lines(args, view_model, source_label)
    blocked = args.reload_command == "load-preview"
    _emit(payload, text_lines, args, error=blocked)
    return 2 if blocked else 0


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
