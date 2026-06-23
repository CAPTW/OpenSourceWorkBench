from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "roadmap" / "post_v0_1_5_rc1_next_worktrack_selection.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_next_worktrack_selection_doc_exists() -> None:
    assert DOC.exists()


def test_doc_says_v0_1_5_rc1_is_public_prerelease() -> None:
    text = _normalized()

    assert "v0.1.5-rc1" in text
    assert "public prerelease" in text
    assert "not draft" in text


def test_doc_says_assets_audit_and_body_note_are_done() -> None:
    text = _normalized()

    assert "assets present" in text
    assert "post-public audit: passed" in text
    assert "release body note: corrected" in text


def test_doc_lists_open_live_optional_validation_issues() -> None:
    text = _read()

    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    assert "remains open" in _normalized()


def test_doc_says_calculix_skipped_missing_because_ccx_absent() -> None:
    text = _normalized()

    assert "#8" in text
    assert "skipped-missing" in text
    assert "ccx" in text
    assert "absent" in text


def test_doc_contains_exactly_one_selected_worktrack() -> None:
    selected_lines = [
        line.strip()
        for line in _read().splitlines()
        if line.strip().startswith("Selected worktrack:")
    ]

    expected = (
        "Selected worktrack: `maintenance hardening for GUI aggregate timeout "
        "and release-monitoring notes`"
    )
    assert selected_lines == [expected]


def test_doc_lists_next_recommended_gate() -> None:
    text = _read()

    assert "OSW-MAINT-018_GUI_AGGREGATE_TIMEOUT_AND_RELEASE_MONITORING_HARDENING" in text


def test_doc_does_not_claim_live_calculix_validation_passed() -> None:
    text = _normalized()

    forbidden = (
        "live calculix validation passed",
        "calculix validation passed",
        "#8 passed",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_doc_does_not_claim_issue_8_can_close() -> None:
    text = _normalized()

    forbidden = (
        "#8 can close",
        "issue #8 can close",
        "#8 may close",
        "issue #8 may close",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_doc_does_not_claim_bundled_solvers_or_certification() -> None:
    text = _normalized()

    forbidden = (
        "solvers are bundled",
        "external solvers are bundled",
        "industrial certification",
        "certified for production",
        "certification is provided",
    )
    for phrase in forbidden:
        assert phrase not in text
