from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_health_panel_implementation.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_gui_health_panel_implementation_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_public_class() -> None:
    text = _read()
    normalized = text.lower()

    assert "Experimental PySide display component implemented" in text
    assert "view-model driven" in normalized
    assert "OptionalSolverHealthPanel" in text
    assert "src/osw/gui/dialogs/optional_solver_health_panel.py" in text


def test_doc_records_rendered_sections_and_viewmodel_relationship() -> None:
    text = _normalized()

    for phrase in (
        "summary header",
        "stack cards/list",
        "details panel",
        "diagnostics panel",
        "guidance and safety panel",
        "validation history panel",
        "action-state panel",
        "accepts an `optionalsolverhealthpanelviewmodel` object",
        "built outside the widget",
    ):
        assert phrase in text


def test_doc_records_action_privacy_and_safety_boundaries() -> None:
    text = _normalized()

    assert "refresh passive discovery: explicit passive discovery action" in text
    assert "no automatic startup refresh" in text
    assert "no active smoke validation" in text
    assert "run validation: disabled" in text
    assert "install solver: unavailable" in text
    assert "close issue: unavailable" in text
    assert "no clipboard access" in text
    assert "no shell or browser action" in text
    assert "redacted paths remain redacted" in text
    assert "environment values are not displayed" in text
    assert "passive discovery refresh only after explicit user action" in text
    assert "no solver execution" in text
    assert "no subprocess usage" in text
    assert "no install action" in text
    assert "no issue closure action" in text


def test_doc_records_issue_relationship_and_future_gates() -> None:
    text = _read()

    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    assert "Issues `#6` through `#11` remain open." in text
    assert "skipped-missing" in _normalized()
    assert "OSW-EXP-063_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_DESIGN" in text
    assert "OSW-EXP-068_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_IMPLEMENTATION" in text
    assert "OSW-VALID" in text


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "discovery refresh is implemented",
        "active smoke validation exists",
        "install command exists",
        "solvers are installed",
        "solvers are bundled",
        "external solvers are bundled",
        "validation passed",
        "#6 through #11 passed",
        "#8 can close",
        "issues can close",
        "issue closure readiness",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
