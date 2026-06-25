from __future__ import annotations

import json
from pathlib import Path

from osw.cli.main import main

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
VALID_PROJECT = FIXTURES / "valid_project_local_manifest.json"
INVALID_BUNDLED = FIXTURES / "invalid_bundled_solver_claim.json"
DUPLICATE_BUILTIN = FIXTURES / "duplicate_stack_plugin_manifest.json"


def test_json_output_parses_and_includes_report_sections(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(VALID_PROJECT),
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "optional-solver-plugin-manifest-preview"
    assert payload["accepted_count"] == 1
    assert payload["rejected_count"] == 0
    assert payload["conflict_count"] == 0
    assert payload["accepted"]
    assert payload["rejected"] == []
    assert "conflicts" in payload
    assert "diagnostics" in payload
    assert payload["plugin_manifest_presence_is_validation_evidence"] is False
    assert payload["policy"]["third_party_plugin_manifests_trusted_by_default"] is False


def test_json_output_reports_rejected_manifest_with_default_success_exit(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(INVALID_BUNDLED),
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["accepted_count"] == 0
    assert payload["rejected_count"] == 1
    assert any(item["code"] == "OSPL_BUNDLED_SOLVER_CLAIM" for item in payload["diagnostics"])


def test_include_builtins_detects_duplicate_builtin_conflict(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(DUPLICATE_BUILTIN),
            "--include-builtins",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["conflict_count"] == 1
    assert payload["conflicts"][0]["stack_id"] == "gmsh"
    assert payload["policy"]["include_builtins"] is True


def test_repeated_manifest_paths_detect_duplicate_stack_conflict(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(VALID_PROJECT),
            "--manifest",
            str(VALID_PROJECT),
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["accepted_count"] == 1
    assert payload["rejected_count"] == 1
    assert payload["conflict_count"] == 1
    assert payload["conflicts"][0]["stack_id"] == "project_local_stack"
