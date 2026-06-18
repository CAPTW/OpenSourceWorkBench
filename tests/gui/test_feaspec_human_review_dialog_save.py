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


def test_dialog_constructs_with_save_integration_available(app: object) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    assert dialog.last_save_status() == "idle"
    assert dialog.last_save_error() == ""
    assert dialog.saved_record_path() == ""
    assert dialog.save_status_label.objectName() == "oswFeaspecHumanReviewSaveStatus"


def test_save_action_disabled_when_no_save_path(app: object) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    assert "save path is required" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )
    assert dialog.trigger_save_record() is False
    assert dialog.last_save_status() == "blocked"
    assert "save path is required" in dialog.last_save_error()


def test_save_action_disabled_when_parent_directory_missing(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "missing" / "review.json"
    dialog = FEASpecHumanReviewDialog(state=_ready_state(), save_path=save_path)

    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    assert "parent directory does not exist" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )
    assert dialog.trigger_save_record() is False
    assert not save_path.parent.exists()


def test_save_action_disabled_when_record_preview_invalid(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(reviewer=""),
        save_path=tmp_path / "review.json",
    )

    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    assert "record preview invalid" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )
    assert "reviewer is required" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )


def test_save_action_enabled_when_explicit_tmp_path_is_valid(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(),
        save_path=tmp_path / "review.json",
    )

    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is True
    assert dialog.action_disabled_reason(HumanReviewDialogAction.SAVE_RECORD) == ""


def test_triggering_save_writes_exactly_one_json_review_record(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec.human_review_io import load_human_review_record
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "review.json"
    dialog = FEASpecHumanReviewDialog(state=_ready_state(), save_path=save_path)

    assert dialog.trigger_save_record() is True

    files = [path for path in tmp_path.iterdir() if path.is_file()]
    assert files == [save_path]
    record = load_human_review_record(save_path)
    assert record.source_feaspec_id == "cantilever-approved"
    assert record.solver_execution_performed is False
    assert dialog.last_save_status() == "saved"
    assert dialog.last_save_error() == ""
    assert dialog.saved_record_path() == str(save_path)
    assert str(save_path) in dialog.save_status_label.text()


def test_write_refuses_overwrite_by_default(app: object, tmp_path: Path) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "review.json"
    dialog = FEASpecHumanReviewDialog(state=_ready_state(), save_path=save_path)

    assert dialog.trigger_save_record() is True
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    assert "overwrite" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )
    first_payload = save_path.read_text(encoding="utf-8")
    assert dialog.trigger_save_record() is False
    assert save_path.read_text(encoding="utf-8") == first_payload


def test_overwrite_succeeds_only_when_overwrite_enabled(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec.human_review_io import load_human_review_record
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "review.json"
    save_path.write_text('{"existing": true}\n', encoding="utf-8")
    blocked = FEASpecHumanReviewDialog(state=_ready_state(), save_path=save_path)

    assert blocked.trigger_save_record() is False
    assert "overwrite" in blocked.last_save_error()

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(),
        save_path=save_path,
        overwrite=True,
    )
    assert dialog.trigger_save_record() is True
    assert load_human_review_record(save_path).source_feaspec_id == (
        "cantilever-approved"
    )


def test_set_save_path_and_overwrite_update_action_state(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "review.json"
    save_path.write_text("{}\n", encoding="utf-8")
    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    dialog.set_save_path(save_path)
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False

    dialog.set_overwrite_enabled(True)
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is True


def test_save_does_not_create_parent_directory(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "missing" / "review.json"
    dialog = FEASpecHumanReviewDialog(state=_ready_state(), save_path=save_path)

    assert dialog.trigger_save_record() is False
    assert not save_path.parent.exists()


def test_save_does_not_write_inp_or_export_bundle_files(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(),
        save_path=tmp_path / "review.json",
    )

    assert dialog.trigger_save_record() is True
    names = {path.name for path in tmp_path.iterdir()}
    assert names == {"review.json"}
    assert not list(tmp_path.glob("*.inp"))
    assert "manifest.json" not in names
    assert "diagnostics.json" not in names
    assert "README_RUN_FIRST.txt" not in names


def test_close_still_has_no_side_effects(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    save_path = tmp_path / "review.json"
    dialog = FEASpecHumanReviewDialog(state=_ready_state(), save_path=save_path)

    dialog.close_button.click()

    assert not save_path.exists()
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Rejected
