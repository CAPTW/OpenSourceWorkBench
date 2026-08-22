"""Post-publication documentation contract for published v0.1.5-rc3."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RC3_SOURCE = "4b1effccf3bbc4fd18073c0ab39f90cfb6822232"
RC3_TAG_OBJECT = "841db318dade807e5294718d4e50813934752d0a"
RC3_RELEASE_ID = "374854738"
RC3_RELEASE_URL = "https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc3"


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_current_facing_docs_record_published_rc3_identity() -> None:
    current_cycle = _read("docs/development/current_cycle.md")
    changelog = _read("CHANGELOG.md")
    readme = _read("README.md")
    checklist = _read("docs/10_release_checklist.md")
    monitoring = _read("docs/release/v0_1_5_rc3_post_release_monitoring.md")

    for text in (current_cycle, changelog, readme, checklist, monitoring):
        assert "`0.1.5rc3`" in text
        assert "`v0.1.5-rc3`" in text
        assert RC3_SOURCE in text

    assert "RC3_PUBLISHED_VERIFIED_POST_PUBLICATION_DOCUMENTATION_CLOSURE" in current_cycle
    assert "RC3_RELEASE_SOURCE" in current_cycle
    assert "CURRENT_DEVELOP_AFTER_DOCS_CLOSURE" in current_cycle
    assert "Planned next annotated tag: `v0.1.5-rc3` (not created)" not in current_cycle
    assert "Current public prerelease: `v0.1.5-rc2`" not in current_cycle

    assert "### 3D Workspace MVP RC3 Publication" in changelog
    assert "### 3D Workspace MVP RC3 Metadata Preparation" in changelog
    assert RC3_RELEASE_ID in changelog
    assert RC3_RELEASE_URL in changelog
    assert "2026-08-22T06:51:24Z" in changelog

    assert "Current public prerelease tag: `v0.1.5-rc3`" in readme
    assert "Later docs-only `develop`" in readme or "later docs-only `develop`" in readme.lower()


def test_release_checklist_and_records_preserve_history() -> None:
    checklist = _read("docs/10_release_checklist.md")
    decision_log = _read("docs/07_decision_log.md")
    validation = _read("docs/04_validation_matrix.md")

    assert "| v0.1.5-rc3 local metadata alignment | `IN_PROGRESS_LOCAL` |" in checklist
    assert "| v0.1.5-rc3 public prerelease | `PASS_WITH_WARNINGS` |" in checklist
    assert "| v0.1.5-rc3 post-publication documentation and monitoring | `PASS` |" in checklist
    assert RC3_RELEASE_ID in checklist
    assert "32555950013" in checklist
    assert "32555949955" in checklist

    assert "## ADR-0186:" in decision_log
    assert "## ADR-0187:" in decision_log
    assert decision_log.count("## ADR-0187:") == 1
    assert "later docs-only develop commits" in decision_log

    assert "| VAL-3D-012 |" in validation
    assert "| VAL-3D-013 |" in validation
    assert validation.count("| VAL-3D-013 |") == 1
    assert "exact four-asset verification" in validation
    assert "downloaded base/native smokes" in validation


def test_monitoring_doc_records_evidence_and_non_claims() -> None:
    monitoring = _read("docs/release/v0_1_5_rc3_post_release_monitoring.md")

    assert RC3_TAG_OBJECT in monitoring
    assert RC3_RELEASE_ID in monitoring
    assert RC3_RELEASE_URL in monitoring
    assert "2026-08-22T06:51:24Z" in monitoring
    assert "open_solver_workbench-0.1.5rc3-py3-none-any.whl" in monitoring
    assert "524764240" in monitoring
    assert "40023dad707adeb16dd2bbbc00477bda31ae39eae83e44983f84b79ee7f36c5e" in monitoring
    assert "Downloaded base installed-package smoke passed." in monitoring
    assert "Downloaded native installed-package smoke passed." in monitoring
    assert "32555950013" in monitoring
    assert "32555949955" in monitoring
    assert "DEFERRED_RETAINED" in monitoring
    assert "No industrial-certification claim." in monitoring
    assert "No production-readiness claim." in monitoring
    assert "not final `0.1.5`" in monitoring
    assert "85c8144f7ff19159ab02c40adb6483ce6b13c017" in monitoring
    assert "3eced55adf49e70690af80aeb1eb9a8b053555fd" in monitoring
