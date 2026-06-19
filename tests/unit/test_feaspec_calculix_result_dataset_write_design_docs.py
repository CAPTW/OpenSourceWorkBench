from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_dataset_write_design.md"
)

REQUIRED_FDW_CODES = {
    "FDW_WRITE_NOT_IMPLEMENTED",
    "FDW_OUTPUT_PATH_REQUIRED",
    "FDW_PARENT_MISSING",
    "FDW_OUTPUT_EXISTS",
    "FDW_UNSAFE_PATH",
    "FDW_DRAFT_BLOCKED",
    "FDW_SCHEMA_VERSION_MISSING",
    "FDW_PROVENANCE_INCOMPLETE",
    "FDW_ARTIFACT_REFERENCE_MISSING",
    "FDW_ARTIFACT_HASH_MISMATCH",
    "FDW_DIAGNOSTICS_UNREVIEWED",
    "FDW_ATOMIC_WRITE_FAILED",
    "FDW_PARTIAL_WRITE_CLEANUP_FAILED",
    "FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN",
}


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_resultdataset_write_design_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_forbidden_capabilities_are_explicit() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no resultdataset persistence implementation" in text
    assert "no file writes" in text
    assert "no solver execution" in text


def test_relationship_to_draft_mapping_is_defined() -> None:
    text = _normalized()

    assert "relationship to existing layers" in text
    assert "resultdataset draft mapping" in text
    assert "reviewable in-memory source" in text


def test_output_layout_and_schema_versioning_are_defined() -> None:
    text = _normalized()

    assert "proposed output layout" in text
    assert "result_dataset.json" in text
    assert "result_dataset_manifest.json" in text
    assert "diagnostics.json" in text
    assert "provenance.json" in text
    assert "readme_review_first.txt" in text
    assert "schema/versioning" in text
    assert "schema_name" in text
    assert "schema_version" in text
    assert "producer_version" in text


def test_write_preconditions_and_path_policies_are_defined() -> None:
    text = _normalized()

    assert "write preconditions" in text
    assert "explicit output path or output directory" in text
    assert "non-blocked resultdataset draft mapping" in text
    assert "output path policy" in text
    assert "explicit user-supplied paths only" in text
    assert "path traversal rejection" in text
    assert "overwrite policy" in text
    assert "default is no overwrite" in text


def test_atomic_artifact_and_validation_design_are_defined() -> None:
    text = _normalized()

    assert "atomic write design" in text
    assert "write to a temporary path" in text
    assert "atomically rename or replace" in text
    assert "artifact reference policy" in text
    assert "default policy references original artifacts" in text
    assert "validation before write" in text
    assert "draft status and blocker diagnostics" in text


def test_all_fdw_diagnostic_codes_are_listed() -> None:
    text = _read()

    for code in REQUIRED_FDW_CODES:
        assert code in text


def test_cli_gui_security_and_tests_are_defined() -> None:
    text = _normalized()

    assert "cli future design" in text
    assert "explicit `--output`" in text
    assert "explicit `--overwrite`" in text
    assert "explicit `--acknowledge-limitations`" in text
    assert "gui future design" in text
    assert "review-first" in text
    assert "security and safety boundary" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "test strategy" in text
    assert "no file writes in this design gate" in text


def test_issue_8_remains_open_and_live_validation_not_claimed() -> None:
    text = _normalized()

    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()

    forbidden_claims = (
        "resultdataset persistence exists",
        "file write implementation exists",
        "live validation passed",
        "external solvers are bundled",
        "solver is bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
