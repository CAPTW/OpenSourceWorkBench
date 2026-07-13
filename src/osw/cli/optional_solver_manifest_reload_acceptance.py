"""Stdout-first CLI for optional solver plugin manifest reload acceptance review.

The command family renders deterministic, already-built in-memory
``OptionalSolverPluginManifestReloadAcceptanceViewModel`` records. It performs
no file IO, reader invocation, GUI calls, subprocess use, persistence writes,
ProjectSchema mutation, discovery, validation, solver execution, activation,
trust restoration, issue/release/tag/asset mutation, or certification claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel import (
    OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW,
    OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES,
    OSPMG_RELOAD_ACCEPTANCE_READY,
    RELOAD_ACCEPTANCE_REQUIRED_ACKS,
    OptionalSolverPluginManifestReloadAcceptanceViewModel,
)

OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND = (
    "optional-solver-plugin-manifest-reload-acceptance"
)

_ACCEPTANCE_SUBCOMMANDS = (
    "explain",
    "preview",
    "summary",
    "blockers",
    "acknowledgements",
    "expiry",
    "diagnostics",
    "actions",
    "safety",
    "accept-future",
)

_STATE_SOURCE_FLAGS = (
    "sample_state",
    "empty_state",
    "unavailable_state",
    "not_requested_state",
    "blocked_state",
    "ready_state",
    "accepted_state",
)

_COMMAND_PURPOSE = {
    "explain": "Explain the reload acceptance CLI review boundary.",
    "preview": "Render all reload acceptance review sections.",
    "summary": "Render acceptance summary, readiness, and action state.",
    "blockers": "Render acceptance preconditions and blockers.",
    "acknowledgements": "Render required acknowledgement rows.",
    "expiry": "Render acknowledgement expiry reasons.",
    "diagnostics": "Render OSPMG_RELOAD_ACCEPTANCE diagnostics.",
    "actions": "Render disabled and future-only action states.",
    "safety": "Render acceptance safety guidance.",
    "accept-future": (
        "Show that acceptance mutation remains disabled and future-only."
    ),
}

_NON_ACTION_DENIALS = (
    "CLI acceptance review is not runtime acceptance.",
    "CLI acceptance review is not active acceptance mutation.",
    "CLI acceptance review performs no file IO.",
    "CLI acceptance review reads no files.",
    "CLI acceptance review parses no files.",
    "CLI acceptance review invokes no reload file reader.",
    "CLI acceptance review calls no GUI code.",
    "CLI acceptance review uses no GUI subprocess.",
    "CLI acceptance review writes no persistence/state files.",
    "CLI acceptance review mutates no ProjectSchema.",
    "CLI acceptance review uses no default reload path.",
    "CLI acceptance review performs no background reload.",
    "CLI acceptance review scans no directories.",
    "CLI acceptance review fetches no network manifests.",
    "CLI acceptance review imports no plugin packages.",
    "CLI acceptance review creates no reloadable bundles.",
    "CLI acceptance review creates no export files.",
    "CLI acceptance review creates no report files.",
    "CLI acceptance review uses no clipboard.",
    "CLI acceptance review attaches no report.",
    "CLI acceptance review opens no output folder.",
    "CLI acceptance review performs no live discovery.",
    "CLI acceptance review performs no passive refresh.",
    "CLI acceptance review executes no validation.",
    "CLI acceptance review executes no solver.",
    "CLI acceptance review installs no dependencies.",
    "CLI acceptance review uninstalls no dependencies.",
    "CLI acceptance review uninstalls no solvers.",
    "CLI acceptance review automatically activates no candidates.",
    "CLI acceptance review restores no trust.",
    "CLI acceptance review mutates no issues.",
    "CLI acceptance review mutates no releases.",
    "CLI acceptance review mutates no tags.",
    "CLI acceptance review mutates no assets.",
    "CLI acceptance review bumps no version.",
    "CLI acceptance review claims no validation success.",
    "CLI acceptance review claims no validation failure.",
    "CLI acceptance review claims no issue closure.",
    "CLI acceptance review claims no bundled solver.",
    "CLI acceptance review claims no certification.",
)

_SAFETY_GUIDANCE = (
    "CLI acceptance review is not runtime acceptance.",
    "Preview success is not acceptance.",
    "Command success is not acceptance.",
    "Exit code 0 is not validation success.",
    "Exit code 0 is not validation failure.",
    "Acceptance readiness is not validation evidence.",
    "Acceptance readiness is not validation failure.",
    "Accepted-for-session-review remains untrusted by default.",
    "Trust label is not certification.",
    "Skipped-missing remains skipped-missing.",
    "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
    "bounded, issue-specific evidence.",
    "Prepared-machine validation remains separate.",
)

_SCHEMA_MIGRATION_ROWS = (
    ("payload_kind_required", "required", "payload kind is required"),
    ("schema_version_required", "required", "schema version is required"),
    ("unsupported_schema_blocks", "blocks", "unsupported schema blocks review"),
    ("migration_required_blocks", "blocks", "migration remains future-gated"),
    (
        "schema_mismatch_is_validation_failure",
        "no",
        "schema mismatch is not validation failure",
    ),
    (
        "persistence_schema_separate_from_project_schema",
        "yes",
        "persistence schema remains separate from ProjectSchema",
    ),
    ("cli_repairs_or_migrates_files", "no", "CLI does not repair or migrate"),
)

_REDACTION_PRIVACY_ROWS = (
    ("raw_paths_hidden_by_default", "yes", "basename/hash/source-id preferred"),
    ("home_directories_blocked", "yes", "home directory disclosure is blocked"),
    ("environment_variables_blocked", "yes", "environment values are blocked"),
    ("secrets_tokens_api_keys_blocked", "yes", "secret-like values are blocked"),
    (
        "unredacted_path_allowance",
        "future_policy_required",
        "future explicit policy required",
    ),
    ("fingerprints_are_trust_signals", "no", "fingerprints are not trust"),
    ("diagnostics_use_redacted_context", "yes", "diagnostics stay redacted"),
    ("accepted_state_stores_secrets_as_truth", "never", "never stores secrets"),
)

_CANDIDATE_LIFECYCLE_ROWS = (
    ("inactive_preview", "review_only", "inactive preview remains review-only"),
    (
        "persisted_active",
        "future_activation_review_required",
        "future activation review required",
    ),
    ("deactivated", "review_state", "deactivated remains review state"),
    (
        "reactivation",
        "future_activation_review_required",
        "reactivation routes to future activation review",
    ),
    (
        "discovery_refresh",
        "future_review",
        "discovery-refresh state remains review state",
    ),
    ("automatic_activation", "no", "no automatic activation"),
    ("trust_restoration", "no", "no trust restoration"),
    ("built_in_override", "no", "accepted state does not override built-ins"),
)

_STALE_SOURCE_ROWS = (
    ("old_preview_silently_trusted", "no", "old preview is not silently trusted"),
    (
        "missing_moved_changed_sources",
        "repreview_required",
        "changed source requires re-preview",
    ),
    (
        "source_file_inspection",
        "no",
        "CLI acceptance review does not inspect source files",
    ),
    ("stale_source_is_validation_failure", "no", "stale source is not failure"),
    ("repreview_gate", "future", "re-preview remains future-gated"),
    (
        "future_discovery_refresh_result",
        "expires_acknowledgements",
        "future refresh may expire acknowledgements",
    ),
)

_CONFLICT_ROWS = (
    ("conflicts_visible", "yes", "conflicts are visible"),
    ("built_ins_win_by_default", "yes", "built-ins win by default"),
    ("accepted_state_overrides_built_ins", "no", "accepted state does not override"),
    ("shared_stack_warnings_visible", "yes", "shared-stack warnings are visible"),
    ("cli_resolves_conflicts", "no", "CLI does not resolve conflicts"),
    ("future_policy_required", "yes", "future policy is required"),
)

_UNSAFE_CLAIM_ROWS = (
    ("unsafe_claims_visible", "yes", "unsafe claims are visible and blocked"),
    ("unsafe_claims_rendered_as_truth", "no", "unsafe claims are not truth"),
    ("validation_success_claims", "blocked", "validation success claims blocked"),
    ("validation_failure_claims", "blocked", "validation failure claims blocked"),
    ("issue_closure_claims", "blocked", "issue closure claims blocked"),
    ("release_mutation_claims", "blocked", "release mutation claims blocked"),
    ("bundled_solver_claims", "blocked", "bundled solver claims blocked"),
    ("dependency_install_claims", "blocked", "dependency install claims blocked"),
    ("solver_execution_claims", "blocked", "solver execution claims blocked"),
    ("trust_restoration_claims", "blocked", "trust restoration claims blocked"),
    ("certification_claims", "blocked", "certification claims blocked"),
)


def add_optional_solver_plugin_manifest_reload_acceptance_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the reload acceptance review CLI command family."""

    parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND,
        help="Review optional solver plugin manifest reload acceptance state.",
        description=(
            "Render deterministic in-memory reload acceptance view-model records. "
            "This command is stdout-first, review-only, non-mutating, "
            "non-reading, non-parsing, non-discovering, non-validating, "
            "non-executing, ProjectSchema-safe, issue-safe, release-safe, "
            "and certification-safe."
        ),
    )
    parser.add_argument(
        "acceptance_command",
        choices=_ACCEPTANCE_SUBCOMMANDS,
        help="Reload acceptance review operation to perform.",
    )
    parser.add_argument(
        "--sample-state",
        action="store_true",
        help="Use deterministic representative in-memory acceptance state.",
    )
    parser.add_argument(
        "--empty-state",
        action="store_true",
        help="Use deterministic empty/no-preview acceptance state.",
    )
    parser.add_argument(
        "--unavailable-state",
        action="store_true",
        help="Use deterministic unavailable/no-preview state; also the default.",
    )
    parser.add_argument(
        "--not-requested-state",
        action="store_true",
        help="Use deterministic preview-available/not-requested state.",
    )
    parser.add_argument(
        "--blocked-state",
        action="store_true",
        help="Use deterministic blocked acceptance state.",
    )
    parser.add_argument(
        "--ready-state",
        action="store_true",
        help="Use deterministic ready/future-only acceptance state.",
    )
    parser.add_argument(
        "--accepted-state",
        action="store_true",
        help="Use deterministic accepted-for-session-review representation.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON.")
    parser.add_argument(
        "--diagnostics-only",
        action="store_true",
        help="Render only diagnostics.",
    )
    parser.add_argument(
        "--blockers-only",
        action="store_true",
        help="Render only blockers.",
    )
    parser.add_argument(
        "--acknowledgements-only",
        action="store_true",
        help="Render only acknowledgements.",
    )
    parser.add_argument(
        "--actions-only",
        action="store_true",
        help="Render only disabled/future actions.",
    )
    parser.add_argument(
        "--safety-only",
        action="store_true",
        help="Render only safety guidance.",
    )
    return parser


