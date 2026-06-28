"""Stdout-first CLI for optional solver plugin manifest export summaries."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_export_summary_viewmodel import (
    EXPORT_SUMMARY_REQUIRED_ACKS,
    OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES,
    OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION,
    OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT,
    OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION,
    OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE,
    OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE,
    OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION,
    OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE,
    OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE,
    OSPMG_EXPORT_SUMMARY_NOT_VALIDATION,
    OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED,
    OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM,
    OptionalSolverPluginManifestExportSummaryCandidateRow,
    OptionalSolverPluginManifestExportSummaryConflictRow,
    OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow,
    OptionalSolverPluginManifestExportSummaryLimitationRow,
    OptionalSolverPluginManifestExportSummarySourceRow,
    OptionalSolverPluginManifestExportSummaryStaleSourceRow,
    OptionalSolverPluginManifestExportSummaryUnsafeClaimRow,
    OptionalSolverPluginManifestExportSummaryViewModel,
)

OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND = (
    "optional-solver-plugin-manifest-export-summary"
)

OSPMG_EXPORT_SUMMARY_CLI_PREVIEW_ONLY = "OSPMG_EXPORT_SUMMARY_CLI_PREVIEW_ONLY"
OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY = "OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY"
OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED = (
    "OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED"
)
OSPMG_EXPORT_SUMMARY_CLI_RELOAD_BUNDLE_DISABLED = (
    "OSPMG_EXPORT_SUMMARY_CLI_RELOAD_BUNDLE_DISABLED"
)
OSPMG_EXPORT_SUMMARY_CLI_REPORT_ATTACHMENT_DISABLED = (
    "OSPMG_EXPORT_SUMMARY_CLI_REPORT_ATTACHMENT_DISABLED"
)
OSPMG_EXPORT_SUMMARY_CLI_CLIPBOARD_DISABLED = (
    "OSPMG_EXPORT_SUMMARY_CLI_CLIPBOARD_DISABLED"
)
OSPMG_EXPORT_SUMMARY_CLI_OPEN_OUTPUT_FOLDER_DISABLED = (
    "OSPMG_EXPORT_SUMMARY_CLI_OPEN_OUTPUT_FOLDER_DISABLED"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_VALIDATION = "OSPMG_EXPORT_SUMMARY_CLI_NOT_VALIDATION"
OSPMG_EXPORT_SUMMARY_CLI_NOT_PERSISTENCE = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_PERSISTENCE"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_RELOADABLE_BUNDLE = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_RELOADABLE_BUNDLE"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_TRUST_RESTORE = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_TRUST_RESTORE"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_AUTOMATIC_ACTIVATION = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_AUTOMATIC_ACTIVATION"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_ISSUE_CLOSURE = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_ISSUE_CLOSURE"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_RELEASE_MUTATION = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_RELEASE_MUTATION"
)
OSPMG_EXPORT_SUMMARY_CLI_NOT_CERTIFICATION = (
    "OSPMG_EXPORT_SUMMARY_CLI_NOT_CERTIFICATION"
)
OSPMG_EXPORT_SUMMARY_CLI_REDACTION_REQUIRED = (
    "OSPMG_EXPORT_SUMMARY_CLI_REDACTION_REQUIRED"
)
OSPMG_EXPORT_SUMMARY_CLI_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_EXPORT_SUMMARY_CLI_UNREDACTED_PATH_BLOCKED"
)
OSPMG_EXPORT_SUMMARY_CLI_SECRET_LIKE_CONTENT_BLOCKED = (
    "OSPMG_EXPORT_SUMMARY_CLI_SECRET_LIKE_CONTENT_BLOCKED"
)
OSPMG_EXPORT_SUMMARY_CLI_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_EXPORT_SUMMARY_CLI_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_EXPORT_SUMMARY_CLI_UNTRUSTED_SOURCE = (
    "OSPMG_EXPORT_SUMMARY_CLI_UNTRUSTED_SOURCE"
)
OSPMG_EXPORT_SUMMARY_CLI_CONFLICT_VISIBLE = (
    "OSPMG_EXPORT_SUMMARY_CLI_CONFLICT_VISIBLE"
)
OSPMG_EXPORT_SUMMARY_CLI_SHARED_STACK_VISIBLE = (
    "OSPMG_EXPORT_SUMMARY_CLI_SHARED_STACK_VISIBLE"
)
OSPMG_EXPORT_SUMMARY_CLI_UNSAFE_CLAIM_BLOCKED = (
    "OSPMG_EXPORT_SUMMARY_CLI_UNSAFE_CLAIM_BLOCKED"
)
OSPMG_EXPORT_SUMMARY_CLI_EVIDENCE_RETAINED = (
    "OSPMG_EXPORT_SUMMARY_CLI_EVIDENCE_RETAINED"
)
OSPMG_EXPORT_SUMMARY_CLI_HISTORY_RETAINED = (
    "OSPMG_EXPORT_SUMMARY_CLI_HISTORY_RETAINED"
)
OSPMG_EXPORT_SUMMARY_CLI_NO_DISCOVERY_EXECUTION = (
    "OSPMG_EXPORT_SUMMARY_CLI_NO_DISCOVERY_EXECUTION"
)
OSPMG_EXPORT_SUMMARY_CLI_NO_PLUGIN_IMPORT = (
    "OSPMG_EXPORT_SUMMARY_CLI_NO_PLUGIN_IMPORT"
)
OSPMG_EXPORT_SUMMARY_CLI_NO_VALIDATION_EXECUTION = (
    "OSPMG_EXPORT_SUMMARY_CLI_NO_VALIDATION_EXECUTION"
)
OSPMG_EXPORT_SUMMARY_CLI_NO_SOLVER_EXECUTION = (
    "OSPMG_EXPORT_SUMMARY_CLI_NO_SOLVER_EXECUTION"
)
OSPMG_EXPORT_SUMMARY_CLI_PROJECT_SCHEMA_MUTATION_DISABLED = (
    "OSPMG_EXPORT_SUMMARY_CLI_PROJECT_SCHEMA_MUTATION_DISABLED"
)
OSPMG_EXPORT_SUMMARY_CLI_FUTURE_GATE = "OSPMG_EXPORT_SUMMARY_CLI_FUTURE_GATE"

OSPMG_EXPORT_SUMMARY_CLI_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_EXPORT_SUMMARY_CLI_PREVIEW_ONLY,
    OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY,
    OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED,
    OSPMG_EXPORT_SUMMARY_CLI_RELOAD_BUNDLE_DISABLED,
    OSPMG_EXPORT_SUMMARY_CLI_REPORT_ATTACHMENT_DISABLED,
    OSPMG_EXPORT_SUMMARY_CLI_CLIPBOARD_DISABLED,
    OSPMG_EXPORT_SUMMARY_CLI_OPEN_OUTPUT_FOLDER_DISABLED,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_VALIDATION,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_PERSISTENCE,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_RELOADABLE_BUNDLE,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_TRUST_RESTORE,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_ISSUE_CLOSURE,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_RELEASE_MUTATION,
    OSPMG_EXPORT_SUMMARY_CLI_NOT_CERTIFICATION,
    OSPMG_EXPORT_SUMMARY_CLI_REDACTION_REQUIRED,
    OSPMG_EXPORT_SUMMARY_CLI_UNREDACTED_PATH_BLOCKED,
    OSPMG_EXPORT_SUMMARY_CLI_SECRET_LIKE_CONTENT_BLOCKED,
    OSPMG_EXPORT_SUMMARY_CLI_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_EXPORT_SUMMARY_CLI_UNTRUSTED_SOURCE,
    OSPMG_EXPORT_SUMMARY_CLI_CONFLICT_VISIBLE,
    OSPMG_EXPORT_SUMMARY_CLI_SHARED_STACK_VISIBLE,
    OSPMG_EXPORT_SUMMARY_CLI_UNSAFE_CLAIM_BLOCKED,
    OSPMG_EXPORT_SUMMARY_CLI_EVIDENCE_RETAINED,
    OSPMG_EXPORT_SUMMARY_CLI_HISTORY_RETAINED,
    OSPMG_EXPORT_SUMMARY_CLI_NO_DISCOVERY_EXECUTION,
    OSPMG_EXPORT_SUMMARY_CLI_NO_PLUGIN_IMPORT,
    OSPMG_EXPORT_SUMMARY_CLI_NO_VALIDATION_EXECUTION,
    OSPMG_EXPORT_SUMMARY_CLI_NO_SOLVER_EXECUTION,
    OSPMG_EXPORT_SUMMARY_CLI_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_EXPORT_SUMMARY_CLI_FUTURE_GATE,
)

_EXPORT_SUMMARY_SUBCOMMANDS = (
    "explain",
    "preview",
    "sections",
    "sources",
    "candidates",
    "acknowledgements",
    "diagnostics",
    "redaction",
    "stale-sources",
    "conflicts",
    "unsafe-claims",
    "evidence",
    "limitations",
    "actions",
    "write-summary",
)

_STATE_SOURCE_FLAGS = ("sample_state", "empty_state", "unavailable_state")

_ACK_ALIASES: Mapping[str, str] = {
    "export_not_validation": "export_summary_not_validation",
    "export_not_persistence": "export_summary_not_persistence",
    "export_not_reloadable_bundle": "export_summary_not_reloadable_bundle",
    "export_not_trust_restoration": "export_summary_not_trust_restoration",
    "export_not_issue_closure": "export_summary_not_issue_closure",
    "export_not_release_mutation": "export_summary_not_release_mutation",
}

_NON_ACTION_LINES = (
    "Export summary is not validation evidence.",
    "Export summary is not persistence.",
    "Export summary is not a reloadable bundle.",
    "Export summary is not trust restoration.",
    "Export summary is not automatic activation.",
    "Export summary is not issue closure.",
    "Export summary is not release mutation.",
    "Export summary is not certification.",
    "A trust label is not certification.",
    "User/plugin manifests remain untrusted by default.",
    "Built-ins are authoritative by default.",
    "No export file creation.",
    "No report file creation.",
    "No reloadable bundle creation.",
    "No clipboard behavior.",
    "No report attachment.",
    "No open-output-folder behavior.",
    "No GUI behavior.",
    "No reload behavior.",
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
    "explain": "Explain the export-summary CLI safety boundary.",
    "preview": "Render a stable stdout export-summary preview.",
    "sections": "List available export-summary sections in stable order.",
    "sources": "Render redacted source and provenance rows.",
    "candidates": "Render candidate lifecycle/source-state summaries.",
    "acknowledgements": "Render acknowledgement categories and expiry policy.",
    "diagnostics": "Render export-summary and CLI diagnostics.",
    "redaction": "Render redaction and privacy state.",
    "stale-sources": "Render stale-source and re-preview state.",
    "conflicts": "Render conflict and shared-stack state.",
    "unsafe-claims": "Render unsafe-claim blockers.",
    "evidence": "Render evidence and history retention state.",
    "limitations": "Render visible limitations.",
    "actions": "Render disabled and future-only action states.",
    "write-summary": "Blocked future file-output action; no file is created.",
}


def add_optional_solver_plugin_manifest_export_summary_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the stdout-only export-summary CLI."""

    parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND,
        help="Review optional solver plugin manifest export-summary state.",
        description=(
            "Review supplied optional solver plugin manifest export-summary "
            "state through stdout only. This command is redaction-first, "
            "non-exporting, non-discovering, non-validating, non-executing, "
            "ProjectSchema-safe, and issue/release-safe."
        ),
    )
    parser.add_argument(
        "export_summary_command",
        choices=_EXPORT_SUMMARY_SUBCOMMANDS,
        help="Export-summary review operation to perform.",
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=("text", "json"),
        help="Output format.",
    )
    parser.add_argument(
        "--sample-state",
        action="store_true",
        help="Use deterministic in-memory sample state for tests and review.",
    )
    parser.add_argument(
        "--empty-state",
        action="store_true",
        help="Use deterministic empty in-memory state.",
    )
    parser.add_argument(
        "--unavailable-state",
        action="store_true",
        help="Use deterministic unavailable state; this is also the default.",
    )
    return parser


