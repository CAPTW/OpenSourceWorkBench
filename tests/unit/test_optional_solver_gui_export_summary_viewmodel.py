from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiagnosticRowViewModel,
    OptionalSolverExportSummaryDiagnostic,
    OptionalSolverExportSummaryFormat,
    OptionalSolverExportSummaryOptions,
    OptionalSolverExportSummaryPayload,
    OptionalSolverExportSummaryPrivacyWarning,
    OptionalSolverExportSummaryRenderResult,
    OptionalSolverExportSummarySavePlan,
    OptionalSolverExportSummaryViewModel,
    OptionalSolverGuidanceRowViewModel,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverStackCardViewModel,
    OptionalSolverValidationHistoryRowViewModel,
    build_optional_solver_export_summary_payload,
    build_optional_solver_export_summary_viewmodel,
    explain_optional_solver_export_summary,
)


def _panel_with_issues() -> OptionalSolverHealthPanelViewModel:
    cards = tuple(
        OptionalSolverStackCardViewModel(
            stack_id=f"stack_{issue}",
            display_name=f"Stack {issue}",
            related_issue=issue,
            issue_reference=f"#{issue}",
            health_state="missing" if issue != 11 else "discovered",
            support_status="experimental",
            short_status_text="Missing required optional components",
            missing_requirements_count=1,
            diagnostics_count=1,
            has_non_bundled_disclaimer=True,
        )
        for issue in range(6, 12)
    )
    return OptionalSolverHealthPanelViewModel(
        summary=OptionalSolverHealthSummaryViewModel(
            total_stacks=6,
            counts_by_health_state={"discovered": 1, "missing": 5},
            missing_count=5,
            partial_count=0,
            discovered_count=1,
            open_issue_count=6,
            validation_warning_count=1,
        ),
        cards=cards,
        details=None,
        diagnostics=(
            OptionalSolverDiagnosticRowViewModel(
                stack_id="stack_6",
                severity="warning",
                code="OSD_MISSING_EXECUTABLE",
                message="Required executable was not discovered.",
                path="executable_requirements.gmsh",
                suggested_fix="Use a prepared validation machine.",
            ),
        ),
        guidance=(
            OptionalSolverGuidanceRowViewModel(
                category="validation_gate",
                text="Use an explicit OSW-VALID prepared-machine gate.",
            ),
        ),
        validation_history=(
            OptionalSolverValidationHistoryRowViewModel(
                source="OSW-VALID-005",
                status="skipped-missing",
                summary="Optional tools missing on this machine.",
                related_issue=6,
                is_pass_evidence=False,
            ),
        ),
        actions=(),
    )


def test_public_api_imports() -> None:
    assert OptionalSolverExportSummaryFormat.JSON.value == "json"
    assert OptionalSolverExportSummaryOptions
    assert OptionalSolverExportSummaryPayload
    assert OptionalSolverExportSummaryViewModel
    assert OptionalSolverExportSummarySavePlan
    assert OptionalSolverExportSummaryDiagnostic
    assert OptionalSolverExportSummaryPrivacyWarning
    assert OptionalSolverExportSummaryRenderResult
    assert callable(build_optional_solver_export_summary_viewmodel)
    assert callable(build_optional_solver_export_summary_payload)


def test_builds_export_viewmodel_from_health_panel_viewmodel() -> None:
    panel = _panel_with_issues()

    view_model = build_optional_solver_export_summary_viewmodel(
        panel,
        OptionalSolverExportSummaryOptions(
            package_version="0.1.5rc1",
            generated_at="2026-06-25T00:00:00Z",
        ),
    )

    assert view_model.payload.package_version == "0.1.5rc1"
    assert view_model.payload.generated_at == "2026-06-25T00:00:00Z"
    assert view_model.payload.summary["total_stacks"] == 6
    assert view_model.payload.issue_references == (
        "#6",
        "#7",
        "#8",
        "#9",
        "#10",
        "#11",
    )
    assert len(view_model.render_results) == 3
    assert "not validation evidence" in explain_optional_solver_export_summary(
        view_model
    )


def test_payload_states_summary_is_not_validation_evidence() -> None:
    payload = build_optional_solver_export_summary_payload(_panel_with_issues())

    assert payload.not_validation_evidence is True
    assert "Exported summary is not validation evidence." in payload.safety_notes
    assert "Skipped-missing is not pass evidence." in payload.safety_notes
