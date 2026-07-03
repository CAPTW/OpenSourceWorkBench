"""Stdout-first reload acceptance persistence CLI review and explicit write.

This command renders deterministic in-memory persistence view-model records and
dry-run writer plans. Its write subcommand performs an explicit local
review-record write only through the OSW-EXP-126 writer API after explicit
target, fresh dry-run, acknowledgement, and confirmation gates pass. It performs
no input state-file reading/parsing, no reload file-reader invocation, no
OSW-EXP-102 state-writer invocation, no GUI calls, no subprocess use, no runtime
reload acceptance, no ProjectSchema mutation, no discovery, no validation, no
solver execution, no activation, no trust restoration, no issue/release/tag/asset
mutation, and no certification claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from osw.experimental.optional_solvers import (
    RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS,
    RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
    OptionalSolverPluginManifestReloadAcceptanceViewModel,
    OptionalSolverPluginManifestReloadViewModel,
    ReloadAcceptancePersistenceWriteRequest,
    plan_reload_acceptance_persistence_write,
    write_reload_acceptance_persistence_record,
)

OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND = (
    "optional-solver-plugin-manifest-reload-acceptance-persistence"
)

_SUBCOMMANDS = (
    "explain",
    "preview",
    "plan",
    "diagnostics",
    "acknowledgements",
    "expiry",
    "storage",
    "actions",
    "safety",
    "write",
    "write-future",
)

_STATE_SOURCE_FLAGS = (
    "sample_state",
    "empty_state",
    "unavailable_state",
    "blocked_state",
    "ready_state",
    "writer_ready_state",
)

_COMMAND_PURPOSE = {
    "explain": "Explain the reload acceptance persistence CLI boundary.",
    "preview": "Render all persistence review and dry-run planning sections.",
    "plan": "Render a dry-run writer plan without creating files.",
    "diagnostics": "Render persistence CLI, view-model, and writer diagnostics.",
    "acknowledgements": "Render required persistence acknowledgement rows.",
    "expiry": "Render acknowledgement expiry reasons.",
    "storage": "Render storage, target, schema, and path policy.",
    "actions": "Render disabled and future action states.",
    "safety": "Render persistence CLI safety guidance.",
    "write": (
        "Write an explicit local review record after dry-run, acknowledgement, "
        "and confirmation gates."
    ),
    "write-future": "Show that actual CLI writes remain disabled and future-only.",
}

_CLI_DIAGNOSTICS = {
    "unavailable": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_UNAVAILABLE",
    "target_required": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_TARGET_REQUIRED",
    "dry_run_only": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_DRY_RUN_ONLY",
    "writer_plan_rendered": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITER_PLAN_RENDERED"
    ),
    "write_future_disabled": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_FUTURE_DISABLED"
    ),
    "write_target_required": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_TARGET_REQUIRED"
    ),
    "write_ack_required": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ACK_REQUIRED"
    ),
    "write_confirm_required": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_CONFIRM_REQUIRED"
    ),
    "write_dry_run_not_write": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_DRY_RUN_NOT_WRITE"
    ),
    "write_completed_local_only": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_COMPLETED_LOCAL_ONLY"
    ),
    "write_blocked": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_BLOCKED",
    "write_error": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ERROR",
    "write_no_validation_claim": (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_NO_VALIDATION_CLAIM"
    ),
    "safety_guidance": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_SAFETY_GUIDANCE",
}

_SECRET_MARKERS = (
    "secret",
    "token",
    "api_key",
    "apikey",
    "password",
    "passwd",
    "bearer",
    "credential",
    "private_key",
    "access_key",
)

_SAFETY_GUIDANCE = (
    "Persistence CLI review is not runtime reload acceptance.",
    "Dry-run planning success is not validation success.",
    "Dry-run planning success is not validation failure.",
    "Dry-run planning success is not a persistence write.",
    "Explicit write success is local review-record persistence only.",
    "Explicit write success is not runtime reload acceptance.",
    "Explicit write success is not validation success.",
    "Explicit write success is not validation failure.",
    "Explicit write success is not ProjectSchema mutation.",
    "Explicit write success is not trust restoration.",
    "Explicit write success is not automatic activation.",
    "Explicit write success is not discovery success.",
    "Explicit write success is not dependency installation.",
    "Explicit write success is not solver execution.",
    "Explicit write success is not issue closure.",
    "Explicit write success is not release mutation.",
    "Explicit write success is not certification.",
    "Dry-run planning success is not ProjectSchema mutation.",
    "Dry-run planning success is not trust restoration.",
    "Dry-run planning success is not automatic activation.",
    "Command success is not runtime acceptance.",
    "Exit code 0 is command completion only.",
    "Exit code 0 is not validation success.",
    "Exit code 0 is not validation failure.",
    "Exit code 0 is not runtime acceptance.",
    "Exit code 0 is not persistence write.",
    "Persisted review records remain untrusted by default.",
    "Trust labels are not certification.",
    "Skipped-missing remains skipped-missing.",
    "Live issues #6 through #11 remain open.",
    "Prepared-machine validation remains separate.",
)

_NON_ACTION_DENIALS = (
    "Persistence CLI review subcommands perform no actual CLI writes.",
    (
        "Persistence CLI write performs only explicit local review-record writes "
        "through the OSW-EXP-126 writer."
    ),
    "Persistence CLI performs no runtime reload acceptance.",
    "Persistence CLI performs no active acceptance mutation.",
    "Persistence CLI reads no input state files.",
    "Persistence CLI parses no input state files.",
    "Persistence CLI invokes no reload file reader.",
    "Persistence CLI invokes no OSW-EXP-102 state writer.",
    "Persistence CLI calls no GUI code.",
    "Persistence CLI uses no subprocesses.",
    "Persistence CLI mutates no ProjectSchema.",
    "Persistence CLI uses no default target path.",
    "Persistence CLI performs no background write.",
    "Persistence CLI scans no directories.",
    "Persistence CLI fetches no network manifests.",
    "Persistence CLI imports no plugin packages.",
    "Persistence CLI creates no reloadable bundles.",
    "Persistence CLI creates no export files.",
    "Persistence CLI creates no report files.",
    "Persistence CLI uses no clipboard.",
    "Persistence CLI attaches no report.",
    "Persistence CLI opens no output folder.",
    "Persistence CLI performs no live discovery.",
    "Persistence CLI performs no passive refresh.",
    "Persistence CLI executes no validation.",
    "Persistence CLI executes no solver.",
    "Persistence CLI installs no dependencies.",
    "Persistence CLI uninstalls no dependencies.",
    "Persistence CLI uninstalls no solvers.",
    "Persistence CLI automatically activates no candidates.",
    "Persistence CLI restores no trust.",
    "Persistence CLI mutates no issues.",
    "Persistence CLI mutates no releases.",
    "Persistence CLI mutates no tags.",
    "Persistence CLI mutates no assets.",
    "Persistence CLI bumps no version.",
    "Persistence CLI claims no validation success.",
    "Persistence CLI claims no validation failure.",
    "Persistence CLI claims no issue closure.",
    "Persistence CLI claims no bundled solver.",
    "Persistence CLI claims no certification.",
)

_SCHEMA_MIGRATION_ROWS = (
    ("payload_kind_required", "required", "payload kind is required"),
    ("schema_version_required", "required", "schema version is required"),
    ("unsupported_schema_blocks", "blocks", "unsupported schema blocks"),
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
    ("automatic_activation", "no", "no automatic activation"),
    ("trust_restoration", "no", "no trust restoration"),
    ("built_in_override", "no", "persisted state does not override built-ins"),
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
        "CLI persistence review does not inspect source files",
    ),
    ("stale_source_is_validation_failure", "no", "stale source is not failure"),
    ("repreview_gate", "future", "re-preview remains future-gated"),
)

_CONFLICT_ROWS = (
    ("conflicts_visible", "yes", "conflicts are visible"),
    ("built_ins_win_by_default", "yes", "built-ins win by default"),
    ("persisted_state_overrides_built_ins", "no", "persisted state does not override"),
    ("shared_stack_warnings_visible", "yes", "shared-stack warnings are visible"),
    ("cli_resolves_conflicts", "no", "CLI does not resolve conflicts"),
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

_CLI_ACTION_ROWS = (
    ("request_persistence", False, True, "Persistence request mutation is future-gated."),
    ("plan_persistence_write", True, False, "Dry-run planning is implemented."),
    (
        "write_acceptance_review_record",
        True,
        False,
        "Explicit local review-record write is implemented only through write gates.",
    ),
    ("persist_acceptance_record", False, True, "Runtime persistence remains future-gated."),
)


def add_optional_solver_plugin_manifest_reload_acceptance_persistence_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the reload acceptance persistence review CLI command family."""

    parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND,
        help="Review reload acceptance persistence state, plans, and explicit writes.",
        description=(
            "Render deterministic in-memory reload acceptance persistence "
            "view-model records, dry-run writer plans, and explicit local "
            "review-record writes. This command is stdout-first, "
            "explicit-target-only, dry-run-first, acknowledgement-gated, "
            "confirmation-gated, non-reading, non-parsing, non-GUI, "
            "non-subprocess, ProjectSchema-safe, issue-safe, release-safe, "
            "and certification-safe."
        ),
    )
    parser.add_argument(
        "persistence_command",
        choices=_SUBCOMMANDS,
        help="Reload acceptance persistence review operation to perform.",
    )
    parser.add_argument(
        "--sample-state",
        action="store_true",
        help="Use deterministic representative in-memory persistence state.",
    )
    parser.add_argument(
        "--empty-state",
        action="store_true",
        help="Use deterministic empty/no-acceptance persistence state.",
    )
    parser.add_argument(
        "--unavailable-state",
        action="store_true",
        help="Use deterministic unavailable state; also the default.",
    )
    parser.add_argument(
        "--blocked-state",
        action="store_true",
        help="Use deterministic blocked persistence state.",
    )
    parser.add_argument(
        "--ready-state",
        action="store_true",
        help="Use deterministic ready/future-writer-only persistence state.",
    )
    parser.add_argument(
        "--writer-ready-state",
        action="store_true",
        help="Use the OSW-EXP-125 ready_for_future_writer sample.",
    )
    parser.add_argument(
        "--target",
        help="Explicit target path for dry-run plan or write review.",
    )
    parser.add_argument(
        "--allow-replace",
        action="store_true",
        help="Show replacement policy in dry-run writer planning.",
    )
    parser.add_argument(
        "--acknowledge-persistence-write",
        action="store_true",
        help="Acknowledge that any write is local review-record persistence only.",
    )
    parser.add_argument(
        "--confirm-persistence-write",
        action="store_true",
        help="Confirm the explicit local write after dry-run planning.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON.")
    return parser


