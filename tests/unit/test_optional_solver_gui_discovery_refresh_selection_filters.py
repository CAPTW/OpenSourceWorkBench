from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverHealthState,
    OptionalSolverRefreshRequest,
    OptionalSolverRefreshResult,
    OptionalSolverStackDiscovery,
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


def _report(*stack_ids: str):
    return OptionalSolverDiscoveryReport(
        stacks=tuple(
            OptionalSolverStackDiscovery(
                stack_id=stack_id,
                display_name=stack_id.title(),
                related_issue=6,
                health_state=OptionalSolverHealthState.DISCOVERED,
            )
            for stack_id in stack_ids
        )
    )


def test_selected_stack_preserved_when_present() -> None:
    current = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("alpha"), _manifest("beta")],
        selected_stack_id="beta",
        filter_text="",
    )
    request = OptionalSolverRefreshRequest(
        request_id="req",
        selected_stack_id="beta",
        filter_text="",
    )

    applied = apply_optional_solver_refresh_success(
        current,
        manifests=[_manifest("alpha"), _manifest("beta")],
        result=OptionalSolverRefreshResult("req", discovery_reports=_report("alpha", "beta")),
        request=request,
        active_request_id="req",
    )

    assert applied.selected_stack_id == "beta"
    assert applied.panel.selected_stack_id == "beta"


def test_selected_stack_falls_back_when_missing() -> None:
    current = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("alpha"), _manifest("beta")],
        selected_stack_id="beta",
    )

    applied = apply_optional_solver_refresh_success(
        current,
        manifests=[_manifest("alpha")],
        result=OptionalSolverRefreshResult("req", discovery_reports=_report("alpha")),
        active_request_id="req",
    )

    assert applied.selected_stack_id == "alpha"
    assert applied.panel.selected_stack_id == "alpha"


def test_filters_preserved_where_safe() -> None:
    current = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("alpha"), _manifest("beta")],
        selected_stack_id="alpha",
        filter_text="alp",
        health_state_filters=("discovered",),
    )

    applied = apply_optional_solver_refresh_success(
        current,
        manifests=[_manifest("alpha"), _manifest("beta")],
        result=OptionalSolverRefreshResult("req", discovery_reports=_report("alpha", "beta")),
        active_request_id="req",
    )

    assert applied.filter_text == "alp"
    assert applied.health_state_filters == ("discovered",)
    assert [card.stack_id for card in applied.panel.cards] == ["alpha"]
