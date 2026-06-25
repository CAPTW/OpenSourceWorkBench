from __future__ import annotations

from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverManifestSource,
    OptionalSolverManifestSourceType,
    OptionalSolverManifestTrustLabel,
    OptionalSolverPluginManifestAcceptedRowViewModel,
    OptionalSolverPluginManifestAction,
    OptionalSolverPluginManifestActionState,
    OptionalSolverPluginManifestConflictRowViewModel,
    OptionalSolverPluginManifestDiagnosticRowViewModel,
    OptionalSolverPluginManifestGuiViewModel,
    OptionalSolverPluginManifestRejectedRowViewModel,
    OptionalSolverPluginManifestSummaryViewModel,
    OptionalSolverPluginManifestTrustBadgeViewModel,
    build_optional_solver_plugin_manifest_gui_viewmodel,
    explain_optional_solver_plugin_manifest_gui_viewmodel,
    load_optional_solver_plugin_manifest_dict,
    load_optional_solver_plugin_manifest_json,
    summarize_optional_solver_plugin_manifest_gui_viewmodel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
VALID_PROJECT = FIXTURES / "valid_project_local_manifest.json"
DUPLICATE_STACK = FIXTURES / "duplicate_stack_plugin_manifest.json"
INVALID_BUNDLED = FIXTURES / "invalid_bundled_solver_claim.json"


def valid_project_report():
    return load_optional_solver_plugin_manifest_json(VALID_PROJECT)


def duplicate_stack_report():
    return load_optional_solver_plugin_manifest_json(DUPLICATE_STACK)


def invalid_bundled_report():
    return load_optional_solver_plugin_manifest_json(INVALID_BUNDLED)


def third_party_report():
    return load_optional_solver_plugin_manifest_dict(
        {
            "stack_id": "third_party_stack",
            "display_name": "Third Party Stack",
            "related_issue": 11,
            "capabilities": [
                {
                    "capability_id": "third_party_guidance",
                    "description": "Third-party preview guidance.",
                }
            ],
            "executable_requirements": [{"identifier": "third-party-tool"}],
            "python_package_requirements": [],
            "environment_variable_hints": [],
            "smoke_test_description": "Prepared-machine check only.",
            "prepared_machine_notes": [
                "Use only where third-party-tool is already available."
            ],
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
        },
        source=OptionalSolverManifestSource(
            source_type=OptionalSolverManifestSourceType.PLUGIN_PACKAGE,
            trust_label=OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN,
            label="Third-party fixture",
            reference="plugin:third_party_fixture",
        ),
    )


def test_public_api_imports() -> None:
    assert OptionalSolverPluginManifestGuiViewModel
    assert OptionalSolverPluginManifestSummaryViewModel
    assert OptionalSolverPluginManifestAcceptedRowViewModel
    assert OptionalSolverPluginManifestRejectedRowViewModel
    assert OptionalSolverPluginManifestConflictRowViewModel
    assert OptionalSolverPluginManifestDiagnosticRowViewModel
    assert OptionalSolverPluginManifestTrustBadgeViewModel
    assert OptionalSolverPluginManifestAction.CHOOSE_EXPLICIT_JSON_FILES.value
    assert OptionalSolverPluginManifestActionState
    assert callable(build_optional_solver_plugin_manifest_gui_viewmodel)
    assert callable(summarize_optional_solver_plugin_manifest_gui_viewmodel)
    assert callable(explain_optional_solver_plugin_manifest_gui_viewmodel)


def test_builds_viewmodel_from_accepted_only_load_report() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report(),
        selected_stack_id="project_local_stack",
    )

    assert view_model.summary.accepted_count == 1
    assert view_model.summary.rejected_count == 0
    assert view_model.summary.conflict_count == 0
    assert view_model.accepted_rows[0].stack_id == "project_local_stack"
    assert view_model.selected_stack_present is True
    assert view_model.not_validation_evidence is True
    assert "not validation evidence" in summarize_optional_solver_plugin_manifest_gui_viewmodel(
        view_model
    ).lower()


def test_explanation_records_safety_boundary() -> None:
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )
    explanation = explain_optional_solver_plugin_manifest_gui_viewmodel(view_model).lower()

    assert "consumes loader reports only" in explanation
    assert "does not load files" in explanation
    assert "parse json" in explanation
    assert "execute solvers" in explanation
