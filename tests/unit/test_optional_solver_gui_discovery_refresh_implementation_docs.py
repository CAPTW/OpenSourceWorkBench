from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_discovery_refresh_implementation.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def _squashed() -> str:
    return " ".join(_normalized().split())


def test_optional_solver_gui_discovery_refresh_implementation_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental gui passive refresh implemented" in text
    assert "explicit user action only" in text
    assert "no automatic startup refresh" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text
    assert "no issue mutation" in text
    assert "no release mutation" in text


def test_doc_defines_class_runner_and_status_behavior() -> None:
    raw = _read()
    text = _normalized()

    assert "src/osw/gui/dialogs/optional_solver_health_panel.py" in raw
    assert "OptionalSolverHealthPanel" in raw
    assert "relationship to refresh view-model" in text
    assert "injected runner" in text
    assert "default built-in passive discovery runner" in text
    assert "status/error display" in text
    assert "refresh_status_text()" in raw
    assert "trigger_refresh_for_test()" in raw


def test_doc_records_viewmodel_export_and_privacy_behavior() -> None:
    text = _normalized()
    squashed = _squashed()

    assert "swaps the accepted `optionalsolverhealthpanelviewmodel` atomically" in text
    assert "failed, canceled, or stale refresh preserves the current view-model" in text
    assert "export after successful refresh uses the refreshed view-model" in text
    assert "export remains not validation evidence" in text
    assert "paths are redacted by default" in text
    assert "environment values are never displayed" in text
    assert "refresh is not validation evidence" in squashed


def test_doc_records_relationship_to_open_issues_and_future_gates() -> None:
    raw = _read()
    text = _normalized()
    squashed = _squashed()

    assert "issues `#6` through `#11` remain open" in text
    assert "skipped-missing remains not pass evidence" in squashed
    assert "OSW-EXP-069_OPTIONAL_SOLVER_PLUGIN_MANIFEST_LOADING_DESIGN" in raw
    assert "OSW-VALID" in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "active smoke validation exists",
        "install command exists",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "optional solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
