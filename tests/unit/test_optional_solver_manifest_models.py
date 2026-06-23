from __future__ import annotations

from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverCapability,
    OptionalSolverHealthState,
    OptionalSolverManifest,
    OptionalSolverManifestDiagnostic,
    OptionalSolverManifestValidationReport,
    OptionalSolverProbe,
    OptionalSolverRequirement,
    OptionalSolverStackId,
    OptionalSolverSupportStatus,
    builtin_optional_solver_manifests,
    dump_optional_solver_manifest_json,
    explain_optional_solver_manifest,
    get_builtin_optional_solver_manifest,
    load_optional_solver_manifest_json,
    parse_optional_solver_manifest_dict,
    validate_optional_solver_manifest,
)


def _valid_manifest_dict() -> dict[str, object]:
    return {
        "stack_id": "example_stack",
        "display_name": "Example Stack",
        "related_issue": 6,
        "capabilities": [
            {
                "capability_id": "example_capability",
                "description": "Example capability.",
            }
        ],
        "executable_requirements": [
            {
                "identifier": "example-tool",
                "display_name": "Example executable",
            }
        ],
        "python_package_requirements": [
            {
                "identifier": "example_package",
                "display_name": "Example package",
                "required": False,
            }
        ],
        "environment_variable_hints": ["EXAMPLE_HOME"],
        "version_probe": {
            "name": "example version",
            "command": ["example-tool", "--version"],
            "description": "Declarative version probe.",
        },
        "help_probe": {
            "name": "example help",
            "command": ["example-tool", "--help"],
        },
        "smoke_test_description": "Declarative smoke description.",
        "prepared_machine_notes": ["Use an already prepared machine."],
        "platform_notes": ["Example platform note."],
        "documentation_refs": ["docs/example.md"],
        "support_status": "experimental",
        "non_bundled_disclaimer": "External solvers are not bundled.",
        "safety_notes": [
            "No solver install.",
            "No dependency install.",
            "No bundled solver.",
        ],
    }


def test_public_api_imports() -> None:
    assert OptionalSolverManifest
    assert OptionalSolverRequirement
    assert OptionalSolverCapability
    assert OptionalSolverProbe
    assert OptionalSolverStackId.GMSH.value == "gmsh"
    assert OptionalSolverHealthState.UNKNOWN.value == "unknown"
    assert OptionalSolverSupportStatus.EXPERIMENTAL.value == "experimental"
    assert OptionalSolverManifestDiagnostic
    assert OptionalSolverManifestValidationReport
    assert callable(parse_optional_solver_manifest_dict)
    assert callable(validate_optional_solver_manifest)
    assert callable(load_optional_solver_manifest_json)
    assert callable(dump_optional_solver_manifest_json)
    assert callable(builtin_optional_solver_manifests)
    assert callable(get_builtin_optional_solver_manifest)
    assert callable(explain_optional_solver_manifest)


def test_parse_valid_manifest_dict() -> None:
    manifest = parse_optional_solver_manifest_dict(_valid_manifest_dict())

    assert manifest.stack_id == "example_stack"
    assert manifest.display_name == "Example Stack"
    assert manifest.related_issue == 6
    assert manifest.capabilities[0].capability_id == "example_capability"
    assert manifest.executable_requirements[0].identifier == "example-tool"
    assert manifest.python_package_requirements[0].identifier == "example_package"
    assert manifest.version_probe is not None
    assert manifest.version_probe.command == ("example-tool", "--version")


def test_dump_load_json_round_trip(tmp_path: Path) -> None:
    manifest = parse_optional_solver_manifest_dict(_valid_manifest_dict())
    path = tmp_path / "manifest.json"

    dump_optional_solver_manifest_json(manifest, path)
    loaded = load_optional_solver_manifest_json(path)

    assert loaded == manifest
    assert loaded.to_dict() == manifest.to_dict()


def test_validation_report_has_expected_shape() -> None:
    manifest = parse_optional_solver_manifest_dict(_valid_manifest_dict())
    report = validate_optional_solver_manifest(manifest)

    assert isinstance(report, OptionalSolverManifestValidationReport)
    assert report.stack_id == "example_stack"
    assert report.is_valid
    payload = report.to_dict()
    assert payload["stack_id"] == "example_stack"
    assert payload["is_valid"] is True
    assert payload["diagnostics"] == []


def test_health_states_include_required_values() -> None:
    values = {state.value for state in OptionalSolverHealthState}

    assert values == {
        "unknown",
        "missing",
        "partially_installed",
        "discovered",
        "smoke_passed",
        "smoke_failed",
        "blocked_no_safe_case",
        "unsupported_platform",
        "skipped_by_user",
    }


def test_explain_manifest_states_declarative_boundary() -> None:
    manifest = parse_optional_solver_manifest_dict(_valid_manifest_dict())

    explanation = explain_optional_solver_manifest(manifest).lower()

    assert "declarative only" in explanation
    assert "does not install" in explanation
    assert "execute probes" in explanation