def run_optional_solver_plugin_manifest_reload_acceptance_persistence_cli(
    args: argparse.Namespace,
) -> int:
    """Run a bounded persistence review operation."""

    validation_error = _validate_args(args)
    if validation_error:
        _emit({"error": validation_error}, [validation_error], args, error=True)
        return 2

    view_model, state_source = _view_model_from_args(args)
    plan_result = _plan_result(args, view_model)
    write_result = _write_result(args, view_model)
    exit_code = _return_code(args.persistence_command, write_result)
    payload = _payload(args, view_model, state_source, plan_result, write_result, exit_code)
    text_lines = _text_lines(args, view_model, state_source, plan_result, write_result, exit_code)
    disabled_future = args.persistence_command == "write-future"
    _emit(payload, text_lines, args, error=disabled_future or exit_code != 0)
    return exit_code


def _validate_args(args: argparse.Namespace) -> str:
    selected = [bool(getattr(args, flag, False)) for flag in _STATE_SOURCE_FLAGS]
    if sum(1 for value in selected if value) > 1:
        return (
            "Select only one persistence state source: --sample-state, "
            "--empty-state, --unavailable-state, --blocked-state, "
            "--ready-state, or --writer-ready-state."
        )
    target = str(getattr(args, "target", "") or "").strip()
    if target and args.persistence_command not in {"plan", "write", "write-future"}:
        return "--target is accepted only for plan, write, and write-future review."
    return ""


def _view_model_from_args(
    args: argparse.Namespace,
) -> tuple[OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel, str]:
    if args.sample_state:
        return _sample_state(), "deterministic representative in-memory state"
    if args.empty_state:
        return (
            OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.unavailable(
                "No reload acceptance persistence view-model was supplied."
            ),
            "deterministic empty in-memory state",
        )
    if args.blocked_state:
        return _blocked_state(), "deterministic blocked in-memory state"
    if args.ready_state:
        return _ready_state(), "deterministic ready in-memory state"
    if args.writer_ready_state:
        return (
            OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.ready_for_future_writer(
                _ready_acceptance()
            ),
            "deterministic writer-ready in-memory state",
        )
    if args.unavailable_state:
        return (
            OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.unavailable(),
            "deterministic unavailable in-memory state",
        )
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.unavailable(),
        "unavailable in-memory state; no input file is read",
    )