def run_optional_solver_plugin_manifest_reload_acceptance_cli(
    args: argparse.Namespace,
) -> int:
    """Run a bounded acceptance review operation."""

    state_error = _validate_state_source_flags(args)
    if state_error:
        _emit({"error": state_error}, [state_error], args, error=True)
        return 2

    view_model, state_source = _view_model_from_args(args)
    payload = _payload(args, view_model, state_source)
    text_lines = _text_lines(args, view_model, state_source)
    disabled_future = args.acceptance_command == "accept-future"
    _emit(payload, text_lines, args, error=disabled_future)
    return 2 if disabled_future else 0


def _validate_state_source_flags(args: argparse.Namespace) -> str:
    selected = [bool(getattr(args, flag, False)) for flag in _STATE_SOURCE_FLAGS]
    if sum(1 for value in selected if value) > 1:
        return (
            "Select only one acceptance state source: --sample-state, "
            "--empty-state, --unavailable-state, --not-requested-state, "
            "--blocked-state, --ready-state, or --accepted-state."
        )
    section_filters = (
        bool(args.diagnostics_only),
        bool(args.blockers_only),
        bool(args.acknowledgements_only),
        bool(args.actions_only),
        bool(args.safety_only),
    )
    if sum(1 for value in section_filters if value) > 1:
        return "Select only one section-only output option."
    return ""


