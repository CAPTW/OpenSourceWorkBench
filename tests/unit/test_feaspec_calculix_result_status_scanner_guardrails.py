from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs/experimental/feaspec_calculix_result_status_scanner.md"
SOURCE_PATH = (
    ROOT / "src/osw/experimental/feaspec/calculix_result_status_scanner.py"
)


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8").lower()


def _source_text() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def test_status_scanner_docs_lock_safety_boundary() -> None:
    text = _doc_text()

    assert "status scanner" in text
    assert "no numerical parser" in text
    assert "no numeric convergence parsing" in text
    assert "no resultdataset write" in text
    assert "no solver execution" in text
    assert "issue #8 remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text


def test_status_scanner_docs_do_not_claim_forbidden_capabilities() -> None:
    text = _doc_text()

    forbidden_claims = [
        "numerical result parsing exists",
        "numeric convergence values are parsed",
        "resultdataset persistence exists",
        "solver execution is allowed",
        "ccx validation has passed",
        "issue #8 can close",
        "bundled solver included",
        "industrial certification provided",
    ]
    for claim in forbidden_claims:
        assert claim not in text


def test_status_scanner_source_has_no_forbidden_execution_or_write_paths() -> None:
    source = _source_text()

    forbidden_tokens = [
        "subprocess",
        "SolverAdapter",
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


def test_status_scanner_source_does_not_parse_numeric_values() -> None:
    source = _source_text()

    assert "float(" not in source
    assert "Decimal(" not in source
    assert "numeric_tokens_not_parsed" in source
