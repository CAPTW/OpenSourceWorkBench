from __future__ import annotations

from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverManifestSource,
    OptionalSolverManifestSourceType,
    OptionalSolverManifestTrustLabel,
    load_optional_solver_plugin_manifest_dict,
    load_optional_solver_plugin_manifest_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"


def _valid_manifest(stack_id: str) -> dict[str, object]:
    return {
        "stack_id": stack_id,
        "display_name": "Diagnostic Stack",
        "related_issue": 6,
        "capabilities": [{"capability_id": "diagnostic_guidance"}],
        "executable_requirements": [{"identifier": "diagnostic-tool"}],
        "python_package_requirements": [],
        "environment_variable_hints": [],
        "smoke_test_description": "Prepared-machine check only.",
        "prepared_machine_notes": ["Use only where diagnostic-tool is available."],
        "platform_notes": [],
        "documentation_refs": [
            "docs/experimental/optional_solver_plugin_manifest_loading_design.md"
        ],
        "support_status": "experimental",
        "non_bundled_disclaimer": "External solvers are not bundled.",
        "safety_notes": [
            "No install workflow.",
            "No dependency install.",
            "No bundled solver.",
        ],
    }


def _project_source() -> OptionalSolverManifestSource:
    return OptionalSolverManifestSource(
        source_type=OptionalSolverManifestSourceType.PROJECT_LOCAL,
        trust_label=OptionalSolverManifestTrustLabel.REVIEWED_PROJECT,
        label="Project source",
        reference="project:diagnostic.json",
    )


def _blocking_codes(report: object) -> set[str]:
    return {
        diagnostic.code
        for diagnostic in report.diagnostics
        if diagnostic.is_blocking
    }


def test_invalid_missing_source_metadata_is_rejected() -> None:
    report = load_optional_solver_plugin_manifest_json(
        FIXTURES / "invalid_missing_source_metadata.json"
    )

    assert not report.accepted_manifests
    assert "OSPL_SOURCE_METADATA_INCOMPLETE" in _blocking_codes(report)


def test_unsupported_schema_version_is_diagnosed() -> None:
    report = load_optional_solver_plugin_manifest_dict(
        {
            "schema_version": "999",
            "source": {
                "type": "project_local",
                "label": "Project source",
                "reference": "project:unsupported.json",
            },
            "manifest": _valid_manifest("unsupported_schema_stack"),
        }
    )

    assert not report.accepted_manifests
    assert "OSPL_SCHEMA_VERSION_UNSUPPORTED" in _blocking_codes(report)


def test_installer_command_wording_is_rejected() -> None:
    report = load_optional_solver_plugin_manifest_json(
        FIXTURES / "invalid_installer_command.json"
    )

    assert not report.accepted_manifests
    assert "OSPL_INSTALLER_COMMAND_PRESENT" in _blocking_codes(report)


def test_bundled_solver_claim_is_rejected() -> None:
    report = load_optional_solver_plugin_manifest_json(
        FIXTURES / "invalid_bundled_solver_claim.json"
    )

    assert not report.accepted_manifests
    assert "OSPL_BUNDLED_SOLVER_CLAIM" in _blocking_codes(report)


def test_certification_claim_is_rejected() -> None:
    manifest = _valid_manifest("certification_claim_stack")
    manifest["prepared_machine_notes"] = ["This stack is certified for production."]

    report = load_optional_solver_plugin_manifest_dict(
        manifest,
        source=_project_source(),
    )

    assert not report.accepted_manifests
    assert "OSPL_CERTIFICATION_CLAIM" in _blocking_codes(report)
