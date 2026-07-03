from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_DIAGNOSTIC_CODES,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING,
    RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRY_REASONS,
    RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS,
    OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit,
    ReloadAcceptancePersistenceSummaryAuditAction,
    ReloadAcceptancePersistenceSummaryAuditNonActionFlags,
    ReloadAcceptancePersistenceSummaryAuditReadiness,
    ReloadAcceptancePersistenceSummaryAuditState,
    all_reload_acceptance_persistence_summary_audit_acknowledgements,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers" / (
    "plugin_manifest_reload_acceptance_persistence_summary_audit.py"
)
MODULE_NAME = (
    "osw.experimental.optional_solvers."
    "plugin_manifest_reload_acceptance_persistence_summary_audit"
)


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_module_source())


def _imported_modules() -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _called_names() -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return {call.lower() for call in calls}


def _text(audit: OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit) -> str:
    return "\n".join(audit.to_text_lines())


def _codes(
    audit: OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit,
) -> set[str]:
    return {row.code for row in audit.diagnostics}


def _chain_records() -> list[dict[str, object]]:
    return [
        {
            "gate_id": gate_id,
            "title": f"{gate_id} supplied",
            "artifact_type": "supplied",
            "implementation_status": "implemented",
            "evidence_type": "source/test evidence",
            "safety_summary": "supplied chain row only",
            "non_authoritative_caveat": "not validation evidence",
        }
        for gate_id in [f"OSW-EXP-{number}" for number in range(124, 137)]
    ]


def _persistence_mapping() -> dict[str, object]:
    return {
        "summary": {
            "state": "persistence_ready_future_only",
            "readiness": "writer_future_only",
            "ready_for_future_write_plan": True,
            "persistence_readiness_is_validation_evidence": False,
            "persistence_readiness_is_validation_failure": False,
            "persistence_readiness_mutates_project_schema": False,
        },
        "acknowledgements": [
            {"acknowledgement_id": ack, "satisfied": True, "expired": False}
            for ack in RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS
        ],
        "schema": [
            {
                "schema_version": "osw-exp-125-preview",
                "payload_kind": (
                    "optional_solver_plugin_manifest_reload_acceptance_"
                    "persistence_state"
                ),
            }
        ],
        "provenance": [
            {
                "source_display": r"C:\Users\USER\private\manifest.json",
                "source_kind": "supplied_acceptance_viewmodel",
            }
        ],
        "evidence_history": [
            {"evidence_id": "skipped-missing", "evidence_type": "skipped-missing"}
        ],
        "diagnostics": [
            {
                "severity": "info",
                "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY",
                "message": "supplied lower level diagnostic",
                "section": "persistence",
                "blocker": False,
            }
        ],
    }


def _writer_mapping(*, completed: bool = True) -> dict[str, object]:
    return {
        "status": "completed" if completed else "planned",
        "target_display": r"C:\Users\USER\private\reload-acceptance-state.json",
        "target_redacted": True,
        "dry_run": not completed,
        "planned": not completed,
        "written": completed,
        "bytes_count": 1234,
        "sha256": "abc123",
        "payload_kind": (
            "optional_solver_plugin_manifest_reload_acceptance_persistence_record"
        ),
        "payload_schema_version": (
            "osw-exp-126-reload-acceptance-persistence-writer-1"
        ),
        "diagnostics": [
            {
                "severity": "info",
                "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED",
                "message": "writer completed local review record only",
                "section": "writer",
                "blocker": False,
            },
            {
                "severity": "warning",
                "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE",
                "message": "token=sk-secret-value",
                "section": "writer",
                "blocker": False,
            },
        ],
        "blockers": [],
        "warnings": ["password=secret"],
        "non_action_flags": {
            "runtime_reload_acceptance_performed": False,
            "project_schema_mutated": False,
            "validation_executed": False,
            "solver_executed": False,
            "issue_mutated": False,
            "release_mutated": False,
            "certification_claimed": False,
        },
        "write_performed": completed,
        "persistence_write_performed": completed,
        "runtime_reload_acceptance_performed": False,
        "project_schema_mutated": False,
        "cleanup_performed": completed,
        "temp_file_used": completed,
        "atomic_replace_performed": completed,
    }


