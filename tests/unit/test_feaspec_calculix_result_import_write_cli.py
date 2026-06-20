from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main

STANDARD_FILES = [
    "README_REVIEW_FIRST.txt",
    "diagnostics.json",
    "provenance.json",
    "result_dataset.json",
    "result_dataset_manifest.json",
]


def _run_cli(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_result_dir(root: Path) -> Path:
    root.mkdir(parents=True)
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": True,
            "exit_code": 0,
            "timed_out": False,
            "source_feaspec_id": "write_cli_feaspec",
            "case_id": "write_cli_case",
            "osw_version": "0.1.4rc1",
            "scalar_summaries": {"metadata_only": "preserved"},
        },
    )
    _write_json(
        root / "write_cli_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "write_cli_feaspec",
            "case_id": "write_cli_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "write_cli_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "write_cli_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "write_cli_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "write_cli_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "write_cli_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "write_cli_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def test_cli_help_includes_result_import_write_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    assert "feaspec-calculix-result-import-write" in capsys.readouterr().out


def test_command_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["feaspec-calculix-result-import-write", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--result-dir" in help_text
    assert "--output-dir" in help_text
    assert "--plan-only" in help_text
    assert "--write" in help_text
    assert "--acknowledge-limitations" in help_text
    assert "--acknowledge-review-required" in help_text


def test_missing_required_arguments_raise_usage_error() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as missing_both:
        parser.parse_args(["feaspec-calculix-result-import-write"])
    with pytest.raises(SystemExit) as missing_output:
        parser.parse_args(
            [
                "feaspec-calculix-result-import-write",
                "--result-dir",
                "result",
            ]
        )

    assert missing_both.value.code == 2
    assert missing_output.value.code == 2


def test_plan_only_default_writes_no_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    output_dir = tmp_path / "dataset"

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(output_dir),
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert output_dir.exists() is False
    assert "Mode: plan-only" in out
    assert "Files written: false" in out
    assert "Solver execution performed by this command: false" in out
    assert "Artifact copying performed by this command: false" in out
    assert "Issue #8 remains separate and open." in out


def test_explicit_plan_only_json_is_parseable_and_writes_no_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    output_dir = tmp_path / "dataset"

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(output_dir),
            "--plan-only",
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert output_dir.exists() is False
    payload = json.loads(out)
    assert payload["command"] == "feaspec-calculix-result-import-write"
    assert payload["mode"] == "plan-only"
    assert payload["plan_status"] in {"planned", "planned-with-warnings"}
    assert payload["schema_status"] in {"payload-ready", "payload-ready-with-warnings"}
    assert payload["write_status"] == "plan-only"
    assert payload["planned_files"]
    assert payload["written_files"] == []
    assert payload["files_written"] is False
    assert payload["solver_execution_performed"] is False
    assert payload["artifact_copy_performed"] is False
    assert payload["issue_mutation_performed"] is False
    assert payload["release_mutation_performed"] is False


def test_write_requires_both_acknowledgements(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")

    missing_both = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(tmp_path / "dataset_a"),
            "--write",
            "--format",
            "json",
        ],
        capsys,
    )
    missing_limitations = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(tmp_path / "dataset_b"),
            "--write",
            "--acknowledge-review-required",
            "--format",
            "json",
        ],
        capsys,
    )
    missing_review = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(tmp_path / "dataset_c"),
            "--write",
            "--acknowledge-limitations",
            "--format",
            "json",
        ],
        capsys,
    )

    for code, out, err in (missing_both, missing_limitations, missing_review):
        assert code == 2
        assert err == ""
        payload = json.loads(out)
        assert payload["write_status"] == "blocked"
        assert payload["files_written"] is False
    assert "FCW_LIMITATIONS_ACKNOWLEDGEMENT_REQUIRED" in missing_both[1]
    assert "FCW_REVIEW_ACKNOWLEDGEMENT_REQUIRED" in missing_both[1]
    assert "FCW_LIMITATIONS_ACKNOWLEDGEMENT_REQUIRED" in missing_limitations[1]
    assert "FCW_REVIEW_ACKNOWLEDGEMENT_REQUIRED" in missing_review[1]