def _view_model_from_args(
    args: argparse.Namespace,
) -> tuple[OptionalSolverPluginManifestReloadAcceptanceViewModel, str]:
    if args.sample_state:
        return _sample_state(), "deterministic representative in-memory state"
    if args.empty_state:
        return (
            OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable(
                "No reload acceptance preview was supplied for the empty state."
            ),
            "deterministic empty in-memory state",
        )
    if args.not_requested_state:
        return (
            OptionalSolverPluginManifestReloadAcceptanceViewModel.from_preview_mapping(
                _sample_reload_preview_mapping()
            ),
            "deterministic not-requested in-memory state",
        )
    if args.blocked_state:
        return (
            OptionalSolverPluginManifestReloadAcceptanceViewModel.from_preview_mapping(
                _sample_reload_preview_mapping(),
                requested=True,
                acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS[:4],
                policy_flags=_blocked_policy_flags(),
            ),
            "deterministic blocked in-memory state",
        )
    if args.ready_state:
        return (
            OptionalSolverPluginManifestReloadAcceptanceViewModel.from_preview_mapping(
                _sample_reload_preview_mapping(),
                requested=True,
                acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
                policy_flags={
                    "future_activation_review_required": True,
                    "future_discovery_refresh_required": True,
                },
            ),
            "deterministic ready/future-only in-memory state",
        )
    if args.accepted_state:
        return (
            OptionalSolverPluginManifestReloadAcceptanceViewModel.from_preview_mapping(
                _sample_reload_preview_mapping(),
                requested=True,
                acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
                accepted_for_session_review=True,
                policy_flags={
                    "future_activation_review_required": True,
                    "future_discovery_refresh_required": True,
                },
            ),
            "deterministic accepted-for-session-review in-memory state",
        )
    if args.unavailable_state:
        return (
            OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable(),
            "deterministic unavailable/no-preview in-memory state",
        )
    return (
        OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable(),
        "unavailable/no-preview in-memory state; no live source is read",
    )


