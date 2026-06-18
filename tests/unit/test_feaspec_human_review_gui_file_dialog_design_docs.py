from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_file_dialog_design.md"
)


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_doc_says_design_only() -> None:
    assert "design-only" in _normalized()


def test_doc_says_no_file_dialog_implementation() -> None:
    assert "no file dialog implementation" in _normalized()


def test_doc_says_no_solver_execution() -> None:
    assert "no solver execution" in _normalized()


def test_doc_defines_file_dialog_goals() -> None:
    text = _normalized()

    assert "file-dialog goals" in text
    assert "choose review record json save path" in text
    assert "keep explicit user intent" in text


def test_doc_defines_entry_points() -> None:
    text = _normalized()

    assert "entry points" in text
    assert "save record button" in text
    assert "choose path button" in text


def test_doc_defines_default_filename_strategy() -> None:
    text = _normalized()

    assert "default filename strategy" in text
    assert "source feaspec id" in text
    assert ".human_review.json" in text
    assert "sanitize unsafe characters" in text


def test_doc_defines_json_extension_filter_policy() -> None:
    text = _normalized()

    assert "filter/extension policy" in text
    assert "json files only" in text
    assert ".human_review.json" in text
    assert "non-json extension" in text


def test_doc_defines_directory_policy() -> None:
    text = _normalized()

    assert "directory policy" in text
    assert "initial directory" in text
    assert "parent directories must already exist" in text


def test_doc_says_no_hidden_parent_creation() -> None:
    assert "no hidden parent creation" in _normalized()


def test_doc_defines_overwrite_policy() -> None:
    text = _normalized()

    assert "overwrite policy" in text
    assert "existing target prompts user" in text
    assert "there is no silent overwrite" in text


def test_doc_defines_path_safety() -> None:
    text = _normalized()

    assert "path safety" in text
    assert "no traversal" in text
    assert "no drive/path injection through filename" in text
    assert "no wildcard/control chars" in text


def test_doc_defines_save_plan_integration() -> None:
    text = _normalized()

    assert "save-plan integration" in text
    assert "selected path updates view-model/dialog save path" in text
    assert "actual write still uses existing save integration" in text


def test_doc_says_canceled_dialog_is_no_op() -> None:
    assert "canceled dialog is no-op" in _normalized()


def test_doc_says_save_writes_review_record_only() -> None:
    assert "saves review record only" in _normalized()


def test_doc_says_no_export_bundle_write() -> None:
    assert "no export bundle write" in _normalized()


def test_doc_repeats_no_solver_execution() -> None:
    assert "does not run solver" in _normalized()


def test_doc_says_no_bundled_solver() -> None:
    assert "no bundled solver" in _normalized()


def test_doc_says_no_industrial_certification() -> None:
    assert "no industrial certification" in _normalized()


def test_doc_defines_future_implementation_test_plan() -> None:
    text = _normalized()

    assert "test plan for future implementation" in text
    assert "dialog cancel" in text
    assert "selected safe path" in text
    assert "overwrite prompt accept/reject" in text
    assert "no solver/export side effects" in text


def test_doc_does_not_claim_qfiledialog_implementation_exists() -> None:
    assert "qfiledialog implementation exists" not in _normalized()


def test_doc_does_not_claim_result_import_exists() -> None:
    text = _normalized()

    assert "no result import" in text
    assert "result import implementation exists" not in text


def test_doc_does_not_claim_run_gate_exists() -> None:
    text = _normalized()

    assert "no run gate" in text
    assert "run gate implementation exists" not in text
