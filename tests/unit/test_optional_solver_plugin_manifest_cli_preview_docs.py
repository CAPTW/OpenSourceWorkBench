from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_cli_preview.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_plugin_manifest_cli_preview_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental cli preview implemented" in text
    assert "explicit json files only" in text
    assert "no plugin package loading" in text
    assert "no directory scan" in text
    assert "no network fetch" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_records_command_options_and_output_behavior() -> None:
    raw = _read()
    text = raw.lower()

    assert "optional-solver-plugin-manifest-preview" in raw
    assert "--manifest" in raw
    assert "--format text|json" in raw
    assert "--include-builtins" in raw
    assert "--strict" in raw
    assert "text output behavior" in text
    assert "json output behavior" in text
    assert "accepted_count" in raw
    assert "rejected_count" in raw
    assert "conflict_count" in raw


def test_doc_records_trust_diagnostics_conflicts_and_strict_mode() -> None:
    text = _normalized()

    assert "strict mode" in text
    assert "built-in conflict context" in text
    assert "diagnostics and conflicts" in text
    assert "third-party manifests are not trusted by default" in text
    assert "trust labels are display and policy signals, not certification" in text


def test_doc_records_safety_and_issue_relationship() -> None:
    text = _normalized()

    for phrase in (
        "data-only loading",
        "no plugin code execution",
        "no install commands",
        "no issue mutation",
        "preview is not validation evidence",
        "issues `#6` through `#11` remain open",
        "skipped-missing remains not pass evidence",
    ):
        assert phrase in text


def test_doc_lists_future_gates() -> None:
    raw = _read()

    for gate in (
        "OSW-EXP-072_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_DESIGN",
        "OSW-EXP-073_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPLICIT_IMPORT_GUI",
        "OSW-VALID",
    ):
        assert gate in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "gui plugin display exists",
        "directory scan exists",
        "plugin package loading exists",
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
