from __future__ import annotations

import hashlib
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


def _ready_case_plan_dict() -> dict[str, object]:
    nodes = [
        {"node_id": "1", "coordinates": [0.0, 0.0, 0.0], "source_ref": "node_1"},
        {"node_id": "2", "coordinates": [1.0, 0.0, 0.0], "source_ref": "node_2"},
        {"node_id": "3", "coordinates": [1.0, 1.0, 0.0], "source_ref": "node_3"},
        {"node_id": "4", "coordinates": [0.0, 1.0, 0.0], "source_ref": "node_4"},
        {"node_id": "5", "coordinates": [0.0, 0.0, 1.0], "source_ref": "node_5"},
        {"node_id": "6", "coordinates": [1.0, 0.0, 1.0], "source_ref": "node_6"},
        {"node_id": "7", "coordinates": [1.0, 1.0, 1.0], "source_ref": "node_7"},
        {"node_id": "8", "coordinates": [0.0, 1.0, 1.0], "source_ref": "node_8"},
    ]
    return {
        "status": "plan-ready",
        "case_id": "synthetic-ready-calculix-case-plan",
        "source_feaspec_id": "synthetic_ready_cli",
        "target_solver": "calculix",
        "unit_context": {"force": "N", "length": "m", "name": "SI", "stress": "Pa"},
        "nodes": nodes,
        "elements": [
            {
                "element_id": "1",
                "element_type": "C3D8",
                "node_refs": [node["node_id"] for node in nodes],
                "source_ref": "element_solid_1",
                "metadata": {"element_set": "EALL"},
            }
        ],
        "materials": [
            {
                "material_id": "mat_steel",
                "name": "Steel",
                "model": "isotropic_linear_elastic",
                "properties": {
                    "young_modulus": {"value": 210_000_000_000.0, "units": "Pa"},
                    "poisson_ratio": 0.3,
                    "density": {"value": 7850.0, "units": "kg/m^3"},
                },
                "units": {"stress": "Pa"},
                "source_ref": "material_steel",
            }
        ],
        "sections": [
            {
                "section_id": "sec_solid",
                "material_ref": "mat_steel",
                "target_refs": ["EALL"],
                "section_type": "solid",
                "source_ref": "section_solid",
            }
        ],
        "boundary_conditions": [
            {
                "bc_id": "bc_fixed_left",
                "kind": "fixed",
                "target_refs": ["1"],
                "degrees_of_freedom": ["ux", "uy", "uz"],
                "values": [0.0, 0.0, 0.0],
                "source_ref": "bc_fixed_left",
            }
        ],
        "loads": [
            {
                "load_id": "load_tip",
                "kind": "point_force",
                "target_refs": ["2"],
                "vector": [0.0, -100.0, 0.0],
                "units": {"magnitude": "N"},
                "source_ref": "load_tip",
            }
        ],
        "steps": [{"step_id": "linear_static", "analysis_type": "static"}],
        "output_requests": [
            {
                "request_id": "default_displacement_stress",
                "kind": "field",
                "target": "all",
                "variables": ["U", "S"],
            }
        ],
        "provenance_comments": [
            "Human review: synthetic ready case approved for CLI write unit tests.",
            "Source FEASpec: synthetic_ready_cli.",
        ],
        "diagnostics": [],
        "unmapped_fields": [],
        "extension_needs": [],
        "bridge_status": "",
        "validator_report": {},
        "ready_for_inp_writer": True,
        "ready_for_solver_execution": False,
        "inp_writer_performed": False,
        "solver_execution_performed": False,
    }


def _write_ready_case_plan(path: Path) -> None:
    path.write_text(json.dumps(_ready_case_plan_dict(), indent=2), encoding="utf-8")


def test_cli_help_includes_feaspec_calculix_export_write_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    assert "feaspec-calculix-export-write" in capsys.readouterr().out


def test_write_command_help_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["feaspec-calculix-export-write", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out.lower()
    assert "no-run export bundle" in help_text
    assert "no solver execution" in help_text


def test_write_command_requires_input_and_output_dir() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["feaspec-calculix-export-write", "--output-dir", "out"])
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "feaspec-calculix-export-write",
                "--feaspec",
                "case.json",
            ]
        )


