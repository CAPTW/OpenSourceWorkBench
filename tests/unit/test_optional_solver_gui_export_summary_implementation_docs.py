from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_export_summary_implementation.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_gui_export_summary_implementation_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental gui export action implemented" in text
    assert "redacted summary export only" in text
    assert "no clipboard" in text
    assert "no shell or browser action" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_public_class_formats_and_save_policy() -> None:
    text = _read()
    normalized = text.lower()

    assert "OptionalSolverHealthPanel" in text
    assert "src/osw/gui/dialogs/optional_solver_health_panel.py" in text
    assert "JSON" in text
    assert "Markdown" in text
    assert "plain text" in normalized
    assert "parent directory must already exist" in normalized
    assert "parent directories are not created implicitly" in normalized
    assert "existing targets require explicit overwrite confirmation" in normalized
    assert "a successful export writes exactly one selected file" in normalized


def test_doc_records_viewmodel_relationship_privacy_and_status() -> None:
    text = _normalized()

    assert "optional_solver_gui_export_summary_viewmodel.md" in text
    assert "redacted paths remain redacted" in text
    assert "full user paths are omitted by default" in text
    assert "environment variable values are not exported" in text
    assert "not validation evidence" in text
    assert "export status text" in text
    assert "export error text" in text
    assert "last export format" in text


def test_doc_records_issue_relationship_and_future_gates() -> None:
    text = _read()
    normalized = text.lower()

    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    assert "Issues `#6` through `#11` remain open." in text
    assert "skipped-missing" in normalized
    assert "OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN" in text
    assert "OSW-EXP-067_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_POLISH" in text
    assert "OSW-VALID" in text


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "full-path export is default",
        "clipboard exists",
        "open output folder exists",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
