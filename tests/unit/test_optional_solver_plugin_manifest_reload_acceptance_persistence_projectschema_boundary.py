from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_DIAGNOSTIC_CODES,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED,
    OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary,
    ReloadAcceptancePersistenceProjectSchemaBoundaryAction,
    ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags,
    ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness,
    ReloadAcceptancePersistenceProjectSchemaBoundaryState,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / ("plugin_manifest_reload_acceptance_persistence_projectschema_boundary.py")
)
MODULE_NAME = (
    "osw.experimental.optional_solvers."
    "plugin_manifest_reload_acceptance_persistence_projectschema_boundary"
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


def _text(
    boundary: OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary,
) -> str:
    return "\n".join(boundary.to_text_lines())


def _rows(mapping: dict[str, object], key: str) -> dict[str, dict[str, object]]:
    return {row["row_id"]: row for row in mapping[key]}


def _sample_boundary() -> (
    OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary
):
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.from_records(
            persistence_record_mapping={
                "payload_kind": (
                    "optional_solver_plugin_manifest_reload_acceptance_persistence_record"
                ),
                "payload_schema_version": ("osw-exp-126-reload-acceptance-persistence-writer-1"),
                "target_display": r"C:\Users\USER\private\reload-acceptance-state.json",
                "source_display": r"C:\Users\USER\private\manifest.json",
                "api_key": "sk-secret-value",
                "diagnostics": [
                    {
                        "severity": "info",
                        "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY",
                        "message": "persistence ready local review only",
                        "section": "persistence",
                        "blocker": False,
                    }
                ],
            },
            persistence_viewmodel_mapping={
                "summary": {
                    "state": "ready_future_only",
                    "project_schema_mutated": False,
                    "validation_evidence_claimed": False,
                }
            },
            writer_result_mapping={
                "status": "completed",
                "target_display": r"C:\Users\USER\private\writer-state.json",
                "bytes_count": 1234,
                "sha256": "writer-sha",
                "diagnostics": [
                    {
                        "severity": "warning",
                        "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED",
                        "message": "token=sk-secret-value",
                        "section": "writer",
                        "blocker": False,
                    }
                ],
            },
            cli_write_result_mapping={
                "status": "completed",
                "source_surface": "CLI",
                "persistence_write_performed": True,
                "project_schema_mutated": False,
            },
            gui_write_result_mapping={
                "status": "completed",
                "source_surface": "GUI",
                "persistence_write_performed": True,
                "project_schema_mutated": False,
            },
            summary_audit_mapping={
                "summary": {
                    "state": "ready_for_prepared_machine_review",
                    "summary_is_project_schema_state": False,
                },
                "lower_level_diagnostics": [
                    {
                        "severity": "info",
                        "code": (
                            "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_"
                            "NO_PROJECT_SCHEMA_MUTATION"
                        ),
                        "message": "summary audit supplied only",
                        "section": "summary_audit",
                        "blocker": False,
                    }
                ],
            },
            issue_state_snapshot={"6": "open", "7": {"state": "open"}},
            prepared_machine_validation_snapshot={"status": "future_supplied_only"},
            limitations=("supplied records only",),
        )
    )


def test_module_imports_and_package_exports() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert hasattr(
        module,
        "OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary",
    )
    assert hasattr(module, "ReloadAcceptancePersistenceProjectSchemaBoundaryState")
    assert hasattr(module, "ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness")
    assert OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary
    assert (
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.MUTATE_PROJECT_SCHEMA.value
        == "mutate_project_schema"
    )
    assert (
        ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags().project_schema_mutated
        is False
    )