def run_optional_solver_plugin_manifest_export_summary_cli(
    args: argparse.Namespace,
) -> int:
    """Run a bounded export-summary CLI review operation."""

    state_source_error = _validate_state_source_flags(args)
    if state_source_error:
        _emit(
            {"error": state_source_error, "command": args.export_summary_command},
            [state_source_error],
            args,
            error=True,
        )
        return 2

    view_model, source_label = _view_model_from_args(args)
    payload = _payload(args, view_model, source_label)
    text_lines = _text_lines(args, view_model, source_label)
    blocked = args.export_summary_command == "write-summary"
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
) -> tuple[OptionalSolverPluginManifestExportSummaryViewModel, str]:
    if args.sample_state:
        return _sample_view_model(), "deterministic sample in-memory state"
    if args.empty_state:
        return (
            OptionalSolverPluginManifestExportSummaryViewModel.empty(),
            "deterministic empty in-memory state",
        )
    return (
        OptionalSolverPluginManifestExportSummaryViewModel.unavailable(),
        "unavailable in-memory state; live source integration is future-gated",
    )


def _sample_view_model() -> OptionalSolverPluginManifestExportSummaryViewModel:
    acknowledgements = {ack: True for ack in EXPORT_SUMMARY_REQUIRED_ACKS}
    sources = (
        OptionalSolverPluginManifestExportSummarySourceRow(
            source_id="built_in_gmsh",
            source_type="built_in_manifest",
            source_label="Built-in Gmsh manifest",
            source_reference_display="built-in:gmsh",
            source_reference_redacted=False,
            trust_label="built_in",
            built_in_authoritative=True,
        ),
        OptionalSolverPluginManifestExportSummarySourceRow(
            source_id="user_gmsh",
            source_type="user_selected_json_file",
            source_label="User selected Gmsh plugin manifest",
            source_reference_display="C:/Users/Research/.osw/plugins/user-gmsh.json",
            source_reference_redacted=True,
            trust_label="untrusted_user_file",
            stale_source_state="stale",
            repreview_required=True,
        ),
    )
    candidates = (
        OptionalSolverPluginManifestExportSummaryCandidateRow(
            stack_id="gmsh",
            display_name="Gmsh built-in optional solver stack",
            source_id="built_in_gmsh",
            source_type="built_in_manifest",
            trust_label="built_in",
            activation_state="inactive_preview",
            persistence_state="session_only",
            source_reference_display="built-in:gmsh",
            source_reference_redacted=False,
            built_in_authoritative=True,
            is_untrusted=False,
        ),
        OptionalSolverPluginManifestExportSummaryCandidateRow(
            stack_id="gmsh",
            display_name="User Gmsh plugin manifest candidate",
            source_id="user_gmsh",
            source_type="user_selected_json_file",
            trust_label="untrusted_user_file",
            activation_state="inactive_preview",
            deactivation_state="history_retained",
            reactivation_state="not_requested",
            discovery_refresh_state="not_refreshed",
            persistence_state="not_persisted",
            stale_source_state="stale",
            repreview_required=True,
            source_reference_display="user-gmsh.json",
            source_reference_redacted=True,
            shared_stack_indicators=("shares stack id with built-in gmsh",),
        ),
    )
    return OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=sources,
        candidates=candidates,
        acknowledgements=acknowledgements,
        stale_source_rows=(
            OptionalSolverPluginManifestExportSummaryStaleSourceRow(
                stale_source_state="stale",
                repreview_required=True,
                source_reference_display="user-gmsh.json",
            ),
        ),
        conflicts=(
            OptionalSolverPluginManifestExportSummaryConflictRow(
                stack_id="gmsh",
                built_in_source_id="built_in_gmsh",
                user_or_plugin_source_id="user_gmsh",
                active_source_state="built_in_wins_by_default",
                deactivated_source_state="user_manifest_not_activated",
                reactivation_source_state="not_requested",
                persistence_state="not_persisted",
            ),
        ),
        unsafe_claims=(
            OptionalSolverPluginManifestExportSummaryUnsafeClaimRow(
                claim_id="validation_success_claim",
                related_candidate_id="gmsh",
                related_source_id="user_gmsh",
                claim_text="User manifest claims validation success.",
            ),
        ),
        evidence_history=(
            OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow(
                stack_id="gmsh",
            ),
        ),
        limitations=(
            OptionalSolverPluginManifestExportSummaryLimitationRow(
                limitation_id="stdout_review_only",
                title="Stdout review only",
                message=(
                    "This CLI prints redacted review state only and creates no "
                    "export, report, or reloadable-bundle output."
                ),
            ),
            OptionalSolverPluginManifestExportSummaryLimitationRow(
                limitation_id="skipped_missing_separate",
                title="Skipped-missing remains separate",
                message=(
                    "Skipped-missing optional validation remains skipped-missing "
                    "and is not changed by export-summary output."
                ),
            ),
        ),
    )


