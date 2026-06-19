from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main


def _run_cli(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_result_dir(
    root: Path,
    *,
    include_primary: bool = True,
    include_status: bool = False,
    dat_text: str = "not parsed\n",
    solver_execution_performed: bool = True,
) -> Path:
    root.mkdir()
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": solver_execution_performed,
            "exit_code": 0,
            "timed_out": False,
            "source_feaspec_id": "cli_preview_feaspec",
            "case_id": "cli_preview_case",
            "osw_version": "0.1.4rc1",
            "scalar_summaries": {"source": "metadata-only"},
        },
    )
    _write_json(
        root / "cli_preview_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "cli_preview_feaspec",
            "case_id": "cli_preview_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "cli_preview_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "cli_preview_case.inp").write_text("*NODE\n", encoding="utf-8")
    if include_primary:
        (root / "cli_preview_case.dat").write_text(dat_text, encoding="utf-8")
        (root / "cli_preview_case.frd").write_text("not parsed\n", encoding="utf-8")
    if include_status:
        (root / "cli_preview_case.sta").write_text(
            "step 1 increment 2\nanalysis completed\n",
            encoding="utf-8",
        )
        (root / "cli_preview_case.cvg").write_text(
            "convergence residual 1.0E-03\n",
            encoding="utf-8",
        )
    return root


def test_cli_help_includes_result_import_preview_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    assert "feaspec-calculix-result-import-preview" in capsys.readouterr().out


def test_cli_command_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["feaspec-calculix-result-import-preview", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--result-dir" in help_text
    assert "--format" in help_text
    assert "--strict" in help_text
    assert "--include-artifacts" in help_text
    assert "--include-diagnostics" in help_text


def test_text_preview_exits_zero_and_writes_no_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    before = sorted(path.name for path in result_dir.iterdir())

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
        ],
        capsys,
    )
    after = sorted(path.name for path in result_dir.iterdir())

    assert code == 0
    assert err == ""
    assert before == after
    assert "FEASpec CalculiX result import preview" in out
    assert "Preview only: true" in out
    assert "Files written: false" in out
    assert "Solver execution performed by this command: false" in out
    assert "Broad numerical parser implemented: false" in out
    assert "ResultDataset persistence: false" in out
    assert "Issue #8 remains separate." in out
    assert "External solvers are optional and not bundled." in out


