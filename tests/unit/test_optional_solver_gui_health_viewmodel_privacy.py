from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverEnvironmentHintDiscovery,
    OptionalSolverExecutableDiscovery,
    OptionalSolverHealthState,
    OptionalSolverStackDiscovery,
    build_optional_solver_health_panel_viewmodel,
    parse_optional_solver_manifest_dict,
)


def test_redacted_paths_remain_redacted_and_environment_values_are_hidden() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "openfoam",
            "display_name": "OpenFOAM",
            "related_issue": 9,
            "capabilities": ["cfd"],
            "executable_requirements": ["foamVersion"],
            "environment_variable_hints": ["FOAM_APPBIN"],
            "smoke_test_description": "Prepared smoke.",
            "prepared_machine_notes": ["Use an initialized OpenFOAM shell."],
            "documentation_refs": ["docs/validation/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver install.", "No dependency install."],
        }
    )
    report = OptionalSolverDiscoveryReport(
        stacks=(
            OptionalSolverStackDiscovery(
                stack_id="openfoam",
                display_name="OpenFOAM",
                related_issue=9,
                health_state=OptionalSolverHealthState.DISCOVERED,
                executables=(
                    OptionalSolverExecutableDiscovery(
                        identifier="foamVersion",
                        found=True,
                        path="C:/Users/USER/OpenFOAM/bin/foamVersion.exe",
                    ),
                ),
                environment_hints=(
                    OptionalSolverEnvironmentHintDiscovery(
                        name="FOAM_APPBIN",
                        present=True,
                        value="C:/Users/USER/OpenFOAM/bin",
                    ),
                ),
            ),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[manifest],
        discovery_reports=report,
        selected_stack_id="openfoam",
    )
    panel_text = str(panel)

    assert "C:/Users/USER/OpenFOAM" not in panel_text
    assert panel.details is not None
    assert panel.details.executable_requirements[0].detail_text == "<redacted>"
    assert panel.details.environment_hints[0].detail_text == "<redacted>"