def _payload(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
    source_label: str,
) -> dict[str, object]:
    return {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND,
        "subcommand": args.export_summary_command,
        "purpose": _COMMAND_PURPOSE[args.export_summary_command],
        "state_source": source_label,
        "state_source_policy": {
            "deterministic_in_memory_only": True,
            "live_discovery_performed": False,
            "passive_refresh_performed": False,
            "plugin_package_import_performed": False,
            "directory_scan_performed": False,
            "network_fetch_performed": False,
            "validation_execution_performed": False,
            "solver_execution_performed": False,
        },
        "output_mode": args.format,
        "stdout_first": True,
        "file_output_enabled": False,
        "write_summary_enabled": False,
        "write_summary_blocked": args.export_summary_command == "write-summary",
        "view_model": view_model.to_mapping(),
        "selected": _selected_payload(args.export_summary_command, view_model),
        "cli_diagnostics": list(OSPMG_EXPORT_SUMMARY_CLI_DIAGNOSTIC_CODES),
        "model_diagnostics": list(OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES),
        "non_actions": list(_NON_ACTION_LINES),
    }


def _selected_payload(
    subcommand: str,
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> object:
    mapping = view_model.to_mapping()
    key_by_command = {
        "sections": "sections",
        "sources": "sources",
        "candidates": "candidates",
        "acknowledgements": "acknowledgements",
        "diagnostics": "diagnostics",
        "redaction": "redaction",
        "stale-sources": "stale_sources",
        "conflicts": "conflicts",
        "unsafe-claims": "unsafe_claims",
        "evidence": "evidence_history",
        "limitations": "limitations",
        "actions": "actions",
    }
    if subcommand in key_by_command:
        return mapping.get(key_by_command[subcommand], mapping)
    return mapping


def _text_lines(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
    source_label: str,
) -> list[str]:
    lines = _common_header(args, view_model, source_label)
    subcommand = args.export_summary_command
    if subcommand == "explain":
        lines.extend(_explain_lines())
    elif subcommand == "preview":
        lines.extend(_preview_lines(view_model))
    elif subcommand == "sections":
        lines.extend(_section_lines(view_model))
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
    elif subcommand == "limitations":
        lines.extend(_limitation_lines(view_model))
    elif subcommand == "actions":
        lines.extend(_action_lines(view_model))
    elif subcommand == "write-summary":
        lines.extend(_write_summary_disabled_lines())
    lines.extend(_safety_boundary_lines())
    return lines


def _common_header(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
    source_label: str,
) -> list[str]:
    header = view_model.header
    return [
        "Optional Solver Plugin Manifest Export-Summary CLI",
        f"command: {OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND}",
        f"subcommand: {args.export_summary_command}",
        f"purpose: {_COMMAND_PURPOSE[args.export_summary_command]}",
        f"state source: {source_label}",
        "state source policy: deterministic in-memory only; no live discovery; "
        "no passive refresh; no plugin package import; no directory scan; no "
        "network fetch; no validation execution; no solver execution",
        f"state scope: {header.state_scope}",
        f"readiness: {header.readiness}",
        f"export-summary state: {header.export_summary_state}",
        f"schema version display: {header.schema_version_display}",
        "output mode: stdout-only review",
        "file output: disabled",
        "redaction-first: true",
        "trust/provenance: user/plugin manifests remain untrusted by default; "
        "built-ins are authoritative by default; trust label is not certification",
    ]


def _explain_lines() -> list[str]:
    return [
        "Definition:",
        "- The export-summary CLI is a redaction-first, stdout-first, "
        "human-reviewable surface over supplied export-summary view-model state.",
        "- It does not persist state, reload state, create reports, create export "
        "files, or create reloadable bundles.",
        "- It does not run discovery, import plugin packages, validate optional "
        "solvers, execute solvers, install dependencies, close issues, mutate "
        "releases, or certify results.",
    ]


def _preview_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    header = view_model.header
    return [
        "Preview:",
        f"- summary kind: {header.summary_kind}",
        f"- sources: {header.source_count}",
        f"- candidates: {header.candidate_count}",
        f"- diagnostics: {header.diagnostic_count}",
        f"- limitations: {header.limitations_count}",
        f"- redaction required: {header.redaction_required_count}",
        f"- stale sources: {header.stale_source_count}",
        f"- conflicts: {header.conflict_count}",
        f"- unsafe claims: {header.unsafe_claim_count}",
        f"- evidence retained: {header.evidence_retained_count}",
        f"- history retained: {header.history_retained_count}",
        *[f"- model line: {line}" for line in view_model.to_text_lines()],
    ]


def _section_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = ["Sections:"]
    if not view_model.sections:
        return [*lines, "- none"]
    for section in view_model.sections:
        lines.append(
            "- "
            f"{section.section_id}: {section.title}; severity={section.severity}; "
            f"visible={section.visible}; blocker={section.blocker}"
        )
    return lines


def _source_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Sources/provenance:",
        "- User/plugin manifests remain untrusted by default.",
        "- Built-ins are authoritative by default.",
        "- A trust label is not certification.",
    ]
    if not view_model.source_rows:
        return [*lines, "- none"]
    for row in view_model.source_rows:
        lines.append(
            "- "
            f"{row.source_id}: type={row.source_type}; trust={row.trust_label}; "
            f"display={row.source_reference_display or '<none>'}; "
            f"redacted={row.source_reference_redacted}; "
            f"raw_reference_blocked={row.raw_reference_blocked}; "
            f"built_in_authoritative={row.built_in_authoritative}"
        )
    return lines


