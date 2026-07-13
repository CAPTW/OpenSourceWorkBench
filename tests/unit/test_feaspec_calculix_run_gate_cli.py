from __future__ import annotations

import json
import os
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


def _write_bundle(root: Path) -> Path:
    root.mkdir()
    inp = root / "ready_case.inp"
    diagnostics = root / "ready_case.diagnostics.json"
    readme = root / "README_RUN_FIRST.txt"
    manifest = root / "ready_case.manifest.json"
    inp.write_text("*NODE\n1, 0., 0., 0.\n", encoding="utf-8")
    diagnostics.write_text('{"solver_execution_performed": false}\n', encoding="utf-8")
    readme.write_text("README reviewed separately. Issue #8 remains open.\n", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "target_solver": "calculix",
                "source_feaspec_id": "cli_test",
                "case_id": "ready_case",
                "solver_execution_performed": False,
                "ready_for_solver_execution": False,
                "files": [
                    {"role": "inp", "filename": inp.name},
                    {"role": "diagnostics", "filename": diagnostics.name},
                    {"role": "readme", "filename": readme.name},
                ],
                "limitations": ["No solver run was performed by this exporter."],
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_fake_ccx(tmp_path: Path) -> Path:
    if os.name == "nt":
        path = tmp_path / "fake_ccx_success.cmd"
        path.write_text(
            "@echo off\r\n"
            "echo fake cli ccx success %*\r\n"
            "echo fake cli stderr 1>&2\r\n"
            "exit /b 0\r\n",
            encoding="utf-8",
        )
        return path
    path = tmp_path / "fake_ccx_success"
    path.write_text(
        "#!/bin/sh\n"
        "echo fake cli ccx success \"$@\"\n"
        "echo fake cli stderr >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_cli_help_includes_installed_only_run_gate_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    assert "feaspec-calculix-run-installed-only" in capsys.readouterr().out


def test_cli_command_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["feaspec-calculix-run-installed-only", "--help"])

    assert exc_info.value.code == 0
    text = capsys.readouterr().out
    assert "--export-dir" in text
    assert "--execute" in text
    assert "--confirm-run" in text
    assert "--acknowledge-readme" in text


def test_cli_dry_run_exits_zero_and_writes_no_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    run_dir = tmp_path / "run"
    fake_ccx = _write_fake_ccx(tmp_path)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-run-installed-only",
            "--export-dir",
            str(export_dir),
            "--ccx",
            str(fake_ccx),
            "--run-dir",
            str(run_dir),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "installed-only" in out.lower()
    assert "Solver execution performed: false" in out
    assert (
        "GitHub state verified 2026-07-14: Issue #8 is closed after bounded WSL "
        "CalculiX evidence; this workflow does not broaden that closure."
    ) in out
    assert not run_dir.exists()


def test_cli_execute_missing_confirm_exits_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-run-installed-only",
            "--export-dir",
            str(export_dir),
            "--ccx",
            str(fake_ccx),
            "--execute",
            "--acknowledge-readme",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "FR_CONFIRMATION_REQUIRED" in out
    assert "Solver execution performed: false" in out


def test_cli_execute_with_fake_ccx_success_exits_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    run_dir = tmp_path / "run"
    fake_ccx = _write_fake_ccx(tmp_path)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-run-installed-only",
            "--export-dir",
            str(export_dir),
            "--ccx",
            str(fake_ccx),
            "--run-dir",
            str(run_dir),
            "--execute",
            "--confirm-run",
            "--acknowledge-readme",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "status: ran" in out.lower()
    assert "Solver execution performed: true" in out
    assert (run_dir / "run_metadata.json").is_file()
    assert (run_dir / "stdout.txt").is_file()
    assert (run_dir / "stderr.txt").is_file()


def test_cli_json_output_parses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_dir = _write_bundle(tmp_path / "bundle")
    fake_ccx = _write_fake_ccx(tmp_path)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-run-installed-only",
            "--export-dir",
            str(export_dir),
            "--ccx",
            str(fake_ccx),
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["status"] == "dry-run-ready"
    assert payload["ccx_discovered"] is True
    assert payload["execute_requested"] is False
    assert payload["solver_execution_performed"] is False
    assert payload["run_metadata_path"] == ""
