from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _validator_summary() -> dict[str, object]:
    return {
        "has_blockers": False,
        "has_errors": False,
        "diagnostics": [],
    }


def _ready_state(**overrides: object):
    from osw.experimental.feaspec import (
        HumanReviewDialogAction,
        build_human_review_dialog_state,
    )

    kwargs = {
        "source_feaspec_id": "cantilever-approved",
        "reviewer": "reviewer@example.test",
        "reviewed_at": "2026-06-18T00:00:00Z",
        "notes": ("reviewed and approved for no-run export evidence",),
        "desired_action": HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT,
        "validator_summary": _validator_summary(),
        "validator_report_hash": "sha256:validator",
        "bridge_summary": {"status": "ready"},
        "case_plan_summary": {"status": "ready"},
        "export_preview_summary": {"status": "ready"},
        "export_write_summary": {"status": "not-written"},
    }
    kwargs.update(overrides)
    return build_human_review_dialog_state(**kwargs)


def _dialog(*, selected: object = "", confirm: bool = False, state: object | None = None):
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    return FEASpecHumanReviewDialog(
        state=state or _ready_state(),
        save_path_dialog_provider=lambda _title, _default, _filter: selected,
        overwrite_confirmation_provider=lambda _path: confirm,
    )


def test_dialog_exposes_choose_save_path_action(app: object) -> None:
    dialog = _dialog()

    assert hasattr(dialog, "choose_review_record_save_path")
    assert dialog.choose_save_path_button.objectName() == (
        "oswFeaspecHumanReviewChooseSavePathButton"
    )
    assert dialog.review_record_file_filter() == (
        "FEASpec human review records (*.human_review.json *.json);;JSON files (*.json)"
    )


def test_choose_path_cancel_is_no_op_and_writes_no_files(
    app: object,
    tmp_path: Path,
) -> None:
    save_path = tmp_path / "existing.json"
    dialog = _dialog(selected="", state=_ready_state())
    before = dialog.current_save_path()

    assert dialog.choose_review_record_save_path() is False

    assert dialog.current_save_path() == before
    assert dialog.last_save_status() == "canceled"
    assert dialog.last_save_error() == ""
    assert not save_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_default_filename_uses_sanitized_source_feaspec_id(app: object) -> None:
    dialog = _dialog(state=_ready_state(source_feaspec_id="beam #1 / load:A"))

    assert dialog.suggested_review_record_filename() == (
        "beam-1-load-A.human_review.json"
    )
    assert dialog.default_review_record_save_path().endswith(
        "beam-1-load-A.human_review.json"
    )


def test_default_filename_falls_back_for_unsafe_or_missing_source_id(
    app: object,
) -> None:
    missing = _dialog(state=_ready_state(source_feaspec_id=""))
    unsafe = _dialog(state=_ready_state(source_feaspec_id="../.."))

    assert missing.suggested_review_record_filename() == (
        "feaspec-human-review.human_review.json"
    )
    assert unsafe.suggested_review_record_filename() == (
        "feaspec-human-review.human_review.json"
    )


def test_selected_path_updates_save_path_and_action_state(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction

    save_path = tmp_path / "review.human_review.json"
    dialog = _dialog(selected=(str(save_path), "JSON files (*.json)"))

    assert dialog.choose_review_record_save_path() is True

    assert dialog.current_save_path() == str(save_path)
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is True
    assert dialog.last_save_status() == "selected"


def test_selected_path_without_suffix_gains_human_review_json_suffix(
    app: object,
    tmp_path: Path,
) -> None:
    dialog = _dialog(selected=str(tmp_path / "review"))

    assert dialog.choose_review_record_save_path() is True

    assert dialog.current_save_path() == str(tmp_path / "review.human_review.json")


def test_selected_path_with_non_json_suffix_is_rejected(
    app: object,
    tmp_path: Path,
) -> None:
    dialog = _dialog(selected=str(tmp_path / "review.txt"))

    assert dialog.choose_review_record_save_path() is False

    assert dialog.current_save_path() == ""
    assert dialog.last_save_status() == "error"
    assert "must use a .json path" in dialog.last_save_error()
    assert list(tmp_path.iterdir()) == []


def test_selected_missing_parent_does_not_create_directory_and_disables_save(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction

    save_path = tmp_path / "missing" / "review.json"
    dialog = _dialog(selected=str(save_path))

    assert dialog.choose_review_record_save_path() is False

    assert dialog.current_save_path() == str(save_path)
    assert not save_path.parent.exists()
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    assert "parent directory does not exist" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )


def test_existing_file_requires_overwrite_confirmation_reject_noop(
    app: object,
    tmp_path: Path,
) -> None:
    save_path = tmp_path / "review.json"
    save_path.write_text('{"existing": true}\n', encoding="utf-8")
    dialog = _dialog(selected=str(save_path), confirm=False)

    assert dialog.choose_review_record_save_path() is False

    assert dialog.current_save_path() == ""
    assert dialog.last_save_status() == "canceled"
    assert save_path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_existing_file_overwrite_accept_enables_save_path(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction

    save_path = tmp_path / "review.json"
    save_path.write_text('{"existing": true}\n', encoding="utf-8")
    dialog = _dialog(selected=str(save_path), confirm=True)

    assert dialog.choose_review_record_save_path() is True

    assert dialog.current_save_path() == str(save_path)
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is True


def test_save_after_selected_path_writes_exactly_one_review_json(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec.human_review_io import load_human_review_record

    save_path = tmp_path / "review.human_review.json"
    dialog = _dialog(selected=str(save_path))

    assert dialog.choose_review_record_save_path() is True
    assert dialog.trigger_save_record() is True

    assert [path.name for path in tmp_path.iterdir()] == ["review.human_review.json"]
    record = load_human_review_record(save_path)
    assert record.source_feaspec_id == "cantilever-approved"
    assert record.solver_execution_performed is False


def test_choose_path_alone_writes_no_inp_or_export_bundle_files(
    app: object,
    tmp_path: Path,
) -> None:
    dialog = _dialog(selected=str(tmp_path / "review.json"))

    assert dialog.choose_review_record_save_path() is True

    assert list(tmp_path.iterdir()) == []
    assert not list(tmp_path.glob("*.inp"))
    assert not (tmp_path / "manifest.json").exists()
    assert not (tmp_path / "diagnostics.json").exists()
    assert not (tmp_path / "README_RUN_FIRST.txt").exists()


def test_mocked_provider_prevents_native_file_dialog_usage(
    app: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert QtWidgets is not None

    def fail_native_dialog(*_args: object, **_kwargs: object) -> tuple[str, str]:
        raise AssertionError("native dialog should not be called")

    monkeypatch.setattr(QtWidgets.QFileDialog, "getSaveFileName", fail_native_dialog)
    dialog = _dialog(selected=str(tmp_path / "review.json"))

    assert dialog.choose_review_record_save_path() is True


def test_selected_path_rejects_inp_suffix(
    app: object,
    tmp_path: Path,
) -> None:
    dialog = _dialog(selected=str(tmp_path / "model.inp.json"))

    assert dialog.choose_review_record_save_path() is False

    assert dialog.current_save_path() == ""
    assert "must not target .inp files" in dialog.last_save_error()
