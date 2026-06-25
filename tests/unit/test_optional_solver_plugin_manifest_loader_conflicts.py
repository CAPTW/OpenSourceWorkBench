from __future__ import annotations

from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestDocument,
    load_optional_solver_plugin_manifest_documents,
    load_optional_solver_plugin_manifest_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"


def _manifest(stack_id: str) -> dict[str, object]:
    return {
        "stack_id": stack_id,
        "display_name": "Duplicate Stack",
        "related_issue": 6,
        "capabilities": [{"capability_id": "duplicate_guidance"}],
        "executable_requirements": [{"identifier": "duplicate-tool"}],
        "python_package_requirements": [],
        "environment_variable_hints": [],
        "smoke_test_description": "Prepared-machine check only.",
        "prepared_machine_notes": ["Use only where duplicate-tool is available."],
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


def test_builtin_conflict_policy_prevents_plugin_override_by_default() -> None:
    report = load_optional_solver_plugin_manifest_json(
        FIXTURES / "duplicate_stack_plugin_manifest.json"
    )

    assert not report.accepted_manifests
    assert len(report.rejected_manifests) == 1
    assert report.conflicts[0].stack_id == "gmsh"
    assert any(
        diagnostic.code == "OSPL_BUILTIN_OVERRIDE_FORBIDDEN"
        for diagnostic in report.diagnostics
    )


def test_duplicate_stack_id_conflict_is_diagnosed() -> None:
    first = {
        "schema_version": "1",
        "source": {
            "type": "project_local",
            "label": "Project source",
            "reference": "project:one.json",
        },
        "manifest": _manifest("duplicate_custom_stack"),
    }
    second = {
        "schema_version": "1",
        "source": {
            "type": "user_local",
            "label": "User source",
            "reference": "user:two.json",
        },
        "manifest": _manifest("duplicate_custom_stack"),
    }

    report = load_optional_solver_plugin_manifest_documents((first, second))

    assert len(report.accepted_manifests) == 1
    assert len(report.rejected_manifests) == 1
    assert report.conflicts[0].stack_id == "duplicate_custom_stack"
    assert any(diagnostic.code == "OSPL_DUPLICATE_STACK_ID" for diagnostic in report.diagnostics)


def test_document_model_can_be_loaded_explicitly() -> None:
    document = OptionalSolverPluginManifestDocument(
        manifest_data=_manifest("document_stack"),
        source=load_optional_solver_plugin_manifest_json(
            FIXTURES / "valid_project_local_manifest.json"
        ).accepted_manifests[0].source,
        schema_version="1",
        document_ref="document:test",
    )

    report = load_optional_solver_plugin_manifest_documents((document,))

    assert report.accepted_manifests[0].stack_id == "document_stack"
