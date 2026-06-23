from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_health_panel_design.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_gui_health_panel_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_current_baseline() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no gui implementation" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text
    assert "`v0.1.5-rc1` is a public prerelease" in text
    assert "optional solver manifest schema/model exists" in text
    assert "passive discovery service exists" in text
    assert "cli doctor preview exists" in text
    assert "issues `#6` through `#11` are open and `skipped-missing`" in text


def test_doc_defines_cli_relationship_entry_points_and_layout() -> None:
    text = _normalized()

    assert "relationship to cli doctor" in text
    assert "same manifest and passive discovery concepts" in text
    assert "align health states, diagnostics, redaction, and issue references" in text
    assert "entry points" in text
    for phrase in (
        "future menu item",
        "future validation dashboard link",
        "future project settings link",
        "future release/first-run guidance link",
    ):
        assert phrase in text
    for phrase in (
        "summary header",
        "stack filter/search",
        "per-stack cards",
        "details panel",
        "diagnostics panel",
        "guidance panel",
        "validation history panel",
        "safety/privacy footer",
    ):
        assert phrase in text


def test_doc_defines_cards_details_and_diagnostics() -> None:
    text = _normalized()

    for phrase in (
        "stack cards",
        "stack id",
        "display name",
        "issue reference",
        "health state",
        "missing requirements count",
        "support status",
        "non-bundled disclaimer",
        "details panel",
        "executable requirements",
        "python package requirements",
        "environment hints, redacted",
        "version/help probe declarations, not executed",
        "diagnostics display",
        "missing executable",
        "missing python package",
        "partial stack",
        "unsupported platform",
        "manifest error",
        "path redaction notice",
        "passive-discovery-only notice",
    ):
        assert phrase in text


def test_doc_defines_privacy_and_user_actions() -> None:
    text = _normalized()

    assert "privacy and redaction" in text
    assert "paths are redacted by default" in text
    assert "environment values are hidden" in text
    assert "no telemetry" in text
    assert "full path display requires explicit opt-in in future" in text
    assert "user actions" in text
    assert "refresh passive discovery" in text
    assert "no install button in initial scope" in text
    assert "no run-smoke button in initial scope" in text
    assert "validation run links must go through explicit validation gates" in text


def test_doc_defines_validation_history_viewmodel_plugin_and_accessibility() -> None:
    text = _normalized()

    assert "validation history" in text
    assert "skipped-missing is not pass" in text
    assert "closure review" in text
    assert "issue closure not available from panel" in text
    assert "future view-model boundary" in text
    assert "pure view-model consumes discovery report objects" in text
    assert "gui widgets do not perform discovery directly" in text
    assert "no solver command execution from view-model" in text
    assert "plugin ecosystem" in text
    assert "built-in stacks come first" in text
    assert "trust labels" in text
    assert "untrusted manifests cannot execute code" in text
    assert "schema validation required" in text
    assert "accessibility and clarity" in text
    assert "text alternatives for health states" in text
    assert "plain-language missing/partial messages" in text


def test_doc_lists_future_implementation_slices() -> None:
    text = _read()

    assert "OSW-EXP-061_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_VIEWMODEL" in text
    assert "OSW-EXP-062_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_IMPLEMENTATION" in text
    assert "OSW-EXP-063_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_DESIGN" in text
    assert "OSW-VALID" in text


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "gui panel exists",
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
