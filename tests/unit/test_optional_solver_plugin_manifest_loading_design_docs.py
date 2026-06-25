from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_loading_design.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def _squashed() -> str:
    return " ".join(_normalized().split())


def test_optional_solver_plugin_manifest_loading_design_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_non_actions() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no plugin loading implementation" in text
    assert "no plugin code execution" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_current_baseline() -> None:
    raw = _read()
    text = _normalized()

    assert "v0.1.5-rc1 public prerelease" in text
    assert "built-in optional solver manifests exist" in text
    assert "passive discovery service exists" in text
    assert "GUI health panel/refresh/export exist" in raw
    assert "#6~#11 open/skipped-missing" in raw
    assert "external solvers are not bundled" in text


def test_doc_defines_purpose_sources_and_trust_model() -> None:
    text = _normalized()

    assert "purpose" in text
    assert "allow future plugins to contribute optional solver manifest metadata" in text
    assert "manifest source categories" in text
    for source in (
        "built-in core manifests",
        "project-local manifests",
        "user-local manifests",
        "plugin package manifests",
        "future organization-managed manifests",
        "no network marketplace in initial scope",
    ):
        assert source in text

    assert "trust model" in text
    assert "built-in trusted" in text
    assert "plugin-provided third-party" in text
    assert "untrusted/invalid blocked" in text
    assert "trust label is not certification" in text


def test_doc_defines_loading_boundary_formats_locations_and_conflicts() -> None:
    text = _normalized()

    assert "loading boundary" in text
    assert "load manifest data only" in text
    assert "never execute plugin code during manifest loading" in text
    assert "schema validate before use" in text
    assert "candidate file formats" in text
    assert "json first" in text
    assert "no executable manifest format" in text
    assert "schema version required" in text
    assert "candidate locations" in text
    assert "project `.osw/optional_solvers/` future path" in text
    assert "safe path/traversal checks" in text
    assert "conflict handling" in text
    assert "duplicate stack id" in text
    assert "built-ins win by default" in text


def test_doc_defines_diagnostics_display_privacy_and_validation_relationship() -> None:
    text = _normalized()
    squashed = _squashed()

    assert "validation diagnostics" in text
    for diagnostic in (
        "schema invalid",
        "unsupported schema version",
        "duplicate stack id",
        "unsafe path",
        "untrusted source",
        "missing trust metadata",
        "installer command present",
        "executable code reference present",
        "bundled-solver claim present",
        "certification claim present",
    ):
        assert diagnostic in text
    assert "cli/gui display implications" in text
    assert "list source and trust label" in text
    assert "show invalid manifests separately" in text
    assert "discovery/refresh consumes only accepted manifests" in text
    assert "privacy/security" in text
    assert "no telemetry" in text
    assert "no network fetch in initial scope" in text
    assert "no execution from manifest" in text
    assert "relationship to validation" in text
    assert "plugin manifest presence is not validation evidence" in text
    assert "skipped-missing remains not pass" in squashed


def test_doc_lists_future_gates() -> None:
    raw = _read()

    for gate in (
        "OSW-EXP-070_OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOADER_MODEL",
        "OSW-EXP-071_OPTIONAL_SOLVER_PLUGIN_MANIFEST_CLI_PREVIEW",
        "OSW-EXP-072_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_DESIGN",
        "OSW-VALID",
    ):
        assert gate in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "plugin manifest loading exists",
        "plugin loading exists",
        "plugin manifests are trusted by default",
        "solvers are bundled",
        "external solvers are bundled",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "certified for production",
        "industrial certification claim",
    ):
        assert phrase not in text
