from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_discovery_refresh_design.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def _squashed() -> str:
    return " ".join(_normalized().split())


def test_optional_solver_gui_discovery_refresh_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_design_only_status_and_non_actions() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no refresh implementation" in text
    assert "no background worker implementation" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_baseline_and_issue_state() -> None:
    text = _normalized()

    assert "passive discovery service implemented" in text
    assert "cli doctor preview implemented" in text
    assert "gui health panel implemented" in text
    assert "gui export summary implemented" in text
    assert "issues `#6` through `#11` remain open and `skipped-missing`" in text
    assert "external solvers are not bundled" in text


def test_doc_defines_purpose_and_passive_boundary() -> None:
    text = _normalized()
    squashed = _squashed()

    assert "purpose" in text
    assert "explicitly refresh passive optional-solver discovery" in squashed
    assert "keep gui state aligned with cli doctor semantics" in squashed
    assert "avoid hidden solver execution" in squashed
    assert "preserve privacy/redaction" in squashed
    assert "passive refresh boundary" in text
    assert "allowed future checks are passive resolver checks only" in text
    assert "no active smoke validation" in text
    assert "no solver command execution" in text
    assert "no dependency install" in text
    assert "no automatic refresh on startup in initial scope" in text


def test_doc_defines_flow_worker_viewmodel_status_and_privacy() -> None:
    text = _normalized()

    assert "user flow" in text
    assert "user presses refresh passive discovery" in text
    assert "future injected runner" in text
    assert "worker and threading model" in text
    assert "no direct discovery in widgets" in text
    assert "stale result rejection" in text
    assert "ui remains responsive" in text
    assert "view-model update boundary" in text
    assert "widget swaps view-model atomically" in text
    assert "selected stack preserved by stack id" in text
    assert "status/error display" in text
    for phrase in (
        "idle",
        "refresh pending",
        "refresh running",
        "refresh completed",
        "refresh failed",
        "refresh canceled",
        "stale result ignored",
    ):
        assert phrase in text
    assert "privacy/redaction" in text
    assert "redacted paths by default" in text
    assert "environment values hidden" in text
    assert "no telemetry" in text


def test_doc_defines_export_validation_failure_tests_and_gates() -> None:
    text = _normalized()
    raw = _read()

    assert "interaction with export summary" in text
    assert "export before refresh uses the current view-model" in text
    assert "export after refresh uses the new view-model" in text
    assert "exported summary is not validation evidence" in text
    assert "interaction with validation gates" in text
    assert "skipped-missing remains not pass evidence" in text
    assert "active smoke validation remains separate" in text
    assert "issue closure remains unavailable from the panel" in text
    assert "failure handling" in text
    for phrase in (
        "discovery service exception",
        "malformed manifest",
        "path permission issue",
        "canceled refresh",
        "stale worker result",
        "privacy/redaction violation",
        "unexpected health state",
    ):
        assert phrase in text
    assert "test plan for future implementation" in text
    for phrase in (
        "injected runner success",
        "injected runner failure",
        "no startup refresh",
        "no solver execution",
        "selected stack preserved",
        "stale result ignored",
        "export after refresh uses refreshed data",
        "privacy retained",
        "issue mutation absent",
        "release mutation absent",
    ):
        assert phrase in text
    assert "OSW-EXP-067_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_VIEWMODEL" in raw
    assert "OSW-EXP-068_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_IMPLEMENTATION" in raw
    assert "OSW-VALID" in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "refresh is implemented",
        "active validation exists",
        "solvers are installed",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
