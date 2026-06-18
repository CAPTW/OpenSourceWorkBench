from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_import_or_run_gate_design.md"
)

REQUIRED_FR_CODES = {
    "FR_RUN_NOT_AUTHORIZED",
    "FR_EXECUTE_FLAG_REQUIRED",
    "FR_CONFIRMATION_REQUIRED",
    "FR_README_NOT_ACKNOWLEDGED",
    "FR_CCX_MISSING",
    "FR_CCX_NOT_EXECUTABLE",
    "FR_EXPORT_BUNDLE_INVALID",
    "FR_MANIFEST_MISSING",
    "FR_INP_MISSING",
    "FR_README_MISSING",
    "FR_RUN_DIR_UNSAFE",
    "FR_RUN_DIR_NOT_EMPTY",
    "FR_TIMEOUT",
    "FR_NONZERO_EXIT",
    "FR_OUTPUT_MISSING",
    "FR_FORBIDDEN_PATH",
    "FR_METADATA_WRITE_FAILED",
    "FR_PROCESS_START_FAILED",
}

REQUIRED_FI_CODES = {
    "FI_RESULT_DIR_MISSING",
    "FI_MANIFEST_MISSING",
    "FI_RUN_METADATA_MISSING",
    "FI_UNSUPPORTED_FILE",
    "FI_PARSE_FAILED",
    "FI_PARTIAL_IMPORT",
    "FI_NO_PRIMARY_RESULT",
    "FI_PROVENANCE_INCOMPLETE",
}


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_result_import_run_gate_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_design_status_and_non_implementation_scope() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no result import implementation" in text
    assert "no run gate implementation" in text
    assert "no solver execution" in text


def test_export_review_run_import_are_separate_gates() -> None:
    text = _normalized()

    assert "export, review, run, and import are separate gates" in text
    assert "no automatic unreviewed solver execution" in text
    assert "the no-run export boundary must not implicitly trigger `ccx`" in text


def test_installed_only_run_gate_preconditions() -> None:
    text = _normalized()

    assert "the user explicitly requests the run gate" in text
    assert "`ccx` is installed and discovered" in text
    assert "no hidden solver install" in text
    assert "installed-only" in text
    assert "short timeout" in text


def test_run_gate_outputs_and_diagnostics() -> None:
    text = _read()
    normalized = _normalized()

    assert "run metadata JSON" in text
    assert "stdout and stderr logs" in text
    assert "exit code" in normalized
    assert "generated CalculiX files if any" in text
    assert "no tracked solver outputs" in normalized
    for code in REQUIRED_FR_CODES:
        assert code in text


def test_result_import_boundary_and_inputs() -> None:
    text = _read()
    normalized = _normalized()

    assert "result import may import only from an explicit result directory" in normalized
    assert "result import does not execute solver commands" in normalized
    assert ".dat" in text
    assert ".frd" in text
    assert ".sta" in text
    assert ".cvg" in text
    assert "stdout/stderr logs" in text
    assert "export manifest" in normalized
    assert "run metadata" in normalized


def test_result_import_outputs_and_diagnostics() -> None:
    text = _read()
    normalized = _normalized()

    assert "ResultDataset draft" in text
    assert "solver run summary" in normalized
    assert "artifact manifest" in normalized
    assert "parser diagnostics" in normalized
    assert "provenance links to FEASpec, export, and run metadata" in text
    for code in REQUIRED_FI_CODES:
        assert code in text


def test_result_dataset_mapping_is_defined() -> None:
    normalized = _normalized()

    assert "resultdataset mapping" in normalized
    assert "scalar summaries" in normalized
    assert "tables" in normalized
    assert "artifacts" in normalized
    assert "field references" in normalized
    assert "provenance links" in normalized
    assert "limitations" in normalized


def test_issue_8_remains_open_until_installed_only_validation() -> None:
    text = _normalized()

    assert "issue `#8` remains open until installed-only `ccx` validation passes" in text
    assert "does not run live optional validation" in text
    assert "does not record issue `#8` pass evidence" in text
    assert "does not close issue `#8`" in text


def test_cli_separation_is_documented() -> None:
    text = _read()
    normalized = _normalized()

    assert "feaspec-calculix-run-installed-only" in text
    assert "feaspec-calculix-result-import-preview" in text
    assert "run command has since landed as the installed-only gate" in normalized
    assert "result import model and a preview-only cli have landed" in normalized
    assert "write-capable result import command remains future only" in normalized
    assert "this design gate did not implement those follow-up commands" in normalized


def test_design_doc_does_not_claim_forbidden_maturity() -> None:
    text = _read().lower()
    forbidden_claims = (
        "ccx validation has passed",
        "result import implementation exists",
        "run gate implementation exists",
        "industrial certification is provided",
        "external solvers are bundled",
        "solver execution exists",
        "stable production",
    )
    for claim in forbidden_claims:
        assert claim not in text
