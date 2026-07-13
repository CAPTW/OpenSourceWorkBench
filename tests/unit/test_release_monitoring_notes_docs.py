from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "release" / "v0_1_5_rc1_post_release_monitoring.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_release_monitoring_doc_exists() -> None:
    assert DOC.exists()


def test_doc_says_v0_1_5_rc1_public_prerelease_is_live() -> None:
    text = _normalized()

    assert "v0.1.5-rc1" in text
    assert "live as a public prerelease" in text
    assert "not draft" in text


def test_doc_says_audit_and_body_note_are_done() -> None:
    text = _normalized()

    assert "post-public audit passed" in text
    assert "release body note was corrected" in text
    assert "fresh public asset download smoke completed" in text


def test_doc_says_validation_issues_are_closed_with_scoped_claims() -> None:
    text = _read()
    normalized = " ".join(_normalized().split())

    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    for boundary in (
        "not certification",
        "production-readiness",
        "release-readiness",
        "bundled-solver support",
        "broad solver/science correctness",
        "native-windows validation where evidence was wsl-scoped",
    ):
        assert boundary in normalized
    for current_claim in (
        "remain closed",
        "historical `skipped-missing` checks remain historical setup evidence only",
        "do not replace the later issue-specific validation evidence",
        "issue `#8` closure is limited to its later bounded wsl calculix evidence",
    ):
        assert current_claim in normalized
    assert "remain open" not in normalized
    assert "no issue `#8` closure claim" not in normalized


def test_doc_says_external_solvers_not_bundled_and_no_certification() -> None:
    text = _normalized()

    assert "external solvers are not bundled" in text
    assert "no bundled solver claim" in text
    assert "no certification claim" in text
