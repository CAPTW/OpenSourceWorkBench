from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_loader_model.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_plugin_manifest_loader_model_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental loader model implemented" in text
    assert "explicit dict/file loading only" in text
    assert "no plugin code execution" in text
    assert "no directory scanning" in text
    assert "no network fetch" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_lists_public_api_source_types_and_trust_labels() -> None:
    raw = _read()
    text = raw.lower()

    for name in (
        "OptionalSolverManifestSourceType",
        "OptionalSolverManifestTrustLabel",
        "OptionalSolverManifestSource",
        "OptionalSolverPluginManifestDocument",
        "OptionalSolverLoadedManifest",
        "OptionalSolverRejectedManifest",
        "OptionalSolverManifestConflict",
        "OptionalSolverPluginManifestLoadDiagnostic",
        "OptionalSolverPluginManifestLoadReport",
        "OptionalSolverPluginManifestLoaderOptions",
        "load_optional_solver_plugin_manifest_dict",
        "load_optional_solver_plugin_manifest_json",
        "load_optional_solver_plugin_manifest_documents",
        "explain_optional_solver_plugin_manifest_load_report",
    ):
        assert name in raw
    for source_type in (
        "builtin",
        "project_local",
        "user_local",
        "plugin_package",
        "organization_managed",
        "explicit_file",
        "explicit_dict",
    ):
        assert source_type in text
    assert "third-party plugin manifests are not trusted by default" in text
    assert "not certification" in text


def test_doc_defines_inputs_validation_conflicts_and_records() -> None:
    text = _normalized()

    assert "loader inputs" in text
    assert "explicit dict" in text
    assert "explicit json file" in text
    assert "validation and diagnostics" in text
    assert "parse_optional_solver_manifest_dict" in text
    assert "validate_optional_solver_manifest" in text
    assert "conflict handling" in text
    assert "built-ins win by default" in text
    assert "plugin overrides are forbidden by default" in text
    assert "accepted/rejected manifest records" in text


def test_doc_defines_safety_cli_gui_and_issue_relationships() -> None:
    text = _normalized()

    for phrase in (
        "installer commands",
        "executable code references",
        "bundled-solver claims",
        "certification claims",
        "future cli and gui preview gates",
        "no current cli/gui behavior change",
        "manifest loading is not validation evidence",
        "issues `#6` through `#11` remain open",
        "skipped-missing remains not pass evidence",
    ):
        assert phrase in text


def test_doc_lists_future_gates() -> None:
    raw = _read()

    for gate in (
        "OSW-EXP-071_OPTIONAL_SOLVER_PLUGIN_MANIFEST_CLI_PREVIEW",
        "OSW-EXP-072_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_DESIGN",
        "OSW-VALID",
    ):
        assert gate in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "directory scan exists",
        "plugin package loading exists",
        "cli preview exists",
        "gui plugin manifest display exists",
        "plugin manifests are trusted by default",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