def _candidate_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Candidates:",
        "- Candidate rows do not imply automatic activation or trust restoration.",
    ]
    if not view_model.candidate_rows:
        return [*lines, "- none"]
    for row in view_model.candidate_rows:
        lines.append(
            "- "
            f"{row.stack_id}: {row.display_name}; readiness={row.readiness}; "
            f"trust={row.trust_label}; activation={row.activation_state}; "
            f"source={row.source_id}; untrusted={row.is_untrusted}; "
            f"built_in_authoritative={row.built_in_authoritative}; "
            f"warnings={'; '.join(row.warnings) or 'none'}"
        )
    return lines


def _acknowledgement_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Acknowledgements:",
        "- Missing or satisfied acknowledgements do not validate, persist, reload, "
        "trust, activate, close issues, mutate releases, or certify anything.",
        "- export_summary_not_automatic_activation: required boundary.",
        "- export_summary_not_certification: required boundary.",
        "- no_validation_execution: required boundary.",
        "- no_solver_execution: required boundary.",
    ]
    for row in view_model.acknowledgement_rows:
        alias = _ACK_ALIASES.get(row.acknowledgement_id, row.acknowledgement_id)
        lines.append(
            "- "
            f"{row.acknowledgement_id} (alias: {alias}): required={row.required}; "
            f"satisfied={row.satisfied}; expires_on_reload={row.expires_on_reload}; "
            f"expires_on_source_change={row.expires_on_source_change}; "
            f"expires_on_schema_change={row.expires_on_schema_change}; "
            f"expires_on_unsafe_claim={row.expires_on_unsafe_claim}"
        )
    return lines


