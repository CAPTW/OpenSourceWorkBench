from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverHealthState,
    OptionalSolverRefreshResult,
    OptionalSolverRefreshState,
    OptionalSolverStackDiscovery,
    apply_optional_solver_refresh_success,
    build_optional_solver_health_panel_viewmodel,
    ignore_optional_solver_stale_refresh_result,
    parse_optional_solver_manifest_dict,
)


def _manifest():
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": "alpha",
            "display_name": "Alpha",
            "capabilities": [{"capability_id": "example", "description": "Example"}],
            "executable_requirements": [{"identifier": "alpha-tool"}],
            "prepared_machine_notes": ["Use a prepared machine."],
            "documentation_refs": ["docs/example.md"],
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver install."],
        }
    )


def _panel():
    return build_optional_solver_health_panel_viewmodel(manifests=[_manifest()])


def test_stale_request_id_is_ignored() -> None:
    current = _panel()
    result = OptionalSolverRefreshResult(
        request_id="old-req",
        discovery_reports=OptionalSolverDiscoveryReport(
            stacks=(
                OptionalSolverStackDiscovery(
                    stack_id="alpha",
                    display_name="Alpha",
                    related_issue=6,
                    health_state=OptionalSolverHealthState.DISCOVERED,
                ),
            )
        ),
    )

    applied = apply_optional_solver_refresh_success(
        current,
        manifests=[_manifest()],
        result=result,
        active_request_id="new-req",
    )

    assert applied.panel is current
    assert applied.ignored is True
    assert applied.state == OptionalSolverRefreshState.STALE_IGNORED
    assert applied.diagnostics[0].code == "OSR_STALE_RESULT_IGNORED"


def test_ignore_stale_helper_preserves_current_panel() -> None:
    current = _panel()

    applied = ignore_optional_solver_stale_refresh_result(
        current,
        active_request_id="current",
        result_request_id="previous",
    )

    assert applied.panel is current
    assert applied.applied is False
    assert applied.ignored is True
    assert "not validation evidence" in applied.status_text
