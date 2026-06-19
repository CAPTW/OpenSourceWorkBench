from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_frd_block_scanner_design.md"
)

REQUIRED_FP_FRD_CODES = {
    "FP_FRD_PARSE_NOT_IMPLEMENTED",
    "FP_FRD_BLOCK_SCAN_ONLY",
    "FP_FRD_BLOCK_UNSUPPORTED",
    "FP_FRD_BLOCK_TOO_LARGE",
    "FP_FRD_BLOCK_LIMIT_EXCEEDED",
    "FP_FRD_UNKNOWN_RECORD",
    "FP_FRD_BINARY_UNSUPPORTED",
    "FP_FRD_FIELD_VALUES_NOT_PARSED",
    "FP_FRD_MESH_RECONSTRUCTION_FORBIDDEN",
    "FP_FRD_UNITS_MISSING",
    "FP_FRD_PROVENANCE_MISSING",
    "FP_FRD_RESULT_DATASET_WRITE_FORBIDDEN",
    "FP_FRD_NO_RECOGNIZED_BLOCKS",
    "FP_FRD_REFERENCE_CANDIDATE_ONLY",
}


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_frd_block_scanner_design_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_forbidden_capabilities_are_explicit() -> None:
    text = _normalized()

    assert "design baseline retained" in text
    assert "experimental `.frd` block metadata scanner is now implemented" in text
    assert "no numerical field parser" in text
    assert "no node or element value arrays" in text
    assert "no mesh reconstruction" in text
    assert "no resultdataset write" in text
    assert "no solver execution" in text


def test_scanner_principles_are_defined() -> None:
    text = _normalized()

    assert "scanner principles" in text
    assert "explicit `.frd` files only" in text
    assert "metadata-first" in text
    assert "detect block boundaries" in text
    assert "do not infer units" in text
    assert "no external tools" in text


def test_implemented_scanner_subset_is_defined() -> None:
    text = _normalized()

    assert "implemented scanner subset" in text
    assert "file metadata" in text
    assert "block boundary candidates" in text
    assert "block kinds" in text
    assert "field-reference candidates" in text
    assert "mesh-reference candidates" in text
    assert "unsupported-block diagnostics" in text


def test_explicitly_unsupported_content_is_defined() -> None:
    text = _normalized()

    assert "explicitly unsupported" in text
    assert "node value arrays" in text
    assert "element value arrays" in text
    assert "full mesh reconstruction" in text
    assert "field array parsing" in text
    assert "binary `.frd` parsing" in text


def test_safety_limits_and_encoding_policy_are_defined() -> None:
    text = _normalized()

    assert "safety limits" in text
    assert "max_file_size_bytes" in text
    assert "max_line_count" in text
    assert "max_record_count" in text
    assert "max_block_count" in text
    assert "max_block_span" in text
    assert "encoding and format handling" in text
    assert "binary, mixed binary, or unknown encodings" in text


def test_all_fp_frd_diagnostic_codes_are_listed() -> None:
    text = _read()

    for code in REQUIRED_FP_FRD_CODES:
        assert code in text


def test_output_model_and_resultdataset_mapping_are_defined() -> None:
    text = _normalized()

    assert "scanner output model" in text
    assert "block_candidates" in text
    assert "field_reference_candidates" in text
    assert "mesh_reference_candidates" in text
    assert "unsupported_blocks" in text
    assert "resultdataset mapping" in text
    assert "candidate-only" in text
    assert "deferred field references" in text


def test_fixture_and_future_test_strategy_are_defined() -> None:
    text = _normalized()

    assert "fixture strategy" in text
    assert "no tracked solver output fixtures" in text
    assert "future test strategy" in text
    assert "block boundary detection" in text
    assert "unsupported-block diagnostics" in text
    assert "no external command invocation" in text
    assert "no resultdataset write" in text


def test_issue_8_remains_open_and_live_validation_not_claimed() -> None:
    text = _normalized()

    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()

    forbidden_claims = (
        "`.frd` parser implementation exists",
        "numerical parsing exists",
        "numerical field parsing exists",
        "mesh reconstruction exists",
        "resultdataset persistence exists",
        "live validation passed",
        "external solvers are bundled",
        "solver is bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