def _ready_reload() -> OptionalSolverPluginManifestReloadViewModel:
    return OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()


def _ready_acceptance() -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    return OptionalSolverPluginManifestReloadAcceptanceViewModel.ready_for_future_acceptance(
        _ready_reload()
    )


def _sample_state() -> (
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
):
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_viewmodel(
            _ready_acceptance(),
            persistence_requested=True,
            acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS[:8],
            expired_acknowledgements=(
                RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS[2],
            ),
            storage_policy_id="explicit_user_selected_path",
            storage_label="Explicit user-selected local state path",
            target_display="sample-acceptance-state.json",
            policy_flags=_blocked_policy_flags(),
        )
    )


def _blocked_state() -> (
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
):
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_viewmodel(
            _ready_acceptance(),
            persistence_requested=True,
            acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS[:4],
            storage_policy_id="explicit_user_selected_path",
            storage_label="Explicit user-selected local state path",
            target_display="blocked-acceptance-state.json",
            policy_flags=_blocked_policy_flags(),
        )
    )


def _ready_state() -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_viewmodel(
            _ready_acceptance(),
            persistence_requested=True,
            acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
            storage_policy_id="explicit_user_selected_path",
            storage_label="Explicit user-selected local state path",
            target_display="reload-acceptance-state.json",
            dry_run_confirmed=True,
        )
    )


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
        "persistence_policy_changed": True,
    }


def _plan_result(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
) -> Mapping[str, object] | None:
    if args.persistence_command != "plan":
        return None
    request = ReloadAcceptancePersistenceWriteRequest(
        persistence_viewmodel=view_model,
        target_path=args.target,
        dry_run=True,
        allow_replace=bool(args.allow_replace),
        caller_acknowledged_persistence_write=bool(
            args.acknowledge_persistence_write
        ),
        request_context="reload_acceptance_persistence_cli_dry_run_plan",
    )
    return plan_reload_acceptance_persistence_write(request).to_mapping()


def _write_result(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
) -> Mapping[str, object] | None:
    if args.persistence_command != "write":
        return None
    target = str(args.target or "").strip()
    if not target:
        return _cli_write_blocked(
            "write_target_required",
            "Explicit --target is required before CLI persistence write.",
            args.target,
        )
    if not bool(args.acknowledge_persistence_write):
        return _cli_write_blocked(
            "write_ack_required",
            "--acknowledge-persistence-write is required before CLI persistence write.",
            args.target,
        )
    if not bool(args.confirm_persistence_write):
        return _cli_write_blocked(
            "write_confirm_required",
            "--confirm-persistence-write is required before CLI persistence write.",
            args.target,
        )

    dry_run_request = ReloadAcceptancePersistenceWriteRequest(
        persistence_viewmodel=view_model,
        target_path=args.target,
        dry_run=True,
        allow_replace=bool(args.allow_replace),
        caller_acknowledged_persistence_write=True,
        safety_review_id="OSW-EXP-134_CLI_WRITE_DRY_RUN",
        request_context="reload_acceptance_persistence_cli_write_dry_run",
    )
    dry_run_plan = _result_to_mapping(
        write_reload_acceptance_persistence_record(dry_run_request)
    )
    dry_run_status = str(dry_run_plan.get("status") or "")
    if dry_run_status != "planned":
        status = "error" if dry_run_status == "error" else "blocked"
        return {
            "status": status,
            "phase": "dry_run",
            "target_display": _safe_display(args.target),
            "target_redacted": True,
            "dry_run_plan": dry_run_plan,
            "writer_result": None,
            "diagnostics": _write_diagnostics_from(
                status,
                "write_blocked" if status == "blocked" else "write_error",
                "CLI persistence write stopped because dry-run planning did not pass.",
                dry_run_plan,
                None,
            ),
            "blockers": list(_sequence(dry_run_plan.get("blockers"))),
            "warnings": list(_sequence(dry_run_plan.get("warnings"))),
            "non_action_flags": _state_source_policy(),
            "write_performed": False,
            "persistence_write_performed": False,
            "runtime_reload_acceptance_performed": False,
            "project_schema_mutated": False,
        }

    write_request = ReloadAcceptancePersistenceWriteRequest(
        persistence_viewmodel=view_model,
        target_path=args.target,
        dry_run=False,
        allow_replace=bool(args.allow_replace),
        caller_acknowledged_persistence_write=True,
        safety_review_id="OSW-EXP-134_CLI_WRITE_CONFIRMED",
        request_context="reload_acceptance_persistence_cli_write_confirmed",
    )
    writer_result = _result_to_mapping(
        write_reload_acceptance_persistence_record(write_request)
    )
    status = str(writer_result.get("status") or "")
    diagnostic_key = (
        "write_completed_local_only"
        if status == "completed"
        else "write_error"
        if status == "error"
        else "write_blocked"
    )
    message = (
        "CLI persistence write completed local review-record persistence only."
        if status == "completed"
        else "CLI persistence write did not complete."
    )
    return {
        "status": status,
        "phase": "write",
        "target_display": writer_result.get("target_display", _safe_display(args.target)),
        "target_redacted": True,
        "dry_run_plan": dry_run_plan,
        "writer_result": writer_result,
        "diagnostics": _write_diagnostics_from(
            status,
            diagnostic_key,
            message,
            dry_run_plan,
            writer_result,
        ),
        "blockers": list(_sequence(writer_result.get("blockers"))),
        "warnings": list(_sequence(writer_result.get("warnings"))),
        "non_action_flags": _mapping(writer_result.get("non_action_flags")),
        "write_performed": bool(writer_result.get("write_performed")),
        "persistence_write_performed": bool(
            writer_result.get("persistence_write_performed")
        ),
        "runtime_reload_acceptance_performed": False,
        "project_schema_mutated": False,
    }