def _sample_state() -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    return OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        _sample_reload_preview_mapping(),
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS[:8],
        expired_acknowledgements=(RELOAD_ACCEPTANCE_REQUIRED_ACKS[2],),
        policy_flags=_blocked_policy_flags(),
    )


def _sample_reload_preview_mapping() -> dict[str, object]:
    return {
        "summary": {
            "state": "ready_review_only",
            "readiness": "ready_review_only",
            "payload_kind": "optional_solver_plugin_manifest_reload_state",
            "payload_schema_version": "osw-exp-119",
            "source_display": "sample-state.json",
        },
        "sources": [
            {
                "source_id": "sample-source",
                "source_display": "sample-state.json",
                "source_reference_redacted": True,
                "provenance_label": "deterministic_cli_sample",
                "trust_label": "untrusted_user_source",
                "user_plugin_sources_untrusted_by_default": True,
            }
        ],
        "candidates": [
            {
                "candidate_id": "sample-calculix-plugin",
                "display_name": "Sample CalculiX Plugin",
                "lifecycle_state": "inactive_preview",
                "reload_review_state": "future_activation_review_required",
                "requires_future_activation_review": True,
                "requires_future_discovery_refresh": True,
            }
        ],
        "diagnostics": [
            {
                "severity": "info",
                "code": "OSPMG_RELOAD_NO_VALIDATION_EXECUTION",
                "message": "Reload preview did not run validation.",
                "blocker": False,
            }
        ],
        "evidence_history": [
            {
                "evidence_id": "history-sample-1",
                "candidate_id": "sample-calculix-plugin",
                "evidence_type": "deactivation_history_reference",
            }
        ],
    }


def _blocked_policy_flags() -> dict[str, bool]:
    return {
        "stale_source_requires_repreview": True,
        "conflict_review_required": True,
        "shared_stack_review_required": True,
        "unsafe_claim_blocked": True,
        "unsupported_schema": True,
        "migration_required": True,
        "unredacted_path_blocked": True,
        "secret_like_value_blocked": True,
        "trust_policy_changed": True,
        "source_fingerprint_changed": True,
        "acceptance_policy_changed": True,
        "future_activation_review_required": True,
        "future_discovery_refresh_required": True,
    }


