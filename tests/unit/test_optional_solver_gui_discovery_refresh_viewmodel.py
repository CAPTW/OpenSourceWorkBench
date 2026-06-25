from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverExecutableDiscovery,
    OptionalSolverHealthState,
    OptionalSolverRefreshAction,
    OptionalSolverRefreshActionState,
    OptionalSolverRefreshPlan,
    OptionalSolverRefreshRequest,
    OptionalSolverRefreshResult,
    OptionalSolverRefreshState,
    OptionalSolverRefreshStatusViewModel,
    OptionalSolverStackDiscovery,
    apply_optional_solver_refresh_success,
    build_optional_solver_health_panel_viewmodel,
    build_optional_solver_refresh_plan,
    build_optional_solver_refresh_status_viewmodel,
    explain_optional_solver_refresh,
    parse_optional_solver_manifest_dict,
)


def _manifest(stack_id: str, issue: int = 6):
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": stack_id,
            "display_name": stack_id.title(),
            "related_issue": issue,
            "capabilities": [{"capability_id": "example", "description": "Example"}],
            "executable_requirements": [
                {"identifier": f"{stack_id}-tool", "display_name": "Example Tool"}
            ],
            "smoke_test_description": "Passive fixture.",
            "prepared_machine_notes": ["Use a prepared machine."],
            "documentation_refs": ["docs/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver install.", "No bundled solver."],
        }
    )


def _stack(stack_id: str, state: OptionalSolverHealthState):
    found = state == OptionalSolverHealthState.DISCOVERED
    return OptionalSolverStackDiscovery(
        stack_id=stack_id,
        display_name=stack_id.title(),
        related_issue=6,
        health_state=state,
        executables=(
            OptionalSolverExecutableDiscovery(
                identifier=f"{stack_id}-tool",
                required=True,
                found=found,
                redacted_path=f"<redacted:{stack_id}-tool.exe>" if found else "",
            ),
        ),
    )


def _panel():
    return build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("alpha"), _manifest("beta")],
        selected_stack_id="alpha",
        filter_text="",
    )


def test_public_api_imports() -> None:
    assert OptionalSolverRefreshState.IDLE.value == "idle"
    assert OptionalSolverRefreshAction.REFRESH_PASSIVE_DISCOVERY.value
    assert OptionalSolverRefreshActionState
    assert OptionalSolverRefreshPlan
    assert OptionalSolverRefreshRequest
    assert OptionalSolverRefreshResult
    assert OptionalSolverRefreshStatusViewModel
    assert callable(build_optional_solver_refresh_plan)
    assert callable(build_optional_solver_refresh_status_viewmodel)


def test_build_idle_refresh_plan() -> None:
    panel = _panel()

    plan = build_optional_solver_refresh_plan(panel)

    assert plan.state == OptionalSolverRefreshState.IDLE
    assert plan.request is None
    assert plan.can_request_refresh is True
    assert plan.can_cancel_refresh is False
    assert plan.status.status_text == "Refresh idle."
    assert plan.not_validation_evidence is True


def test_generated_request_id_when_not_injected() -> None:
    plan = build_optional_solver_refresh_plan(
        _panel(),
        state=OptionalSolverRefreshState.PENDING,
    )

    assert plan.request is not None
    assert plan.request.request_id.startswith("osr-")


def test_injected_request_id_is_deterministic() -> None:
    plan = build_optional_solver_refresh_plan(
        _panel(),
        state=OptionalSolverRefreshState.RUNNING,
        request_id="req-123",
    )

    assert plan.request is not None
    assert plan.request.request_id == "req-123"
    assert plan.status.active_request_id == "req-123"


def test_explain_refresh_mentions_no_execution() -> None:
    plan = build_optional_solver_refresh_plan(_panel())

    explanation = explain_optional_solver_refresh(plan)

    assert "does not run discovery" in explanation
    assert "execute solvers" in explanation


def test_success_applies_supplied_reports() -> None:
    current = _panel()
    report = OptionalSolverDiscoveryReport(
        stacks=(_stack("alpha", OptionalSolverHealthState.DISCOVERED),),
        generated_at="2026-06-25T00:00:00Z",
        source="test_runner",
    )
    result = OptionalSolverRefreshResult(
        request_id="req-1",
        discovery_reports=report,
        generated_at=report.generated_at,
        source=report.source,
    )

    applied = apply_optional_solver_refresh_success(
        current,
        manifests=[_manifest("alpha")],
        result=result,
        active_request_id="req-1",
    )

    assert applied.applied is True
    assert applied.ignored is False
    assert applied.state == OptionalSolverRefreshState.COMPLETED
    assert applied.panel.cards[0].health_state == "discovered"
    assert applied.last_refresh_timestamp == "2026-06-25T00:00:00Z"
    assert applied.source == "test_runner"
    assert applied.not_validation_evidence is True
