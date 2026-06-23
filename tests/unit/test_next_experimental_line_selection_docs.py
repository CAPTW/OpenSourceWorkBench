from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "roadmap" / "next_experimental_line_selection.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_next_experimental_line_selection_doc_exists() -> None:
    assert DOC.exists()


def test_doc_says_v0_1_5_rc1_public_prerelease() -> None:
    text = _normalized()

    assert "v0.1.5-rc1" in text
    assert "public prerelease" in text
    assert "not draft" in text


def test_doc_records_release_flow_audit_and_body_correction() -> None:
    text = _normalized()

    assert "release flow: closed" in text
    assert "fresh post-public audit: passed" in text
    assert "release body note: corrected" in text


def test_doc_records_osw_valid_005_skipped_missing() -> None:
    text = _read()
    normalized = text.lower()

    assert "OSW-VALID-005" in text
    assert "skipped-missing" in normalized
    assert "all `#6` through `#11` targets" in text


def test_doc_lists_open_validation_issues() -> None:
    text = _read()
    normalized = text.lower()

    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    assert "remains open" in normalized


def test_doc_lists_candidate_lines() -> None:
    text = _read()

    expected_candidates = (
        "Prepared-machine validation retry planning",
        "FEASpec / VFEA workflow expansion",
        "ResultDataset parser extension planning",
        "ProjectSchema integration hardening",
        "Plugin ecosystem / optional solver manifest UX",
        "Maintenance / monitoring continuation",
        "Pause active experimental work",
    )
    for candidate in expected_candidates:
        assert candidate in text


def test_doc_contains_exactly_one_selected_line() -> None:
    selected_lines = [
        line.strip()
        for line in _read().splitlines()
        if line.strip().startswith("Selected line:")
    ]

    assert selected_lines == [
        "Selected line: `Plugin ecosystem / optional solver manifest UX`"
    ]


def test_doc_lists_next_recommended_gate() -> None:
    assert "OSW-EXP-055_OPTIONAL_SOLVER_MANIFEST_UX_DESIGN" in _read()


def test_doc_lists_required_non_actions() -> None:
    text = _normalized()

    assert "no source implementation" in text
    assert "no solver execution" in text
    assert "no dependency install" in text


def test_doc_does_not_claim_live_validation_passed() -> None:
    text = _normalized()

    forbidden = (
        "live validation passed",
        "live optional validation passed",
        "calculix validation passed",
        "#8 passed",
        "#6 through #11 passed",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_doc_does_not_claim_issue_closure() -> None:
    text = _normalized()

    forbidden = (
        "#6 can close",
        "#8 can close",
        "#6 through #11 can close",
        "issues #6 through #11 can close",
        "closure ready",
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
