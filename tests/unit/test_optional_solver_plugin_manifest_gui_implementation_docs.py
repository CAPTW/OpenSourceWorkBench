from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_gui_implementation.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_plugin_manifest_gui_implementation_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental pyside display component implemented" in text
    assert "view-model driven" in text
    assert "no file dialog" in text
    assert "no plugin loading" in text
    assert "no plugin activation" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_package_and_viewmodel_relationship() -> None:
    raw = _read()
    text = raw.lower()

    assert "package path and public class" in text
    assert "optional_solver_plugin_manifest_panel.py" in text
    assert "OptionalSolverPluginManifestPanel" in raw
    assert "relationship to plugin manifest gui view-model" in text
    assert "OptionalSolverPluginManifestGuiViewModel" in raw
    assert "does not parse json" in text
    assert "does not run loader validation or discovery" in text


def test_doc_records_rendered_sections_and_displays() -> None:
    text = _normalized()

    assert "rendered sections" in text
    for section in (
        "summary header",
        "accepted manifests table",
        "rejected manifests table",
        "conflict table",
        "diagnostics table",
        "trust/source labels panel",
        "safety/policy guidance panel",
        "disabled action-state footer",
    ):
        assert section in text
    assert "accepted/rejected/conflict display" in text
    assert "diagnostics display" in text
    assert "trust/source labels" in text


def test_doc_records_safety_action_boundary() -> None:
    text = _normalized()

    assert "safety/action boundary" in text
    assert "no plugin code execution" in text
    assert "no file loading" in text
    assert "no directory scan" in text
    assert "no network fetch" in text
    assert "no solver execution" in text
    assert "no install action" in text
    assert "no issue closure action" in text
    assert "choose explicit json files" in text
    assert "activate manifest" in text
    assert "run discovery with plugin manifests" in text
    assert "run validation" in text
    assert "install solver" in text
    assert "close issue" in text


def test_doc_records_relationships_and_future_gates() -> None:
    raw = _read()
    text = raw.lower()

    assert "relationship to cli preview" in text
    assert "optional-solver-plugin-manifest-preview" in text
    assert "relationship to health panel" in text
    assert "does not activate plugin manifests for health checks" in text
    for gate in (
        "OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI_DESIGN",
        "OSW-EXP-076_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN",
        "OSW-VALID",
    ):
        assert gate in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "explicit import gui exists",
        "file dialog exists",
        "activation exists",
        "directory scan exists",
        "plugin package loading exists",
        "plugin manifests are trusted by default",
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
