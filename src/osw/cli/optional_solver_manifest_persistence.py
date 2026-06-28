"""Bounded CLI for optional solver plugin manifest persistence review."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from osw.experimental.optional_solvers import (
    OSPMG_STATE_WRITER_WRITE_BLOCKED,
    STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
    OptionalSolverPluginManifestStateWriter,
    OptionalSolverPluginManifestStateWriterRequest,
    OptionalSolverPluginManifestStateWriterResult,
    OptionalSolverPluginManifestStateWriterStatus,
    OptionalSolverPluginManifestStateWriterViewModel,
)

OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND = (
    "optional-solver-plugin-manifest-persistence"
)

_PERSISTENCE_SUBCOMMANDS = (
    "explain",
    "plan",
    "schema",
    "acknowledgements",
    "diagnostics",
    "actions",
    "write",
)

_NON_ACTION_LINES = (
    "Persisted state is not validation evidence.",
    "Persisted state is not trust restoration.",
    "Persisted state is not automatic activation.",
    "Persisted state is not ProjectSchema state.",
    "No discovery execution.",
    "No plugin package import.",
    "No directory scan.",
    "No network fetch.",
    "No validation execution.",
    "No solver execution.",
    "No dependency installation.",
    "No dependency uninstall.",
    "No solver uninstall.",
    "No issue closure.",
    "No release mutation.",
    "No tag mutation.",
    "No asset mutation.",
    "No GUI behavior.",
    "No reload behavior.",
    "No export or report behavior.",
    "No clipboard behavior.",
    "No report attachment.",
    "No open-output-folder behavior.",
    "A trust label is not certification.",
    "User/plugin manifests remain untrusted by default.",
)

_COMMAND_PURPOSE = {
    "explain": "Explain the persistence/state-writer CLI safety boundary.",
    "plan": "Review deterministic in-memory state-writer readiness without writing.",
    "schema": "Show schema and migration readiness from the supplied view-model.",
    "acknowledgements": "Show acknowledgement requirements and expiry boundaries.",
    "diagnostics": "Show OSPMG_STATE_WRITER_* diagnostics from the view-model.",
    "actions": "Show disabled and future action states.",
    "write": "Dry-run or explicitly write local UX state through the state writer.",
}


def add_optional_solver_plugin_manifest_persistence_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the bounded persistence CLI with the repo's flat command style."""

    parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND,
        help="Review or explicitly write optional solver plugin manifest UX state.",
        description=(
            "Review optional solver plugin manifest persistence state and call the "
            "explicit state writer. The command is dry-run-first, uses only "
            "caller-supplied target paths, and does not perform discovery, "
            "validation, solver execution, dependency changes, reload, GUI, "
            "ProjectSchema, issue, release, tag, or asset actions."
        ),
    )
    parser.add_argument(
        "persistence_command",
        choices=_PERSISTENCE_SUBCOMMANDS,
        help="Persistence review/write operation to perform.",
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
        help="Use deterministic empty/unavailable in-memory state.",
    )
    parser.add_argument(
        "--unavailable-state",
        action="store_true",
        help="Use deterministic unavailable state; this is also the default.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Caller-supplied target path for write dry-runs or actual writes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Keep write in dry-run mode. This is the default.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Perform an actual local write after preflight and acknowledgement.",
    )
    parser.add_argument(
        "--acknowledge-state-write",
        action="store_true",
        help="Acknowledge that the explicit local state write is requested.",
    )
    parser.add_argument(
        "--allow-replace",
        action="store_true",
        help="Allow replacing an existing target file.",
    )
    return parser


