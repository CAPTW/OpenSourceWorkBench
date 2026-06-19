from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_dat_minimal_parser_design.md"
)

REQUIRED_FP_DAT_CODES = {
    "FP_DAT_PARSE_NOT_IMPLEMENTED",
    "FP_DAT_SECTION_UNSUPPORTED",
    "FP_DAT_TABLE_HEADER_UNSUPPORTED",
    "FP_DAT_TABLE_TOO_LARGE",
    "FP_DAT_ROW_LIMIT_EXCEEDED",
    "FP_DAT_COLUMN_LIMIT_EXCEEDED",
    "FP_DAT_NUMERIC_VALUE_UNPARSED",
    "FP_DAT_NUMERIC_CONVERSION_FAILED",
    "FP_DAT_UNITS_MISSING",
    "FP_DAT_AMBIGUOUS_UNIT_CONTEXT",
    "FP_DAT_EMPTY_SECTION",
    "FP_DAT_PARTIAL_PARSE",
    "FP_DAT_PROVENANCE_MISSING",
    "FP_DAT_RESULT_DATASET_WRITE_FORBIDDEN",
}


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_dat_minimal_design_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_forbidden_capabilities_are_explicit() -> None:
    text = _normalized()

    assert "design baseline retained" in text
    assert "bounded minimal parser implemented" in text
    assert "no free-form `.dat` parser" in text
    assert "no `.frd` parser" in text
    assert "no unit inference" in text
    assert "no resultdataset write" in text
    assert "no solver execution" in text


def test_parser_principles_are_defined() -> None:
    text = _normalized()

    assert "parser principles" in text
    assert "explicit `.dat` files only" in text
    assert "bounded text subset" in text
    assert "known headings" in text
    assert "no engineering correctness claims" in text


def test_minimum_supported_future_subset_is_defined() -> None:
    text = _normalized()

    assert "minimum supported future subset" in text
    assert "file metadata/header summary" in text
    assert "known small scalar summary sections" in text
    assert "known small text tables" in text
    assert "unsupported-section diagnostics" in text


def test_explicitly_unsupported_content_is_defined() -> None:
    text = _normalized()

    assert "explicitly unsupported" in text
    assert "free-form unknown tables" in text
    assert "ambiguous unitless numeric values" in text
    assert "mesh reconstruction" in text
    assert "`.frd` data" in text


def test_safety_limits_are_defined() -> None:
    text = _normalized()

    assert "safety limits" in text
    assert "max_file_size_bytes" in text
    assert "max_line_count" in text
    assert "max_table_rows" in text
    assert "max_columns" in text
    assert "max_scalar_candidates" in text
    assert "max_unsupported_snippets" in text


def test_no_silent_unit_inference() -> None:
    text = _normalized()

    assert "no unit inference" in text
    assert "missing units produce diagnostics" in text
    assert "ambiguous unit context" in text


def test_all_fp_dat_diagnostic_codes_are_listed() -> None:
    text = _read()

    for code in REQUIRED_FP_DAT_CODES:
        assert code in text


def test_parser_output_model_and_resultdataset_mapping_are_defined() -> None:
    text = _normalized()

    assert "parser output model" in text
    assert "scalar_candidates" in text
    assert "table_candidates" in text
    assert "unsupported_sections" in text
    assert "resultdataset mapping" in text
    assert "field references remain `.frd` block-scanner work" in text


def test_fixture_and_future_test_strategy_are_defined() -> None:
    text = _normalized()

    assert "fixture strategy" in text
    assert "no tracked solver output fixtures" in text
    assert "future implementation tests" in text
    assert "known heading accepted" in text
    assert "unknown heading rejected" in text
    assert "no external command invocation" in text


def test_issue_8_remains_open_and_live_validation_not_claimed() -> None:
    text = _normalized()

    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()

    forbidden_claims = (
        "free-form `.dat` parser exists",
        "broad `.dat` parser exists",
        "`.frd` parser exists",
        "unit inference exists",
        "numerical result parsing exists",
        "resultdataset persistence exists",
        "live validation passed",
        "external solvers are bundled",
        "solver is bundled",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
