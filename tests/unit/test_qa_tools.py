from __future__ import annotations

import hashlib
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


# --- Tracked canonical release-gate evidence fixtures ---
# The strict static gate reads canonical evidence and the queues from the
# committed HEAD only; no untracked runtime report is required. Fixtures write
# LF bytes with core.autocrlf=false so each committed blob equals the written
# bytes, making the SHA-256 bindings deterministic on any host OS.

_CANONICAL_EVIDENCE_PATH = ".codex/release_gate_evidence.json"
_FUNCTIONAL_QUEUE_PATH = ".codex/func_queue_state.json"
_UI_QUEUE_PATH = ".codex/ui_queue_state.json"
_OLD_RAW_REPORT_PATH = ".codex/reports/func/OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF.md"

_release_gate_module = load_module(
    REPO_ROOT / "tools" / "qa" / "check_release_gate.py",
    "check_release_gate_for_fixtures",
)
_FUNC_STEPS = list(_release_gate_module.FUNC_STEPS)
_UI_STEPS = list(_release_gate_module.UI_STEPS)


def _git_in(root: Path, *args: str) -> None:
    proc = subprocess.run(
        [GIT_BIN or "git", *args],
        cwd=root,
        env=tool_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def _canonical_func_bytes(**overrides: object) -> bytes:
    payload = {
        "completed": _FUNC_STEPS,
        "current_step": None,
        "next_step": None,
        "release_state": "v0.1-internal-rc-frozen",
        "last_report": _CANONICAL_EVIDENCE_PATH,
    }
    payload.update(overrides)
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")


def _canonical_ui_bytes(**overrides: object) -> bytes:
    payload = {"completed": _UI_STEPS, "current_step": None, "status": "complete"}
    payload.update(overrides)
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")


def _canonical_manifest_dict(func_sha: str, ui_sha: str) -> dict[str, object]:
    return {
        "claim_scope": "tracked-static-release-gate-invariants-only",
        "evidence_kind": "osw-release-gate-canonical",
        "functional_queue_path": _FUNCTIONAL_QUEUE_PATH,
        "functional_queue_sha256": func_sha,
        "required_functional_step": "OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF",
        "required_release_state": "v0.1-internal-rc-frozen",
        "required_ui_status": "complete",
        "runtime_report_policy": "local-untracked-noncanonical",
        "schema_version": 1,
        "ui_queue_path": _UI_QUEUE_PATH,
        "ui_queue_sha256": ui_sha,
        "validation_evidence": "separate-fresh-full-range-required",
    }


def _canonical_bytes(mapping: dict[str, object]) -> bytes:
    return (json.dumps(mapping, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _canonical_release_repo(
    tmp_path: Path,
    *,
    func_bytes: bytes | None = None,
    ui_bytes: bytes | None = None,
    manifest_builder=None,
    commit_manifest: bool = True,
    post_commit=None,
) -> Path:
    root = tmp_path / "release-gate-repo"
    (root / ".codex").mkdir(parents=True)
    _git_in(root, "init", "--quiet")
    _git_in(root, "config", "user.email", "osw-test@example.invalid")
    _git_in(root, "config", "user.name", "OSW Test")
    _git_in(root, "config", "core.autocrlf", "false")

    resolved_func = _canonical_func_bytes() if func_bytes is None else func_bytes
    resolved_ui = _canonical_ui_bytes() if ui_bytes is None else ui_bytes
    (root / _FUNCTIONAL_QUEUE_PATH).write_bytes(resolved_func)
    (root / _UI_QUEUE_PATH).write_bytes(resolved_ui)

    func_sha = hashlib.sha256(resolved_func).hexdigest()
    ui_sha = hashlib.sha256(resolved_ui).hexdigest()
    if manifest_builder is None:
        manifest_bytes = _canonical_bytes(_canonical_manifest_dict(func_sha, ui_sha))
    else:
        manifest_bytes = manifest_builder(func_sha, ui_sha)
    (root / _CANONICAL_EVIDENCE_PATH).write_bytes(manifest_bytes)

    add_paths = [_FUNCTIONAL_QUEUE_PATH, _UI_QUEUE_PATH]
    if commit_manifest:
        add_paths.append(_CANONICAL_EVIDENCE_PATH)
    _git_in(root, "add", "--", *add_paths)
    _git_in(root, "commit", "--quiet", "-m", "canonical release evidence")

    if post_commit is not None:
        post_commit(root)
    return root


def _run_release_gate_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return run_tool(str(REPO_ROOT / "tools" / "qa" / "check_release_gate.py"), cwd=root)


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


def test_release_gate_checker_passes_from_committed_canonical_evidence(tmp_path: Path) -> None:
    root = _canonical_release_repo(tmp_path)
    assert not (root / _OLD_RAW_REPORT_PATH).exists()

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Tracked static release-gate invariants passed" in proc.stdout
    # Strict static success must not overclaim validation/publication readiness.
    assert "publication" not in proc.stdout.lower()


def test_release_gate_checker_passes_without_and_ignores_old_raw_report(tmp_path: Path) -> None:
    def add_untracked_report(root: Path) -> None:
        report = root / _OLD_RAW_REPORT_PATH
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# arbitrary local runtime markdown\n", encoding="utf-8")

    root = _canonical_release_repo(tmp_path, post_commit=add_untracked_report)

    proc = _run_release_gate_checker(root)

    # An arbitrary untracked markdown at the old report path neither satisfies nor
    # breaks the canonical gate; tracked evidence alone governs.
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_release_gate_checker_fails_when_canonical_evidence_untracked(tmp_path: Path) -> None:
    root = _canonical_release_repo(tmp_path, commit_manifest=False)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_untracked" in proc.stdout
    assert "Traceback" not in (proc.stdout + proc.stderr)


def test_release_gate_checker_fails_when_canonical_evidence_deleted(tmp_path: Path) -> None:
    def delete_manifest(root: Path) -> None:
        (root / _CANONICAL_EVIDENCE_PATH).unlink()

    root = _canonical_release_repo(tmp_path, post_commit=delete_manifest)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_dirty" in proc.stdout


def test_release_gate_checker_fails_when_committed_queue_worktree_modified(tmp_path: Path) -> None:
    def modify_queue(root: Path) -> None:
        (root / _FUNCTIONAL_QUEUE_PATH).write_bytes(_canonical_func_bytes() + b"\n")

    root = _canonical_release_repo(tmp_path, post_commit=modify_queue)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_dirty" in proc.stdout


@pytest.mark.parametrize("digest_field", ["functional_queue_sha256", "ui_queue_sha256"])
def test_release_gate_checker_fails_on_queue_digest_mismatch(
    tmp_path: Path, digest_field: str
) -> None:
    def builder(func_sha: str, ui_sha: str) -> bytes:
        mapping = _canonical_manifest_dict(func_sha, ui_sha)
        mapping[digest_field] = "0" * 64
        return _canonical_bytes(mapping)

    root = _canonical_release_repo(tmp_path, manifest_builder=builder)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_digest_mismatch" in proc.stdout


@pytest.mark.parametrize(
    "mutate",
    [
        lambda mapping: {**mapping, "unexpected_key": "x"},
        lambda mapping: {k: v for k, v in mapping.items() if k != "schema_version"},
        lambda mapping: {**mapping, "schema_version": 2},
        lambda mapping: {**mapping, "claim_scope": "broad-release-claim"},
        lambda mapping: {**mapping, "validation_evidence": "already-validated"},
        lambda mapping: {**mapping, "functional_queue_sha256": "NOTHEX"},
    ],
)
def test_release_gate_checker_fails_on_schema_violation(tmp_path: Path, mutate) -> None:
    def builder(func_sha: str, ui_sha: str) -> bytes:
        return _canonical_bytes(mutate(_canonical_manifest_dict(func_sha, ui_sha)))

    root = _canonical_release_repo(tmp_path, manifest_builder=builder)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_schema_mismatch" in proc.stdout
    assert "Traceback" not in (proc.stdout + proc.stderr)


@pytest.mark.parametrize(
    "raw",
    [
        b"{ this is not json",
        b"\xef\xbb\xbf{}\n",
        b'{\n  "claim_scope": "a",\n  "claim_scope": "b"\n}\n',
    ],
)
def test_release_gate_checker_fails_on_malformed_canonical_bytes(
    tmp_path: Path, raw: bytes
) -> None:
    root = _canonical_release_repo(tmp_path, manifest_builder=lambda _f, _u: raw)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_malformed_json" in proc.stdout
    assert "Traceback" not in (proc.stdout + proc.stderr)


@pytest.mark.parametrize(
    "bad_path",
    [
        "/abs/queue.json",
        "C:/queue.json",
        "\\\\unc\\queue.json",
        "../escape.json",
        ".codex/../x.json",
    ],
)
def test_release_gate_checker_fails_on_noncanonical_path(tmp_path: Path, bad_path: str) -> None:
    def builder(func_sha: str, ui_sha: str) -> bytes:
        mapping = _canonical_manifest_dict(func_sha, ui_sha)
        mapping["functional_queue_path"] = bad_path
        return _canonical_bytes(mapping)

    root = _canonical_release_repo(tmp_path, manifest_builder=builder)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_path_invalid" in proc.stdout


def test_release_gate_checker_fails_on_wrong_release_state(tmp_path: Path) -> None:
    root = _canonical_release_repo(
        tmp_path, func_bytes=_canonical_func_bytes(release_state="draft")
    )

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_release_state_mismatch" in proc.stdout


def test_release_gate_checker_fails_on_wrong_ui_status(tmp_path: Path) -> None:
    root = _canonical_release_repo(tmp_path, ui_bytes=_canonical_ui_bytes(status="in_progress"))

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_ui_status_mismatch" in proc.stdout


def test_release_gate_checker_fails_on_wrong_last_report_pointer(tmp_path: Path) -> None:
    root = _canonical_release_repo(
        tmp_path,
        func_bytes=_canonical_func_bytes(last_report=_OLD_RAW_REPORT_PATH),
    )

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "release_evidence_pointer_mismatch" in proc.stdout


def test_release_gate_checker_fails_when_required_terminal_step_missing(tmp_path: Path) -> None:
    truncated = [step for step in _FUNC_STEPS if step != "OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF"]
    root = _canonical_release_repo(tmp_path, func_bytes=_canonical_func_bytes(completed=truncated))

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert (
        "functional queue missing OSW-FUNC-023_V0_1_FREEZE_AND_HANDOFF" in proc.stdout
        or "release_evidence_pointer_mismatch" in proc.stdout
    )


def test_release_gate_checker_rejects_staged_forbidden_report_artifact(tmp_path: Path) -> None:
    def stage_report(root: Path) -> None:
        report = root / ".codex" / "reports" / "func" / "SYNTHETIC_STAGED.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("synthetic\n", encoding="utf-8")
        _git_in(root, "add", "--", ".codex/reports/func/SYNTHETIC_STAGED.md")

    root = _canonical_release_repo(tmp_path, post_commit=stage_report)

    proc = _run_release_gate_checker(root)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "forbidden runtime/report/duplicate files are staged" in proc.stdout


def test_release_gate_checker_rejects_removed_allow_missing_report_flag(tmp_path: Path) -> None:
    root = _canonical_release_repo(tmp_path)

    proc = run_tool(
        str(REPO_ROOT / "tools" / "qa" / "check_release_gate.py"),
        "--allow-missing-report",
        cwd=root,
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "allow-missing-report" in (proc.stdout + proc.stderr)


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