def _diagnostic_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Diagnostics:",
        "- Diagnostics are review state, not validation success or validation failure.",
        "- CLI diagnostic codes:",
        *[f"  - {code}" for code in OSPMG_EXPORT_SUMMARY_CLI_DIAGNOSTIC_CODES],
        "- View-model diagnostic rows:",
    ]
    if not view_model.diagnostics:
        return [*lines, "  - none"]
    for row in view_model.diagnostics:
        lines.append(
            "  - "
            f"{row.severity}/{row.category}: {row.code}; blocker={row.blocker}; "
            f"{row.message}"
        )
    return lines


def _redaction_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Redaction/privacy:",
        "- Raw absolute paths are hidden by default.",
        "- Secrets, tokens, credentials, environment variables, and API keys are "
        "blocked or redacted.",
        "- Fingerprints are not trust signals.",
    ]
    if not view_model.redaction_rows:
        return [*lines, "- none"]
    for row in view_model.redaction_rows:
        lines.append(
            "- "
            f"display={row.display_reference or '<none>'}; "
            f"status={row.redaction_status}; required={row.redaction_required}; "
            f"unredacted_path_blocked={row.unredacted_path_blocked}; "
            f"secret_like_content_blocked={row.secret_like_content_blocked}"
        )
    return lines