def test_json_preview_has_required_fields_and_no_write_flags(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["command"] == "feaspec-calculix-result-import-preview"
    assert payload["status"] == "import-ready-with-warnings"
    assert payload["artifact_count"] >= 1
    assert payload["artifacts"]
    assert payload["diagnostics"]
    assert payload["provenance"]["case_id"] == "cli_preview_case"
    assert payload["dataset_draft"]["writes_files"] is False
    assert payload["dataset_draft"]["artifacts"]
    assert payload["dat_minimal_parse_summary"]["available"] is True
    assert payload["parse_not_implemented"] is True
    assert payload["solver_execution_performed"] is False
    assert payload["source_run_solver_execution_performed"] is True
    assert payload["files_written"] is False
    assert any("No free-form .dat parser" in item for item in payload["limitations"])


def test_json_preview_includes_text_only_status_summary_when_status_files_exist(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result", include_status=True)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    status_summary = payload["status_summary"]
    assert status_summary["available"] is True
    assert status_summary["file_count"] == 2
    assert status_summary["numerical_values_parsed"] is False
    assert status_summary["writes_files"] is False
    assert status_summary["category_counts"]["progress"] == 1
    assert status_summary["category_counts"]["convergence"] == 1
    assert status_summary["completion_indicated"] is True
    assert status_summary["numeric_tokens_not_parsed"] is True


def test_json_preview_includes_dat_section_summary_when_dat_file_is_present(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(
        tmp_path / "result",
        dat_text="CalculiX result file\nTOTAL ENERGY SUMMARY\nenergy text 1.0\n",
    )

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    dat_summary = payload["dat_section_summary"]
    assert dat_summary["available"] is True
    assert dat_summary["file_count"] == 1
    assert dat_summary["section_count"] == 2
    assert dat_summary["numerical_values_parsed"] is False
    assert dat_summary["numeric_values_extracted"] is False
    assert dat_summary["tables_extracted"] is False
    assert dat_summary["units_inferred"] is False
    assert dat_summary["writes_files"] is False
    assert dat_summary["kind_counts"]["header"] == 1
    assert dat_summary["kind_counts"]["scalar_candidate"] == 1
    assert dat_summary["numeric_tokens_not_parsed"] is True


def test_json_preview_includes_dat_minimal_parse_summary_when_dat_file_is_present(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(
        tmp_path / "result",
        dat_text=(
            "TOTAL ENERGY SUMMARY\nmax displacement = 2.5 mm\n"
            "DISPLACEMENTS\nnode | ux\nunits | - | mm\n1 | 0.1\n"
        ),
    )

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    dat_parse_summary = payload["dat_minimal_parse_summary"]
    assert dat_parse_summary["available"] is True
    assert dat_parse_summary["file_count"] == 1
    assert dat_parse_summary["scalar_candidate_count"] == 1
    assert dat_parse_summary["table_candidate_count"] == 1
    assert dat_parse_summary["parsed_numeric_value_count"] == 2
    assert dat_parse_summary["minimal_parser"] is True
    assert dat_parse_summary["freeform_parser"] is False
    assert dat_parse_summary["frd_parser"] is False
    assert dat_parse_summary["units_inferred"] is False
    assert dat_parse_summary["writes_files"] is False
    assert payload["dataset_draft"]["scalar_summaries"]["dat_minimal_candidates"]
    assert payload["dataset_draft"]["tables"]


def test_text_preview_prints_status_summary_when_status_files_exist(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result", include_status=True)
    before = sorted(path.name for path in result_dir.iterdir())

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
        ],
        capsys,
    )
    after = sorted(path.name for path in result_dir.iterdir())

    assert code == 0
    assert err == ""
    assert before == after
    assert "Status summary: available" in out
    assert "Status numeric values parsed: false" in out
    assert "Status category counts:" in out


def test_text_preview_prints_dat_section_summary_when_dat_file_is_present(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(
        tmp_path / "result",
        dat_text="CalculiX result file\nTOTAL ENERGY SUMMARY\nenergy text 1.0\n",
    )
    before = sorted(path.name for path in result_dir.iterdir())

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
        ],
        capsys,
    )
    after = sorted(path.name for path in result_dir.iterdir())

    assert code == 0
    assert err == ""
    assert before == after
    assert "DAT section summary: available" in out
    assert "DAT numeric values parsed: false" in out
    assert "DAT tables extracted: false" in out
    assert "DAT section kind counts:" in out


def test_text_preview_prints_dat_minimal_parse_summary_when_dat_file_is_present(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(
        tmp_path / "result",
        dat_text="TOTAL ENERGY SUMMARY\nmax displacement = 2.5 mm\n",
    )
    before = sorted(path.name for path in result_dir.iterdir())

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
        ],
        capsys,
    )
    after = sorted(path.name for path in result_dir.iterdir())

    assert code == 0
    assert err == ""
    assert before == after
    assert "DAT minimal parse summary: available" in out
    assert "DAT scalar candidates: 1" in out
    assert "DAT free-form parser: false" in out
    assert "DAT units inferred: false" in out


def test_json_preview_can_hide_top_level_artifacts_and_diagnostics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--format",
            "json",
            "--no-include-artifacts",
            "--no-include-diagnostics",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["artifacts"] == []
    assert payload["diagnostics"] == []
    assert payload["artifact_count"] > 0
    assert payload["diagnostic_count"] > 0
    assert payload["dataset_draft"]["artifacts"]


def test_missing_result_dir_exits_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(tmp_path / "missing"),
        ],
        capsys,
    )

    assert code == 1
    assert err == ""
    assert "FI_RESULT_DIR_MISSING" in out


def test_empty_result_dir_preview_is_non_strict_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = tmp_path / "empty"
    result_dir.mkdir()

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Status: unsupported" in out
    assert "FI_NO_PRIMARY_RESULT" in out


def test_strict_empty_result_dir_exits_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = tmp_path / "empty"
    result_dir.mkdir()

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--strict",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "Status: unsupported" in out


def test_strict_parse_not_implemented_exits_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-preview",
            "--result-dir",
            str(result_dir),
            "--strict",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "FI_PARSE_NOT_IMPLEMENTED" in out


def test_preview_uses_tmp_path_not_tracked_result_fixtures() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "tmp_path" in source
    assert "tests/" + "fixtures" not in source
    assert "fixtures/" + "calculix" not in source