def _payload(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadAcceptanceViewModel,
    state_source: str,
) -> dict[str, object]:
    mapping = view_model.to_mapping()
    return {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND,
        "subcommand": args.acceptance_command,
        "purpose": _COMMAND_PURPOSE[args.acceptance_command],
        "stdout_first": True,
        "review_only": True,
        "state_source": state_source,
        "state_source_policy": _state_source_policy(),
        "output_mode": "json" if args.json else "text",
        "view_model": mapping,
        "summary": mapping["summary"],
        "blockers": mapping["blockers"],
        "acknowledgements": mapping["acknowledgements"],
        "acknowledgement_expiry_reasons": mapping[
            "acknowledgement_expiry_reasons"
        ],
        "accepted_state_scope": mapping["accepted_state"],
        "reader_preview_provenance": mapping["source_provenance"],
        "schema_migration": _table_payload(_SCHEMA_MIGRATION_ROWS),
        "redaction_privacy": _table_payload(_REDACTION_PRIVACY_ROWS),
        "candidate_lifecycle": _table_payload(_CANDIDATE_LIFECYCLE_ROWS),
        "stale_source_repreview": _table_payload(_STALE_SOURCE_ROWS),
        "conflict_shared_stack": _table_payload(_CONFLICT_ROWS),
        "unsafe_claims": _table_payload(_UNSAFE_CLAIM_ROWS),
        "evidence_history": mapping["evidence_history"],
        "diagnostics": mapping["diagnostics"],
        "reserved_diagnostic_codes": list(OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES),
        "non_action_flags": mapping["non_action_flags"],
        "disabled_future_actions": mapping["actions"],
        "safety_guidance": list(_SAFETY_GUIDANCE),
        "exit_semantics": _exit_semantics(args.acceptance_command),
        "selected": _selected_payload(args, mapping),
        "no_side_effect_boundaries": _state_source_policy(),
    }


def _state_source_policy() -> dict[str, bool]:
    return {
        "deterministic_in_memory_acceptance_viewmodel_records_only": True,
        "file_io_performed": False,
        "file_reading_performed": False,
        "file_parsing_performed": False,
        "reader_invocation_performed": False,
        "gui_call_performed": False,
        "gui_subprocess_used": False,
        "persistence_write_performed": False,
        "project_schema_mutated": False,
        "default_reload_path_used": False,
        "background_reload_performed": False,
        "directory_scan_performed": False,
        "network_fetch_performed": False,
        "plugin_package_imported": False,
        "live_discovery_executed": False,
        "passive_refresh_executed": False,
        "validation_executed": False,
        "solver_executed": False,
        "candidate_activated": False,
        "trust_restored": False,
        "issue_mutated": False,
        "release_mutated": False,
        "tag_mutated": False,
        "asset_mutated": False,
        "version_bumped": False,
        "certification_claimed": False,
    }


def _selected_payload(
    args: argparse.Namespace,
    mapping: Mapping[str, object],
) -> object:
    section = _selected_section(args)
    if section == "summary":
        return mapping["summary"]
    if section == "blockers":
        return mapping["blockers"]
    if section == "acknowledgements":
        return mapping["acknowledgements"]
    if section == "expiry":
        return mapping["acknowledgement_expiry_reasons"]
    if section == "diagnostics":
        return mapping["diagnostics"]
    if section == "actions":
        return mapping["actions"]
    if section == "safety":
        return list(_SAFETY_GUIDANCE)
    return mapping


def _selected_section(args: argparse.Namespace) -> str:
    if args.diagnostics_only:
        return "diagnostics"
    if args.blockers_only:
        return "blockers"
    if args.acknowledgements_only:
        return "acknowledgements"
    if args.actions_only:
        return "actions"
    if args.safety_only:
        return "safety"
    if args.acceptance_command in {
        "summary",
        "blockers",
        "acknowledgements",
        "expiry",
        "diagnostics",
        "actions",
        "safety",
    }:
        return args.acceptance_command
    return "preview"


