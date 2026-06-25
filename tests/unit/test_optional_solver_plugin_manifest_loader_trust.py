from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverManifestSource,
    OptionalSolverManifestSourceType,
    OptionalSolverManifestTrustLabel,
    get_builtin_optional_solver_manifest,
    load_optional_solver_plugin_manifest_dict,
)


def _valid_manifest(stack_id: str) -> dict[str, object]:
    return {
        "stack_id": stack_id,
        "display_name": "Trust Stack",
        "related_issue": 6,
        "capabilities": [{"capability_id": "trust_guidance"}],
        "executable_requirements": [{"identifier": "trust-tool"}],
        "python_package_requirements": [],
        "environment_variable_hints": [],
        "smoke_test_description": "Prepared-machine check only.",
        "prepared_machine_notes": ["Use only where trust-tool is available."],
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


def test_builtin_source_is_trusted_when_explicitly_supplied() -> None:
    source = OptionalSolverManifestSource(
        source_type=OptionalSolverManifestSourceType.BUILTIN,
        trust_label=OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN,
        label="Built-in manifests",
        reference="builtin:gmsh",
    )
    report = load_optional_solver_plugin_manifest_dict(
        get_builtin_optional_solver_manifest("gmsh").to_dict(),
        source=source,
    )

    assert len(report.accepted_manifests) == 1
    assert report.accepted_manifests[0].source.trust_label == (
        OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN
    )


def test_plugin_package_source_is_third_party_not_trusted_by_default() -> None:
    source = OptionalSolverManifestSource(
        source_type=OptionalSolverManifestSourceType.PLUGIN_PACKAGE,
        trust_label=OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN,
        label="Third-party plugin",
        reference="plugin:example.stack",
    )
    report = load_optional_solver_plugin_manifest_dict(
        _valid_manifest("third_party_stack"),
        source=source,
    )

    assert len(report.accepted_manifests) == 1
    assert report.accepted_manifests[0].source.trust_label == (
        OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN
    )
    assert report.accepted_manifests[0].source.trust_label != (
        OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN
    )


def test_mismatched_trust_label_is_normalized_with_warning() -> None:
    source = OptionalSolverManifestSource(
        source_type=OptionalSolverManifestSourceType.USER_LOCAL,
        trust_label=OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN,
        label="User source",
        reference="user:stack.json",
    )
    report = load_optional_solver_plugin_manifest_dict(
        _valid_manifest("user_stack"),
        source=source,
    )

    assert report.accepted_manifests[0].source.trust_label == (
        OptionalSolverManifestTrustLabel.USER_PROVIDED
    )
    assert any(
        diagnostic.code == "OSPL_TRUST_LABEL_NORMALIZED"
        for diagnostic in report.diagnostics
    )
