"""Certification denial vs overclaim contract for the scope-drift checker."""

from __future__ import annotations

from types import ModuleType

import pytest
from test_qa_tools import REPO_ROOT, load_module, run_tool

CHECKER_PATH = REPO_ROOT / "tools" / "qa" / "check_scope_drift.py"

README_LINE = "It is not production-ready or industrially certified."
ARCHITECTURE_LINE = (
    "It is not production-ready, not industrially certified, not a full "
    "ANSYS/MATLAB/ParaView replacement, and not a claim of all-topology "
    "support or solver numerical correctness."
)
VALIDATION_LINE = (
    "No tag/push/publication; `v0.1.5-rc1` remains immutable; native locality "
    "remains `DEFERRED_RETAINED`; no solver numerical or industrial "
    "certification claim"
)

REQUIRED_DENIALS = (
    "not industrially certified",
    "not production-ready or industrially certified",
    "no solver numerical or industrial certification claim",
    README_LINE,
    ARCHITECTURE_LINE,
    VALIDATION_LINE,
)

REQUIRED_OVERCLAIMS = (
    "industrially certified",
    "industrial certification complete",
    "solver numerical certification achieved",
    "not only industrially certified but production ready",
    "not merely industrially certified",
    "OSW is certified.",
)


def _checker() -> ModuleType:
    return load_module(CHECKER_PATH, "check_scope_drift_negation_under_test")


def _certification_findings(text: str) -> list[str]:
    return _checker().findings_for_text(text, label="<text>")


@pytest.mark.parametrize("text", REQUIRED_DENIALS)
def test_scope_drift_accepts_accurate_certification_denials(text: str) -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _certification_findings(text) == []


@pytest.mark.parametrize("text", REQUIRED_OVERCLAIMS)
def test_scope_drift_rejects_positive_or_evasive_certification_claims(text: str) -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "industrial certification" in proc.stdout
    assert _certification_findings(text)


def test_scope_drift_one_denial_does_not_suppress_later_positive_claim() -> None:
    text = "OSW is not industrially certified; the companion is industrially certified."

    proc = run_tool("tools/qa/check_scope_drift.py", "--text", text)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert proc.stdout.count("possible scope drift (industrial certification)") == 1


def test_scope_drift_changed_file_range_excludes_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = _checker()
    monkeypatch.setattr(
        checker,
        "changed_files",
        lambda base, root: ["tests/unit/foo.py", "README.md"],
    )

    labels = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in checker.default_scan_paths(REPO_ROOT, "origin/develop")
    }

    assert labels == {"README.md"}


def test_scope_drift_empty_develop_range_uses_intended_full_scan() -> None:
    checker = _checker()
    paths = checker.default_scan_paths(REPO_ROOT, "develop")
    labels = {path.relative_to(REPO_ROOT).as_posix() for path in paths}

    assert "README.md" in labels
    assert "docs/02_architecture.md" in labels
    assert "docs/04_validation_matrix.md" in labels
    assert all(not label.startswith("tests/") for label in labels)


def test_scope_drift_ci_command_accepts_current_repository_docs() -> None:
    proc = run_tool("tools/qa/check_scope_drift.py")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "README.md:179" not in proc.stdout
    assert "docs/02_architecture.md:466" not in proc.stdout
    assert "docs/04_validation_matrix.md:68" not in proc.stdout