def _text_lines(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadAcceptanceViewModel,
    state_source: str,
) -> list[str]:
    mapping = view_model.to_mapping()
    lines = _header_lines(args, mapping, state_source)
    section = _selected_section(args)
    if args.acceptance_command == "accept-future":
        lines.extend(_accept_future_lines())
    elif args.acceptance_command == "explain":
        lines.extend(_explain_lines())
    if section == "preview":
        lines.extend(_summary_lines(mapping))
        lines.extend(_blocker_lines(mapping))
        lines.extend(_acknowledgement_lines(mapping))
        lines.extend(_expiry_lines(mapping))
        lines.extend(_accepted_state_lines(mapping))
        lines.extend(_provenance_lines(mapping))
        lines.extend(_schema_migration_lines())
        lines.extend(_redaction_privacy_lines())
        lines.extend(_candidate_lifecycle_lines())
        lines.extend(_stale_source_lines())
        lines.extend(_conflict_lines())
        lines.extend(_unsafe_claim_lines())
        lines.extend(_evidence_history_lines(mapping))
        lines.extend(_diagnostic_lines(mapping))
        lines.extend(_non_action_flag_lines(mapping))
        lines.extend(_action_lines(mapping))
        lines.extend(_safety_lines())
    elif section == "summary":
        lines.extend(_summary_lines(mapping))
    elif section == "blockers":
        lines.extend(_blocker_lines(mapping))
    elif section == "acknowledgements":
        lines.extend(_acknowledgement_lines(mapping))
    elif section == "expiry":
        lines.extend(_expiry_lines(mapping))
    elif section == "diagnostics":
        lines.extend(_diagnostic_lines(mapping))
    elif section == "actions":
        lines.extend(_action_lines(mapping))
    elif section == "safety":
        lines.extend(_safety_lines())
    if section != "safety" and args.acceptance_command not in {"preview"}:
        lines.extend(_safety_lines())
    lines.extend(_exit_lines(args.acceptance_command))
    return lines


def _header_lines(
    args: argparse.Namespace,
    mapping: Mapping[str, object],
    state_source: str,
) -> list[str]:
    summary = _mapping(mapping.get("summary"))
    return [
        "Optional Solver Plugin Manifest Reload Acceptance CLI",
        f"command: {OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND}",
        f"subcommand: {args.acceptance_command}",
        f"purpose: {_COMMAND_PURPOSE[args.acceptance_command]}",
        f"state source: {state_source}",
        (
            "state source policy: deterministic in-memory acceptance "
            "view-model records only; no file IO; no file reading; no file "
            "parsing; no reader invocation; no GUI calls; no persistence "
            "writes; no ProjectSchema mutation"
        ),
        f"state: {summary.get('state')}",
        f"readiness: {summary.get('readiness')}",
        "action state: disabled_future_only",
        f"requested: {summary.get('requested')}",
        f"preview_available: {summary.get('preview_available')}",
        (
            "accepted_for_session_review: "
            f"{summary.get('accepted_for_session_review')}"
        ),
    ]


def _explain_lines() -> list[str]:
    return [
        "Definition:",
        "- The command renders reload acceptance review records to stdout.",
        "- The command consumes deterministic in-memory view-model records only.",
        "- Review commands may return 0 for blocked review states.",
        "- Exit code 0 means command completion only.",
        "Non-actions:",
        *[f"- {line}" for line in _NON_ACTION_DENIALS],
    ]


def _summary_lines(mapping: Mapping[str, object]) -> list[str]:
    summary = _mapping(mapping.get("summary"))
    return [
        "Summary/readiness:",
        f"- state: {summary.get('state')}",
        f"- readiness: {summary.get('readiness')}",
        "- action_state: disabled_future_only",
        f"- requested: {summary.get('requested')}",
        f"- preview_available: {summary.get('preview_available')}",
        f"- ready_future_only: {summary.get('ready_for_future_acceptance')}",
        (
            "- accepted_for_session_review: "
            f"{summary.get('accepted_for_session_review')}"
        ),
        f"- source_count: {summary.get('source_count')}",
        f"- blocker_count: {summary.get('blocker_count')}",
        f"- acknowledgement_count: {summary.get('acknowledgement_count')}",
        "- no validation: yes",
        "- no validation failure: yes",
        "- no ProjectSchema mutation: yes",
        "- no persistence write: yes",
        "- no activation: yes",
        "- no trust restoration: yes",
        "- no discovery: yes",
        "- no solver execution: yes",
        "- no issue/release mutation: yes",
        "- no certification: yes",
    ]


def _blocker_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Preconditions/blockers:",
        "- missing preview blocks acceptance review.",
        "- reader blocked diagnostics block acceptance review.",
        "- view-model blocked diagnostics block acceptance review.",
        "- missing acknowledgements block requested acceptance.",
        "- stale-source/re-preview required blocks acceptance.",
        "- conflict/shared-stack review required blocks acceptance.",
        "- unsafe claim blocked remains visible.",
        "- unsupported schema and migration-required states block acceptance.",
        "- unredacted paths and secret-like values block acceptance.",
        "- trust, source-fingerprint, and policy changes require re-review.",
    ]
    blockers = _mapping_list(mapping.get("blockers"))
    if not blockers:
        return [*lines, "- active blockers: none"]
    for row in blockers:
        lines.append(
            "- "
            f"{row.get('diagnostic_code')}: {row.get('label')} "
            f"required_action={row.get('required_action')}"
        )
    return lines


