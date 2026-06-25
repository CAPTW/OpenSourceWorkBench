from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiagnosticSeverity,
    OptionalSolverDiscoveryDiagnostic,
    OptionalSolverDiscoveryReport,
    OptionalSolverHealthState,
    OptionalSolverStackDiscovery,
    build_optional_solver_health_panel_viewmodel,
    parse_optional_solver_manifest_dict,
)


def _manifest():
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": "gmsh",
            "display_name": "Gmsh",
            "related_issue": 6,
            "capabilities": ["meshing"],
            "executable_requirements": ["gmsh"],
            "smoke_test_description": "Prepared smoke.",
            "prepared_machine_notes": ["Install externally before validation."],
            "documentation_refs": ["docs/validation/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver install.", "No dependency install."],
        }
    )


def test_diagnostic_rows_preserve_severity_code_message_and_path() -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            OptionalSolverStackDiscovery(
                stack_id="gmsh",
                display_name="Gmsh",
                related_issue=6,
                health_state=OptionalSolverHealthState.MISSING,
                diagnostics=(
                    OptionalSolverDiscoveryDiagnostic(
                        code="OSD_MISSING_EXECUTABLE",
                        severity=OptionalSolverDiagnosticSeverity.WARNING,
                        message="Required executable was not discovered: gmsh",
                        path="executable_requirements.gmsh",
                        suggested_fix="Expose gmsh on PATH.",
                    ),
                ),
            ),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest()],
        discovery_reports=report,
    )

    assert len(panel.diagnostics) == 1
    row = panel.diagnostics[0]
    assert row.severity == "warning"
    assert row.code == "OSD_MISSING_EXECUTABLE"
    assert row.message == "Required executable was not discovered: gmsh"
    assert row.path == "executable_requirements.gmsh"
    assert row.suggested_fix == "Expose gmsh on PATH."
    assert row.redaction_notice == ""
    assert panel.summary.validation_warning_count == 1


def test_guidance_and_validation_history_rows_are_safe_by_default() -> None:
    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest()],
        validation_history=[
            {
                "source": "OSW-VALID-005",
                "status": "skipped-missing",
                "summary": "Gmsh not installed.",
                "related_issue": 6,
            }
        ],
    )

    guidance_text = "\n".join(row.text for row in panel.guidance)
    assert "not bundled" in guidance_text
    assert "OSW-VALID prepared-machine gate" in guidance_text
    assert "Issue closure remains unavailable" in guidance_text
    assert panel.validation_history[0].status == "skipped-missing"
    assert panel.validation_history[0].is_pass_evidence is False
    assert panel.validation_history[0].closure_review_required is True
    assert any(row.category == "safety" for row in panel.guidance)


def test_diagnostic_rows_include_redaction_notice_for_redaction_diagnostics() -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            OptionalSolverStackDiscovery(
                stack_id="gmsh",
                display_name="Gmsh",
                related_issue=6,
                health_state=OptionalSolverHealthState.DISCOVERED,
                diagnostics=(
                    OptionalSolverDiscoveryDiagnostic(
                        code="OSD_PATH_REDACTED",
                        severity=OptionalSolverDiagnosticSeverity.INFO,
                        message="Path for gmsh was redacted.",
                        path="executable_requirements.gmsh",
                    ),
                ),
            ),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest()],
        discovery_reports=report,
    )

    assert "redacted" in panel.diagnostics[0].redaction_notice