def test_write_with_acknowledgements_writes_standard_files_and_hashes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    output_dir = tmp_path / "dataset"

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(output_dir),
            "--write",
            "--acknowledge-limitations",
            "--acknowledge-review-required",
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert sorted(path.name for path in output_dir.iterdir()) == STANDARD_FILES
    payload = json.loads(out)
    assert payload["mode"] == "write"
    assert payload["write_status"] in {"written", "written-with-warnings"}
    assert payload["files_written"] is True
    assert len(payload["written_files"]) == 5
    assert all(item["sha256"] for item in payload["written_files"])
    assert payload["solver_execution_performed"] is False
    assert payload["artifact_copy_performed"] is False
    assert not (output_dir / "artifacts").exists()


def test_write_refuses_existing_standard_files_without_overwrite(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    output_dir = tmp_path / "dataset"
    output_dir.mkdir()
    (output_dir / "README_REVIEW_FIRST.txt").write_text("existing\n", encoding="utf-8")

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(output_dir),
            "--write",
            "--acknowledge-limitations",
            "--acknowledge-review-required",
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    payload = json.loads(out)
    assert payload["write_status"] == "blocked"
    assert payload["files_written"] is False
    assert "FDW_OUTPUT_NOT_EMPTY" in out
    assert (output_dir / "README_REVIEW_FIRST.txt").read_text(encoding="utf-8") == "existing\n"


def test_write_allows_standard_file_overwrite_when_explicit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    output_dir = tmp_path / "dataset"
    output_dir.mkdir()
    for name in STANDARD_FILES:
        (output_dir / name).write_text("stale\n", encoding="utf-8")

    code, out, err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(output_dir),
            "--write",
            "--acknowledge-limitations",
            "--acknowledge-review-required",
            "--overwrite",
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["files_written"] is True
    assert sorted(path.name for path in output_dir.iterdir()) == STANDARD_FILES
    assert "stale" not in (output_dir / "README_REVIEW_FIRST.txt").read_text(
        encoding="utf-8"
    )


def test_create_dir_policy_follows_write_plan_and_writer(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    blocked_output = tmp_path / "missing" / "dataset"

    blocked_code, blocked_out, blocked_err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(blocked_output),
            "--write",
            "--acknowledge-limitations",
            "--acknowledge-review-required",
            "--format",
            "json",
        ],
        capsys,
    )

    assert blocked_code == 2
    assert blocked_err == ""
    assert json.loads(blocked_out)["files_written"] is False
    assert blocked_output.exists() is False

    allowed_output = tmp_path / "created" / "dataset"
    allowed_code, allowed_out, allowed_err = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(allowed_output),
            "--write",
            "--acknowledge-limitations",
            "--acknowledge-review-required",
            "--create-dir",
            "--format",
            "json",
        ],
        capsys,
    )

    assert allowed_code == 0
    assert allowed_err == ""
    assert json.loads(allowed_out)["files_written"] is True
    assert sorted(path.name for path in allowed_output.iterdir()) == STANDARD_FILES


def test_unsafe_and_traversal_output_paths_are_blocked(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result_dir = _write_result_dir(tmp_path / "result")

    unsafe = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(tmp_path / ".git" / "dataset"),
            "--plan-only",
            "--format",
            "json",
        ],
        capsys,
    )
    traversal = _run_cli(
        [
            "feaspec-calculix-result-import-write",
            "--result-dir",
            str(result_dir),
            "--output-dir",
            str(tmp_path / "safe" / ".." / "dataset"),
            "--plan-only",
            "--format",
            "json",
        ],
        capsys,
    )

    assert unsafe[0] == 2
    assert traversal[0] == 2
    assert "FDW_UNSAFE_PATH" in unsafe[1]
    assert "FDW_PATH_TRAVERSAL_REJECTED" in traversal[1]


def test_write_cli_uses_tmp_path_not_tracked_result_fixtures() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "tmp_path" in source
    assert "tests/" + "fixtures" not in source
    assert "fixtures/" + "calculix" not in source