def _acknowledgement_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Acknowledgements:",
        "- acknowledgement is not validation evidence.",
        "- acknowledgement is not trust restoration.",
        "- required acknowledgements:",
    ]
    for ack_id in RELOAD_ACCEPTANCE_REQUIRED_ACKS:
        lines.append(f"  - {ack_id}")
    for row in _mapping_list(mapping.get("acknowledgements")):
        lines.append(
            "- "
            f"{row.get('acknowledgement_id')}: "
            f"required={row.get('required')}; "
            f"satisfied={row.get('satisfied')}; "
            f"expired={row.get('expired')}; "
            f"blocking={row.get('blocker')}; "
            f"not_validation_evidence={row.get('not_validation_evidence')}; "
            f"not_trust_restoration={row.get('not_trust_restoration')}"
        )
    return lines


def _expiry_lines(mapping: Mapping[str, object]) -> list[str]:
    reasons = _sequence(mapping.get("acknowledgement_expiry_reasons"))
    return [
        "Acknowledgement expiry:",
        *[f"- {reason}" for reason in reasons],
    ]


def _accepted_state_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Accepted-state scope:",
        "- session/review scoped.",
        "- untrusted by default.",
        "- not persistence.",
        "- not ProjectSchema.",
        "- not validation evidence.",
        "- not validation failure.",
        "- not automatic activation.",
        "- not trust restoration.",
        "- does not override built-ins.",
        "- future activation/discovery review required where applicable.",
    ]
    for row in _mapping_list(mapping.get("accepted_state")):
        lines.append(
            "- "
            f"{row.get('state_id')}: "
            f"accepted_for_session_review={row.get('accepted_for_session_review')}; "
            f"scope={row.get('scope')}; "
            f"untrusted_by_default={row.get('untrusted_by_default')}; "
            f"persisted_state={row.get('persisted_state')}; "
            f"project_schema_state={row.get('project_schema_state')}; "
            f"validation_evidence={row.get('validation_evidence')}; "
            f"validation_failure={row.get('validation_failure')}; "
            f"automatic_activation={row.get('automatic_activation')}; "
            f"trust_restoration={row.get('trust_restoration')}"
        )
    return lines


def _provenance_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Reader/preview provenance:",
        "- supplied reader diagnostics/provenance rows are rendered when present.",
        "- payload hash is shown only when supplied as safe/redacted metadata.",
        "- target/source display is redacted.",
        "- no raw absolute paths by default.",
        "- no secrets, tokens, API keys, or full file content display.",
    ]
    for row in _mapping_list(mapping.get("source_provenance")):
        lines.append(
            "- "
            f"{row.get('source_id')}: display={row.get('source_display')}; "
            f"redacted={row.get('source_reference_redacted')}; "
            f"provenance={row.get('provenance_label')}; "
            f"trust={row.get('trust_label')}; "
            f"fingerprint_changed={row.get('source_fingerprint_changed')}; "
            "trust_label_is_certification="
            f"{row.get('trust_label_is_certification')}"
        )
    return lines


def _schema_migration_lines() -> list[str]:
    return _table_lines("Schema/migration:", _SCHEMA_MIGRATION_ROWS)


def _redaction_privacy_lines() -> list[str]:
    return _table_lines("Redaction/privacy:", _REDACTION_PRIVACY_ROWS)


def _candidate_lifecycle_lines() -> list[str]:
    return _table_lines("Candidate lifecycle:", _CANDIDATE_LIFECYCLE_ROWS)


def _stale_source_lines() -> list[str]:
    return _table_lines("Stale-source/re-preview:", _STALE_SOURCE_ROWS)


def _conflict_lines() -> list[str]:
    return _table_lines("Conflict/shared-stack:", _CONFLICT_ROWS)


def _unsafe_claim_lines() -> list[str]:
    return _table_lines("Unsafe claims:", _UNSAFE_CLAIM_ROWS)


