from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main

cli_main = importlib.import_module("osw.cli.main")
REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_human_review_cli_approval.md"
TUTORIAL_DOC = REPO_ROOT / "docs" / "tutorials" / "feaspec_human_review_cli.md"


def _doc_text(path: Path = CLI_DOC) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def _run_cli(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _validator_summary(*, blockers: bool = False, errors: bool = False) -> str:
    return json.dumps(
        {
            "has_blockers": blockers,
            "has_errors": errors,
            "diagnostics": [],
        }
    )


def _base_create_args(output: Path, action: str = "needs-changes") -> list[str]:
    return [
        "feaspec-human-review-create",
        "--output",
        str(output),
        "--source-feaspec-id",
        "cantilever-approved",
        "--reviewer",
        "reviewer@example.test",
        "--reviewed-at",
        "2026-06-18T00:00:00Z",
        "--action",
        action,
    ]


def _create_valid_review(
    output: Path,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    return _run_cli(
        [
            *_base_create_args(output, "approve-no-run-export"),
            "--validator-summary",
            _validator_summary(),
            "--validator-report-hash",
            "sha256:validator",
            "--bridge-summary",
            '{"status":"ready"}',
            "--case-plan-summary",
            '{"status":"ready"}',
            "--export-preview-summary",
            '{"status":"ready"}',
        ],
        capsys,
    )


def test_cli_help_includes_human_review_commands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "feaspec-human-review-create" in output
    assert "feaspec-human-review-validate" in output
    assert "feaspec-human-review-summary" in output


@pytest.mark.parametrize(
    "command",
    [
        "feaspec-human-review-create",
        "feaspec-human-review-validate",
        "feaspec-human-review-summary",
    ],
)
def test_human_review_command_help_exits_zero(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([command, "--help"])

    assert exc_info.value.code == 0
    assert command in capsys.readouterr().out


def test_create_needs_changes_record_writes_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _run_cli(_base_create_args(output, "needs-changes"), capsys)

    assert code == 0
    assert err == ""
    assert output.is_file()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["state"] == "needs_changes"
    assert payload["action"] == "mark_needs_changes"
    assert payload["solver_execution_performed"] is False
    assert "No solver execution was performed." in out
    assert "Run gate remains separate." in out


def test_create_rejected_record_writes_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, _out, err = _run_cli(_base_create_args(output, "reject"), capsys)

    assert code == 0
    assert err == ""
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["state"] == "rejected"
    assert payload["action"] == "reject"


def test_create_approved_no_run_export_record_writes_with_required_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _create_valid_review(output, capsys)

    assert code == 0
    assert err == ""
    assert "Status: written" in out
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["state"] == "approved_for_no_run_export"
    assert payload["validator_report_hash"] == "sha256:validator"


def test_create_approved_no_run_export_blocks_with_validator_blockers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _run_cli(
        [
            *_base_create_args(output, "approve-no-run-export"),
            "--validator-summary",
            _validator_summary(blockers=True),
            "--validator-report-hash",
            "sha256:validator",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "validation-blocked" in out
    assert "blocker" in out.casefold()
    assert not output.exists()


def test_create_installed_only_run_request_records_no_solver_execution(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _run_cli(
        [
            *_base_create_args(output, "request-installed-only-run"),
            "--validator-summary",
            _validator_summary(),
            "--validator-report-hash",
            "sha256:validator",
            "--acknowledge-limitations",
            "--acknowledge-readme",
            "--acknowledge-run-gate-separate",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Run gate remains separate." in out
    assert "Issue #8 live CalculiX validation remains separate." in out
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["state"] == "approved_for_installed_only_run_request"
    assert payload["solver_execution_authorized"] is True
    assert payload["solver_execution_performed"] is False


def test_installed_only_run_request_requires_run_gate_separate_acknowledgement(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _run_cli(
        [
            *_base_create_args(output, "request-installed-only-run"),
            "--validator-summary",
            _validator_summary(),
            "--validator-report-hash",
            "sha256:validator",
            "--acknowledge-limitations",
            "--acknowledge-readme",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "actual run gate is separate" in out
    assert not output.exists()


def test_accept_warning_without_reason_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _run_cli(
        [
            *_base_create_args(output, "needs-changes"),
            "--accept-warning",
            "FS_CONFIDENCE_LOW:",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "requires reason" in out
    assert not output.exists()


def test_accept_warning_with_reason_succeeds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, _out, err = _run_cli(
        [
            *_base_create_args(output, "needs-changes"),
            "--accept-warning",
            "FS_CONFIDENCE_LOW:reviewed manually",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["accepted_warnings"][0]["reason"] == "reviewed manually"


def test_reject_diagnostic_records_decision(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, _out, err = _run_cli(
        [
            *_base_create_args(output, "needs-changes"),
            "--reject-diagnostic",
            "FS_LOAD_INVALID_TARGET:repair target",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["diagnostic_decisions"][0]["action"] == "reject_diagnostic"


def test_create_refuses_overwrite_by_default(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"
    assert _run_cli(_base_create_args(output, "needs-changes"), capsys)[0] == 0

    code, _out, err = _run_cli(_base_create_args(output, "reject"), capsys)

    assert code == 1
    assert "already exists" in err


def test_create_overwrites_only_with_overwrite(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"
    assert _run_cli(_base_create_args(output, "needs-changes"), capsys)[0] == 0

    code, _out, err = _run_cli(
        [*_base_create_args(output, "reject"), "--overwrite"],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["state"] == "rejected"


def test_create_does_not_create_parent_dirs_implicitly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "missing" / "review.json"

    code, _out, err = _run_cli(_base_create_args(output, "needs-changes"), capsys)

    assert code == 1
    assert "Parent directory does not exist" in err
    assert not output.parent.exists()


def test_validate_valid_record_exits_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = tmp_path / "review.json"
    assert _create_valid_review(record, capsys)[0] == 0

    code, out, err = _run_cli(
        ["feaspec-human-review-validate", "--record", str(record)],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Valid: true" in out


def test_validate_invalid_record_exits_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = tmp_path / "invalid.json"
    record.write_text(json.dumps({"reviewer": ""}), encoding="utf-8")

    code, out, err = _run_cli(
        ["feaspec-human-review-validate", "--record", str(record)],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "Valid: false" in out


def test_summary_outputs_source_reviewer_state_and_action(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = tmp_path / "review.json"
    assert _create_valid_review(record, capsys)[0] == 0

    code, out, err = _run_cli(
        ["feaspec-human-review-summary", "--record", str(record)],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Source FEASpec: cantilever-approved" in out
    assert "Reviewer: reviewer@example.test" in out
    assert "State: approved_for_no_run_export" in out
    assert "Action: approve_no_run_export" in out


def test_create_json_output_parses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.json"

    code, out, err = _run_cli([*_base_create_args(output), "--format", "json"], capsys)

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["command"] == "feaspec-human-review-create"
    assert payload["valid"] is True
    assert payload["solver_execution_performed"] is False


def test_validate_json_output_parses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = tmp_path / "review.json"
    assert _create_valid_review(record, capsys)[0] == 0

    code, out, err = _run_cli(
        ["feaspec-human-review-validate", "--record", str(record), "--format", "json"],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["command"] == "feaspec-human-review-validate"
    assert payload["valid"] is True


def test_summary_json_output_parses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = tmp_path / "review.json"
    assert _create_valid_review(record, capsys)[0] == 0

    code, out, err = _run_cli(
        ["feaspec-human-review-summary", "--record", str(record), "--format", "json"],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["command"] == "feaspec-human-review-summary"
    assert payload["source_feaspec_id"] == "cantilever-approved"


def test_human_review_commands_write_no_export_bundles_or_inp(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = tmp_path / "review.json"
    assert _create_valid_review(record, capsys)[0] == 0
    assert _run_cli(["feaspec-human-review-validate", "--record", str(record)], capsys)[0] == 0
    assert _run_cli(["feaspec-human-review-summary", "--record", str(record)], capsys)[0] == 0

    assert sorted(path.name for path in tmp_path.rglob("*")) == ["review.json"]
    assert not list(tmp_path.rglob("*.inp"))
    assert not list(tmp_path.rglob("*.manifest.json"))
    assert not list(tmp_path.rglob("*.diagnostics.json"))
    assert not list(tmp_path.rglob("README_RUN_FIRST.txt"))


def test_human_review_cli_helpers_do_not_import_forbidden_execution_paths() -> None:
    source = "\n".join(
        inspect.getsource(obj)
        for obj in (
            cli_main._run_feaspec_human_review_create,
            cli_main._run_feaspec_human_review_validate,
            cli_main._run_feaspec_human_review_summary,
            cli_main._human_review_warning_from_cli,
            cli_main._human_review_rejected_diagnostic_from_cli,
        )
    )

    assert "subprocess" not in source
    assert "SolverAdapter" not in source
    assert "osw.solvers.runner" not in source
    assert "osw.runners" not in source
    assert "CalculiXRunner" not in source
    assert "find_ccx" not in source


def test_human_review_cli_docs_exist() -> None:
    assert CLI_DOC.exists()
    assert TUTORIAL_DOC.exists()


def test_human_review_cli_docs_define_commands() -> None:
    text = _doc_text()

    assert "feaspec-human-review-create" in text
    assert "feaspec-human-review-validate" in text
    assert "feaspec-human-review-summary" in text


def test_human_review_cli_docs_define_record_only_status() -> None:
    text = _doc_text()

    assert "experimental cli record workflow" in text
    assert "approval is not solver execution" in text
    assert "installed-only run request is not a run" in text


def test_human_review_cli_docs_define_create_validate_summary() -> None:
    text = _doc_text()

    assert "accepted warning syntax is `code:reason`" in text
    assert "diagnostic decision syntax is also `code:reason`" in text
    assert "refuse overwrite unless `--overwrite`" in text
    assert "do not create parent directories implicitly" in text
    assert "`0`: record is valid" in text
    assert "state, action, source feaspec id, reviewer" in text


def test_human_review_cli_docs_define_output_and_exit_codes() -> None:
    text = _doc_text()

    assert "`solver_execution_performed` remains `false`" in text
    assert "`2`: validation-blocked record, no write" in text
    assert "`2`: invalid record" in text
    assert "run gate remains separate" in text
    assert "external solvers are optional and not bundled" in text


def test_human_review_cli_docs_keep_issue_8_separate() -> None:
    text = _doc_text()

    assert "issue `#8` live calculix validation remains separate" in text
    assert "live `ccx` validation" in text


def test_human_review_cli_docs_do_not_claim_gui_or_solver_execution() -> None:
    text = _doc_text()

    assert "no gui implementation" in text
    assert "no solver execution" in text
    assert "no calculix execution" in text
    assert "no stable production claim" in text
    assert "no industrial certification" in text
    assert "no bundled external solver" in text


def test_human_review_cli_docs_do_not_claim_result_import_or_run_gate() -> None:
    text = _doc_text()

    assert "no result import implementation" in text
    assert "no installed-only run gate implementation" in text
    assert "no run gate implementation" in text


def test_human_review_cli_docs_do_not_add_vlm_or_credentials() -> None:
    text = _doc_text()

    assert "no vlm api or credentials" in text
    assert "no credentials or api keys" in text
