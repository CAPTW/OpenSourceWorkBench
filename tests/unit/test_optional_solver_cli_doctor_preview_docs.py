from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / "optional_solver_cli_doctor_preview.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_cli_doctor_preview_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_non_actions() -> None:
    text = _normalized()

    assert "experimental cli preview implemented" in text
    assert "passive discovery only" in text
    assert "no solver execution" in text
    assert "no external solver command execution" in text
    assert "no active smoke validation" in text
    assert "no dependency installation" in text


def test_doc_lists_command_names_and_examples() -> None:
    text = _read()

    for command in (
        "optional-solver-list",
        "optional-solver-doctor",
        "optional-solver-explain",
    ):
        assert command in text


def test_doc_defines_manifest_and_discovery_relationship() -> None:
    text = _read()

    assert "Optional solver manifest schema model" in text
    assert "Optional solver discovery service implementation" in text
    assert "`optional-solver-list` reads manifest metadata only" in text
    assert "`optional-solver-doctor` runs passive discovery only" in text
    assert "`optional-solver-explain` reads one manifest" in text


def test_doc_defines_text_json_and_redaction_behavior() -> None:
    text = _normalized()

    assert "text output behavior" in text
    assert "json output behavior" in text
    assert "json output is parseable" in text
    assert "paths are redacted by default" in text
    assert "--show-full-paths" in text
    assert "environment values are not exposed" in text


def test_doc_defines_states_safety_and_issue_relationship() -> None:
    text = _normalized()

    for state in ("missing", "partially_installed", "discovered", "unknown"):
        assert state in text
    assert "no install command" in text
    assert "no solver command execution" in text
    assert "no bundled solvers" in text
    assert "#6" in text
    assert "#11" in text
    assert "issue closure remains separate" in text


def test_doc_lists_future_gates() -> None:
    text = _read()

    assert "OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN" in text
    assert "OSW-VALID" in text


def test_doc_does_not_claim_validation_or_closure_or_certification() -> None:
    text = _normalized()

    for phrase in (
        "active smoke validation exists",
        "gui panel exists",
        "install command exists",
        "solvers are installed",
        "solvers are bundled",
        "external solvers are bundled",
        "live validation passed",
        "#6 through #11 passed",
        "#8 can close",
        "issues can close",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
