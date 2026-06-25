from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverStackCardViewModel,
    build_optional_solver_export_summary_payload,
    render_optional_solver_export_summary_text,
)


def test_text_renderer_includes_summary_and_stack_statuses() -> None:
    panel = OptionalSolverHealthPanelViewModel(
        summary=OptionalSolverHealthSummaryViewModel(
            total_stacks=1,
            counts_by_health_state={"partially_installed": 1},
            missing_count=0,
            partial_count=1,
            discovered_count=0,
            open_issue_count=1,
            validation_warning_count=0,
        ),
        cards=(
            OptionalSolverStackCardViewModel(
                stack_id="openfoam",
                display_name="OpenFOAM",
                related_issue=9,
                issue_reference="#9",
                health_state="partially_installed",
                support_status="experimental",
                short_status_text="Partially installed optional stack",
                missing_requirements_count=1,
                diagnostics_count=1,
                has_non_bundled_disclaimer=True,
            ),
        ),
        details=None,
        diagnostics=(),
        guidance=(),
        validation_history=(),
        actions=(),
    )
    result = render_optional_solver_export_summary_text(
        build_optional_solver_export_summary_payload(panel)
    )

    assert result.media_type == "text/plain"
    assert result.file_extension == ".txt"
    assert "Optional Solver Health Summary" in result.content
    assert "Total stacks: 1" in result.content
    assert "openfoam: OpenFOAM | health=partially_installed | issue=#9" in (
        result.content
    )
    assert "Not validation evidence: True" in result.content
