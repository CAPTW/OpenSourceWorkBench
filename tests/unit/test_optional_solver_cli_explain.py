from __future__ import annotations

import json

import pytest

from osw.cli.main import build_parser, main


def test_optional_solver_explain_requires_stack_id(capsys) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["optional-solver-explain"])

    assert exc_info.value.code == 2
    assert "--stack" in capsys.readouterr().err


def test_optional_solver_explain_text_includes_non_bundled_disclaimer(capsys) -> None:
    exit_code = main(["optional-solver-explain", "--stack", "calculix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CalculiX ccx" in output
    assert "not bundled" in output
    assert "No solver execution" in output


def test_optional_solver_explain_json_parses(capsys) -> None:
    exit_code = main(
        ["optional-solver-explain", "--stack", "calculix", "--format", "json"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["stack_id"] == "calculix"
    assert payload["issue_reference"] == "#8"
    assert payload["passive_only"] is True
    assert payload["no_solver_execution"] is True


def test_optional_solver_explain_unknown_stack_exits_nonzero(capsys) -> None:
    exit_code = main(["optional-solver-explain", "--stack", "does_not_exist"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "does_not_exist" in captured.err
