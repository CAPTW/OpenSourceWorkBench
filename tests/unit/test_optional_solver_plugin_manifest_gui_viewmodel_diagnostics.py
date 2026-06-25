from __future__ import annotations

from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    duplicate_stack_report,
    invalid_bundled_report,
)

from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_gui_viewmodel,
)


def test_summary_counts_accepted_rejected_conflicts_and_diagnostics() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        duplicate_stack_report()
    )

    assert view_model.summary.accepted_count == 0
    assert view_model.summary.rejected_count == 1
    assert view_model.summary.conflict_count == 1
    assert view_model.summary.diagnostic_count == 1
    assert "0 accepted, 1 rejected, 1 conflicts" in view_model.summary.status_text


def test_diagnostic_rows_preserve_category_severity_code_and_message() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        invalid_bundled_report()
    )
    row = view_model.diagnostic_rows[0]

    assert row.severity == "blocker"
    assert row.category == "safety"
    assert row.code == "OSPL_BUNDLED_SOLVER_CLAIM"
    assert "claims a solver is bundled" in row.message
    assert row.stack_id == "bundled_claim_stack"
    assert row.suggested_fix


def test_diagnostic_filtering_by_text() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        invalid_bundled_report(),
        filter_text="BUNDLED_SOLVER",
    )

    assert len(view_model.diagnostic_rows) == 1
    assert view_model.diagnostic_rows[0].code == "OSPL_BUNDLED_SOLVER_CLAIM"
