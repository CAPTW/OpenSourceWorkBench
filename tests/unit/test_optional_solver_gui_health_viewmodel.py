from __future__ import annotations

from dataclasses import dataclass

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverExecutableDiscovery,
    OptionalSolverHealthPanelAction,
    OptionalSolverHealthPanelActionState,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthState,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverPythonPackageDiscovery,
    OptionalSolverStackDiscovery,
    build_optional_solver_health_panel_viewmodel,
    explain_optional_solver_health_panel,
    parse_optional_solver_manifest_dict,
    summarize_optional_solver_health_panel,
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
            "python_package_requirements": [
                {"identifier": f"{stack_id}_pkg", "display_name": "Example Package"}
            ],
            "smoke_test_description": "Passive fixture.",
            "prepared_machine_notes": ["Use a prepared machine."],
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


def _stack(
    stack_id: str,
    state: OptionalSolverHealthState,
) -> OptionalSolverStackDiscovery:
    found = state == OptionalSolverHealthState.DISCOVERED
    partial = state == OptionalSolverHealthState.PARTIALLY_INSTALLED
    return OptionalSolverStackDiscovery(
        stack_id=stack_id,
        display_name=stack_id.title(),
        related_issue=6,
        health_state=state,
        executables=(
            OptionalSolverExecutableDiscovery(
                identifier=f"{stack_id}-tool",
                display_name="Example Tool",
                required=True,
                found=found or partial,
                redacted_path=(
                    f"<redacted:{stack_id}-tool.exe>" if found or partial else ""
                ),
            ),
        ),
        python_packages=(
            OptionalSolverPythonPackageDiscovery(
                identifier=f"{stack_id}_pkg",
                display_name="Example Package",
                required=True,
                found=found,
            ),
        ),
    )


def test_public_api_imports() -> None:
    assert OptionalSolverHealthPanelViewModel
    assert OptionalSolverHealthSummaryViewModel
    assert OptionalSolverHealthPanelAction.INSTALL_SOLVER.value == "install_solver"
    assert OptionalSolverHealthPanelActionState
    assert callable(build_optional_solver_health_panel_viewmodel)
    assert callable(summarize_optional_solver_health_panel)
    assert callable(explain_optional_solver_health_panel)


def test_builds_panel_viewmodel_from_supplied_manifests_and_reports() -> None:
    manifests = [_manifest("missing"), _manifest("partial"), _manifest("discovered")]
    report = OptionalSolverDiscoveryReport(
        stacks=(
            _stack("missing", OptionalSolverHealthState.MISSING),
            _stack("partial", OptionalSolverHealthState.PARTIALLY_INSTALLED),
            _stack("discovered", OptionalSolverHealthState.DISCOVERED),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=manifests,
        discovery_reports=report,
        selected_stack_id="partial",
    )

    assert panel.summary.total_stacks == 3
    assert panel.summary.missing_count == 1
    assert panel.summary.partial_count == 1
    assert panel.summary.discovered_count == 1
    assert panel.summary.open_issue_count == 3
    assert panel.selected_stack_id == "partial"
    assert panel.details is not None
    assert panel.details.stack_id == "partial"
    assert "does not run discovery" in explain_optional_solver_health_panel(panel)


def test_absent_discovery_reports_render_unknown_without_running_discovery() -> None:
    panel = build_optional_solver_health_panel_viewmodel(manifests=[_manifest("alpha")])

    assert panel.summary.counts_by_health_state == {"unknown": 1}
    assert panel.cards[0].health_state == "unknown"
    assert panel.cards[0].short_status_text == "No passive discovery report supplied"


def test_supplied_empty_manifest_list_stays_empty() -> None:
    panel = build_optional_solver_health_panel_viewmodel(manifests=[])

    assert panel.summary.total_stacks == 0
    assert panel.cards == ()
    assert panel.details is None


@dataclass(frozen=True)
class _HistoryRecord:
    source: str
    status: str
    summary: str
    related_issue: int


def test_plain_dataclass_validation_history_records_are_supported() -> None:
    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[_manifest("alpha")],
        validation_history=[
            _HistoryRecord(
                source="OSW-VALID-005",
                status="skipped-missing",
                summary="Not installed on this machine.",
                related_issue=6,
            )
        ],
    )

    assert panel.validation_history[0].source == "OSW-VALID-005"
    assert panel.validation_history[0].is_pass_evidence is False
