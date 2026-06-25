from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_export_summary_viewmodel.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_gui_export_summary_viewmodel_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_non_actions() -> None:
    text = _normalized()

    assert "experimental pure export payload/view-model implemented" in text
    assert "no file write" in text
    assert "no file dialog" in text
    assert "no clipboard" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_lists_public_api_and_formats() -> None:
    text = _read()

    for name in (
        "OptionalSolverExportSummaryFormat",
        "OptionalSolverExportSummaryOptions",
        "OptionalSolverExportSummaryPayload",
        "OptionalSolverExportSummaryViewModel",
        "OptionalSolverExportSummarySavePlan",
        "OptionalSolverExportSummaryDiagnostic",
        "OptionalSolverExportSummaryPrivacyWarning",
        "OptionalSolverExportSummaryRenderResult",
        "build_optional_solver_export_summary_viewmodel",
        "build_optional_solver_export_summary_payload",
        "render_optional_solver_export_summary_json",
        "render_optional_solver_export_summary_markdown",
        "render_optional_solver_export_summary_text",
        "plan_optional_solver_export_summary_save",
        "explain_optional_solver_export_summary",
    ):
        assert name in text
    normalized = text.lower()
    assert "json" in normalized
    assert "markdown" in normalized
    assert "text" in normalized


def test_doc_defines_payload_renderers_and_save_plan() -> None:
    text = _normalized()

    for phrase in (
        "payload fields",
        "summary counts",
        "stack card summaries",
        "health states",
        "diagnostics",
        "guidance",
        "validation history",
        "issue references",
        "redaction state",
        "json rendering",
        "markdown rendering",
        "plain-text rendering",
        "save-plan analysis",
        "requires an explicit path",
        "rejects missing parent directories",
        "rejects traversal or unsafe paths",
        "rejects unsupported extensions",
        "blocks overwrite by default",
        "would_write_file=false",
    ):
        assert phrase in text


def test_doc_defines_privacy_safety_issue_relationship_and_future_gates() -> None:
    text = _normalized()
    raw = _read()

    assert "export summaries are redacted by default" in text
    assert "environment values are never exported" in text
    assert "full paths require explicit opt-in warning" in text
    assert "export summary is not validation evidence" in text
    assert "no discovery execution" in text
    assert "no subprocess" in text
    assert "no file write" in text
    assert "no clipboard, shell, or browser action" in text
    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in raw
    assert "Issues `#6` through `#11` remain open." in raw
    assert "skipped-missing` is not pass evidence" in raw
    assert "OSW-EXP-065_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_IMPLEMENTATION" in raw
    assert "OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN" in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "gui export action exists",
        "file dialog exists",
        "clipboard exists",
        "actual file write exists",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