def run_optional_solver_plugin_manifest_persistence_cli(args: argparse.Namespace) -> int:
    """Run a bounded persistence CLI operation."""

    state_source_error = _validate_state_source_flags(args)
    if state_source_error:
        _emit(
            {"error": state_source_error, "command": args.persistence_command},
            [state_source_error],
            args,
            error=True,
        )
        return 2

    view_model, source_label = _view_model_from_args(args)
    writer_result: OptionalSolverPluginManifestStateWriterResult | None = None

    if args.persistence_command == "write":
        if not args.output:
            writer_result = _plan_or_write(
                view_model,
                target_path=None,
                dry_run=not bool(args.write),
                caller_acknowledged_write=bool(args.acknowledge_state_write),
                allow_replace=bool(args.allow_replace),
            )
        else:
            writer_result = _plan_or_write(
                view_model,
                target_path=args.output,
                dry_run=not bool(args.write),
                caller_acknowledged_write=bool(args.acknowledge_state_write),
                allow_replace=bool(args.allow_replace),
            )
    elif args.persistence_command == "plan" and args.output:
        writer_result = _plan_or_write(
            view_model,
            target_path=args.output,
            dry_run=True,
            caller_acknowledged_write=False,
            allow_replace=bool(args.allow_replace),
        )

    payload = _payload(args, view_model, source_label, writer_result)
    text_lines = _text_lines(args, view_model, source_label, writer_result)
    is_error = bool(
        writer_result
        and writer_result.status
        not in {
            OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED,
            OptionalSolverPluginManifestStateWriterStatus.WRITTEN,
        }
    )
    _emit(payload, text_lines, args, error=is_error)
    if args.persistence_command == "write" and writer_result is not None:
        return _exit_code(writer_result)
    return 0


def _validate_state_source_flags(args: argparse.Namespace) -> str:
    selected = [
        bool(args.sample_state),
        bool(args.empty_state),
        bool(args.unavailable_state),
    ]
    if sum(1 for value in selected if value) > 1:
        return (
            "Select only one state source: --sample-state, --empty-state, or "
            "--unavailable-state."
        )
    return ""


def _view_model_from_args(
    args: argparse.Namespace,
) -> tuple[OptionalSolverPluginManifestStateWriterViewModel, str]:
    if args.sample_state:
        return (
            OptionalSolverPluginManifestStateWriterViewModel.ready_for_future_write(),
            "deterministic sample in-memory state",
        )
    if args.empty_state:
        return (
            OptionalSolverPluginManifestStateWriterViewModel.dry_run_only(),
            "deterministic empty in-memory state",
        )
    return (
        OptionalSolverPluginManifestStateWriterViewModel.unavailable(),
        "unavailable in-memory state; live source integration is future-gated",
    )


def _plan_or_write(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
    *,
    target_path: str | Path | None,
    dry_run: bool,
    caller_acknowledged_write: bool,
    allow_replace: bool,
) -> OptionalSolverPluginManifestStateWriterResult:
    writer = OptionalSolverPluginManifestStateWriter()
    request = OptionalSolverPluginManifestStateWriterRequest(
        target_path=target_path,
        allow_replace=allow_replace,
        dry_run=dry_run,
        expected_schema_version=STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
        operation_label=OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND,
        caller_acknowledged_write=caller_acknowledged_write,
    )
    return writer.write_state(view_model, request)


def _payload(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
    source_label: str,
    writer_result: OptionalSolverPluginManifestStateWriterResult | None,
) -> dict[str, object]:
    return {
        "command": OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND,
        "subcommand": args.persistence_command,
        "purpose": _COMMAND_PURPOSE[args.persistence_command],
        "state_source": source_label,
        "state_source_policy": {
            "deterministic_in_memory_only": True,
            "live_discovery_performed": False,
            "plugin_package_import_performed": False,
            "directory_scan_performed": False,
            "network_fetch_performed": False,
        },
        "mode": "write" if bool(args.write) else "dry-run",
        "target_reference_display": _target_display(args.output),
        "acknowledgement_state": (
            "acknowledged"
            if bool(args.acknowledge_state_write)
            else "not_acknowledged"
        ),
        "allow_replace": bool(args.allow_replace),
        "writer_payload_schema_version": STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
        "view_model": view_model.to_mapping(),
        "writer_result": writer_result.to_mapping() if writer_result else None,
        "cli_diagnostics": _cli_diagnostics(writer_result),
        "non_actions": list(_NON_ACTION_LINES),
        "future_source_integration_required": True,
    }


