from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverLoadedManifest,
    OptionalSolverManifestConflict,
    OptionalSolverManifestSource,
    OptionalSolverManifestSourceType,
    OptionalSolverManifestTrustLabel,
    OptionalSolverPluginManifestDocument,
    OptionalSolverPluginManifestLoadDiagnostic,
    OptionalSolverPluginManifestLoaderOptions,
    OptionalSolverPluginManifestLoadReport,
    OptionalSolverRejectedManifest,
    explain_optional_solver_plugin_manifest_load_report,
    load_optional_solver_plugin_manifest_dict,
    load_optional_solver_plugin_manifest_documents,
    load_optional_solver_plugin_manifest_json,
)


def _valid_manifest(stack_id: str = "project_stack") -> dict[str, object]:
    return {
        "stack_id": stack_id,
        "display_name": "Project Stack",
        "related_issue": 6,
        "capabilities": [
            {
                "capability_id": "project_guidance",
                "description": "Project optional stack guidance.",
            }
        ],
        "executable_requirements": [
            {
                "identifier": "project-tool",
                "display_name": "Project tool",
            }
        ],
        "python_package_requirements": [],
        "environment_variable_hints": [],
        "smoke_test_description": "Prepared-machine check only.",
        "prepared_machine_notes": ["Use only where project-tool is available."],
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
        label="Project fixtures",
        reference="project:.osw/optional_solvers/project_stack.json",
    )


def test_public_api_imports() -> None:
    assert OptionalSolverManifestSourceType.PROJECT_LOCAL.value == "project_local"
    assert OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN.value
    assert OptionalSolverManifestSource
    assert OptionalSolverPluginManifestDocument
    assert OptionalSolverLoadedManifest
    assert OptionalSolverRejectedManifest
    assert OptionalSolverManifestConflict
    assert OptionalSolverPluginManifestLoadDiagnostic
    assert OptionalSolverPluginManifestLoadReport
    assert OptionalSolverPluginManifestLoaderOptions
    assert callable(load_optional_solver_plugin_manifest_dict)
    assert callable(load_optional_solver_plugin_manifest_json)
    assert callable(load_optional_solver_plugin_manifest_documents)
    assert callable(explain_optional_solver_plugin_manifest_load_report)


def test_load_valid_manifest_from_dict() -> None:
    report = load_optional_solver_plugin_manifest_dict(
        _valid_manifest(),
        source=_project_source(),
    )

    assert len(report.accepted_manifests) == 1
    assert not report.rejected_manifests
    loaded = report.accepted_manifests[0]
    assert loaded.stack_id == "project_stack"
    assert loaded.source.source_type == OptionalSolverManifestSourceType.PROJECT_LOCAL
    assert loaded.source.trust_label == OptionalSolverManifestTrustLabel.REVIEWED_PROJECT
    assert loaded.validation_report.is_valid


def test_report_serializes_and_explains_non_validation_boundary() -> None:
    report = load_optional_solver_plugin_manifest_dict(
        _valid_manifest(),
        source=_project_source(),
    )
    payload = report.to_dict()
    explanation = explain_optional_solver_plugin_manifest_load_report(report).lower()

    assert payload["accepted_count"] == 1
    assert payload["plugin_manifest_presence_is_validation_evidence"] is False
    assert "does not execute plugin code" in explanation
    assert "provide validation evidence" in explanation
