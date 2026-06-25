from __future__ import annotations

from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    duplicate_stack_report,
    invalid_bundled_report,
    valid_project_report,
)

from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_gui_viewmodel,
)


def test_accepted_rows_include_source_trust_issue_and_not_validation_evidence() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )
    row = view_model.accepted_rows[0]

    assert row.stack_id == "project_local_stack"
    assert row.display_name == "Project Local Stack"
    assert row.source_type == "project_local"
    assert row.source_label == "Project optional solver fixtures"
    assert row.trust_label == "reviewed_project"
    assert row.related_issue == "#6"
    assert row.support_status == "experimental"
    assert "project_guidance" in row.capabilities_summary
    assert "not validation evidence" in row.not_validation_evidence_text.lower()


def test_rejected_rows_include_reason_diagnostics_and_suggested_fix() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        invalid_bundled_report()
    )
    row = view_model.rejected_rows[0]

    assert row.stack_id == "bundled_claim_stack"
    assert row.trust_label == "invalid"
    assert "claims a solver is bundled" in row.rejection_reason
    assert any("OSPL_BUNDLED_SOLVER_CLAIM" in item for item in row.diagnostics)
    assert "external-solver bundling claim" in row.unsafe_claim_indicators
    assert row.suggested_fix


def test_conflict_rows_include_builtin_wins_and_override_disabled() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        duplicate_stack_report()
    )
    row = view_model.conflict_rows[0]

    assert row.stack_id == "gmsh"
    assert row.winning_source_type == "builtin"
    assert row.rejected_source_type == "plugin_package"
    assert "Built-in manifests win by default." == row.built_in_wins_text
    assert "Plugin override is disabled by default." == (
        row.plugin_override_disabled_text
    )


def test_filtering_by_text_trust_and_source_is_deterministic() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report(),
        filter_text="project_local_stack",
        trust_filters=("reviewed_project",),
        source_filters=("project_local",),
    )

    assert len(view_model.accepted_rows) == 1
    assert view_model.summary.visible_accepted_count == 1

    hidden = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report(),
        filter_text="does-not-match",
        trust_filters=("reviewed_project",),
        source_filters=("project_local",),
    )

    assert hidden.accepted_rows == ()
    assert hidden.summary.visible_accepted_count == 0