@pytest.mark.parametrize(
    ("filename", "expected_text"),
    [
        ("cantilever_beam_approved.json", "MESH_REQUIRED"),
        ("cantilever_beam_candidate.json", "approval"),
        ("invalid_load_target.json", "LOAD_INVALID_TARGET"),
    ],
)
def test_write_examples_block_and_write_no_files(
    filename: str,
    expected_text: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "bundle"
    out_dir.mkdir()

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--feaspec",
            str(EXAMPLES / filename),
            "--output-dir",
            str(out_dir),
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "Export status: blocked" in out
    assert "Files written: false" in out
    assert "Solver execution performed: false" in out
    assert "Issue #8 live CalculiX validation remains separate." in out
    assert expected_text.casefold() in out.casefold()
    assert list(out_dir.iterdir()) == []
    assert not list(tmp_path.rglob("*.inp"))
    assert not list(tmp_path.rglob("*.manifest.json"))
    assert not list(tmp_path.rglob("*.diagnostics.json"))
    assert not list(tmp_path.rglob("README_RUN_FIRST.txt"))


def test_write_json_blocked_output_parses_and_records_no_write_flags(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "bundle"
    out_dir.mkdir()

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--feaspec",
            str(EXAMPLES / "cantilever_beam_approved.json"),
            "--output-dir",
            str(out_dir),
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    payload = json.loads(out)
    assert payload["version"] == "0.1.5rc2"
    assert payload["target_solver"] == "calculix"
    assert payload["export_status"] == "blocked"
    assert payload["files_written"] is False
    assert payload["solver_execution_performed"] is False
    assert payload["written_files"] == []
    assert list(out_dir.iterdir()) == []


def test_write_strict_and_non_strict_blocked_exports_return_exit_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for args in ([], ["--strict"]):
        out_dir = tmp_path / f"bundle_{len(args)}"
        out_dir.mkdir()
        code, out, err = _run_cli(
            [
                "feaspec-calculix-export-write",
                "--feaspec",
                str(EXAMPLES / "cantilever_beam_approved.json"),
                "--output-dir",
                str(out_dir),
                *args,
            ],
            capsys,
        )

        assert code == 2
        assert err == ""
        assert "Export status: blocked" in out
        assert list(out_dir.iterdir()) == []


def test_successful_case_plan_write_exports_exact_no_run_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_plan = tmp_path / "ready_case_plan.json"
    out_dir = tmp_path / "bundle"
    out_dir.mkdir()
    _write_ready_case_plan(case_plan)
    before_hash = hashlib.sha256(case_plan.read_bytes()).hexdigest()

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(out_dir),
            "--basename",
            "ready_case",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    assert "Export status: exported" in out
    assert "Files written: true" in out
    assert "Solver execution performed: false" in out
    assert sorted(path.name for path in out_dir.iterdir()) == [
        "README_RUN_FIRST.txt",
        "ready_case.diagnostics.json",
        "ready_case.inp",
        "ready_case.manifest.json",
    ]
    readme = (out_dir / "README_RUN_FIRST.txt").read_text(encoding="utf-8").lower()
    manifest = json.loads((out_dir / "ready_case.manifest.json").read_text())
    assert "no solver execution was performed" in readme
    assert "issue #8" in readme
    assert manifest["solver_execution_performed"] is False
    assert hashlib.sha256(case_plan.read_bytes()).hexdigest() == before_hash


def test_successful_case_plan_write_json_output_parses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_plan = tmp_path / "ready_case_plan.json"
    out_dir = tmp_path / "bundle"
    out_dir.mkdir()
    _write_ready_case_plan(case_plan)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(out_dir),
            "--basename",
            "ready_case",
            "--format",
            "json",
        ],
        capsys,
    )

    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["input_kind"] == "case_plan"
    assert payload["export_status"] == "exported"
    assert payload["files_written"] is True
    assert payload["solver_execution_performed"] is False
    assert {Path(item["path"]).name for item in payload["written_files"]} == {
        "README_RUN_FIRST.txt",
        "ready_case.diagnostics.json",
        "ready_case.inp",
        "ready_case.manifest.json",
    }


def test_missing_output_dir_blocks_unless_create_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_plan = tmp_path / "ready_case_plan.json"
    _write_ready_case_plan(case_plan)
    missing = tmp_path / "bundle"

    blocked, _, _ = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(missing),
        ],
        capsys,
    )
    created, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(missing),
            "--create-dir",
        ],
        capsys,
    )

    assert blocked == 2
    assert created == 0
    assert err == ""
    assert "Export status: exported" in out
    assert missing.is_dir()
    assert (missing / "feaspec_calculix_case.inp").is_file()


def test_existing_files_block_unless_overwrite_and_preserve_unrelated_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_plan = tmp_path / "ready_case_plan.json"
    out_dir = tmp_path / "bundle"
    out_dir.mkdir()
    _write_ready_case_plan(case_plan)
    unrelated = out_dir / "unrelated.txt"
    stale = out_dir / "ready_case.inp"
    unrelated.write_text("keep me", encoding="utf-8")
    stale.write_text("stale", encoding="utf-8")

    blocked, _, _ = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(out_dir),
            "--basename",
            "ready_case",
        ],
        capsys,
    )
    exported, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(out_dir),
            "--basename",
            "ready_case",
            "--overwrite",
        ],
        capsys,
    )

    assert blocked == 2
    assert exported == 0
    assert err == ""
    assert "Export status: exported" in out
    assert unrelated.read_text(encoding="utf-8") == "keep me"
    assert stale.read_text(encoding="utf-8") != "stale"


@pytest.mark.parametrize("basename", ["nested/case", "../case", r"..\case", "bad*case"])
def test_unsafe_basename_is_rejected(
    basename: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_plan = tmp_path / "ready_case_plan.json"
    out_dir = tmp_path / "bundle"
    out_dir.mkdir()
    _write_ready_case_plan(case_plan)

    code, out, err = _run_cli(
        [
            "feaspec-calculix-export-write",
            "--case-plan",
            str(case_plan),
            "--output-dir",
            str(out_dir),
            "--basename",
            basename,
        ],
        capsys,
    )

    assert code == 2
    assert err == ""
    assert "FX_UNSAFE_BASENAME" in out
    assert list(out_dir.iterdir()) == []
