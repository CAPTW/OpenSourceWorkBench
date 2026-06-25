from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverExportSummaryOptions,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverStackCardViewModel,
    build_optional_solver_export_summary_payload,
    render_optional_solver_export_summary_markdown,
)


def test_markdown_renderer_includes_summary_and_stack_statuses() -> None:
    panel = OptionalSolverHealthPanelViewModel(
        summary=OptionalSolverHealthSummaryViewModel(
            total_stacks=2,
            counts_by_health_state={"discovered": 1, "missing": 1},
            missing_count=1,
            partial_count=0,
            discovered_count=1,
            open_issue_count=2,
            validation_warning_count=0,
        ),
        cards=(
            OptionalSolverStackCardViewModel(
                stack_id="gmsh",
                display_name="Gmsh",
                related_issue=6,
                issue_reference="#6",
                health_state="missing",
                support_status="experimental",
                short_status_text="Missing required optional components",
                missing_requirements_count=1,
                diagnostics_count=0,
                has_non_bundled_disclaimer=True,
            ),
            OptionalSolverStackCardViewModel(
                stack_id="pyvista_meshio",
                display_name="PyVista / meshio",
                related_issue=11,
                issue_reference="#11",
                health_state="discovered",
                support_status="experimental",
                short_status_text="Discovered by passive checks",
                missing_requirements_count=0,
                diagnostics_count=0,
                has_non_bundled_disclaimer=True,
            ),
        ),
        details=None,
        diagnostics=(),
        guidance=(),
        validation_history=(),
        actions=(),
    )
    payload = build_optional_solver_export_summary_payload(
        panel,
        OptionalSolverExportSummaryOptions(generated_at="2026-06-25T00:00:00Z"),
    )

    result = render_optional_solver_export_summary_markdown(payload)

    assert result.media_type == "text/markdown"
    assert result.file_extension == ".md"
    assert "# Optional Solver Health Summary" in result.content
    assert "- Total stacks: 2" in result.content
    assert "gmsh: Gmsh | health=missing | issue=#6" in result.content
    assert "pyvista_meshio: PyVista / meshio | health=discovered | issue=#11" in (
        result.content
    )
    assert "Not validation evidence: True" in result.content
