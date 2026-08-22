"""Current-identity contract for final 0.1.5 metadata preparation."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RC3_SOURCE = "4b1effccf3bbc4fd18073c0ab39f90cfb6822232"
DOCS_CLOSURE = "e3beb87af3e2ac134f848beb599dae12167a9bf0"


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_current_sources_use_final_package_and_planned_tag() -> None:
    pyproject = _read("pyproject.toml")
    init_text = _read("src/osw/__init__.py")
    checker = _read("tools/qa/check_release_metadata.py")
    smoke = _read("tests/unit/test_package_smoke.py")

    assert 'version = "0.1.5"' in pyproject
    assert 'version = "0.1.5rc3"' not in pyproject
    assert '__version__ = "0.1.5"' in init_text
    assert '__version__ = "0.1.5rc3"' not in init_text
    assert 'TARGET_VERSION = "0.1.5"' in checker
    assert 'TARGET_VERSION = "0.1.5rc3"' not in checker
    assert 'DEFAULT_RC_TAG = "v0.1.5"' in checker
    assert 'DEFAULT_PRIOR_PATCH_V015_RC3_TAG = "v0.1.5-rc3"' in checker
    assert RC3_SOURCE in checker
    assert 'EXPECTED_VERSION = "0.1.5"' in smoke
    assert 'EXPECTED_VERSION = "0.1.5rc3"' not in smoke


def test_current_facing_docs_record_final_preparation() -> None:
    current_cycle = _read("docs/development/current_cycle.md")
    changelog = _read("CHANGELOG.md")
    readme = _read("README.md")
    checklist = _read("docs/10_release_checklist.md")

    assert "Current package metadata: `0.1.5`" in current_cycle
    assert "Current public prerelease: `v0.1.5-rc3`" in current_cycle
    assert "Planned annotated tag: `v0.1.5`" in current_cycle
    assert "FINAL_0_1_5_METADATA_PREPARATION" in current_cycle
    assert "RC3_PUBLISHED_VERIFIED_POST_PUBLICATION_DOCUMENTATION_CLOSURE" in current_cycle
    assert "RC3_RELEASE_SOURCE" in current_cycle
    assert "CURRENT_DEVELOP_AFTER_DOCS_CLOSURE" in current_cycle
    assert RC3_SOURCE in current_cycle
    assert DOCS_CLOSURE in current_cycle

    assert "### 3D Workspace MVP Final 0.1.5 Metadata Preparation" in changelog
    assert "### 3D Workspace MVP RC3 Publication" in changelog
    assert "Candidate package version: `0.1.5`" in changelog
    assert "planned annotated tag" in changelog
    assert "`v0.1.5`" in changelog

    assert "Current `develop` package metadata: `0.1.5`." in readme
    assert "Current public prerelease tag: `v0.1.5-rc3`" in readme
    assert "`0.1.5rc3`" in readme

    assert "| v0.1.5 local final metadata alignment | `IN_PROGRESS_LOCAL` |" in checklist
    assert "| v0.1.5-rc3 post-publication documentation and monitoring | `PASS` |" in checklist


def test_decision_validation_and_notes_preserve_history() -> None:
    decision_log = _read("docs/07_decision_log.md")
    validation = _read("docs/04_validation_matrix.md")
    notes = _read("docs/release/v0_1_5_release_notes.md")

    assert "## ADR-0186:" in decision_log
    assert "## ADR-0187:" in decision_log
    assert "## ADR-0188:" in decision_log
    assert decision_log.count("## ADR-0188:") == 1

    assert "| VAL-3D-012 |" in validation
    assert "| VAL-3D-013 |" in validation
    assert "| VAL-3D-014 |" in validation
    assert validation.count("| VAL-3D-014 |") == 1

    assert notes.startswith("# OpenSolver Workbench v0.1.5\n")
    assert "version `0.1.5`" in notes
    assert "annotated tag `v0.1.5`" in notes
    assert RC3_SOURCE in notes
    assert DOCS_CLOSURE in notes
    assert "not created" not in notes.lower()
    assert "publication pending" not in notes.lower()
    assert "local bundle only" not in notes.lower()
    assert "D:/" not in notes
    assert "C:/" not in notes
    assert "owner-file" not in notes.lower()
    assert "746" not in notes
    assert "rescue" not in notes.lower()
    assert "DEFERRED_RETAINED" in notes
    assert "No industrial" in notes or "no industrial" in notes.lower()
    assert "open_solver_workbench-0.1.5-py3-none-any.whl" in notes
    assert "open_solver_workbench-0.1.5.tar.gz" in notes