def _cli_write_blocked(
    diagnostic_key: str,
    message: str,
    target: object,
) -> dict[str, object]:
    return {
        "status": "blocked",
        "phase": "cli_gate",
        "target_display": _safe_display(target),
        "target_redacted": True,
        "dry_run_plan": None,
        "writer_result": None,
        "diagnostics": [
            {
                "severity": "error",
                "code": _CLI_DIAGNOSTICS[diagnostic_key],
                "message": message,
                "blocker": True,
                "target_display": _safe_display(target),
            },
            {
                "severity": "info",
                "code": _CLI_DIAGNOSTICS["write_no_validation_claim"],
                "message": "CLI write gating makes no validation or certification claim.",
                "blocker": False,
                "target_display": _safe_display(target),
            },
        ],
        "blockers": [message],
        "warnings": [],
        "non_action_flags": _state_source_policy(),
        "write_performed": False,
        "persistence_write_performed": False,
        "runtime_reload_acceptance_performed": False,
        "project_schema_mutated": False,
    }


def _write_diagnostics_from(
    status: str,
    diagnostic_key: str,
    message: str,
    dry_run_plan: Mapping[str, object],
    writer_result: Mapping[str, object] | None,
) -> list[object]:
    rows: list[object] = [
        {
            "severity": "info" if status == "completed" else "error",
            "code": _CLI_DIAGNOSTICS[diagnostic_key],
            "message": message,
            "blocker": status != "completed",
            "target_display": str(dry_run_plan.get("target_display") or ""),
        },
        {
            "severity": "info",
            "code": _CLI_DIAGNOSTICS["write_dry_run_not_write"],
            "message": "The required dry-run plan is not a write.",
            "blocker": False,
            "target_display": str(dry_run_plan.get("target_display") or ""),
        },
        {
            "severity": "info",
            "code": _CLI_DIAGNOSTICS["write_no_validation_claim"],
            "message": "Write success is not validation success, failure, or certification.",
            "blocker": False,
            "target_display": str(dry_run_plan.get("target_display") or ""),
        },
    ]
    rows.extend(_sequence(dry_run_plan.get("diagnostics")))
    if writer_result is not None:
        rows.extend(_sequence(writer_result.get("diagnostics")))
    return rows


