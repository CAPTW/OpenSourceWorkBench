from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverDiagnosticSeverity,
    parse_optional_solver_manifest_dict,
    validate_optional_solver_manifest,
)


def test_invalid_missing_fields_produce_diagnostics() -> None:
    report = validate_optional_solver_manifest({})

    assert not report.is_valid
    codes = {diagnostic.code for diagnostic in report.diagnostics}
    assert "OSM_REQUIRED_FIELD_MISSING" in codes
    assert "OSM_STACK_ID_EMPTY" in codes
    assert "OSM_CAPABILITIES_EMPTY" in codes


def test_empty_requirement_identifier_produces_diagnostic() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "example",
            "display_name": "Example",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": [""],
            "smoke_test_description": "Smoke.",
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

    report = validate_optional_solver_manifest(manifest)

    assert not report.is_valid
    assert any(
        diagnostic.code == "OSM_REQUIREMENT_IDENTIFIER_EMPTY"
        for diagnostic in report.diagnostics
    )


def test_installer_probe_command_is_blocked_but_not_executed() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "example",
            "display_name": "Example",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": ["example-tool"],
            "version_probe": {
                "name": "bad installer",
                "command": ["pip", "install", "not-a-real-package"],
            },
            "smoke_test_description": "Smoke.",
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

    report = validate_optional_solver_manifest(manifest)

    assert not report.is_valid
    assert any(
        diagnostic.code == "OSM_PROBE_INSTALLER_COMMAND"
        and diagnostic.severity == OptionalSolverDiagnosticSeverity.BLOCKER
        for diagnostic in report.diagnostics
    )


def test_documentation_refs_must_be_strings() -> None:
    report = validate_optional_solver_manifest(
        {
            "stack_id": "example",
            "display_name": "Example",
            "related_issue": 6,
            "capabilities": ["example"],
            "executable_requirements": ["example-tool"],
            "smoke_test_description": "Smoke.",
            "prepared_machine_notes": ["Prepared only."],
            "documentation_refs": [123],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": [
                "No solver install.",
                "No dependency install.",
                "No bundled solver.",
            ],
        }
    )

    assert not report.is_valid
    assert any(
        diagnostic.code == "OSM_DOCUMENTATION_REF_NOT_STRING"
        for diagnostic in report.diagnostics
    )


def test_builtin_issue_mapping_is_validated() -> None:
    manifest = parse_optional_solver_manifest_dict(
        {
            "stack_id": "calculix",
            "display_name": "CalculiX",
            "related_issue": 6,
            "capabilities": ["installed_only_run_gate"],
            "executable_requirements": ["ccx"],
            "smoke_test_description": "Smoke.",
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

    report = validate_optional_solver_manifest(manifest)

    assert not report.is_valid
    assert any(
        diagnostic.code == "OSM_RELATED_ISSUE_MISMATCH"
        for diagnostic in report.diagnostics
    )