def _evidence_history_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Evidence/history:",
        "- deactivation/reactivation history retained.",
        "- historical evidence retained as reference-only.",
        "- skipped-missing remains skipped-missing.",
        "- accepted state is not validation evidence.",
        "- no evidence deletion or rewrite.",
        "- no issue closure implied.",
    ]
    for row in _mapping_list(mapping.get("evidence_history")):
        lines.append(
            "- "
            f"{row.get('evidence_id')}: candidate={row.get('candidate_id')}; "
            f"type={row.get('evidence_type')}; "
            f"reference_only={row.get('retained_reference_only')}; "
            f"not_validation_evidence={row.get('not_validation_evidence')}; "
            f"issue_closure_implied={row.get('issue_closure_implied')}"
        )
    return lines


def _diagnostic_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Diagnostics:",
        *[f"- reserved: {code}" for code in OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES],
    ]
    for row in _mapping_list(mapping.get("diagnostics")):
        lines.append(
            "- "
            f"{row.get('severity')}: {row.get('code')}; "
            f"blocker={row.get('blocker')}; {row.get('message')}"
        )
    return lines


def _non_action_flag_lines(mapping: Mapping[str, object]) -> list[str]:
    flags = _mapping(mapping.get("non_action_flags"))
    lines = ["Non-action flags:"]
    for name in sorted(flags):
        lines.append(f"- {name}: {str(flags[name]).lower()}")
    return lines


def _action_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Disabled/future actions:",
    ]
    for row in _mapping_list(mapping.get("actions")):
        lines.append(
            "- "
            f"{row.get('action')}: enabled={row.get('enabled')}; "
            f"future_only={row.get('future_only')}; reason={row.get('reason')}"
        )
    return lines


def _safety_lines() -> list[str]:
    return [
        "Safety guidance:",
        *[f"- {line}" for line in _SAFETY_GUIDANCE],
    ]


def _accept_future_lines() -> list[str]:
    return [
        "accept-future: disabled/future-only",
        "- No acceptance mutation is implemented in this gate.",
        "- No runtime reload acceptance is performed.",
        "- No persistence write is performed.",
        "- No ProjectSchema mutation is performed.",
        "- This command returns 2 without implying validation failure.",
        f"- diagnostic: {OSPMG_RELOAD_ACCEPTANCE_READY}",
        f"- diagnostic: {OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW}",
    ]


def _exit_lines(subcommand: str) -> list[str]:
    semantics = _exit_semantics(subcommand)
    return [
        "Exit-code policy:",
        f"- code: {semantics['code']}",
        f"- meaning: {semantics['meaning']}",
        "- exit code 0 is command completion only.",
        "- exit code 0 is not validation success.",
        "- exit code 0 is not validation failure.",
        "- exit code 0 is not runtime acceptance.",
        "- exit code 0 is not issue closure, release mutation, or certification.",
    ]


def _exit_semantics(subcommand: str) -> dict[str, object]:
    if subcommand == "accept-future":
        return {
            "code": 2,
            "meaning": "disabled/future-only acceptance mutation",
            "command_completion": False,
            "runtime_acceptance": False,
            "validation_success": False,
            "validation_failure": False,
            "issue_closure": False,
            "release_mutation": False,
            "certification": False,
        }
    return {
        "code": 0,
        "meaning": "command completion only",
        "command_completion": True,
        "runtime_acceptance": False,
        "validation_success": False,
        "validation_failure": False,
        "issue_closure": False,
        "release_mutation": False,
        "certification": False,
    }


def _table_lines(
    title: str,
    rows: Sequence[tuple[str, str, str]],
) -> list[str]:
    return [
        title,
        *[f"- {field}: state={state}; guidance={guidance}" for field, state, guidance in rows],
    ]


def _table_payload(rows: Sequence[tuple[str, str, str]]) -> list[dict[str, str]]:
    return [
        {"field": field, "state": state, "guidance": guidance}
        for field, state, guidance in rows
    ]


def _emit(
    payload: Mapping[str, object],
    lines: Sequence[str],
    args: argparse.Namespace,
    *,
    error: bool = False,
) -> None:
    stream = sys.stderr if error else sys.stdout
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
    else:
        print("\n".join(lines), file=stream)


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _mapping_list(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value)


__all__ = [
    "OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND",
    "add_optional_solver_plugin_manifest_reload_acceptance_parser",
    "run_optional_solver_plugin_manifest_reload_acceptance_cli",
]
