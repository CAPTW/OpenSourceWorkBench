from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _run_cli(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_cli_help_includes_feaspec_calculix_export_preview_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    assert "feaspec-calculix-export-preview" in capsys.readouterr().out


def test_preview_command_help_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["feaspec-calculix-export-preview", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out.lower()
    assert "preview" in help_text
    assert "no solver execution" in help_text


def test_preview_approved_example_reports_mesh_blocker_without_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    planned_dir = tmp_path / "planned"

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_approved.json"),
            "--planned-output-dir",
            str(planned_dir),
            "--basename",
            "cantilever_preview",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Export preview status: blocked" in out
    assert "FC_MESH_REQUIRED" in out
    assert "No solver execution was performed." in out
    assert "No files written" in out
    assert "Issue #8 live CalculiX validation remains separate." in out
    assert not planned_dir.exists()
    assert not list(tmp_path.rglob("*.inp"))
    assert not list(tmp_path.rglob("*.manifest.json"))
    assert not list(tmp_path.rglob("*.diagnostics.json"))
    assert not list(tmp_path.rglob("README_RUN_FIRST.txt"))


def test_preview_candidate_example_reports_approval_required(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_candidate.json"),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Export preview status: blocked" in out
    assert "approval" in out.casefold()
    assert "solver execution performed: false" in out.casefold()


def test_preview_invalid_example_reports_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "invalid_load_target.json"),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Export preview status: blocked" in out
    assert "FS_LOAD_INVALID_TARGET" in out or "FC_LOAD_INVALID_TARGET" in out


def test_preview_json_output_parses_and_records_no_write_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_approved.json"),
            "--format",
            "json",
            "--basename",
            "preview_case",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["version"] == "0.1.4rc1"
    assert payload["target_solver"] == "calculix"
    assert payload["export_preview_status"] == "blocked"
    assert payload["files_written"] is False
    assert payload["solver_execution_performed"] is False
    assert {item["filename"] for item in payload["planned_files"]} == {
        "README_RUN_FIRST.txt",
        "preview_case.diagnostics.json",
        "preview_case.inp",
        "preview_case.manifest.json",
    }


def test_strict_blocked_preview_returns_exit_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_approved.json"),
            "--strict",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "Export preview status: blocked" in out


def test_blocked_preview_without_strict_returns_exit_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_approved.json"),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Export preview status: blocked" in out


def test_planned_output_dir_is_not_created_for_json_preview(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    planned_dir = tmp_path / "missing" / "planned"

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-preview",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_approved.json"),
            "--format",
            "json",
            "--planned-output-dir",
            str(planned_dir),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["planned_files"]
    assert not planned_dir.exists()
    assert not list(tmp_path.rglob("*.inp"))
    assert not list(tmp_path.rglob("*.manifest.json"))
    assert not list(tmp_path.rglob("*.diagnostics.json"))
    assert not list(tmp_path.rglob("README_RUN_FIRST.txt"))