def _stale_source_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
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
            f"{row.source_reference_display or '<source>'}: "
            f"state={row.stale_source_state}; "
            f"repreview_required={row.repreview_required}; "
            f"old_preview_not_silently_trusted={row.old_preview_not_silently_trusted}"
        )
    return lines


def _conflict_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Conflicts/shared stacks:",
        "- Conflicts are visible.",
        "- Built-ins win by default.",
        "- Export summaries do not resolve conflicts or override built-ins.",
    ]
    if not view_model.conflict_rows:
        return [*lines, "- none"]
    for row in view_model.conflict_rows:
        lines.append(
            "- "
            f"{row.stack_id}: built_in_source={row.built_in_source_id}; "
            f"user_or_plugin_source={row.user_or_plugin_source_id}; "
            f"built_ins_win_by_default={row.built_ins_win_by_default}; "
            f"future_policy_required={row.future_policy_required}"
        )
    return lines


def _unsafe_claim_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Unsafe claims:",
        "- Unsafe claims are visible and blocked.",
        "- Unsafe claims are not exported as truth.",
        "- Unsafe claims include validation success/failure, issue closure, "
        "release mutation, bundled solvers, solver execution, and certification.",
    ]
    if not view_model.unsafe_claim_rows:
        return [*lines, "- none"]
    for row in view_model.unsafe_claim_rows:
        lines.append(
            "- "
            f"{row.claim_id}: blocked={row.blocked}; "
            f"accepted_by_export_summary={row.accepted_by_export_summary}; "
            f"{row.warning_text}"
        )
    return lines


