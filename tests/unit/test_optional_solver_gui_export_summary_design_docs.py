from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_export_summary_design.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_gui_export_summary_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_design_only_status_and_non_actions() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no export implementation" in text
    assert "no file dialog" in text
    assert "no clipboard integration" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_current_baseline_and_issue_state() -> None:
    text = _normalized()

    assert "optional solver gui health panel is implemented" in text
    assert "pure optional solver health view-model is implemented" in text
    assert "cli doctor preview is implemented" in text
    assert "issues `#6` through `#11` remain open and `skipped-missing`" in text
    assert "external solvers are not bundled" in text


def test_doc_defines_purpose_scope_formats_and_exclusions() -> None:
    text = _normalized()

    assert "purpose" in text
    assert "support, debugging, and prepared-machine planning" in text
    assert "export scope" in text
    for phrase in (
        "summary counts",
        "stack card summaries",
        "health states",
        "diagnostics",
        "guidance text",
        "validation history rows",
        "release and version context",
        "timestamp and source surface",
        "issue references",
    ):
        assert phrase in text
    assert "out-of-scope data" in text
    for phrase in (
        "full `path`",
        "environment variable values",
        "credentials or secrets",
        "raw solver outputs",
        "raw validation artifacts",
        "private user paths unless explicitly opted in",
        "issue mutation payloads",
    ):
        assert phrase in text
    assert "supported future formats" in text
    assert "json" in text
    assert "markdown" in text
    assert "plain text" in text


def test_doc_defines_privacy_path_flow_and_action_state() -> None:
    text = _normalized()

    assert "redaction and privacy" in text
    assert "redacted paths remain redacted by default" in text
    assert "environment values are never exported by default" in text
    assert "full path export requires explicit opt-in and a warning" in text
    assert "no telemetry" in text
    assert "file path policy" in text
    assert "explicit save path only" in text
    assert "no implicit parent directory creation" in text
    assert "overwrite requires confirmation" in text
    assert "safe extension policy" in text
    assert "traversal and unsafe path rejection" in text
    assert "gui action flow" in text
    assert "preview" in text
    assert "choose a format" in text
    assert "choose a destination" in text
    assert "action-state design" in text
    assert "export redacted summary is available when the view-model is valid" in text
    assert "copy summary remains a future action" in text
    assert "open output folder is unavailable initially" in text
    assert "install solver remains unavailable" in text
    assert "close issue remains unavailable" in text


def test_doc_defines_payload_boundary_validation_failures_tests_and_gates() -> None:
    text = _normalized()
    raw = _read()

    assert "export payload boundary" in text
    assert "pure export payload builder consumes view-model only" in text
    assert "gui widget does not perform serialization directly" in text
    assert "no discovery execution during export" in text
    assert "no solver execution during export" in text
    assert "exported summary is not validation evidence" in text
    assert "skipped-missing remains not pass evidence" in text
    assert "failure handling" in text
    for phrase in (
        "invalid path",
        "overwrite denied",
        "serialization failure",
        "permission error",
        "redaction policy violation",
    ):
        assert phrase in text
    assert "tests for future implementation" in text
    for phrase in (
        "redacted json payload",
        "markdown payload",
        "plain text payload",
        "unsafe path rejection",
        "overwrite guard",
        "no clipboard side effects",
        "no shell or browser side effects",
        "no solver side effects",
        "privacy warnings",
    ):
        assert phrase in text
    assert "OSW-EXP-064_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_VIEWMODEL" in raw
    assert "OSW-EXP-065_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_IMPLEMENTATION" in raw
    assert "OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN" in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "export is implemented",
        "clipboard exists",
        "file dialog exists",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
