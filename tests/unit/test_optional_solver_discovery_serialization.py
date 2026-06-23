from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryOptions,
    discover_optional_solver_stack,
    optional_solver_discovery_report_from_dict,
    optional_solver_discovery_report_to_dict,
    parse_optional_solver_manifest_dict,
)
from osw.experimental.optional_solvers.discovery_models import (
    OptionalSolverDiscoveryReport,
)


def test_report_serialization_round_trip() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "example_stack",
            "display_name": "Example Stack",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": ["example-tool"],
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
    stack = discover_optional_solver_stack(
        manifest,
        executable_resolver=lambda _name: "C:/Users/USER/tools/example-tool.exe",
    )
    report = OptionalSolverDiscoveryReport(
        generated_at="2026-06-23T00:00:00Z",
        source="unit-test",
        stacks=(stack,),
    )

    payload = optional_solver_discovery_report_to_dict(report)
    loaded = optional_solver_discovery_report_from_dict(payload)

    assert loaded == report
    assert loaded.to_dict() == payload
    assert "C:/Users/USER/tools/example-tool.exe" not in str(payload)


def test_default_path_and_environment_output_are_redacted() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "example_stack",
            "display_name": "Example Stack",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": ["example-tool"],
            "environment_variable_hints": ["EXAMPLE_HOME"],
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

    stack = discover_optional_solver_stack(
        manifest,
        options=OptionalSolverDiscoveryOptions(),
        executable_resolver=lambda _name: "C:/Users/USER/tools/example-tool.exe",
        environment_resolver=lambda _name: "C:/Users/USER/example",
    )
    payload = stack.to_dict()

    assert "C:/Users/USER/tools/example-tool.exe" not in str(payload)
    assert "C:/Users/USER/example" not in str(payload)
    assert "<redacted:example-tool.exe>" in str(payload)
    assert "<redacted>" in str(payload)
