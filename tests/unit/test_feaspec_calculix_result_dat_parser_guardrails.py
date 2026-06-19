from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs/experimental/feaspec_calculix_result_dat_parser.md"
SOURCE_PATH = ROOT / "src/osw/experimental/feaspec/calculix_result_dat_parser.py"


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8").lower()


def _source_text() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def test_dat_minimal_parser_docs_lock_safety_boundary() -> None:
    text = _doc_text()

    assert "minimal parser" in text
    assert "bounded known sections only" in text
    assert "no free-form parser" in text
    assert "no `.frd` parser" in text
    assert "no resultdataset write" in text
    assert "no solver execution" in text
    assert "issue #8 remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text


def test_dat_minimal_parser_docs_do_not_claim_forbidden_capabilities() -> None:
    text = _doc_text()

    forbidden_claims = [
        "broad `.dat` parser exists",
        "`.frd` parser exists",
        "unit inference exists",
        "resultdataset persistence exists",
        "solver execution is allowed",
        "ccx validation has passed",
        "issue #8 can close",
        "external solvers are bundled",
        "industrial certification provided",
    ]
    for claim in forbidden_claims:
        assert claim not in text


def test_dat_minimal_parser_source_has_no_forbidden_execution_or_write_paths() -> None:
    source = _source_text().lower()

    forbidden_tokens = [
        "subprocess",
        "solveradapter",
        "runner",
        "ccx",
        "openai",
        "anthropic",
        "gemini",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
    ]
    for token in forbidden_tokens:
        assert token not in source


def test_dat_minimal_parser_source_does_not_infer_units_or_parse_frd() -> None:
    source = _source_text().lower()

    forbidden_tokens = [
        "infer_unit",
        "guess_unit",
        "parse_frd",
        "mesh_reconstruction",
        "field_reconstruction",
    ]
    for token in forbidden_tokens:
        assert token not in source
    assert "units_inferred: bool = false" in source
    assert "frd_parser: bool = false" in source
    assert "freeform_parser: bool = false" in source


def test_dat_minimal_parser_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    combined = "\n".join(
        [
            (ROOT / "tests/unit/test_feaspec_calculix_result_dat_parser.py").read_text(
                encoding="utf-8"
            ),
            (
                ROOT / "tests/unit/test_feaspec_calculix_result_dat_parser_limits.py"
            ).read_text(encoding="utf-8"),
        ]
    )

    assert "tmp_path" in combined
    assert "fixtures/calculix" not in combined
    assert "tests/fixtures" not in combined
