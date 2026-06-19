from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultMetadataLimits,
    CalculiXResultParserDiagnosticCode,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "experimental" / "feaspec_calculix_result_metadata_scanner.md"
PARSER_DOC_PATH = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_calculix_result_parser_design.md"
)
SCAN_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_result_metadata_scanner.py"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).lower().split())


def test_metadata_scanner_doc_exists_with_required_scope() -> None:
    assert DOC_PATH.exists()

    text = _normalized(DOC_PATH)

    assert "metadata scanner" in text
    assert "metadata-only" in text
    assert "design-only" not in text
    assert "no numerical parser" in text
    assert "no resultdataset write" in text
    assert "no solver execution" in text
    assert "no external command" in text
    assert "no subprocess" in text
    assert "issue `#8` remains open" in text


def test_parser_guardrails_do_not_claim_numerical_capability_or_certification() -> None:
    text = _normalized(PARSER_DOC_PATH)

    assert "does not implement" in text
    assert "no broad numerical parser" in text
    assert "no resultdataset write" in text
    assert "no solver execution" in text
    assert "issue `#8` remains open" in text

    forbidden_claims = (
        "numerical parser exists",
        "result parsing exists",
        "resultdataset persistence exists",
        "live validation passed",
        "industrial certification is provided",
        "solver execution exists",
        "external solvers are bundled",
    )
    for claim in forbidden_claims:
        assert claim not in text


def test_metadata_scanner_lists_required_diagnostic_codes() -> None:
    text = _read(DOC_PATH)

    for code in CalculiXResultParserDiagnosticCode:
        assert code.value in text


def test_metadata_limits_are_documented() -> None:
    limits = CalculiXResultMetadataLimits()
    text = _normalized(DOC_PATH)

    assert str(limits.max_file_bytes) in text
    assert str(limits.max_lines) in text
    assert str(limits.max_snippet_chars) in text
    assert str(limits.max_snippet_lines) in text
    assert "no recursion" in text


def test_metadata_scanner_does_not_import_solver_or_run_commands() -> None:
    source = SCAN_SOURCE.read_text(encoding="utf-8").lower()
    forbidden_tokens = (
        "solveradapter",
        "calculixrunner",
        "run_registered",
        "subprocess",
        "popen(",
        "os.system",
        "ccx.exe",
        "requests",
        "socket",
        "openai",
        "write_text(",
        "write_bytes(",
        "mkdir(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_scanner_and_parser_docs_do_not_allow_vlm_or_credentials() -> None:
    combined = (_normalized(DOC_PATH) + " " + _normalized(PARSER_DOC_PATH))

    assert "vlm api" not in combined
    assert "api key" not in combined
    assert "credentials" not in combined


def test_scanner_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    source = (
        (
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_metadata_scanner.py"
        ).read_text(encoding="utf-8")
        + "\n"
        + (
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_metadata_scanner_limits.py"
        ).read_text(encoding="utf-8")
    )

    assert "tmp_path" in source
    assert "fixtures/calculix" not in source
    assert "tests/fixtures" not in source
