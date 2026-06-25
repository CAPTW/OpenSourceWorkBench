from __future__ import annotations

from pathlib import Path

from osw.cli.main import main

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
VALID_PROJECT = FIXTURES / "valid_project_local_manifest.json"
INVALID_BUNDLED = FIXTURES / "invalid_bundled_solver_claim.json"
MISSING = FIXTURES / "missing_manifest.json"


def test_command_without_manifest_exits_nonzero(capsys) -> None:
    exit_code = main(["optional-solver-plugin-manifest-preview"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "At least one --manifest" in captured.err


def test_command_loads_valid_fixture_manifest_in_text(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(VALID_PROJECT),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "accepted count: 1" in output
    assert "rejected count: 0" in output
    assert "conflict count: 0" in output
    assert "project_local_stack" in output
    assert "source project_local" in output
    assert "trust reviewed_project" in output
    assert "Plugin manifest presence is not validation evidence." in output
    assert "Third-party/plugin manifests are not trusted by default." in output


def test_command_with_missing_file_exits_nonzero(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(MISSING),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "OSPL_JSON_READ_FAILED" in output


def test_default_mode_exits_zero_for_policy_rejected_manifest(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(INVALID_BUNDLED),
            "--include-diagnostics",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "rejected count: 1" in output
    assert "OSPL_BUNDLED_SOLVER_CLAIM" in output


def test_strict_mode_exits_nonzero_for_rejected_manifest(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(INVALID_BUNDLED),
            "--strict",
        ]
    )

    capsys.readouterr()
    assert exit_code == 2
