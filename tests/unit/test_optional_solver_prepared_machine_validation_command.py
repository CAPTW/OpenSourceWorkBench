from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main
from osw.cli.optional_solver_prepared_machine_validation import (
    OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND,
    PreparedMachineValidationStatus,
    build_prerequisite_catalog,
)

COMMAND = OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND
MODULE_NAME = "osw.cli.optional_solver_prepared_machine_validation"


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main([COMMAND, *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _module() -> object:
    return importlib.import_module(MODULE_NAME)


def _module_source() -> str:
    module = _module()
    return Path(module.__file__).read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_module_source())


def _imported_modules() -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _called_names() -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return {call.lower() for call in calls}


def _all_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    monkeypatch.setattr(module.importlib.util, "find_spec", lambda name: None)


def _all_present(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    monkeypatch.setattr(module.shutil, "which", lambda name: f"C:/tools/{name}.exe")
    monkeypatch.setattr(module.importlib.util, "find_spec", lambda name: object())


def test_module_imports_and_catalog_is_stable() -> None:
    module = _module()
    assert hasattr(module, "main")
    assert hasattr(module, "evaluate_prerequisites")
    assert PreparedMachineValidationStatus.PARKED.value == "parked"
    assert [row.identifier for row in build_prerequisite_catalog()] == [
        "gmsh_executable",
        "python_gmsh",
        "octave_executable",
        "ccx_executable",
        "openfoam_commands",
        "python_meshio",
        "python_pyvista",
        "python_vtk",
        "python_coolprop",
        "python_cantera",
    ]


def test_cli_dispatcher_exposes_prepared_machine_validation_command() -> None:
    parser = build_parser()
    parsed = parser.parse_args([COMMAND, "explain"])
    assert parsed.command == COMMAND
    assert parsed.validation_command == "explain"


def test_explain_returns_zero_and_states_no_certification(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["explain"], capsys)
    assert code == 0
    assert err == ""
    assert "optional-solver-prepared-machine-validation" in out
    assert "does not claim certification" in out.lower()
    assert "no solver execution" in out.lower()


def test_safety_returns_zero_and_lists_non_actions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["safety"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "no dependency installation",
        "no solver installation",
        "no solver execution",
        "no projectschema mutation",
        "no issue, release, tag, or asset mutation",
        "no certification",
    ):
        assert phrase in out.lower()


def test_prerequisites_lists_required_optional_solver_prerequisites(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["prerequisites"], capsys)
    assert code == 0
    assert err == ""
    text = out.lower()
    for phrase in (
        "gmsh executable",
        "python gmsh",
        "octave executable",
        "ccx executable",
        "openfoam commands",
        "python meshio",
        "python pyvista",
        "python vtk",
        "python coolprop",
        "python cantera",
    ):
        assert phrase in text


def test_preflight_with_missing_prerequisites_returns_parked_two(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_missing(monkeypatch)
    code, out, err = _run(["preflight"], capsys)
    assert code == 2
    assert out == ""
    assert "status: parked" in err.lower()
    assert "skipped-missing" in err.lower()
    assert "gmsh_executable" in err


def test_preflight_json_is_deterministic_and_includes_missing_prerequisites(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_missing(monkeypatch)
    code, out, err = _run(["preflight", "--json"], capsys)
    assert code == 2
    assert out == ""
    first = json.loads(err)
    code, out, err = _run(["preflight", "--json"], capsys)
    assert code == 2
    assert out == ""
    second = json.loads(err)
    assert first == second
    assert first["status"] == "parked"
    assert "gmsh_executable" in first["missing_prerequisites"]
    assert "python_cantera" in first["skipped_missing"]


def test_plan_returns_zero_and_writes_no_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["plan", "--evidence-dir", str(tmp_path)], capsys)
    assert code == 0
    assert err == ""
    assert "Plan:" in out
    assert list(tmp_path.iterdir()) == []


def test_run_requires_prepared_machine_acknowledgement_and_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cases = (
        [
            "run",
            "--acknowledge-optional-solver-validation",
            "--confirm-local-only",
            "--write-evidence",
            "--evidence-dir",
            str(tmp_path),
        ],
        [
            "run",
            "--prepared-machine",
            "--confirm-local-only",
            "--write-evidence",
            "--evidence-dir",
            str(tmp_path),
        ],
        [
            "run",
            "--prepared-machine",
            "--acknowledge-optional-solver-validation",
            "--write-evidence",
            "--evidence-dir",
            str(tmp_path),
        ],
    )
    for args in cases:
        code, out, err = _run(args, capsys)
        assert code == 2
        assert out == ""
        assert "missing required" in err.lower()
        assert list(tmp_path.iterdir()) == []


def test_run_with_missing_prerequisites_returns_parked_two(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_missing(monkeypatch)
    code, out, err = _run(
        [
            "run",
            "--prepared-machine",
            "--acknowledge-optional-solver-validation",
            "--confirm-local-only",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "status: parked" in err.lower()
    assert "validation is parked" in err.lower()
    assert "validation success" in err.lower()
    assert "not certification" in err.lower()


def test_run_with_fake_all_prerequisites_present_completes_without_certification(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_present(monkeypatch)
    code, out, err = _run(
        [
            "run",
            "--prepared-machine",
            "--acknowledge-optional-solver-validation",
            "--confirm-local-only",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert "status: complete" in out.lower()
    assert "no solver execution occurred" in out.lower()
    assert "not certification" in out.lower()
    assert "certification claim" not in out.lower().replace("no certification claim", "")


def test_run_writes_evidence_only_with_explicit_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_present(monkeypatch)
    code, out, err = _run(
        [
            "run",
            "--prepared-machine",
            "--acknowledge-optional-solver-validation",
            "--confirm-local-only",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert "Evidence paths:\n- none" in out
    assert list(tmp_path.iterdir()) == []

    code, out, err = _run(
        [
            "run",
            "--prepared-machine",
            "--acknowledge-optional-solver-validation",
            "--confirm-local-only",
            "--write-evidence",
            "--evidence-dir",
            str(tmp_path),
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    evidence_files = sorted(path.name for path in tmp_path.iterdir())
    assert evidence_files == [
        "optional_solver_prepared_machine_validation_evidence.json",
        "optional_solver_prepared_machine_validation_evidence.md",
    ]


def test_evidence_is_local_deterministic_and_not_a_release_asset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_present(monkeypatch)
    args = [
        "run",
        "--prepared-machine",
        "--acknowledge-optional-solver-validation",
        "--confirm-local-only",
        "--write-evidence",
        "--evidence-dir",
        str(tmp_path),
        "--json",
    ]
    code, out, err = _run(args, capsys)
    assert code == 0
    assert err == ""
    first = json.loads(
        (tmp_path / "optional_solver_prepared_machine_validation_evidence.json").read_text(
            encoding="utf-8"
        )
    )
    code, out, err = _run(args, capsys)
    assert code == 0
    assert err == ""
    second = json.loads(
        (tmp_path / "optional_solver_prepared_machine_validation_evidence.json").read_text(
            encoding="utf-8"
        )
    )
    assert first == second
    assert first["evidence"]["written"] is True
    assert first["release_asset"] is False
    evidence_paths = [
        path for path in first["evidence"].values() if isinstance(path, str) and path
    ]
    assert all("release" not in path.lower() for path in evidence_paths)


def test_missing_prerequisites_are_not_validation_success_and_skipped_missing_is_separate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_missing(monkeypatch)
    code, out, err = _run(["preflight", "--json"], capsys)
    assert code == 2
    assert out == ""
    payload = json.loads(err)
    assert payload["status"] == "parked"
    assert payload["exit_semantics"]["validation_success_claim"] is False
    assert payload["exit_semantics"]["validation_failure_claim"] is False
    assert payload["missing_prerequisites"]
    assert payload["skipped_missing"]
    assert payload["missing_prerequisites"] == payload["skipped_missing"]


def test_json_output_includes_required_sections_and_no_raw_secret_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _all_present(monkeypatch)
    evidence_dir = tmp_path / "secret-token-dir"
    evidence_dir.mkdir()
    code, out, err = _run(
        [
            "run",
            "--prepared-machine",
            "--acknowledge-optional-solver-validation",
            "--confirm-local-only",
            "--write-evidence",
            "--evidence-dir",
            str(evidence_dir),
            "--git-sha",
            "token-secret-sha",
            "--json",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert "secret-token-dir" not in out
    assert "token-secret-sha" not in out
    payload = json.loads(out)
    for key in (
        "status",
        "prerequisites",
        "diagnostics",
        "non_actions",
        "limitations",
        "safety_guidance",
        "exit_semantics",
    ):
        assert key in payload
    assert payload["git_sha"] == "<redacted-secret-like-value>"


def test_source_guardrails_block_installs_subprocess_projectschema_and_network() -> None:
    source = _module_source().lower()
    imports = _imported_modules()
    calls = _called_names()
    assert not any(
        command in source
        for command in (
            "pip install",
            "conda install",
            "apt install",
            "apt-get install",
            "winget install",
            "choco install",
        )
    )
    assert ".codex/reports/validation" not in source
    assert imports.isdisjoint(
        {
            "subprocess",
            "socket",
            "requests",
            "urllib",
            "urllib.request",
            "http.client",
            "osw.core",
            "osw.core.project_schema",
            "github",
            "pyside6",
            "osw.gui",
            "osw.plugins",
            "osw.solvers",
        }
    )
    assert calls.isdisjoint(
        {
            "run",
            "popen",
            "system",
            "check_call",
            "check_output",
            "urlopen",
            "request",
            "discover_optional_solver_manifests",
            "execute_solver",
            "mutate_project_schema",
            "create_issue",
            "close_issue",
            "create_release",
            "upload_asset",
            "push_tag",
        }
    )
