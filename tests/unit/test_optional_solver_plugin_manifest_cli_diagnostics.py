from __future__ import annotations

import json
from pathlib import Path

from osw.cli.main import main

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
INVALID_SOURCE = FIXTURES / "invalid_missing_source_metadata.json"
DUPLICATE_BUILTIN = FIXTURES / "duplicate_stack_plugin_manifest.json"


def test_text_output_surfaces_source_metadata_diagnostics(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(INVALID_SOURCE),
            "--include-diagnostics",
            "--show-policy",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OSPL_SOURCE_METADATA_INCOMPLETE" in output
    assert "policy: explicit JSON files only" in output
    assert "no plugin package loading" in output
    assert "no solver execution" in output


def test_json_output_surfaces_conflict_diagnostics(capsys) -> None:
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
    assert any(
        diagnostic["code"] == "OSPL_BUILTIN_OVERRIDE_FORBIDDEN"
        for diagnostic in payload["diagnostics"]
    )
    assert payload["policy"]["plugin_manifest_presence_is_validation_evidence"] is False


def test_strict_mode_exits_two_for_conflict(capsys) -> None:
    exit_code = main(
        [
            "optional-solver-plugin-manifest-preview",
            "--manifest",
            str(DUPLICATE_BUILTIN),
            "--include-builtins",
            "--strict",
        ]
    )

    capsys.readouterr()
    assert exit_code == 2
