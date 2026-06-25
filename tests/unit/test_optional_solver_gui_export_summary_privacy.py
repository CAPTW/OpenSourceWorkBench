from __future__ import annotations

import json

from osw.experimental.optional_solvers import (
    OptionalSolverDiagnosticRowViewModel,
    OptionalSolverExportSummaryOptions,
    OptionalSolverGuidanceRowViewModel,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverStackCardViewModel,
    OptionalSolverValidationHistoryRowViewModel,
    build_optional_solver_export_summary_payload,
    render_optional_solver_export_summary_json,
)


def _privacy_panel() -> OptionalSolverHealthPanelViewModel:
    return OptionalSolverHealthPanelViewModel(
        summary=OptionalSolverHealthSummaryViewModel(
            total_stacks=1,
            counts_by_health_state={"missing": 1},
            missing_count=1,
            partial_count=0,
            discovered_count=0,
            open_issue_count=1,
            validation_warning_count=1,
        ),
        cards=(
            OptionalSolverStackCardViewModel(
                stack_id="openfoam",
                display_name="OpenFOAM",
                related_issue=9,
                issue_reference="#9",
                health_state="missing",
                support_status="experimental",
                short_status_text="Missing at C:/Users/USER/OpenFOAM/bin",
                missing_requirements_count=1,
                diagnostics_count=1,
                has_non_bundled_disclaimer=True,
            ),
        ),
        details=None,
        diagnostics=(
            OptionalSolverDiagnosticRowViewModel(
                stack_id="openfoam",
                severity="warning",
                code="OSD_ENVIRONMENT_VALUE_REDACTED",
                message="FOAM_APPBIN=C:/Users/USER/OpenFOAM/bin",
                path="environment_variable_hints.FOAM_APPBIN",
                suggested_fix="Use /home/user/OpenFOAM/bin on a prepared machine.",
                redaction_notice="Local paths or environment values were redacted.",
            ),
        ),
        guidance=(
            OptionalSolverGuidanceRowViewModel(
                category="privacy",
                text="Do not share PATH=C:/Users/USER/OpenFOAM/bin.",
            ),
        ),
        validation_history=(
            OptionalSolverValidationHistoryRowViewModel(
                source="OSW-VALID-005",
                status="skipped-missing",
                summary="Evidence under C:/Users/USER/private",
                related_issue=9,
                is_pass_evidence=False,
            ),
        ),
        actions=(),
    )


def test_environment_values_and_full_paths_are_omitted_by_default() -> None:
    payload = build_optional_solver_export_summary_payload(_privacy_panel())
    rendered = render_optional_solver_export_summary_json(payload).content

    assert "C:/Users/USER" not in rendered
    assert "/home/user" not in rendered
    assert "FOAM_APPBIN=C:/Users/USER" not in rendered
    assert "PATH=C:/Users/USER" not in rendered
    assert "<redacted:path>" in rendered
    assert "FOAM_APPBIN=<redacted>" in rendered
    assert "PATH=<redacted>" in rendered


def test_include_full_paths_requires_privacy_warning() -> None:
    payload = build_optional_solver_export_summary_payload(
        _privacy_panel(),
        OptionalSolverExportSummaryOptions(include_full_paths=True),
    )

    assert payload.privacy_warnings
    assert payload.privacy_warnings[0].acknowledgement_required is True
    assert payload.privacy_warnings[0].acknowledged is False
    assert payload.redaction_state["full_path_export_requested"] is True
    assert payload.redaction_state["environment_values_exported"] is False


def test_acknowledged_full_path_request_still_redacts_environment_values() -> None:
    payload = build_optional_solver_export_summary_payload(
        _privacy_panel(),
        OptionalSolverExportSummaryOptions(
            include_full_paths=True,
            full_paths_acknowledged=True,
        ),
    )
    parsed = json.loads(render_optional_solver_export_summary_json(payload).content)

    assert parsed["privacy_warnings"][0]["acknowledged"] is True
    assert "FOAM_APPBIN=C:/Users/USER" not in json.dumps(parsed)
    assert "PATH=C:/Users/USER" not in json.dumps(parsed)
    assert "FOAM_APPBIN=<redacted>" in json.dumps(parsed)
    assert "PATH=<redacted>" in json.dumps(parsed)
