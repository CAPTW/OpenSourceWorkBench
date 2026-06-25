from __future__ import annotations

import json

from osw.experimental.optional_solvers import (
    OptionalSolverExportSummaryOptions,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverStackCardViewModel,
    build_optional_solver_export_summary_payload,
    render_optional_solver_export_summary_json,
)


def _panel() -> OptionalSolverHealthPanelViewModel:
    return OptionalSolverHealthPanelViewModel(
        summary=OptionalSolverHealthSummaryViewModel(
            total_stacks=1,
            counts_by_health_state={"missing": 1},
            missing_count=1,
            partial_count=0,
            discovered_count=0,
            open_issue_count=1,
            validation_warning_count=0,
        ),
        cards=(
            OptionalSolverStackCardViewModel(
                stack_id="calculix",
                display_name="CalculiX ccx",
                related_issue=8,
                issue_reference="#8",
                health_state="missing",
                support_status="experimental",
                short_status_text="Missing required optional components",
                missing_requirements_count=1,
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


def test_json_payload_parses_and_contains_required_context() -> None:
    payload = build_optional_solver_export_summary_payload(
        _panel(),
        OptionalSolverExportSummaryOptions(
            package_version="0.1.5rc1",
            generated_at="2026-06-25T00:00:00Z",
        ),
    )
    result = render_optional_solver_export_summary_json(payload)

    parsed = json.loads(result.content)

    assert result.media_type == "application/json"
    assert result.file_extension == ".json"
    assert parsed["app_name"] == "OpenSolver Workbench"
    assert parsed["package_version"] == "0.1.5rc1"
    assert parsed["generated_at"] == "2026-06-25T00:00:00Z"
    assert parsed["summary"]["missing_count"] == 1
    assert parsed["stacks"][0]["issue_reference"] == "#8"
    assert parsed["not_validation_evidence"] is True
    assert parsed["redaction_state"]["environment_values_exported"] is False
