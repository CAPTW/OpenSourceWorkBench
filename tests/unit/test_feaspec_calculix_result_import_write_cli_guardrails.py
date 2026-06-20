from __future__ import annotations

import inspect
from pathlib import Path

from osw.cli.main import (
    _build_feaspec_calculix_result_import_write,
    _feaspec_calculix_result_import_write_exit_code,
    _print_feaspec_calculix_result_import_write,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_SOURCE = REPO_ROOT / "src" / "osw" / "cli" / "main.py"
PROJECT_SCHEMA_SOURCE = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_import_write_cli.md"
)


def _helper_source() -> str:
    return "\n".join(
        inspect.getsource(item)
        for item in (
            _build_feaspec_calculix_result_import_write,
            _print_feaspec_calculix_result_import_write,
            _feaspec_calculix_result_import_write_exit_code,
        )
    )


def test_write_cli_helper_has_no_solver_runner_or_subprocess_path() -> None:
    source = _helper_source()
    forbidden_tokens = (
        "CalculiXRunner",
        "SolverAdapter",
        "ExternalCommandRunner",
        "run_input_deck",
        "Popen",
        "ccx.exe",
        "sub" + "process",
    )

    for token in forbidden_tokens:
        assert token not in source


def test_write_cli_helper_uses_existing_writer_and_does_not_copy_artifacts() -> None:
    source = _helper_source()

    assert "write_calculix_result_dataset" in source
    assert "copy_artifacts=False" in source
    assert "copy_artifacts=True" not in source
    assert "artifact_copy_performed" in source
    assert "artifact_copy_performed\": False" in source


def test_write_cli_helper_does_not_add_gui_release_issue_or_tag_mutation() -> None:
    source = _helper_source()
    forbidden_tokens = (
        "osw.gui",
        "gh release",
        "gh issue",
        "git tag",
        "git push",
        "release edit",
        "asset upload",
    )

    for token in forbidden_tokens:
        assert token not in source.lower()
    assert "gui_write_command_added" in source
    assert "issue_mutation_performed" in source
    assert "release_mutation_performed" in source
    assert "tag_mutation_performed" in source


def test_write_cli_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA_SOURCE.read_text(encoding="utf-8")

    assert "feaspec-calculix-result-import-write" not in text
    assert "FEASpecCalculiXResultDatasetWritePlan" not in text
    assert "write_calculix_result_dataset" not in text


def test_write_cli_docs_preserve_required_safety_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "experimental cli write command implemented" in text
    assert "write requires acknowledgements" in text
    assert "--acknowledge-limitations" in text
    assert "--acknowledge-review-required" in text
    assert "no gui write command" in text
    assert "no solver execution" in text
    assert "no artifact copying" in text
    assert "issue `#8` remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text


def test_write_cli_docs_do_not_claim_forbidden_capabilities() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    forbidden_claims = (
        "gui write command exists",
        "solver execution is allowed",
        "live ccx validation passed",
        "issue `#8` can close",
        "external solvers are bundled",
        "industrial certification is provided",
        "stable production",
    )

    for claim in forbidden_claims:
        assert claim not in text


def test_write_cli_source_contains_no_provider_credentials() -> None:
    text = CLI_SOURCE.read_text(encoding="utf-8").lower()
    forbidden_tokens = (
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "api_key",
        "credentials",
        "vlmprovider",
    )

    for token in forbidden_tokens:
        assert token not in text
