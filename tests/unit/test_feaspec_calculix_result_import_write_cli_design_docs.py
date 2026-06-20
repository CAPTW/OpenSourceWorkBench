from __future__ import annotations

from pathlib import Path

from osw.cli.main import build_parser

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_import_write_cli_design.md"
)


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def _subcommand_names() -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            return set(choices)
    return set()


def test_cli_write_design_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_non_implementation_are_explicit() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no cli write command implementation" in text
    assert "no gui write command" in text
    assert "no solver execution" in text


def test_proposed_command_and_modes_are_defined() -> None:
    text = _normalized()

    assert "proposed command" in text
    assert "feaspec-calculix-result-import-write" in text
    assert "command modes" in text
    assert "--plan-only" in text
    assert "future `--write`" in text


def test_required_options_and_acknowledgements_are_defined() -> None:
    text = _normalized()

    assert "required input options" in text
    assert "--result-dir" in text
    assert "--output-dir" in text
    assert "safety and acknowledgement options" in text
    assert "--acknowledge-limitations" in text
    assert "--acknowledge-review-required" in text
    assert "--overwrite" in text
    assert "--create-dir" in text
    assert "--format text|json" in text


def test_default_and_future_write_behavior_are_defined() -> None:
    text = _normalized()

    assert "default behavior" in text
    assert "plan-only by default" in text
    assert "no files written unless the future `--write` mode is explicit" in text
    assert "future write behavior" in text
    assert "call the result import planner" in text
    assert "build the resultdataset draft mapping" in text
    assert "build a write plan" in text
    assert "build the schema payload" in text
    assert "call `write_calculix_result_dataset`" in text


def test_exit_codes_and_output_contracts_are_defined() -> None:
    text = _normalized()

    assert "exit codes" in text
    assert "`0`: successful plan-only review or successful future write" in text
    assert "`2`: blocked plan or write preconditions" in text
    assert "`1`: cli usage errors" in text
    assert "text output" in text
    assert "planned files" in text
    assert "json output" in text
    assert "`command`" in text
    assert "`write_status`" in text
    assert "`written_files`" in text
    assert "`solver_execution_performed`" in text


def test_path_overwrite_policy_and_safety_boundary_are_defined() -> None:
    text = _normalized()

    assert "path and overwrite policy" in text
    assert "require an explicit output directory" in text
    assert "reject path traversal" in text
    assert "do not overwrite existing standard files unless `--overwrite` is explicit" in text
    assert "safety boundary" in text
    assert "no solver execution" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess use" in text
    assert "no projectschema mutation" in text
    assert "no vlm api" in text


def test_issue_8_and_future_tests_are_defined() -> None:
    text = _normalized()

    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text
    assert "future implementation tests" in text
    assert "command help" in text
    assert "writer invocation mocked or observed" in text
    assert "no solver execution" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()

    forbidden_claims = (
        "command is implemented",
        "cli write command exists",
        "gui write command exists",
        "solver execution is allowed",
        "live validation passed",
        "issue `#8` can close",
        "external solver is bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text


def test_actual_cli_write_command_is_not_registered_yet() -> None:
    assert "feaspec-calculix-result-import-write" not in _subcommand_names()
