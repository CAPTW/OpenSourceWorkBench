from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverHealthState,
    OptionalSolverRefreshResult,
    OptionalSolverRefreshState,
    OptionalSolverStackDiscovery,
    apply_optional_solver_refresh_canceled,
    apply_optional_solver_refresh_failure,
    apply_optional_solver_refresh_success,
    build_optional_solver_health_panel_viewmodel,
    parse_optional_solver_manifest_dict,
)


def _manifest(stack_id: str):
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": stack_id,
            "display_name": stack_id.title(),
            "capabilities": [{"capability_id": "example", "description": "Example"}],
            "executable_requirements": [{"identifier": f"{stack_id}-tool"}],
            "prepared_machine_notes": ["Use a prepared machine."],
            "documentation_refs": ["docs/example.md"],
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver install."],
        }
    )


def _current_panel():
    return build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("alpha")],
        selected_stack_id="alpha",
    )


def _success_result():
    return OptionalSolverRefreshResult(
        request_id="req-ok",
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


def test_success_returns_new_health_panel_viewmodel() -> None:
    current = _current_panel()

    applied = apply_optional_solver_refresh_success(
        current,
        manifests=[_manifest("alpha")],
        result=_success_result(),
        active_request_id="req-ok",
    )

    assert applied.panel is not current
    assert applied.panel.cards[0].health_state == "discovered"
    assert "not validation evidence" in applied.status_text


def test_failure_preserves_prior_health_panel_viewmodel() -> None:
    current = _current_panel()
    result = OptionalSolverRefreshResult(
        request_id="req-fail",
        state=OptionalSolverRefreshState.FAILED,
        error_text="runner failed",
    )

    applied = apply_optional_solver_refresh_failure(
        current,
        result=result,
        active_request_id="req-fail",
    )

    assert applied.panel is current
    assert applied.applied is False
    assert applied.state == OptionalSolverRefreshState.FAILED
    assert applied.error_text == "runner failed"


def test_cancel_preserves_prior_health_panel_viewmodel() -> None:
    current = _current_panel()
    result = OptionalSolverRefreshResult(
        request_id="req-cancel",
        state=OptionalSolverRefreshState.CANCELED,
    )

    applied = apply_optional_solver_refresh_canceled(
        current,
        result=result,
        active_request_id="req-cancel",
    )

    assert applied.panel is current
    assert applied.applied is False
    assert applied.state == OptionalSolverRefreshState.CANCELED
    assert "canceled" in applied.status_text.lower()