def test_unavailable_and_no_input_state_render_boundary_guidance() -> None:
    unavailable = (
        OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.unavailable()
    )
    assert unavailable.summary.state == (
        ReloadAcceptancePersistenceProjectSchemaBoundaryState.UNAVAILABLE
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE in {
        row.code for row in unavailable.diagnostics
    }

    boundary = (
        OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.from_records()
    )
    assert boundary.summary.state == (
        ReloadAcceptancePersistenceProjectSchemaBoundaryState.NO_RECORDS_SUPPLIED
    )
    assert boundary.summary.readiness == (
        ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness.NO_RECORDS_SUPPLIED
    )
    assert (
        "ProjectSchema boundary unavailable: no supplied reload acceptance "
        "persistence records were provided."
    ) in _text(boundary)


def test_supplied_records_and_write_successes_do_not_become_projectschema_state() -> None:
    mapping = _sample_boundary().to_mapping()
    records = {row["source_id"]: row for row in mapping["supplied_records"]}
    for key in (
        "persistence_record",
        "summary_audit",
        "cli_write_result",
        "gui_write_result",
        "writer_result",
        "persistence_viewmodel",
    ):
        assert records[key]["supplied"] is True
        assert records[key]["not_project_schema_state"] is True
        assert records[key]["not_project_schema_validation_evidence"] is True
        assert records[key]["not_project_schema_mutation"] is True
    rendered = _text(_sample_boundary())
    assert "Supplied persistence record is not ProjectSchema state." in rendered
    assert "Supplied summary audit is not ProjectSchema state." in rendered
    assert "CLI write success is not ProjectSchema mutation." in rendered
    assert "GUI write success is not ProjectSchema mutation." in rendered


def test_schemas_are_separate_and_prohibited_flows_are_present() -> None:
    mapping = _sample_boundary().to_mapping()
    schema = _rows(mapping, "schema_separation")
    assert schema["persistence_schema_separate"]["value"] is True
    assert schema["summary_audit_schema_separate"]["value"] is True
    assert schema["writer_schema_separate"]["value"] is True
    flows = _rows(mapping, "prohibited_automatic_flows")
    for row_id in (
        "persistence_record_to_project_schema_import",
        "summary_audit_to_project_schema_import",
        "cli_write_to_project_schema_mutation",
        "gui_write_to_project_schema_mutation",
        "reload_acceptance_to_validation_evidence",
        "trust_label_to_trusted_solver_state",
        "persisted_active_to_activated_candidate",
        "skipped_missing_to_validation_success",
        "unsafe_claim_to_projectschema_truth",
        "issue_release_certification_to_evidence",
    ):
        assert flows[row_id]["status"] == "blocked_future_only"
        assert flows[row_id]["value"] is False


def test_projectschema_import_mutation_validation_trust_activation_and_claims_blocked() -> None:
    mapping = _sample_boundary().to_mapping()
    codes = {row["code"] for row in mapping["diagnostics"]}
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED in codes
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED in codes
    assert (
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED
        in codes
    )
    assert any("TRUST_RESTORATION_BLOCKED" in code for code in codes)
    assert any("ACTIVATION_BLOCKED" in code for code in codes)
    assert any("ISSUE_RELEASE_BLOCKED" in code for code in codes)
    assert any("CERTIFICATION_BLOCKED" in code for code in codes)
    text = _text(_sample_boundary())
    assert "ProjectSchema import is blocked" in text
    assert "ProjectSchema mutation is blocked" in text
    assert "ProjectSchema validation evidence creation is blocked" in text


def test_preconditions_candidates_and_mutation_blockers_are_explicit() -> None:
    mapping = _sample_boundary().to_mapping()
    preconditions = _rows(mapping, "future_integration_preconditions")
    assert "prepared_machine_validation_review" in preconditions
    assert "explicit_user_opt_in" in preconditions
    assert "redaction_privacy_review" in preconditions
    assert all(row["status"] == "missing_until_future_gate" for row in preconditions.values())

    candidates = _rows(mapping, "future_permitted_data_candidates")
    assert "redacted_source_identifiers" in candidates
    assert "prepared_machine_validation_status" in candidates
    assert all(row["status"] == "non_authoritative_future_candidate" for row in candidates.values())

    blockers = _rows(mapping, "project_schema_mutation_blockers")
    for row_id in (
        "prepared_machine_validation_missing",
        "stale_source_present",
        "conflict_shared_stack_unresolved",
        "unsafe_claim_present",
        "trust_provenance_unclear",
        "schema_migration_required",
        "acknowledgements_expired",
        "raw_paths_unredacted",
        "secrets_tokens_api_keys_present",
        "live_optional_validation_issues_open",
    ):
        assert blockers[row_id]["status"] == "blocked_future_only"
        assert blockers[row_id]["value"] is True


def test_validation_trust_lifecycle_builtins_and_issue_release_boundaries() -> None:
    mapping = _sample_boundary().to_mapping()
    validation = _rows(mapping, "validation_evidence_boundary")
    assert validation["persistence_writes_not_validation_evidence"]["value"] is True
    assert validation["skipped_missing_remains_skipped_missing"]["guidance"] == (
        "Skipped-missing remains skipped-missing."
    )
    trust = _rows(mapping, "trust_provenance_boundary")
    assert trust["trust_label_not_certification"]["value"] is True
    lifecycle = _rows(mapping, "candidate_lifecycle_boundary")
    assert lifecycle["persisted_active_requires_future_activation_review"]["value"] is True
    builtins = _rows(mapping, "built_in_shared_stack_boundary")
    assert builtins["builtins_remain_authoritative"]["value"] is True
    issue_release = _rows(mapping, "issue_release_certification_boundary")
    assert issue_release["no_issue_closure"]["value"] is True
    assert issue_release["no_release_mutation"]["value"] is True
    assert issue_release["no_tag_mutation"]["value"] is True
    assert issue_release["no_asset_mutation"]["value"] is True
    assert issue_release["no_certification_claim"]["value"] is True


def test_redaction_hides_raw_absolute_paths_and_secret_like_values() -> None:
    boundary = _sample_boundary()
    rendered = json.dumps(boundary.to_mapping(), sort_keys=True) + "\n" + _text(boundary)
    assert r"C:\Users\USER\private" not in rendered
    assert "reload-acceptance-state.json" in rendered
    assert "manifest.json" in rendered
    assert "token=sk-secret-value" not in rendered
    assert "sk-secret-value" not in rendered
    assert "<redacted-secret-like-value>" in rendered


def test_diagnostics_and_lower_level_diagnostics_remain_review_only() -> None:
    mapping = _sample_boundary().to_mapping()
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_DIAGNOSTIC_CODES
    assert all(
        row["code"].startswith("OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_")
        for row in mapping["diagnostics"]
    )
    lower = mapping["lower_level_diagnostics"]
    assert any(
        row["code"] == "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED" for row in lower
    )
    assert all(row["supplied_only"] is True for row in lower)
    assert all(row["not_truth_claim"] is True for row in lower)
    assert all(row["not_projectschema_truth"] is True for row in lower)


def test_non_action_flags_and_disabled_future_actions_remain_blocked() -> None:
    mapping = _sample_boundary().to_mapping()
    flags = mapping["non_action_flags"]
    for field in (
        "project_schema_mutated",
        "project_schema_field_added",
        "project_schema_migration_performed",
        "project_schema_validation_evidence_created",
    ):
        assert flags[field] is False
    assert all(value is False for value in flags.values())

    actions = {row["action"] for row in mapping["disabled_future_actions"]}
    for action in (
        "import_persistence_record_to_project_schema",
        "import_summary_audit_to_project_schema",
        "mutate_project_schema",
        "migrate_project_schema",
        "create_project_validation_evidence",
        "accept_for_session_review",
        "accept_as_trusted",
        "activate_reloaded_candidate",
        "refresh_discovery",
        "validate_solver",
        "execute_solver",
        "install_dependency",
        "uninstall_dependency",
        "uninstall_solver",
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


def test_live_issues_and_prepared_machine_validation_are_separate() -> None:
    mapping = _sample_boundary().to_mapping()
    issues = mapping["live_optional_validation_issues"]
    assert [row["issue_number"] for row in issues] == [6, 7, 8, 9, 10, 11]
    assert all(row["state"] == "open" for row in issues)
    assert all(row["mutation_performed"] is False for row in issues)
    assert all(row["closure_claimed"] is False for row in issues)
    prepared = mapping["prepared_machine_validation"]
    assert prepared["supplied"] is True
    assert prepared["status"] == "future_supplied_only"
    assert prepared["supplied_only"] is True
    assert prepared["future_separate_gate_required"] is True
    assert prepared["boundary_executed_validation"] is False
    assert prepared["project_schema_validation_evidence_created"] is False


def test_mapping_and_text_outputs_are_deterministic() -> None:
    first = _sample_boundary()
    second = _sample_boundary()
    assert first.to_mapping() == second.to_mapping()
    assert first.to_text_lines() == second.to_text_lines()
    json.dumps(first.to_mapping(), sort_keys=True)


def test_source_imports_are_pure_and_optional_dependency_light() -> None:
    imports = _imported_modules() - {"__future__"}
    assert imports == {"collections.abc", "dataclasses", "enum"}


def test_source_scan_confirms_no_projectschema_file_io_writer_reader_cli_gui_or_subprocess() -> (
    None
):
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
