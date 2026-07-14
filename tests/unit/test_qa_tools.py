from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = Path(sys.executable).resolve().parent
ORIGINAL_PATH = os.environ.get("PATH", "")
GIT_BIN = shutil.which("git")


def tool_env() -> dict[str, str]:
    env = os.environ.copy()
    path_parts = [str(PYTHON_BIN)]
    if GIT_BIN:
        path_parts.append(str(Path(GIT_BIN).resolve().parent))
    if ORIGINAL_PATH:
        path_parts.append(ORIGINAL_PATH)
    env["PATH"] = os.pathsep.join(path_parts)
    return env


def run_tool(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        env=tool_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _release_gate_repo(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "release-gate-repo"
    root.mkdir()
    init = subprocess.run(
        [GIT_BIN or "git", "init", "--quiet"],
        cwd=root,
        env=tool_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    assert init.returncode == 0, init.stdout + init.stderr

    codex_dir = root / ".codex"
    codex_dir.mkdir()
    for name in ("func_queue_state.json", "ui_queue_state.json"):
        shutil.copyfile(REPO_ROOT / ".codex" / name, codex_dir / name)

    func_state = json.loads((codex_dir / "func_queue_state.json").read_text(encoding="utf-8"))
    report_value = func_state["last_report"]
    assert isinstance(report_value, str)
    return root, Path(report_value)


def test_scope_drift_flags_forbidden_positive_claim() -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", "Simulink support")

    assert proc.returncode != 0
    assert "Simulink" in proc.stdout


def test_scope_drift_allows_in_scope_adapter_text() -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", "Gmsh adapter")

    assert proc.returncode == 0


@pytest.mark.parametrize(
    "text",
    [
        "OSW is certified.",
        "OSW is certified provider-silent.",
        "OSW is not only certified.",
        "OSW is not merely certified.",
        "Whether certified or not is unresolved.",
        "# Non-goals\nWhether certified or not is unresolved.",
        "# Non-goals\nOSW is certified.",
        "# Non-goals\nCertified products are supported.",
        "# Non-goals\nThe companion is safe and certified.",
        "# Non-goals\nOSW may be certified.",
        "OSW is not a clone; OSW is certified.",
        "OSW is not certified; the companion is certified.",
        "OSW is not, certified.",
    ],
)
def test_scope_drift_rejects_positive_or_ambiguous_certification_claims(
    text: str,
) -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "industrial certification" in proc.stdout


@pytest.mark.parametrize(
    "text",
    [
        "OSW is not certified provider-silent.",
        "OSW is **NOT CERTIFIED** provider-silent!",
        "OSW is not a certified CAE product.",
        "OSW is not industrial-certified.",
        "No industrial certification is provided.",
        "This workbench is offered without industrial certification.",
        "OSW does not claim industrial certification.",
        "OSW makes no industrial certification claim.",
    ],
)
def test_scope_drift_accepts_explicit_certification_negation(text: str) -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_scope_drift_evaluates_certification_matches_independently() -> None:
    proc = run_tool(
        "tools/qa/check_scope_drift.py",
        "--text",
        "OSW is not certified; the companion is certified and the export is certified.",
    )

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert proc.stdout.count("possible scope drift (industrial certification)") == 2


def test_scope_drift_allows_explicit_blocked_unsafe_claim_fixture() -> None:
    proc = run_tool(
        "tools/qa/check_scope_drift.py",
        "--text",
        "\n".join(
            [
                "def blocked_by_unsafe_claim(",
                "    *,",
                '    claim_text: str = "This manifest is certified.",',
                "):",
                "    return build_viewmodel(unsafe_claims=(claim_text,))",
            ]
        ),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_architecture_checker_runs_on_current_repo() -> None:
    proc = run_tool("tools/qa/check_architecture_boundaries.py")

    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_architecture_checker_flags_gui_dynamic_runner_import(tmp_path: Path) -> None:
    checker = load_module(
        REPO_ROOT / "tools" / "qa" / "check_architecture_boundaries.py",
        "check_architecture_boundaries_for_dynamic_runner_test",
    )
    sample = tmp_path / "dialog.py"
    sample.write_text(
        "\n".join(
            [
                "from importlib import import_module",
                "runner_module = import_module('osw.solvers.openfoam.runner')",
            ]
        ),
        encoding="utf-8",
    )

    violations = checker.gui_boundary_violations(sample)

    assert any("openfoam.runner" in violation for violation in violations)


def test_architecture_checker_flags_gui_direct_runner_method(tmp_path: Path) -> None:
    checker = load_module(
        REPO_ROOT / "tools" / "qa" / "check_architecture_boundaries.py",
        "check_architecture_boundaries_for_runner_method_test",
    )
    sample = tmp_path / "dialog.py"
    sample.write_text(
        "def launch(runner):\n    return runner.run_case('case', 'icoFoam', None)\n",
        encoding="utf-8",
    )

    violations = checker.gui_boundary_violations(sample)

    assert any("run_case" in violation for violation in violations)


def test_architecture_checker_allows_run_monitor_status_text(tmp_path: Path) -> None:
    checker = load_module(
        REPO_ROOT / "tools" / "qa" / "check_architecture_boundaries.py",
        "check_architecture_boundaries_for_run_monitor_text_test",
    )
    sample = tmp_path / "run_monitor.py"
    sample.write_text(
        "TITLE = 'Run Monitor'\nSTATUS = 'Run status: not run'\n",
        encoding="utf-8",
    )

    assert checker.gui_boundary_violations(sample) == []


def test_git_clean_reports_branch_and_status() -> None:
    proc = run_tool("tools/qa/check_git_clean.py", "--allow-dirty")

    assert proc.returncode == 0
    assert "branch:" in proc.stdout
    assert "status:" in proc.stdout


def test_fast_qa_runner_handles_available_checks() -> None:
    proc = run_tool("tools/qa/run_fast_qa.py")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "pytest tests/unit -q" in proc.stdout


def test_release_gate_checker_fails_closed_when_synthetic_report_is_missing(
    tmp_path: Path,
) -> None:
    root, report_relative = _release_gate_repo(tmp_path)
    proc = run_tool(str(REPO_ROOT / "tools" / "qa" / "check_release_gate.py"), cwd=root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert f"release report is missing: {report_relative.as_posix()}" in proc.stdout


def test_release_gate_checker_accepts_synthetic_release_fixture(tmp_path: Path) -> None:
    root, report_relative = _release_gate_repo(tmp_path)
    report_path = root / report_relative
    report_path.parent.mkdir(parents=True)
    report_path.write_text("# Synthetic release gate evidence\n", encoding="utf-8")
    proc = run_tool(str(REPO_ROOT / "tools" / "qa" / "check_release_gate.py"), cwd=root)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Release gate queue" in proc.stdout


def test_release_gate_runner_passes_only_when_all_required_subchecks_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_module(
        REPO_ROOT / "tools" / "qa" / "run_release_gate.py",
        "run_release_gate_for_all_pass_test",
    )
    labels: list[str] = []

    monkeypatch.setattr(runner, "repo_root", lambda: REPO_ROOT)
    monkeypatch.setattr(runner, "python_executable", lambda: sys.executable)
    monkeypatch.setattr(
        runner,
        "run",
        lambda _args, *, cwd, label: labels.append(label) or 0,
    )

    assert runner.main() == 0
    assert len(labels) == 7


def test_release_gate_runner_propagates_required_subcheck_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_module(
        REPO_ROOT / "tools" / "qa" / "run_release_gate.py",
        "run_release_gate_for_failure_test",
    )
    labels: list[str] = []

    def fake_run(_args: list[str], *, cwd: Path, label: str) -> int:
        del cwd
        labels.append(label)
        return 1 if label == "python tools/qa/check_scope_drift.py" else 0

    monkeypatch.setattr(runner, "repo_root", lambda: REPO_ROOT)
    monkeypatch.setattr(runner, "python_executable", lambda: sys.executable)
    monkeypatch.setattr(runner, "run", fake_run)

    assert runner.main() == 1
    assert len(labels) == 7


def test_solver_artifact_checker_allows_only_curated_solver_fixture_paths() -> None:
    checker = load_module(
        REPO_ROOT / "tools" / "qa" / "check_no_solver_artifacts_committed.py",
        "check_no_solver_artifacts_committed_for_test",
    )

    assert checker.is_allowed(
        "tests/fixtures/feaspec/calculix_golden/cantilever_minimal.inp"
    )
    assert checker.is_allowed("tests/fixtures/calculix/results/simple_success.frd")
    assert not checker.is_allowed("tests/tmp/generated_case.inp")
    assert not checker.is_allowed("tests/unit/generated_result.frd")