def _audit() -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    return OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.from_records(
        persistence_viewmodel_mapping=_persistence_mapping(),
        writer_result_mapping=_writer_mapping(),
        cli_write_result_mapping={
            "status": "completed",
            "source_surface": "CLI",
            "target_display": "cli-state.json",
            "dry_run_plan": _writer_mapping(completed=False),
            "writer_result": _writer_mapping(completed=True),
            "persistence_write_performed": True,
        },
        gui_write_result_mapping=_writer_mapping(completed=True),
        chain_gate_records=_chain_records(),
        issue_state_snapshot={"6": "open", "7": {"state": "open"}},
        prepared_machine_validation_snapshot={"status": "future_supplied_only"},
        limitations=("supplied records only",),
    )


def test_module_imports_and_package_exports() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert hasattr(
        module,
        "OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit",
    )
    assert hasattr(module, "ReloadAcceptancePersistenceSummaryAuditState")
    assert hasattr(module, "ReloadAcceptancePersistenceSummaryAuditReadiness")
    assert hasattr(module, "ReloadAcceptancePersistenceSummaryAuditDiagnostic")
    assert OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit
    assert ReloadAcceptancePersistenceSummaryAuditAction.VALIDATE_SOLVER.value == (
        "validate_solver"
    )
    assert ReloadAcceptancePersistenceSummaryAuditNonActionFlags().validation_executed is (
        False
    )
    assert all_reload_acceptance_persistence_summary_audit_acknowledgements() == (
        RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS
    )


