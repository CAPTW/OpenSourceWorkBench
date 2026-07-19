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


def run_tool_with_io_encoding(
    io_encoding: str,
    *args: str,
    cwd: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    """Run a QA tool with a forced stdio encoding, deterministic on any host OS.

    Setting ``PYTHONIOENCODING`` makes the child encode ``stdout``/``stderr`` with
    ``io_encoding`` regardless of the host locale, so a ``cp949`` console
    regression is reproduced even on UTF-8 developer machines and Linux CI. The
    captured streams are decoded with the same strict codec so a real
    ``UnicodeEncodeError`` crash surfaces instead of being masked.
    """
    env = tool_env()
    env["PYTHONIOENCODING"] = io_encoding
    env.pop("PYTHONUTF8", None)
    env.pop("PYTHONLEGACYWINDOWSSTDIO", None)
    return subprocess.run(
        [sys.executable, "-B", *args],
        cwd=cwd,
        env=env,
        text=True,
        encoding=io_encoding,
        errors="strict",
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
        "# Non-goals\nOSW supports industrial certification.",
        (
            "# Non-goals\n"
            "The provider is silent about whether OSW supports industrial certification."
        ),
        "OSW is not a clone; OSW is certified.",
        "OSW is not certified; the companion is certified.",
        "OSW is not, certified.",
        "OSW is unrelated not ready but supports industrial certification.",
        "OSW is not industrial certification.",
        "This matrix is not merely an industrial certification plan.",
        "Industrial certification is not optional.",
        "This matrix is not: an industrial certification plan.",
        "This matrix is not — an industrial certification plan.",
        (
            "- This matrix is not an industrial certification plan.\n"
            "  Industrial certification is available."
        ),
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
        "OSW does not claim `industrial certification`.",
        "OSW MAKES NO INDUSTRIAL CERTIFICATION CLAIM!",
        "This matrix is not an industrial certification plan.",
        "This statement was not an industrial certification claim.",
        "These matrices are not industrial certification plans.",
        "These statements were not industrial certification claims.",
        "This matrix **IS NOT AN INDUSTRIAL CERTIFICATION PLAN**.",
    ],
)
def test_scope_drift_accepts_explicit_certification_negation(text: str) -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize(
    ("text", "expected_count"),
    [
        (
            "OSW is not certified; the companion supports industrial certification.",
            1,
        ),
        (
            "OSW supports industrial certification; the companion is not certified.",
            1,
        ),
        (
            "OSW supports industrial certification; the companion is certified.",
            2,
        ),
        (
            "OSW is not certified; the companion has no industrial certification.",
            0,
        ),
        (
            "This matrix is not an industrial certification plan; "
            "the export is certified.",
            1,
        ),
        (
            "This matrix is not an industrial certification plan: "
            "the export supports industrial certification.",
            1,
        ),
        (
            "This matrix is not an industrial certification plan — "
            "the export supports industrial certification.",
            1,
        ),
    ],
)
def test_scope_drift_evaluates_certification_matches_independently(
    text: str,
    expected_count: int,
) -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.stdout.count("possible scope drift (industrial certification)") == expected_count
    assert proc.returncode == (1 if expected_count else 0), proc.stdout + proc.stderr


def test_scope_drift_preserves_certification_source_diagnostics() -> None:
    proc = run_tool(
        "tools/qa/check_scope_drift.py",
        "--text",
        "# Non-goals\nOSW supports industrial certification.",
    )

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert (
        "<text>:2: possible scope drift (industrial certification): "
        "OSW supports industrial certification."
    ) in proc.stdout


def test_scope_drift_certification_changes_preserve_other_scope_categories() -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", "Simulink support")

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "possible scope drift (Simulink)" in proc.stdout


# Finding text intentionally contains an em dash (U+2014), which ``cp949`` cannot
# encode. Forcing ``PYTHONIOENCODING=cp949`` reproduces the Windows console
# regression on any host, including UTF-8 developer machines and Linux CI.
_EM_DASH_SCOPE_DRIFT_TEXT = (
    "This matrix is not an industrial certification plan — "
    "the export supports industrial certification."
)


def test_scope_drift_survives_cp949_console_without_dropping_findings() -> None:
    proc = run_tool_with_io_encoding(
        "cp949",
        "tools/qa/check_scope_drift.py",
        "--text",
        _EM_DASH_SCOPE_DRIFT_TEXT,
    )

    combined = proc.stdout + proc.stderr
    assert "Traceback" not in combined, combined
    assert "UnicodeEncodeError" not in combined, combined
    # Scope-drift semantics are unchanged: the finding is still detected (exit 1).
    assert proc.returncode == 1, combined
    assert proc.stdout.count("possible scope drift (industrial certification)") == 1, proc.stdout
    # The unencodable em dash survives as a visible backslash escape rather than
    # crashing the checker or being silently discarded.
    assert "\\u2014" in proc.stdout, proc.stdout


def test_scope_drift_preserves_unicode_on_utf8_console() -> None:
    proc = run_tool_with_io_encoding(
        "utf-8",
        "tools/qa/check_scope_drift.py",
        "--text",
        _EM_DASH_SCOPE_DRIFT_TEXT,
    )

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr, proc.stderr
    # A UTF-8 console can represent the em dash, so the original Unicode is kept
    # verbatim and is not rewritten as an escape.
    assert "—" in proc.stdout, proc.stdout
    assert "\\u2014" not in proc.stdout, proc.stdout


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