def _result_to_mapping(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return dict(value)
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return dict(mapped)
    return {}


def _payload(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
    state_source: str,
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
    exit_code: int,
) -> dict[str, object]:
    mapping = view_model.to_mapping()
    payload = {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND,
        "subcommand": args.persistence_command,
        "purpose": _COMMAND_PURPOSE[args.persistence_command],
        "stdout_first": True,
        "dry_run_only": args.persistence_command != "write",
        "dry_run_first": True,
        "actual_cli_writes_enabled": args.persistence_command == "write",
        "write_future_disabled": True,
        "state_source": state_source,
        "state_source_policy": _state_source_policy(write_result),
        "target_policy": _target_policy(args, write_result),
        "output_mode": "json" if args.json else "text",
        "view_model": mapping,
        "summary": mapping["summary"],
        "write_plan": mapping["write_plan"],
        "storage": mapping["storage_options"],
        "schema": mapping["schema"],
        "acknowledgements": mapping["acknowledgements"],
        "acknowledgement_expiry": mapping["acknowledgement_expiry"],
        "expiry_reasons": mapping["expiry_reasons"],
        "blockers": mapping["blockers"],
        "diagnostics": _diagnostic_payload(mapping, plan_result, write_result, args),
        "provenance": mapping["provenance"],
        "schema_migration": _table_payload(_SCHEMA_MIGRATION_ROWS),
        "redaction_privacy": _table_payload(_REDACTION_PRIVACY_ROWS),
        "candidate_lifecycle": _table_payload(_CANDIDATE_LIFECYCLE_ROWS),
        "stale_source_repreview": _table_payload(_STALE_SOURCE_ROWS),
        "conflict_shared_stack": _table_payload(_CONFLICT_ROWS),
        "unsafe_claims": _table_payload(_UNSAFE_CLAIM_ROWS),
        "evidence_history": mapping["evidence_history"],
        "non_action_flags": _non_action_flags(mapping, plan_result, write_result),
        "disabled_future_actions": _action_payload(mapping),
        "safety_guidance": list(_SAFETY_GUIDANCE),
        "exit_semantics": _exit_semantics(args.persistence_command, exit_code),
        "writer_plan_result": plan_result,
        "dry_run_plan": _write_dry_run_plan(write_result),
        "write_result": write_result,
        "selected": _selected_payload(args, mapping, plan_result, write_result),
    }
    return _redact_payload(payload, args.target)


def _state_source_policy(
    write_result: Mapping[str, object] | None = None,
) -> dict[str, bool]:
    completed = _write_completed(write_result)
    return {
        "deterministic_in_memory_persistence_viewmodel_records_only": True,
        "input_state_file_read": False,
        "input_state_file_parsed": False,
        "reload_file_reader_invoked": False,
        "state_writer_invoked": False,
        "actual_cli_write_performed": completed,
        "writer_called_with_dry_run_false": completed,
        "file_reading_performed": False,
        "file_parsing_performed": False,
        "gui_call_performed": False,
        "cli_subprocess_used": False,
        "gui_subprocess_used": False,
        "runtime_reload_acceptance_performed": False,
        "active_acceptance_mutation_performed": False,
        "persistence_write_performed": completed,
        "project_schema_mutated": False,
        "default_target_path_used": False,
        "background_write_performed": False,
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
        "validation_pass_claimed": False,
        "validation_fail_claimed": False,
        "issue_closure_claimed": False,
        "bundled_solver_claimed": False,
        "certification_claimed": False,
    }


def _target_policy(
    args: argparse.Namespace,
    write_result: Mapping[str, object] | None,
) -> dict[str, object]:
    selected = bool(str(args.target or "").strip())
    return {
        "explicit_target_required_for_plan": True,
        "explicit_target_required_for_write": True,
        "target_supplied": selected,
        "target_display": _safe_display(args.target),
        "raw_target_display_hidden": True,
        "default_target_path_used": False,
        "background_write_performed": False,
        "actual_cli_write_performed": _write_completed(write_result),
        "write_future_accepts_target_for_review_only": (
            args.persistence_command == "write-future"
        ),
        "allow_replace": bool(args.allow_replace),
        "caller_acknowledged_persistence_write": bool(
            args.acknowledge_persistence_write
        ),
        "caller_confirmed_persistence_write": bool(
            getattr(args, "confirm_persistence_write", False)
        ),
    }


def _diagnostic_payload(
    mapping: Mapping[str, object],
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
    args: argparse.Namespace,
) -> list[object]:
    rows: list[object] = [
        {
            "severity": "info",
            "code": _CLI_DIAGNOSTICS["safety_guidance"],
            "message": "Persistence CLI safety guidance rendered.",
            "blocker": False,
        },
    ]
    if args.persistence_command == "write":
        rows.append(
            {
                "severity": "info",
                "code": _CLI_DIAGNOSTICS["write_dry_run_not_write"],
                "message": "Persistence CLI write requires a dry-run plan first.",
                "blocker": False,
            }
        )
    else:
        rows.append(
            {
                "severity": "info",
                "code": _CLI_DIAGNOSTICS["dry_run_only"],
                "message": "Persistence CLI review uses dry-run writer planning only.",
                "blocker": False,
            }
        )
    if args.persistence_command == "write-future":
        rows.append(
            {
                "severity": "error",
                "code": _CLI_DIAGNOSTICS["write_future_disabled"],
                "message": "Actual CLI persistence writing is disabled.",
                "blocker": True,
            }
        )
    if args.persistence_command == "plan":
        if not args.target:
            rows.append(
                {
                    "severity": "error",
                    "code": _CLI_DIAGNOSTICS["target_required"],
                    "message": "Dry-run plan review requires explicit --target.",
                    "blocker": True,
                }
            )
        rows.append(
            {
                "severity": "info",
                "code": _CLI_DIAGNOSTICS["writer_plan_rendered"],
                "message": "Writer result rendered from dry-run planning.",
                "blocker": False,
            }
        )
    rows.extend(_sequence(mapping.get("diagnostics")))
    if plan_result is not None:
        rows.extend(_sequence(plan_result.get("diagnostics")))
    if write_result is not None:
        rows.extend(_sequence(write_result.get("diagnostics")))
    return rows


def _non_action_flags(
    mapping: Mapping[str, object],
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
) -> dict[str, bool]:
    flags = _state_source_policy(write_result)
    flags.update(dict(_mapping(mapping.get("non_action_flags"))))
    if plan_result is not None:
        flags.update(dict(_mapping(plan_result.get("non_action_flags"))))
    dry_run_plan = _write_dry_run_plan(write_result)
    if dry_run_plan is not None:
        flags.update(dict(_mapping(dry_run_plan.get("non_action_flags"))))
    writer_result = _mapping(_mapping(write_result).get("writer_result"))
    if writer_result:
        flags.update(dict(_mapping(writer_result.get("non_action_flags"))))
    completed = _write_completed(write_result)
    flags["actual_cli_write_performed"] = completed
    flags["writer_called_with_dry_run_false"] = completed
    flags["dry_run_writer_plan_rendered"] = plan_result is not None
    flags["runtime_reload_acceptance_performed"] = False
    flags["active_acceptance_mutation_performed"] = False
    flags["project_schema_mutated"] = False
    flags["validation_executed"] = False
    flags["solver_executed"] = False
    flags["candidate_activated"] = False
    flags["trust_restored"] = False
    flags["issue_mutated"] = False
    flags["release_mutated"] = False
    flags["tag_mutated"] = False
    flags["asset_mutated"] = False
    flags["version_bumped"] = False
    flags["validation_pass_claimed"] = False
    flags["validation_fail_claimed"] = False
    flags["issue_closure_claimed"] = False
    flags["bundled_solver_claimed"] = False
    flags["certification_claimed"] = False
    return {str(key): bool(value) for key, value in sorted(flags.items())}


def _action_payload(mapping: Mapping[str, object]) -> list[dict[str, object]]:
    rows = [
        {
            "action": action,
            "enabled": enabled,
            "future_only": future_only,
            "reason": reason,
        }
        for action, enabled, future_only, reason in _CLI_ACTION_ROWS
    ]
    rows.extend(dict(row) for row in _mapping_list(mapping.get("actions")))
    return rows


def _selected_payload(
    args: argparse.Namespace,
    mapping: Mapping[str, object],
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
) -> object:
    if args.persistence_command == "plan":
        return plan_result or mapping["write_plan"]
    if args.persistence_command == "write":
        return write_result
    if args.persistence_command == "diagnostics":
        return _diagnostic_payload(mapping, plan_result, write_result, args)
    if args.persistence_command == "acknowledgements":
        return mapping["acknowledgements"]
    if args.persistence_command == "expiry":
        return mapping["acknowledgement_expiry"]
    if args.persistence_command == "storage":
        return {
            "storage": mapping["storage_options"],
            "schema": mapping["schema"],
            "write_plan": mapping["write_plan"],
        }
    if args.persistence_command == "actions":
        return _action_payload(mapping)
    if args.persistence_command == "safety":
        return list(_SAFETY_GUIDANCE)
    return mapping


def _write_dry_run_plan(
    write_result: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    if write_result is None:
        return None
    dry_run_plan = _mapping(write_result.get("dry_run_plan"))
    return dry_run_plan or None


def _write_completed(write_result: Mapping[str, object] | None) -> bool:
    if write_result is None:
        return False
    writer_result = _mapping(write_result.get("writer_result"))
    return (
        str(write_result.get("status") or "") == "completed"
        and bool(writer_result.get("write_performed"))
        and bool(writer_result.get("persistence_write_performed"))
    )


def _text_lines(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
    state_source: str,
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
    exit_code: int,
) -> list[str]:
    mapping = view_model.to_mapping()
    lines = _header_lines(args, mapping, state_source)
    if args.persistence_command == "write-future":
        lines.extend(_write_future_lines(args))
    elif args.persistence_command == "explain":
        lines.extend(_explain_lines())

    if args.persistence_command == "preview":
        lines.extend(_summary_lines(mapping))
        lines.extend(_plan_lines(mapping, plan_result))
        lines.extend(_storage_lines(mapping, args))
        lines.extend(_acknowledgement_lines(mapping))
        lines.extend(_expiry_lines(mapping))
        lines.extend(_schema_migration_lines(mapping))
        lines.extend(_redaction_privacy_lines())
        lines.extend(_provenance_lines(mapping))
        lines.extend(_candidate_lifecycle_lines())
        lines.extend(_stale_source_lines())
        lines.extend(_conflict_lines())
        lines.extend(_unsafe_claim_lines())
        lines.extend(_evidence_history_lines(mapping))
        lines.extend(_diagnostic_lines(mapping, plan_result, write_result, args))
        lines.extend(_non_action_flag_lines(mapping, plan_result, write_result))
        lines.extend(_action_lines(mapping))
        lines.extend(_safety_lines())
    elif args.persistence_command == "plan":
        lines.extend(_plan_lines(mapping, plan_result))
        lines.extend(_storage_lines(mapping, args))
        lines.extend(_diagnostic_lines(mapping, plan_result, write_result, args))
        lines.extend(_safety_lines())
    elif args.persistence_command == "write":
        lines.extend(_write_lines(args, write_result))
        lines.extend(_storage_lines(mapping, args))
        lines.extend(_diagnostic_lines(mapping, plan_result, write_result, args))
        lines.extend(_non_action_flag_lines(mapping, plan_result, write_result))
        lines.extend(_safety_lines())
    elif args.persistence_command == "diagnostics":
        lines.extend(_diagnostic_lines(mapping, plan_result, write_result, args))
    elif args.persistence_command == "acknowledgements":
        lines.extend(_acknowledgement_lines(mapping))
    elif args.persistence_command == "expiry":
        lines.extend(_expiry_lines(mapping))
    elif args.persistence_command == "storage":
        lines.extend(_storage_lines(mapping, args))
        lines.extend(_schema_migration_lines(mapping))
    elif args.persistence_command == "actions":
        lines.extend(_action_lines(mapping))
    elif args.persistence_command == "safety":
        lines.extend(_safety_lines())

    if args.persistence_command not in {"preview", "plan", "safety"}:
        lines.extend(_safety_lines())
    lines.extend(_exit_lines(args.persistence_command, exit_code))
    return _redact_lines(lines, args.target)


def _header_lines(
    args: argparse.Namespace,
    mapping: Mapping[str, object],
    state_source: str,
) -> list[str]:
    summary = _mapping(mapping.get("summary"))
    return [
        "Optional Solver Plugin Manifest Reload Acceptance Persistence CLI",
        f"command: {OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND}",
        f"subcommand: {args.persistence_command}",
        f"purpose: {_COMMAND_PURPOSE[args.persistence_command]}",
        f"state source: {state_source}",
        (
            "state source policy: deterministic in-memory persistence "
            "view-model records only; no input state-file reading; no input "
            "state-file parsing; no reload file-reader invocation; no "
            "OSW-EXP-102 state-writer invocation; no GUI calls; no subprocess "
            "use; review subcommands perform no actual CLI writes; explicit "
            "write subcommand writes only through OSW-EXP-126 writer after "
            "dry-run/ack/confirm gates; no ProjectSchema mutation"
        ),
        f"state: {summary.get('state')}",
        f"readiness: {summary.get('readiness')}",
        f"persistence_requested: {summary.get('persistence_requested')}",
        f"acceptance_available: {summary.get('acceptance_available')}",
        (
            "accepted_for_session_review: "
            f"{summary.get('accepted_for_session_review')}"
        ),
        (
            "ready_for_future_write_plan: "
            f"{summary.get('ready_for_future_write_plan')}"
        ),
        f"actual_cli_writes_enabled: {args.persistence_command == 'write'}",
        "write_future: disabled_future_only",
    ]


def _explain_lines() -> list[str]:
    return [
        "Definition:",
        "- The command renders reload acceptance persistence review records.",
        "- The command consumes deterministic in-memory view-model records only.",
        "- The plan command calls the writer only with dry_run=True.",
        "- The plan command creates no file.",
        "- The write command calls the writer first with dry_run=True.",
        (
            "- The write command calls the writer with dry_run=False only after "
            "explicit --target, --acknowledge-persistence-write, and "
            "--confirm-persistence-write gates pass."
        ),
        "- The write command creates only an explicit local review record.",
        "- write-future remains disabled and non-mutating.",
        "Non-actions:",
        *[f"- {line}" for line in _NON_ACTION_DENIALS],
    ]


def _write_future_lines(args: argparse.Namespace) -> list[str]:
    return [
        "Write-future:",
        "- status: disabled/future-only.",
        "- result_code: 2.",
        "- no file is created even when --target is supplied.",
        "- non-dry-run writer calls are unavailable from this CLI.",
        f"- target_display: {_safe_display(args.target)}",
    ]


def _summary_lines(mapping: Mapping[str, object]) -> list[str]:
    summary = _mapping(mapping.get("summary"))
    return [
        "Summary/readiness:",
        f"- state: {summary.get('state')}",
        f"- readiness: {summary.get('readiness')}",
        f"- persistence_requested: {summary.get('persistence_requested')}",
        f"- acceptance_available: {summary.get('acceptance_available')}",
        f"- accepted_for_session_review: {summary.get('accepted_for_session_review')}",
        (
            "- ready_for_future_write_plan: "
            f"{summary.get('ready_for_future_write_plan')}"
        ),
        f"- storage_policy_id: {summary.get('storage_policy_id')}",
        f"- blocker_count: {summary.get('blocker_count')}",
        f"- diagnostic_count: {summary.get('diagnostic_count')}",
        "- no validation: yes",
        "- no validation failure: yes",
        "- no persistence write: yes",
        "- no ProjectSchema mutation: yes",
        "- no activation: yes",
        "- no trust restoration: yes",
        "- no discovery: yes",
        "- no solver execution: yes",
        "- no issue/release mutation: yes",
        "- no certification: yes",
    ]


def _plan_lines(
    mapping: Mapping[str, object],
    plan_result: Mapping[str, object] | None,
) -> list[str]:
    plan = _mapping(mapping.get("write_plan"))
    lines = [
        "Dry-run/write-plan:",
        "- actual_cli_write_performed: False",
        "- writer_called_with_dry_run_false: False",
        f"- view_model_target_display: {plan.get('target_display')}",
        f"- view_model_dry_run_required: {plan.get('dry_run_required')}",
        f"- view_model_writer_future_only: {plan.get('writer_future_only')}",
        f"- view_model_write_performed: {plan.get('write_performed')}",
        (
            "- view_model_persistence_write_performed: "
            f"{plan.get('persistence_write_performed')}"
        ),
    ]
    if plan_result is None:
        return lines
    lines.extend(
        [
            f"- writer_status: {plan_result.get('status')}",
            f"- writer_target_display: {plan_result.get('target_display')}",
            f"- writer_target_redacted: {plan_result.get('target_redacted')}",
            f"- writer_dry_run: {plan_result.get('dry_run')}",
            f"- writer_planned: {plan_result.get('planned')}",
            f"- writer_written: {plan_result.get('written')}",
            f"- writer_bytes_count: {plan_result.get('bytes_count')}",
            f"- writer_sha256: {plan_result.get('sha256')}",
            f"- writer_write_performed: {plan_result.get('write_performed')}",
            (
                "- writer_persistence_write_performed: "
                f"{plan_result.get('persistence_write_performed')}"
            ),
        ]
    )
    for row in _mapping_list(plan_result.get("diagnostics")):
        lines.append(
            "- writer diagnostic: "
            f"{row.get('severity')} {row.get('code')} blocker={row.get('blocker')}"
        )
    return lines


def _write_lines(
    args: argparse.Namespace,
    write_result: Mapping[str, object] | None,
) -> list[str]:
    result = _mapping(write_result)
    dry_run_plan = _mapping(result.get("dry_run_plan"))
    writer_result = _mapping(result.get("writer_result"))
    status = str(result.get("status") or "blocked")
    lines = [
        "Write:",
        f"- status: {status}",
        f"- phase: {result.get('phase')}",
        "- explicit_target_required: True",
        f"- target_selected: {bool(str(args.target or '').strip())}",
        f"- target_display: {_safe_display(args.target)}",
        "- raw_target_display_hidden: True",
        f"- acknowledgement_supplied: {bool(args.acknowledge_persistence_write)}",
        (
            "- confirmation_supplied: "
            f"{bool(getattr(args, 'confirm_persistence_write', False))}"
        ),
        f"- allow_replace: {bool(args.allow_replace)}",
        "- dry_run_first: True",
        f"- dry_run_status: {dry_run_plan.get('status')}",
        f"- dry_run_planned: {dry_run_plan.get('planned')}",
        f"- dry_run_written: {dry_run_plan.get('written')}",
        "- dry_run_is_not_write: True",
        f"- writer_status: {writer_result.get('status')}",
        f"- writer_target_display: {writer_result.get('target_display')}",
        f"- writer_target_redacted: {writer_result.get('target_redacted')}",
        f"- writer_dry_run: {writer_result.get('dry_run')}",
        f"- writer_planned: {writer_result.get('planned')}",
        f"- writer_written: {writer_result.get('written')}",
        f"- writer_bytes_count: {writer_result.get('bytes_count')}",
        f"- writer_sha256: {writer_result.get('sha256')}",
        f"- writer_write_performed: {writer_result.get('write_performed')}",
        (
            "- writer_persistence_write_performed: "
            f"{writer_result.get('persistence_write_performed')}"
        ),
        (
            "- writer_runtime_reload_acceptance_performed: "
            f"{writer_result.get('runtime_reload_acceptance_performed')}"
        ),
        (
            "- writer_project_schema_mutated: "
            f"{writer_result.get('project_schema_mutated')}"
        ),
        f"- cleanup_performed: {writer_result.get('cleanup_performed')}",
        f"- temp_file_used: {writer_result.get('temp_file_used')}",
        (
            "- atomic_replace_performed: "
            f"{writer_result.get('atomic_replace_performed')}"
        ),
        "- local review-record persistence only.",
        "- write success is not runtime acceptance.",
        "- write success is not validation success.",
        "- write success is not validation failure.",
        "- write success is not ProjectSchema mutation.",
        "- write success is not trust restoration.",
        "- write success is not automatic activation.",
        "- write success is not issue closure.",
        "- write success is not release mutation.",
        "- write success is not certification.",
    ]
    for row in _mapping_list(result.get("diagnostics")):
        lines.append(
            "- write diagnostic: "
            f"{row.get('severity')} {row.get('code')} "
            f"blocker={row.get('blocker')}: {row.get('message')}"
        )
    return lines


def _storage_lines(mapping: Mapping[str, object], args: argparse.Namespace) -> list[str]:
    target_display = _safe_display(args.target)
    lines = [
        "Storage/target policy:",
        "- explicit target path is required for dry-run plan and write output.",
        f"- target_selected: {bool(str(args.target or '').strip())}",
        f"- target_display: {target_display}",
        "- raw_target_display_hidden: True",
        "- default_target_path_used: False",
        "- background_write_performed: False",
        "- directory_scan_performed: False",
        "- directory_creation_performed: False",
        f"- allow_replace: {bool(args.allow_replace)}",
        (
            "- caller_acknowledged_persistence_write: "
            f"{bool(args.acknowledge_persistence_write)}"
        ),
        (
            "- caller_confirmed_persistence_write: "
            f"{bool(getattr(args, 'confirm_persistence_write', False))}"
        ),
    ]
    for row in _mapping_list(mapping.get("storage_options")):
        lines.append(
            "- storage: "
            f"{row.get('storage_policy_id')} "
            f"explicit_user_selected={row.get('explicit_user_selected')} "
            f"default_path_used={row.get('default_path_used')} "
            f"allowed_in_this_gate={row.get('allowed_in_this_gate')} "
            f"future_only={row.get('future_only')}"
        )
    return lines


def _acknowledgement_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Acknowledgements:",
        "- acknowledgement is not validation evidence.",
        "- acknowledgement is not validation failure.",
        "- acknowledgement is not trust restoration.",
        "- required acknowledgements:",
    ]
    for ack_id in RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS:
        lines.append(f"  - {ack_id}")
    for row in _mapping_list(mapping.get("acknowledgements")):
        lines.append(
            "- "
            f"{row.get('acknowledgement_id')}: "
            f"required={row.get('required')}; "
            f"satisfied={row.get('satisfied')}; "
            f"expired={row.get('expired')}; "
            f"blocking={row.get('blocking')}; "
            "acknowledgement_is_validation_evidence="
            f"{row.get('acknowledgement_is_validation_evidence')}; "
            "acknowledgement_restores_trust="
            f"{row.get('acknowledgement_restores_trust')}"
        )
    return lines


def _expiry_lines(mapping: Mapping[str, object]) -> list[str]:
    reasons = _sequence(mapping.get("expiry_reasons")) or (
        RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS
    )
    lines = ["Acknowledgement expiry:", *[f"- {reason}" for reason in reasons]]
    for row in _mapping_list(mapping.get("acknowledgement_expiry")):
        lines.append(
            "- expiry row: "
            f"{row.get('reason_id')} active={row.get('active')} "
            f"blocks_when_triggered={row.get('blocks_when_triggered')}"
        )
    return lines


def _schema_migration_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = _table_lines("Schema/migration:", _SCHEMA_MIGRATION_ROWS)
    for row in _mapping_list(mapping.get("schema")):
        lines.append(
            "- schema: "
            f"{row.get('schema_id')} version={row.get('schema_version')} "
            f"payload_kind={row.get('payload_kind')} "
            f"schema_supported={row.get('schema_supported')} "
            f"migration_required={row.get('migration_required')} "
            "separate_from_project_schema="
            f"{row.get('separate_from_project_schema')}"
        )
    return lines


def _redaction_privacy_lines() -> list[str]:
    return _table_lines("Redaction/privacy:", _REDACTION_PRIVACY_ROWS)


def _provenance_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = [
        "Provenance:",
        "- provenance is redacted and non-authoritative.",
        "- payload fingerprints are not trust signals.",
        "- raw absolute paths, secrets, tokens, and API keys are not shown.",
    ]
    for row in _mapping_list(mapping.get("provenance")):
        lines.append(
            "- "
            f"{row.get('provenance_id')}: "
            f"source_display={row.get('source_display')}; "
            f"redacted={row.get('source_reference_redacted')}; "
            f"untrusted_by_default={row.get('untrusted_by_default')}; "
            "trust_label_not_certification="
            f"{row.get('trust_label_not_certification')}"
        )
    return lines


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
        "- evidence/history is reference-only.",
        "- skipped-missing remains skipped-missing.",
        "- no evidence deletion or rewrite.",
        "- no issue closure implied.",
    ]
    for row in _mapping_list(mapping.get("evidence_history")):
        lines.append(
            "- "
            f"{row.get('evidence_id')}: "
            f"type={row.get('evidence_type')}; "
            f"not_validation_evidence={row.get('not_validation_evidence')}; "
            f"not_validation_failure={row.get('not_validation_failure')}; "
            f"issue_closure_implied={row.get('issue_closure_implied')}"
        )
    return lines