def test_unavailable_and_no_input_state_render_no_records_guidance() -> None:
    unavailable = OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.unavailable()
    assert unavailable.summary.state == ReloadAcceptancePersistenceSummaryAuditState.UNAVAILABLE
    assert "UNAVAILABLE" in " ".join(_codes(unavailable))

    audit = OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.from_records()
    assert audit.summary.state == (
        ReloadAcceptancePersistenceSummaryAuditState.NO_RECORDS_SUPPLIED
    )
    assert audit.summary.readiness == (
        ReloadAcceptancePersistenceSummaryAuditReadiness.NO_RECORDS_SUPPLIED
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING in _codes(
        audit
    )
    assert "No supplied summary/audit records are available." in json.dumps(
        audit.to_mapping()
    )


def test_supplied_chain_records_render_osw_exp_124_through_136_coverage() -> None:
    audit = _audit()
    gate_ids = [row["gate_id"] for row in audit.to_mapping()["chain_coverage"]]
    assert gate_ids == [f"OSW-EXP-{number}" for number in range(124, 137)]
    assert audit.summary.chain_complete is True
    assert all(row["supplied"] is True for row in audit.to_mapping()["chain_coverage"])


def test_missing_gate_records_surface_chain_incomplete_diagnostic() -> None:
    audit = OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.from_records(
        persistence_viewmodel_mapping=_persistence_mapping(),
        chain_gate_records=_chain_records()[:-1],
    )
    assert audit.summary.state == (
        ReloadAcceptancePersistenceSummaryAuditState.CHAIN_INCOMPLETE
    )
    assert "OSW-EXP-136" in audit.summary.missing_gate_ids
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE in _codes(
        audit
    )


def test_supplied_persistence_viewmodel_mapping_renders_readiness_and_caveats() -> None:
    mapping = _audit().to_mapping()
    persistence = mapping["persistence_viewmodel_summary"]
    assert persistence["supplied"] is True
    assert persistence["readiness"] == "writer_future_only"
    assert persistence["not_runtime_reload_acceptance"] is True
    assert persistence["not_validation_evidence"] is True
    assert persistence["not_validation_failure"] is True
    assert persistence["not_project_schema_state"] is True


def test_writer_cli_and_gui_write_mappings_render_local_only_summaries() -> None:
    mapping = _audit().to_mapping()
    for key in ("writer_summary", "cli_write_summary", "gui_write_summary"):
        summary = mapping[key]
        assert summary["supplied"] is True
        assert summary["local_review_record_only"] is True
        assert summary["target_display"] == "reload-acceptance-state.json" or key == (
            "cli_write_summary"
        )
        assert summary["bytes_count"] == 1234
        assert summary["final_write_sha256"] == "abc123"
        assert summary["persistence_write_performed"] is True
        assert summary["write_implies_runtime_acceptance"] is False
        assert summary["write_implies_validation_evidence"] is False
        assert summary["write_implies_validation_failure"] is False
        assert summary["write_implies_project_schema_mutation"] is False
        assert summary["write_implies_trust_restoration"] is False
        assert summary["write_implies_activation"] is False
        assert summary["write_implies_issue_closure"] is False
        assert summary["write_implies_release_mutation"] is False
        assert summary["write_implies_certification"] is False
    assert "local-review-record-only=True" in _text(_audit())


def test_acknowledgement_and_expiry_rows_include_required_ids_and_reasons() -> None:
    mapping = _audit().to_mapping()
    ack_ids = {row["row_id"] for row in mapping["acknowledgements"]}
    expiry_ids = {row["row_id"] for row in mapping["expiry"]}
    assert ack_ids == set(RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS)
    assert expiry_ids == set(RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRY_REASONS)
    assert "target_change" in expiry_ids
    assert "summary_audit_policy_change" in expiry_ids


def test_policy_sections_record_storage_schema_redaction_and_trust_boundaries() -> None:
    mapping = _audit().to_mapping()
    target_rows = {row["row_id"]: row for row in mapping["target_storage_policy"]}
    schema_rows = {row["row_id"]: row for row in mapping["schema_migration"]}
    redaction_rows = {row["row_id"]: row for row in mapping["redaction_privacy"]}
    trust_rows = {row["row_id"]: row for row in mapping["provenance_trust"]}
    stale_rows = {row["row_id"]: row for row in mapping["stale_source_repreview"]}
    conflict_rows = {row["row_id"]: row for row in mapping["conflict_shared_stack"]}
    unsafe_rows = {row["row_id"]: row for row in mapping["unsafe_claims"]}
    evidence_rows = {row["row_id"]: row for row in mapping["evidence_history"]}

    assert target_rows["explicit_target_required"]["value"] is True
    assert target_rows["default_target_path_used"]["value"] is False
    assert target_rows["background_write_performed"]["value"] is False
    assert target_rows["directory_scan_performed"]["value"] is False
    assert schema_rows["separate_from_project_schema"]["value"] is True
    assert schema_rows["schema_mismatch_is_validation_failure"]["value"] is False
    assert redaction_rows["raw_absolute_paths_hidden_by_default"]["value"] is True
    assert redaction_rows["secret_like_values_redacted"]["value"] is True
    assert trust_rows["trust_label_not_certification"]["value"] is True
    assert stale_rows["stale_source_is_validation_failure"]["value"] is False
    assert conflict_rows["built_ins_win_by_default"]["value"] is True
    assert unsafe_rows["validation_success_claim_blocked"]["status"] == "blocked"
    assert unsafe_rows["release_mutation_claim_blocked"]["value"] is True
    assert unsafe_rows["certification_claim_blocked"]["value"] is True
    assert evidence_rows["skipped_missing"]["value"] == (
        "skipped-missing remains skipped-missing"
    )


def test_redaction_hides_raw_absolute_paths_and_secret_like_values() -> None:
    audit = _audit()
    rendered = json.dumps(audit.to_mapping(), sort_keys=True) + "\n" + _text(audit)
    assert r"C:\Users\USER\private" not in rendered
    assert "manifest.json" in rendered
    assert "reload-acceptance-state.json" in rendered
    assert "token=sk-secret-value" not in rendered
    assert "password=secret" not in rendered
    assert "<redacted-secret-like-value>" in rendered


def test_diagnostics_surface_vocabulary_and_lower_level_records_as_supplied_only() -> None:
    mapping = _audit().to_mapping()
    codes = {row["code"] for row in mapping["diagnostics"]}
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_DIAGNOSTIC_CODES
    assert (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM"
        in codes
    )
    assert (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION"
        in codes
    )
    lower = mapping["lower_level_diagnostics"]
    assert any(
        row["code"] == "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED"
        for row in lower
    )
    assert all(row["supplied_only"] is True for row in lower)
    assert all(row["not_truth_claim"] is True for row in lower)


def test_non_action_flags_remain_false_and_future_actions_are_present() -> None:
    mapping = _audit().to_mapping()
    flags = mapping["non_action_flags"]
    assert flags
    assert all(value is False for value in flags.values())
    actions = {row["action"] for row in mapping["disabled_future_actions"]}
    for action in (
        "accept_for_session_review",
        "accept_as_trusted",
        "activate_reloaded_candidate",
        "refresh_discovery",
        "validate_solver",
        "execute_solver",
        "install_dependency",
        "uninstall_dependency",
        "uninstall_solver",
        "mutate_project_schema",
        "create_export_summary",
        "create_report_file",
        "create_reloadable_bundle",
        "copy_to_clipboard",
        "attach_to_report",
        "open_output_folder",
        "close_issue",
        "mutate_release",
        "push_tag",
        "upload_asset",
        "claim_validation_success",
        "claim_validation_failure",
        "claim_certification",
    ):
        assert action in actions


def test_live_issues_and_prepared_machine_validation_remain_separate() -> None:
    mapping = _audit().to_mapping()
    issues = mapping["issue_state_separation"]
    assert [row["issue_number"] for row in issues] == [6, 7, 8, 9, 10, 11]
    assert all(row["mutation_performed"] is False for row in issues)
    assert all(row["closure_claimed"] is False for row in issues)
    prepared = mapping["prepared_machine_validation"]
    assert prepared["supplied"] is True
    assert prepared["status"] == "future_supplied_only"
    assert prepared["summary_audit_executed_validation"] is False
    assert prepared["validation_evidence_claimed"] is False
    assert prepared["future_separate_gate_required"] is True


def test_mapping_and_text_outputs_are_deterministic() -> None:
    first = _audit()
    second = _audit()
    assert first.to_mapping() == second.to_mapping()
    assert first.to_text_lines() == second.to_text_lines()
    json.dumps(first.to_mapping(), sort_keys=True)


def test_source_imports_are_pure_and_optional_dependency_light() -> None:
    imports = _imported_modules() - {"__future__"}
    assert imports == {"collections.abc", "dataclasses", "enum"}


def test_source_scan_confirms_no_file_io_writer_reader_cli_gui_or_subprocess() -> None:
    calls = _called_names()
    imports = _imported_modules()
    forbidden_imports = {
        "pathlib",
        "os",
        "io",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "osw.cli",
        "osw.gui",
        "pyside6",
        "osw.core",
        "osw.plugins",
        "osw.solvers",
        "plugin_manifest_reload_acceptance_persistence_writer",
        "plugin_manifest_reload_file_reader",
        "plugin_manifest_state_writer",
        "project_schema",
        "github",
    }
    assert imports.isdisjoint(forbidden_imports)
    forbidden_calls = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
        "glob",
        "iterdir",
        "run",
        "popen",
        "write_reload_acceptance_persistence_record",
        "plan_reload_acceptance_persistence_write",
        "read_optional_solver_plugin_manifest_reload_file",
        "write_optional_solver_plugin_manifest_state",
        "discover_optional_solver_manifests",
        "validate_optional_solver_manifest",
        "execute_solver",
        "mutate_project_schema",
        "create_issue",
        "close_issue",
        "create_release",
        "upload_asset",
        "push_tag",
    }
    assert calls.isdisjoint(forbidden_calls)
