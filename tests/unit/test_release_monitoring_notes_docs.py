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


def test_doc_says_validation_issues_remain_open() -> None:
    text = _read()

    for issue in ("#6", "#7", "#8", "#9", "#10", "#11"):
        assert issue in text
    assert "remain open" in _normalized()


def test_doc_says_external_solvers_not_bundled_and_no_certification() -> None:
    text = _normalized()

    assert "external solvers are not bundled" in text
    assert "no bundled solver claim" in text
    assert "no certification claim" in text