def _diagnostic_lines(
    mapping: Mapping[str, object],
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
    args: argparse.Namespace,
) -> list[str]:
    lines = ["Diagnostics:"]
    for row in _diagnostic_payload(mapping, plan_result, write_result, args):
        diagnostic = _mapping(row)
        lines.append(
            "- "
            f"{diagnostic.get('severity')} {diagnostic.get('code')} "
            f"blocker={diagnostic.get('blocker')}: "
            f"{diagnostic.get('message')}"
        )
    return lines


def _non_action_flag_lines(
    mapping: Mapping[str, object],
    plan_result: Mapping[str, object] | None,
    write_result: Mapping[str, object] | None,
) -> list[str]:
    lines = ["Non-action flags:"]
    for key, value in _non_action_flags(mapping, plan_result, write_result).items():
        lines.append(f"- {key}: {value}")
    return lines


def _action_lines(mapping: Mapping[str, object]) -> list[str]:
    lines = ["Disabled/future actions:"]
    for row in _action_payload(mapping):
        lines.append(
            "- "
            f"{row.get('action')}: enabled={row.get('enabled')} "
            f"future_only={row.get('future_only')} reason={row.get('reason')}"
        )
    return lines


def _safety_lines() -> list[str]:
    return ["Safety guidance:", *[f"- {line}" for line in _SAFETY_GUIDANCE]]