def _text_lines(
    args: argparse.Namespace,
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
    source_label: str,
    writer_result: OptionalSolverPluginManifestStateWriterResult | None,
) -> list[str]:
    summary = view_model.summary
    lines = [
        "Optional Solver Plugin Manifest Persistence CLI",
        f"command: {OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND}",
        f"subcommand: {args.persistence_command}",
        f"purpose: {_COMMAND_PURPOSE[args.persistence_command]}",
        f"state source: {source_label}",
        "state source policy: deterministic in-memory only; no live discovery; "
        "no plugin package import; no directory scan; no network fetch",
        f"state scope: {summary.state_scope}",
        f"readiness: {summary.readiness.value}",
        f"writer state: {summary.writer_state}",
        f"schema version display: {summary.schema_version_display}",
        f"writer payload schema version: {STATE_WRITER_PAYLOAD_SCHEMA_VERSION}",
        f"storage options: {len(view_model.storage_options)}",
        f"target path: {_target_display(args.output)}",
        f"target path redacted: {bool(args.output)}",
        f"mode: {'write' if bool(args.write) else 'dry-run'}",
        "dry-run default: true",
        f"write flag supplied: {bool(args.write)}",
        f"acknowledgement state: "
        f"{'acknowledged' if bool(args.acknowledge_state_write) else 'not acknowledged'}",
        f"allow replace: {bool(args.allow_replace)}",
        f"redaction required count: {summary.redaction_required_count}",
        f"stale-source/re-preview count: {summary.stale_source_count}",
        f"conflict/shared-stack count: {summary.conflict_count}",
        f"unsafe-claim count: {summary.unsafe_claim_count}",
        f"evidence retained count: {summary.evidence_retained_count}",
        f"history retained count: {summary.history_retained_count}",
    ]

    if args.persistence_command in {"explain", "plan", "write"}:
        lines.extend(("Safety boundary:", *[f"- {line}" for line in _NON_ACTION_LINES]))
    if args.persistence_command in {"schema", "plan", "write", "explain"}:
        lines.extend(_schema_lines(view_model))
    if args.persistence_command in {"acknowledgements", "plan", "write", "explain"}:
        lines.extend(_acknowledgement_lines(view_model))
    if args.persistence_command in {"diagnostics", "plan", "write", "explain"}:
        lines.extend(_diagnostic_lines(view_model, writer_result))
    if args.persistence_command in {"actions", "plan", "write", "explain"}:
        lines.extend(_action_lines(view_model))
    if writer_result is not None:
        lines.extend(_writer_result_lines(writer_result))
    lines.append("Live source integration remains future-gated.")
    return lines