def _evidence_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = [
        "Evidence/history:",
        "- Deactivation and reactivation history are retained.",
        "- Historical evidence is retained as reference only.",
        "- Skipped-missing remains skipped-missing.",
        "- Export summary is not validation evidence.",
    ]
    if not view_model.evidence_history_rows:
        return [*lines, "- none"]
    for row in view_model.evidence_history_rows:
        lines.append(
            "- "
            f"{row.stack_id or '<all>'}: "
            f"deactivation_history_retained={row.deactivation_history_retained}; "
            f"reactivation_history_retained={row.reactivation_history_retained}; "
            f"historical_validation_evidence_retained="
            f"{row.historical_validation_evidence_retained}; "
            f"skipped_missing_remains_skipped_missing="
            f"{row.skipped_missing_remains_skipped_missing}; "
            f"issue_closure_implied={row.issue_closure_implied}"
        )
    return lines


def _limitation_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = ["Limitations:"]
    if not view_model.limitation_rows:
        return [*lines, "- none"]
    for row in view_model.limitation_rows:
        lines.append(
            "- "
            f"{row.limitation_id}: {row.title}; severity={row.severity}; "
            f"{row.message}"
        )
    return lines


def _action_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> list[str]:
    lines = ["Actions:"]
    for row in view_model.actions:
        state = "enabled" if row.enabled else "disabled/future-only"
        lines.append(
            "- "
            f"{row.action.value}: {state}; available={row.available}; "
            f"future={row.future_action}; reason={row.reason}"
        )
    lines.extend(
        (
            "- write export-summary file: disabled/future-only",
            "- create report file: disabled/future-only",
            "- attach to report: disabled/future-only",
            "- copy to clipboard: disabled/future-only",
            "- open output folder: disabled/future-only",
            "- create reloadable bundle: disabled/future-only",
            "- run discovery: disabled/future-only",
            "- run validation: disabled/future-only",
            "- execute solver: disabled/future-only",
            "- close issue: disabled/future-only",
            "- mutate release: disabled/future-only",
            "- claim certification: disabled/future-only",
        )
    )
    return lines