def _exit_lines(command: str, exit_code: int) -> list[str]:
    semantics = _exit_semantics(command, exit_code)
    lines = [
        "Exit-code policy:",
        f"- command_completion_code: {semantics['command_completion_code']}",
        f"- this_command_return_code: {semantics['this_command_return_code']}",
        "- exit code 0 is not validation success.",
        "- exit code 0 is not validation failure.",
        "- exit code 0 is not runtime acceptance.",
    ]
    if command != "write":
        lines.append("- exit code 0 is not persistence write.")
    else:
        lines.append(
            "- exit code 0 does not imply any write beyond the reported local "
            "review-record writer result."
        )
    lines.extend(
        [
            "- exit code 0 is not ProjectSchema mutation.",
            "- exit code 0 is not issue closure.",
            "- exit code 0 is not release mutation.",
            "- exit code 0 is not certification.",
        ]
    )
    return lines

def _return_code(
    command: str,
    write_result: Mapping[str, object] | None,
) -> int:
    if command == "write-future":
        return 2
    if command != "write":
        return 0
    status = str(_mapping(write_result).get("status") or "")
    if status == "completed":
        return 0
    if status == "error":
        return 1
    return 2


def _exit_semantics(command: str, exit_code: int) -> dict[str, object]:
    return {
        "command_completion_code": 0,
        "this_command_return_code": exit_code,
        "validation_success": False,
        "validation_failure": False,
        "runtime_acceptance": False,
        "persistence_write": False,
        "local_review_record_write_command": command == "write",
        "project_schema_mutation": False,
        "trust_restoration": False,
        "activation": False,
        "issue_closure": False,
        "release_mutation": False,
        "certification": False,
    }


