from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_parser_design.md"
)

REQUIRED_FP_CODES = {
    "FP_FILE_MISSING",
    "FP_PATH_NOT_FILE",
    "FP_UNSUPPORTED_FORMAT",
    "FP_SIZE_LIMIT_EXCEEDED",
    "FP_LINE_LIMIT_EXCEEDED",
    "FP_SNIPPET_TRUNCATED",
    "FP_HASH_FAILED",
    "FP_ENCODING_UNSUPPORTED",
    "FP_PARSE_NOT_IMPLEMENTED",
    "FP_METADATA_ONLY",
    "FP_PARTIAL_PARSE",
    "FP_UNSUPPORTED_SECTION",
    "FP_UNSUPPORTED_RESULT_BLOCK",
    "FP_NUMERIC_CONVERSION_FAILED",
    "FP_NO_PRIMARY_FIELD",
    "FP_UNITS_MISSING",
    "FP_PROVENANCE_MISSING",
    "FP_SOLVER_RUN_FAILED",
    "FP_FORBIDDEN_PATH",
    "FP_EXTERNAL_COMMAND_FORBIDDEN",
    "FP_RESULT_DATASET_WRITE_FORBIDDEN",
}


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_result_parser_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_design_status_and_no_implementation_scope() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "does not implement" in text
    assert "no numerical parser implementation" in text
    assert "no resultdataset write" in text
    assert "does not execute calculix" in text
    assert "no solver execution" in text


def test_parser_principles_are_declared() -> None:
    text = _normalized()

    assert "parser principles" in text
    assert "explicit input files" in text
    assert "no external command invocation" in text
    assert "no silent unit inference" in text
    assert "deterministic diagnostics" in text


def test_safety_limits_are_documented() -> None:
    text = _normalized()

    assert "safety limits" in text
    assert "max_file_size_bytes" in text
    assert "max_line_count" in text
    assert "max_record_count" in text
    assert "encoding_policy" in text
    assert "no timeout needed" in text


def test_parser_phases_are_documented() -> None:
    text = _normalized()

    assert "parser phases" in text
    assert "phase 0 metadata scanner" in text
    assert "phase 1 `.sta` / `.cvg` status summary scanner" in _read().lower()
    assert "phase 2 `.dat` text summary/table scanner" in _read().lower()
    assert "phase 3 `.frd` field/block scanner" in _read().lower()


def test_sta_cvg_scanner_plan_is_defined() -> None:
    text = _normalized()

    assert "`.sta` / `.cvg`" in text
    assert "unsupported format variants" in text


def test_dat_parser_plan_is_defined() -> None:
    text = _normalized()

    assert "phase 2 `.dat`" in text
    assert "controlled educational linear-static subset" in text
    assert "table candidates" in text


def test_frd_parser_plan_is_defined() -> None:
    text = _normalized()

    assert "phase 3 `.frd`" in text
    assert "field/block" in text
    assert "no full mesh rebuild" in text


def test_no_silent_unit_inference() -> None:
    text = _normalized()

    assert "no unit inference from token shape" in text
    assert "missing units are emitted" in text


def test_all_fp_diagnostic_codes_are_listed() -> None:
    text = _read()

    for code in REQUIRED_FP_CODES:
        assert code in text


def test_parser_output_model_and_dataset_mapping_defined() -> None:
    text = _normalized()

    assert "parser output model" in text
    assert "scalar_candidates" in text
    assert "table_candidates" in text
    assert "field_references" in text
    assert "artifact_references" in text
    assert "resultdataset mapping" in text


def test_fixture_and_test_strategy_are_defined_without_runtime_artifacts() -> None:
    text = _normalized()

    assert "no tracked solver output fixtures" in text
    assert "fixture strategy" in text
    assert "test strategy" in text
    assert "solver-free" in text
    assert "future parser implementation tests" in text


def test_issue_8_remains_open_and_no_validation_claims() -> None:
    text = _normalized()

    assert "issue `#8` remains open." in text
    assert "live validations remain separate" in text


def test_parser_design_does_not_claim_not_allowed_capabilities() -> None:
    text = _normalized()

    forbidden = (
        "numerical parser exists",
        "result parsing exists",
        "resultdataset persistence exists",
        "live validation passed",
        "industrial certification is provided",
        "solver execution exists",
        "result parser exists",
    )
    for token in forbidden:
        assert token not in text
