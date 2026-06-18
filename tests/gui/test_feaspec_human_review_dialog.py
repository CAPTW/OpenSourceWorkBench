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


def _validator_summary(
    *,
    blockers: bool = False,
    errors: bool = False,
    diagnostics: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "has_blockers": blockers,
        "has_errors": errors,
        "diagnostics": diagnostics or [],
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
        "notes": ("reviewed source drawing and generated evidence",),
        "desired_action": HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT,
        "validator_summary": _validator_summary(),
        "validator_report_hash": "sha256:validator",
        "bridge_summary": {"status": "ready", "nodes": 4},
        "case_plan_summary": {"status": "ready", "ready_for_inp_writer": True},
        "export_preview_summary": {"status": "previewed", "format": "calculix"},
        "export_write_summary": {"status": "not-written"},
    }
    kwargs.update(overrides)
    return build_human_review_dialog_state(**kwargs)


def test_dialog_imports_from_module_and_dialog_package(app: object) -> None:
    from osw.gui.dialogs import FEASpecHumanReviewDialog as PackageDialog
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    assert PackageDialog is FEASpecHumanReviewDialog
    assert dialog.objectName() == "oswFeaspecHumanReviewDialog"
    assert dialog.windowTitle() == "FEASpec Human Review"


def test_dialog_constructs_required_panels(app: object) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    assert dialog.header_label.objectName() == "oswFeaspecHumanReviewHeader"
    assert dialog.tabs.objectName() == "oswFeaspecHumanReviewTabs"
    assert dialog.source_panel.objectName() == "oswFeaspecHumanReviewSourcePanel"
    assert dialog.diagnostics_panel.objectName() == (
        "oswFeaspecHumanReviewDiagnosticsPanel"
    )
    assert dialog.diagnostics_table.objectName() == (
        "oswFeaspecHumanReviewDiagnosticsTable"
    )
    assert dialog.warning_list.objectName() == "oswFeaspecHumanReviewWarningList"
    assert dialog.engineering_panel.objectName() == (
        "oswFeaspecHumanReviewEngineeringPanel"
    )
    assert dialog.export_preview_panel.objectName() == (
        "oswFeaspecHumanReviewExportPreviewPanel"
    )
    assert dialog.review_actions_panel.objectName() == (
        "oswFeaspecHumanReviewActionsPanel"
    )
    assert dialog.safety_panel.objectName() == "oswFeaspecHumanReviewSafetyPanel"
    assert dialog.record_preview_panel.objectName() == (
        "oswFeaspecHumanReviewRecordPreviewPanel"
    )
    assert set(dialog.panel_names()) == {
        "source_evidence",
        "diagnostics",
        "engineering_summary",
        "export_preview",
        "review_actions",
        "safety_limitations",
        "record_preview",
    }


def test_source_engineering_export_and_record_preview_render(app: object) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    assert "cantilever-approved" in dialog.source_panel.toPlainText()
    assert "reviewer@example.test" in dialog.source_panel.toPlainText()
    assert "sha256:validator" in dialog.source_panel.toPlainText()
    assert '"nodes": 4' in dialog.engineering_panel.toPlainText()
    assert '"format": "calculix"' in dialog.export_preview_panel.toPlainText()
    assert "cantilever-approved" in dialog.record_preview_text()
    assert '"solver_execution_performed": false' in dialog.record_preview_text()


def test_diagnostics_table_renders_rows_and_blocker_acceptance(app: object) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    state = _ready_state(
        validator_summary=_validator_summary(
            diagnostics=[
                {
                    "code": "FS_CONFIDENCE_LOW",
                    "severity": "warning",
                    "message": "Review inferred load direction.",
                    "target_ref": "load:L1",
                },
                {
                    "code": "FV_BOUNDARY_BLOCKER",
                    "severity": "error",
                    "message": "Boundary target is invalid.",
                    "target_ref": "bc:B1",
                    "blocks_approval": True,
                },
            ],
        )
    )
    dialog = FEASpecHumanReviewDialog(state=state)

    assert dialog.diagnostic_row_count() == 2
    assert dialog.diagnostics_table.item(0, 1).text() == "FS_CONFIDENCE_LOW"
    assert dialog.diagnostics_table.item(0, 4).text() == "yes"
    assert dialog.diagnostics_table.item(1, 1).text() == "FV_BOUNDARY_BLOCKER"
    assert dialog.diagnostics_table.item(1, 4).text() == "no"


def test_warning_rows_render_reason_required_state(app: object) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(
            validator_summary=_validator_summary(
                diagnostics=[
                    {
                        "code": "FS_CONFIDENCE_LOW",
                        "severity": "warning",
                        "message": "Review confidence.",
                    }
                ]
            )
        )
    )

    assert dialog.warning_row_count() == 1
    warning_text = dialog.warning_list.item(0).text()
    assert "FS_CONFIDENCE_LOW" in warning_text
    assert "reason required" in warning_text
    assert "not accepted" in warning_text


def test_action_buttons_and_disabled_reasons_are_visible(app: object) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(
            reviewer="",
            validator_summary=_validator_summary(
                diagnostics=[
                    {
                        "code": "FV_BOUNDARY_BLOCKER",
                        "severity": "error",
                        "message": "Boundary target is invalid.",
                        "blocks_approval": True,
                    }
                ]
            ),
        )
    )

    assert dialog.action_enabled(HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT) is False
    disabled_reason = dialog.action_disabled_reason(
        HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT
    )
    assert "missing reviewer" in disabled_reason
    assert "blocker diagnostics exist" in disabled_reason
    assert dialog.action_enabled(HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN) is False
    assert "missing no-run export acknowledgement" in dialog.action_disabled_reason(
        HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN
    )
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    assert "save path is required" in dialog.action_disabled_reason(
        HumanReviewDialogAction.SAVE_RECORD
    )
    summary_items = [
        dialog.action_summary.item(index).text()
        for index in range(dialog.action_summary.count())
    ]
    assert any("approve_no_run_export: disabled" in item for item in summary_items)


def test_enabled_actions_remain_viewmodel_driven_except_save(app: object) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(
        state=_ready_state(
            limitations_acknowledged=True,
            no_run_export_review_acknowledged=True,
            run_gate_separation_acknowledged=True,
        )
    )

    assert dialog.action_enabled(HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT) is True
    assert dialog.action_enabled(HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN) is True
    assert dialog.action_enabled(HumanReviewDialogAction.PREVIEW_RECORD) is True
    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False


def test_safety_copy_states_no_side_effect_boundaries(app: object) -> None:
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    dialog = FEASpecHumanReviewDialog(state=_ready_state())
    text = dialog.safety_text()

    assert "Experimental prerelease human-review dialog." in text
    assert "No solver execution." in text
    assert "No ccx invocation." in text
    assert "No result import or installed-only run gate implementation." in text
    assert "External solvers are optional and not bundled." in text
    assert "Issue #8 live validation remains separate." in text
    assert "No industrial certification or production accuracy claim." in text
    assert "Record save uses an explicit JSON path only; no file dialog." in text
    assert "Record save does not write export bundles, .inp files, or solver outputs." in text


def test_close_and_disabled_buttons_do_not_write_files(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import HumanReviewDialogAction
    from osw.gui.dialogs.feaspec_human_review_dialog import (
        FEASpecHumanReviewDialog,
    )

    sentinel = tmp_path / "review.json"
    dialog = FEASpecHumanReviewDialog(state=_ready_state())

    assert dialog.action_enabled(HumanReviewDialogAction.SAVE_RECORD) is False
    dialog.close_button.click()

    assert not sentinel.exists()
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Rejected