def _table_payload(rows: Sequence[tuple[str, str, str]]) -> list[dict[str, str]]:
    return [{"id": row[0], "state": row[1], "note": row[2]} for row in rows]


def _table_lines(title: str, rows: Sequence[tuple[str, str, str]]) -> list[str]:
    return [title, *[f"- {row[0]}: {row[1]} ({row[2]})" for row in rows]]


def _emit(
    payload: Mapping[str, object],
    text_lines: Sequence[str],
    args: argparse.Namespace,
    *,
    error: bool = False,
) -> None:
    stream = sys.stderr if error else sys.stdout
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
    else:
        print("\n".join(text_lines), file=stream)


def _redact_lines(lines: Sequence[str], target: object) -> list[str]:
    return [str(_redact_value(line, target)) for line in lines]


def _redact_payload(value: object, target: object) -> dict[str, object]:
    redacted = _redact_value(value, target)
    if not isinstance(redacted, dict):
        return {}
    return redacted


def _redact_value(value: object, target: object) -> object:
    target_text = str(target or "").strip()
    if isinstance(value, Mapping):
        return {str(key): _redact_value(item, target) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_redact_value(item, target) for item in value]
    if isinstance(value, str):
        if _secret_like(value):
            return "<redacted-secret-like-value>"
        if target_text and target_text in value:
            return value.replace(target_text, _safe_display(target))
        return value
    return value


def _safe_display(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if _secret_like(text):
        return "<redacted-secret-like-value>"
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        return Path(normalized).name or "redacted-target"
    return text


def _secret_like(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _SECRET_MARKERS)


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _mapping_list(value: object) -> list[Mapping[str, object]]:
    return [item for item in _sequence(value) if isinstance(item, Mapping)]


def _sequence(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


__all__ = [
    "OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND",
    "add_optional_solver_plugin_manifest_reload_acceptance_persistence_parser",
    "run_optional_solver_plugin_manifest_reload_acceptance_persistence_cli",
]