def _schema_lines(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> list[str]:
    lines = ["Schema/migration:"]
    for row in view_model.file_format_boundaries:
        lines.append(
            "- "
            f"{row.format_kind}: format={row.conceptual_format}; "
            f"supported={row.schema_version_supported}; "
            f"migration_required={row.schema_migration_required}"
        )
    for row in view_model.schema_migration_rows:
        lines.append(
            "- migration: "
            f"{row.schema_version_display}; required={row.migration_required}; "
            f"supported={row.schema_supported}"
        )
    return lines


def _acknowledgement_lines(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> list[str]:
    lines = ["Acknowledgements:"]
    for row in view_model.acknowledgement_rows:
        lines.append(
            "- "
            f"{row.acknowledgement_id}: required={row.required}; "
            f"acknowledged={row.satisfied}; expires_on_reload={row.expires_on_reload}; "
            f"expires_on_source_change={row.expires_on_source_fingerprint_change}; "
            f"expires_on_schema_change={row.expires_on_schema_change}; "
            f"expires_on_unsafe_claims={row.expires_on_unsafe_claim_change}"
        )
    return lines


def _diagnostic_lines(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
    writer_result: OptionalSolverPluginManifestStateWriterResult | None,
) -> list[str]:
    lines = ["Diagnostics:"]
    for row in view_model.diagnostics:
        lines.append(
            "- "
            f"{row.severity} {row.code} blocker={row.blocker}: {row.message}"
        )
    if writer_result is not None:
        for row in writer_result.diagnostics:
            lines.append(
                "- writer "
                f"{row.severity} {row.code} blocker={row.blocker}: {row.message}"
            )
    return lines


def _action_lines(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> list[str]:
    lines = ["Actions:"]
    for row in view_model.actions:
        lines.append(
            "- "
            f"{row.action.value}: enabled={row.enabled}; "
            f"available={row.available}; future={row.future_action}; "
            f"reason={row.reason}"
        )
    return lines


def _writer_result_lines(
    result: OptionalSolverPluginManifestStateWriterResult,
) -> list[str]:
    lines = [
        "Writer result:",
        f"- status: {result.status.value}",
        f"- target: {result.target_reference_display}",
        f"- target redacted: {result.target_reference_redacted}",
        f"- bytes planned: {result.bytes_planned}",
        f"- bytes written: {result.bytes_written}",
        f"- write performed: {result.write_performed}",
        f"- file write performed: {result.file_write_performed}",
        f"- reload behavior added: {result.reload_behavior_added}",
        f"- clipboard performed: {result.clipboard_performed}",
        f"- report attachment performed: {result.report_attachment_performed}",
        f"- open output folder performed: {result.open_output_folder_performed}",
        f"- ProjectSchema mutation performed: "
        f"{result.project_schema_mutation_performed}",
        f"- discovery execution performed: {result.discovery_execution_performed}",
        f"- validation execution performed: {result.validation_execution_performed}",
        f"- solver execution performed: {result.solver_execution_performed}",
        f"- issue mutation performed: {result.issue_mutation_performed}",
        f"- release mutation performed: {result.release_mutation_performed}",
        f"- tag mutation performed: {result.tag_mutation_performed}",
        f"- asset mutation performed: {result.asset_mutation_performed}",
        f"- validation success claimed: {result.validation_success_claimed}",
        f"- validation failure claimed: {result.validation_failure_claimed}",
        f"- issue closure claimed: {result.issue_closure_claimed}",
        f"- certification claimed: {result.certification_claimed}",
    ]
    for code in _cli_diagnostics(result):
        lines.append(f"- cli diagnostic: {code}")
    return lines


def _cli_diagnostics(
    result: OptionalSolverPluginManifestStateWriterResult | None,
) -> list[str]:
    if result is None:
        return []
    if result.status is OptionalSolverPluginManifestStateWriterStatus.BLOCKED:
        return [OSPMG_STATE_WRITER_WRITE_BLOCKED]
    return []


def _target_display(raw_path: str | Path | None) -> str:
    if raw_path is None or str(raw_path).strip() == "":
        return "<not supplied>"
    return Path(str(raw_path)).name or "<target>"


def _emit(
    payload: Mapping[str, object],
    text_lines: Sequence[str],
    args: argparse.Namespace,
    *,
    error: bool,
) -> None:
    stream = None
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if error:
        import sys

        stream = sys.stderr
    print("\n".join(text_lines), file=stream)


def _exit_code(result: OptionalSolverPluginManifestStateWriterResult) -> int:
    if result.status in {
        OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED,
        OptionalSolverPluginManifestStateWriterStatus.WRITTEN,
    }:
        return 0
    if result.status is OptionalSolverPluginManifestStateWriterStatus.ERROR:
        return 1
    return 2


__all__ = [
    "OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_COMMAND",
    "add_optional_solver_plugin_manifest_persistence_parser",
    "run_optional_solver_plugin_manifest_persistence_cli",
]