def _write_summary_disabled_lines() -> list[str]:
    return [
        "write-summary: blocked",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_FUTURE_GATE}",
        "- write-summary is future-only and creates no export file, report file, "
        "reloadable bundle, clipboard content, report attachment, or output folder.",
    ]


def _safety_boundary_lines() -> list[str]:
    return [
        "Safety boundary:",
        *[f"- {line}" for line in _NON_ACTION_LINES],
        "Diagnostics surfaced:",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_PREVIEW_ONLY}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_VALIDATION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_PERSISTENCE}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_RELOADABLE_BUNDLE}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_TRUST_RESTORE}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_AUTOMATIC_ACTIVATION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_ISSUE_CLOSURE}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_RELEASE_MUTATION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NOT_CERTIFICATION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NO_DISCOVERY_EXECUTION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NO_PLUGIN_IMPORT}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NO_VALIDATION_EXECUTION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_NO_SOLVER_EXECUTION}",
        f"- {OSPMG_EXPORT_SUMMARY_CLI_PROJECT_SCHEMA_MUTATION_DISABLED}",
        "View-model diagnostics preserved:",
        f"- {OSPMG_EXPORT_SUMMARY_NOT_VALIDATION}",
        f"- {OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE}",
        f"- {OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE}",
        f"- {OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE}",
        f"- {OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE}",
        f"- {OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION}",
        f"- {OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION}",
        f"- {OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT}",
        f"- {OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION}",
        f"- {OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED}",
        f"- {OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM}",
    ]


def _emit(
    payload: Mapping[str, object],
    text_lines: Sequence[str],
    args: argparse.Namespace,
    *,
    error: bool,
) -> None:
    stream = sys.stderr if error else sys.stdout
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
        return
    print("\n".join(text_lines), file=stream)


__all__ = [
    "OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND",
    "OSPMG_EXPORT_SUMMARY_CLI_DIAGNOSTIC_CODES",
    "add_optional_solver_plugin_manifest_export_summary_parser",
    "run_optional_solver_plugin_manifest_export_summary_cli",
]
