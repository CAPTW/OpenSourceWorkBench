from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_gui_design.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_plugin_manifest_gui_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_design_status_and_non_actions() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no gui implementation" in text
    assert "no view-model implementation" in text
    assert "no file dialog" in text
    assert "no plugin package loading" in text
    assert "no directory scan" in text
    assert "no network fetch" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_current_baseline() -> None:
    raw = _read()
    text = _normalized()

    assert "v0.1.5-rc1 public prerelease" in text
    assert "plugin manifest loader model exists" in text
    assert "plugin manifest cli preview exists" in text
    assert "plugin manifest gui view-model exists" in text
    assert "Optional solver health/export/refresh GUI exists." in raw
    assert "#6~#11 open/skipped-missing" in raw
    assert "external solvers not bundled" in text


def test_doc_defines_purpose_and_entry_points() -> None:
    text = _normalized()

    assert "purpose" in text
    assert "let users preview explicit plugin manifest files in a future gui" in text
    assert "show accepted/rejected/conflict status" in text
    assert "show trust labels and source types" in text
    assert "keep plugin metadata separate from validation evidence" in text
    assert "avoid plugin code execution" in text
    assert "entry points" in text
    assert "future optional solver health panel action" in text
    assert "future plugin manifest preview dialog" in text
    assert "future project settings entry" in text
    assert "no automatic plugin manifest loading on startup" in text


def test_doc_defines_preview_flow_and_layout() -> None:
    text = _normalized()

    assert "explicit file preview flow" in text
    assert "user chooses one or more json manifest files" in text
    assert "loader parses data only" in text
    assert "gui displays accepted/rejected/conflicts/diagnostics" in text
    assert "no accepted manifest is persisted or activated in initial scope" in text
    assert "panel/dialog layout" in text
    for section in (
        "summary header",
        "source/trust overview",
        "accepted manifests table",
        "rejected manifests table",
        "conflict table",
        "diagnostics panel",
        "safety/policy panel",
        "future action footer",
    ):
        assert section in text


def test_doc_defines_accepted_rejected_conflict_display() -> None:
    text = _normalized()

    assert "accepted manifest display" in text
    for phrase in (
        "stack id",
        "display name",
        "source type",
        "trust label",
        "related issue",
        "support status",
        "capabilities summary",
        "not validation evidence notice",
    ):
        assert phrase in text
    assert "rejected manifest display" in text
    assert "source path/ref" in text
    assert "rejection reason" in text
    assert "suggested fixes" in text
    assert "unsafe claim indicators" in text
    assert "conflict display" in text
    assert "duplicate stack id" in text
    assert "built-in wins by default" in text
    assert "plugin override disabled by default" in text
    assert "explicit override policy future-only" in text


def test_doc_defines_trust_safety_privacy_and_relationships() -> None:
    text = _normalized()

    assert "trust/source labels" in text
    for label in (
        "built-in trusted",
        "reviewed project",
        "user provided",
        "third-party plugin",
        "organization managed",
        "untrusted",
        "invalid",
    ):
        assert label in text
    assert "trust label is not certification" in text
    assert "safety/policy messaging" in text
    assert "no plugin code execution" in text
    assert "no package import" in text
    assert "privacy" in text
    assert "display paths redacted by default" in text
    assert "source file names may be shown" in text
    assert "full paths require future explicit opt-in" in text
    assert "relationship to cli preview" in text
    assert "same accepted/rejected/conflict semantics" in text
    assert "relationship to health panel" in text
    assert "future activation would require a separate gate" in text
    assert "plugin manifest preview is not validation evidence" in text


def test_doc_defines_viewmodel_failure_non_goals_and_future_gates() -> None:
    raw = _read()
    text = raw.lower()

    assert "future view-model boundary" in text
    assert "pure view-model consumes loader report" in text
    assert "gui widgets do not parse json directly" in text
    assert "file dialog passes explicit paths to a future runner" in text
    assert "no solver/discovery side effects from view-model" in text
    assert "view-model implementation follow-up" in text
    assert "optional solver plugin manifest gui view-model" in text
    assert "failure handling" in text
    for failure in (
        "invalid json",
        "unsupported schema",
        "unsafe claim",
        "duplicate stack id",
        "untrusted source",
        "path denied",
        "user cancel",
    ):
        assert failure in text
    assert "non-goals" in text
    for gate in (
        "OSW-EXP-073_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_VIEWMODEL",
        "OSW-EXP-074_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_IMPLEMENTATION",
        "OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN",
        "OSW-VALID",
    ):
        assert gate in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "gui plugin preview exists",
        "plugin activation exists",
        "directory scan exists",
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
