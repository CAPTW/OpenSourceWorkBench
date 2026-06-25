from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverExecutableDiscovery,
    OptionalSolverHealthState,
    OptionalSolverPythonPackageDiscovery,
    OptionalSolverStackDiscovery,
    build_optional_solver_health_panel_viewmodel,
    parse_optional_solver_manifest_dict,
)


def test_details_model_includes_capabilities_requirements_and_notes() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "calculix",
            "display_name": "CalculiX",
            "related_issue": 8,
            "capabilities": [
                {
                    "capability_id": "run_gate",
                    "description": "Prepared-machine run gate.",
                }
            ],
            "executable_requirements": [
                {"identifier": "ccx", "display_name": "CalculiX ccx"}
            ],
            "python_package_requirements": [
                {"identifier": "meshio", "display_name": "meshio", "required": False}
            ],
            "version_probe": {"name": "ccx version", "command": ["ccx", "-v"]},
            "help_probe": {"name": "ccx help", "command": ["ccx"]},
            "smoke_test_description": "Prepared smoke.",
            "prepared_machine_notes": ["Run only when ccx is already installed."],
            "documentation_refs": ["docs/validation/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver install.", "No dependency install."],
        }
    )
    report = OptionalSolverDiscoveryReport(
        stacks=(
            OptionalSolverStackDiscovery(
                stack_id="calculix",
                display_name="CalculiX",
                related_issue=8,
                health_state=OptionalSolverHealthState.PARTIALLY_INSTALLED,
                executables=(
                    OptionalSolverExecutableDiscovery(
                        identifier="ccx",
                        display_name="CalculiX ccx",
                        found=True,
                        redacted_path="<redacted:ccx.exe>",
                    ),
                ),
                python_packages=(
                    OptionalSolverPythonPackageDiscovery(
                        identifier="meshio",
                        display_name="meshio",
                        required=False,
                        found=False,
                    ),
                ),
            ),
        )
    )

    panel = build_optional_solver_health_panel_viewmodel(
        manifests=[manifest],
        discovery_reports=report,
        selected_stack_id="calculix",
    )
    assert panel.details is not None
    details = panel.details

    assert details.capabilities == ("run_gate: Prepared-machine run gate.",)
    assert details.executable_requirements[0].identifier == "ccx"
    assert details.executable_requirements[0].detail_text == "<redacted:ccx.exe>"
    assert details.python_package_requirements[0].status_text == "missing"
    assert "not executed" in details.version_probe_text
    assert "not executed" in details.help_probe_text
    assert details.prepared_machine_notes == ("Run only when ccx is already installed.",)
    assert details.documentation_refs == ("docs/validation/example.md",)
