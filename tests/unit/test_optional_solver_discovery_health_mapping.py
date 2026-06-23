from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverHealthState,
    discover_optional_solver_stack,
    parse_optional_solver_manifest_dict,
)


def _manifest():
    return parse_optional_solver_manifest_dict(
        {
            "stack_id": "example_stack",
            "display_name": "Example Stack",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": ["example-tool"],
            "python_package_requirements": ["example_pkg"],
            "smoke_test_description": "Passive discovery fixture.",
            "prepared_machine_notes": ["Prepared machine only."],
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


def test_all_required_missing_maps_to_missing() -> None:
    discovery = discover_optional_solver_stack(
        _manifest(),
        executable_resolver=lambda _name: None,
        python_package_resolver=lambda _name: None,
    )

    assert discovery.health_state == OptionalSolverHealthState.MISSING
    assert discovery.confidence == "passive-missing"


def test_some_required_found_maps_to_partial() -> None:
    discovery = discover_optional_solver_stack(
        _manifest(),
        executable_resolver=lambda _name: "C:/tools/example-tool.exe",
        python_package_resolver=lambda _name: None,
    )

    assert discovery.health_state == OptionalSolverHealthState.PARTIALLY_INSTALLED
    assert discovery.confidence == "passive-partial"
    assert any(item.code == "OSD_PARTIAL_STACK" for item in discovery.diagnostics)


def test_all_required_found_maps_to_discovered() -> None:
    discovery = discover_optional_solver_stack(
        _manifest(),
        executable_resolver=lambda _name: "C:/tools/example-tool.exe",
        python_package_resolver=lambda _name: "1.0",
    )

    assert discovery.health_state == OptionalSolverHealthState.DISCOVERED
    assert discovery.confidence == "passive-high"


def test_passive_discovery_never_emits_smoke_states() -> None:
    discovery = discover_optional_solver_stack(
        _manifest(),
        executable_resolver=lambda _name: "C:/tools/example-tool.exe",
        python_package_resolver=lambda _name: "1.0",
    )

    assert discovery.health_state not in {
        OptionalSolverHealthState.SMOKE_PASSED,
        OptionalSolverHealthState.SMOKE_FAILED,
    }
