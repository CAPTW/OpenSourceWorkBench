from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_gui_viewmodel.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_plugin_manifest_gui_viewmodel_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental pure view-model implemented" in text
    assert "no gui implementation" in text
    assert "no file dialog" in text
    assert "no plugin package loading" in text
    assert "no directory scan" in text
    assert "no network fetch" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_relationship_and_public_api() -> None:
    raw = _read()
    text = raw.lower()

    assert "relationship to gui design and cli preview" in text
    assert "optional-solver-plugin-manifest-preview" in text
    assert "package path and public api" in text
    for symbol in (
        "OptionalSolverPluginManifestGuiViewModel",
        "OptionalSolverPluginManifestSummaryViewModel",
        "OptionalSolverPluginManifestAcceptedRowViewModel",
        "OptionalSolverPluginManifestRejectedRowViewModel",
        "OptionalSolverPluginManifestConflictRowViewModel",
        "OptionalSolverPluginManifestDiagnosticRowViewModel",
        "OptionalSolverPluginManifestTrustBadgeViewModel",
        "OptionalSolverPluginManifestAction",
        "OptionalSolverPluginManifestActionState",
        "build_optional_solver_plugin_manifest_gui_viewmodel",
        "summarize_optional_solver_plugin_manifest_gui_viewmodel",
        "explain_optional_solver_plugin_manifest_gui_viewmodel",
    ):
        assert symbol in raw


def test_doc_records_input_and_models() -> None:
    text = _normalized()

    assert "input load report" in text
    assert "optionalsolverpluginmanifestloadreport" in text
    assert "summary model" in text
    assert "accepted manifest rows" in text
    assert "rejected manifest rows" in text
    assert "conflict rows" in text
    assert "diagnostics rows" in text
    assert "trust badge model" in text
    assert "action-state model" in text


def test_doc_records_row_details_and_trust_behavior() -> None:
    text = _normalized()

    assert "stack id" in text
    assert "display name" in text
    assert "source type" in text
    assert "trust label" in text
    assert "related issue" in text
    assert "capabilities summary" in text
    assert "not-validation-evidence text" in text
    assert "rejection reason" in text
    assert "suggested fix" in text
    assert "built-ins-win text" in text
    assert "plugin-override-disabled text" in text
    assert "third-party/plugin manifests are not trusted by default" in text
    assert "trust label is not certification" in text


def test_doc_records_action_states_and_safety_boundary() -> None:
    text = _normalized()

    assert "choose explicit json files: future/display-only" in text
    assert "activate manifest: unavailable" in text
    assert "run discovery with plugin manifests: unavailable" in text
    assert "run validation: unavailable" in text
    assert "install solver: unavailable" in text
    assert "close issue: unavailable" in text
    assert "safety boundary" in text
    assert "data-only preview" in text
    assert "not validation evidence" in text
    assert "no plugin code execution" in text
    assert "no install actions" in text
    assert "no issue closure action" in text


def test_doc_records_health_panel_relationship_and_future_gates() -> None:
    raw = _read()
    text = raw.lower()

    assert "relationship to health panel" in text
    assert "future gui can display loader reports" in text
    assert "no activation is performed in this gate" in text
    assert "discovery refresh remains built-in" in text
    for gate in (
        "OSW-EXP-074_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_IMPLEMENTATION",
        "OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN",
        "OSW-VALID",
    ):
        assert gate in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "gui plugin preview exists",
        "file dialog exists",
        "plugin activation exists",
        "directory scan exists",
        "plugin package loading exists",
        "plugin manifests are trusted by default",
        "plugin manifest presence is validation evidence",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "external solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
