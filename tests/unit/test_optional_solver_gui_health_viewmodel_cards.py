from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverHealthState,
    OptionalSolverStackDiscovery,
    build_optional_solver_health_panel_viewmodel,
    parse_optional_solver_manifest_dict,
)


def _manifest(stack_id: str):
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": stack_id,
            "display_name": stack_id.upper(),
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": [f"{stack_id}-tool"],
            "smoke_test_description": "Passive fixture.",
            "prepared_machine_notes": ["Prepared only."],
            "documentation_refs": ["docs/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": [
                "No solver install.",
                "No dependency install.",
                "No bundled solver.",
            ],
        }
    )


def _stack(stack_id: str, state: OptionalSolverHealthState):
    return OptionalSolverStackDiscovery(
        stack_id=stack_id,
        display_name=stack_id.upper(),
        related_issue=6,
        health_state=state,
    )


def test_stack_cards_are_sorted_deterministically_by_stack_id() -> None:
    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("zeta"), _manifest("alpha"), _manifest("middle")]
    )

    assert [card.stack_id for card in panel.cards] == ["alpha", "middle", "zeta"]


def test_stack_cards_render_missing_partial_and_discovered_status_text() -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            _stack("missing", OptionalSolverHealthState.MISSING),
            _stack("partial", OptionalSolverHealthState.PARTIALLY_INSTALLED),
            _stack("discovered", OptionalSolverHealthState.DISCOVERED),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("missing"), _manifest("partial"), _manifest("discovered")],
        discovery_reports=report,
    )
    status_by_stack = {card.stack_id: card.short_status_text for card in panel.cards}

    assert status_by_stack["missing"] == "Missing required optional components"
    assert status_by_stack["partial"] == "Partially installed optional stack"
    assert status_by_stack["discovered"] == "Discovered by passive checks"


def test_stack_cards_can_be_filtered_by_text_and_health_state() -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            _stack("gmsh", OptionalSolverHealthState.MISSING),
            _stack("calculix", OptionalSolverHealthState.DISCOVERED),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("gmsh"), _manifest("calculix")],
        discovery_reports=report,
        filter_text="calc",
        health_state_filters=["discovered"],
    )

    assert [card.stack_id for card in panel.cards] == ["calculix"]
    assert panel.summary.total_stacks == 1


def test_stack_cards_accept_enum_health_state_filters() -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            _stack("gmsh", OptionalSolverHealthState.MISSING),
            _stack("calculix", OptionalSolverHealthState.DISCOVERED),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("gmsh"), _manifest("calculix")],
        discovery_reports=report,
        health_state_filters=[OptionalSolverHealthState.MISSING],
    )

    assert [card.stack_id for card in panel.cards] == ["gmsh"]
