from __future__ import annotations

from osw.experimental.optional_solvers import (
    builtin_optional_solver_manifests,
    get_builtin_optional_solver_manifest,
    validate_optional_solver_manifest,
)

EXPECTED_STACKS = {
    "gmsh": 6,
    "octave": 7,
    "calculix": 8,
    "openfoam": 9,
    "coolprop_cantera": 10,
    "pyvista_meshio": 11,
}
INSTALLER_COMMAND_PHRASES = (
    "pip install",
    "conda install",
    "apt install",
    "apt-get install",
    "choco install",
    "winget install",
    "brew install",
    "sudo ",
    "curl ",
    "wget ",
)


def test_builtin_manifests_include_all_six_stack_ids() -> None:
    manifests = builtin_optional_solver_manifests()

    assert {manifest.stack_id for manifest in manifests} == set(EXPECTED_STACKS)


def test_builtin_manifests_map_to_issues_6_through_11() -> None:
    manifests = builtin_optional_solver_manifests()

    assert {manifest.stack_id: manifest.related_issue for manifest in manifests} == EXPECTED_STACKS


def test_get_builtin_optional_solver_manifest() -> None:
    manifest = get_builtin_optional_solver_manifest("calculix")

    assert manifest.display_name == "CalculiX ccx"
    assert manifest.related_issue == 8


def test_builtin_manifests_validate_without_errors_or_blockers() -> None:
    for manifest in builtin_optional_solver_manifests():
        report = validate_optional_solver_manifest(manifest)

        assert report.is_valid, report.to_dict()
        assert not report.has_errors
        assert not report.has_blockers


def test_builtin_manifests_include_non_bundled_disclaimer() -> None:
    for manifest in builtin_optional_solver_manifests():
        assert "not bundled" in manifest.non_bundled_disclaimer.lower()
        assert any("no bundled" in note.lower() for note in manifest.safety_notes)


def test_builtin_manifests_do_not_include_installer_commands() -> None:
    for manifest in builtin_optional_solver_manifests():
        payload = str(manifest.to_dict()).lower()
        for phrase in INSTALLER_COMMAND_PHRASES:
            assert phrase not in payload


def test_builtin_manifests_do_not_claim_tools_are_installed() -> None:
    for manifest in builtin_optional_solver_manifests():
        payload = str(manifest.to_dict()).lower()
        assert "is installed" not in payload
        assert "are installed" not in payload
        assert "bundled by opensolver workbench" in payload
