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


def _write_viewmodel(
    tmp_path: Path,
    *,
    writer_result_summary: dict[str, object] | None = None,
):
    from osw.experimental.feaspec import (
        FEASpecCalculiXResultWriteAcknowledgementState,
        build_calculix_result_write_viewmodel,
    )

    result_dir = tmp_path / "result"
    output_dir = tmp_path / "dataset"
    planned_files = [
        {"relative_path": "result_dataset.json", "exists": False},
        {"relative_path": "result_dataset_manifest.json", "exists": False},
        {"relative_path": "diagnostics.json", "exists": False},
        {"relative_path": "provenance.json", "exists": False},
        {"relative_path": "README_REVIEW_FIRST.txt", "exists": False},
    ]
    return build_calculix_result_write_viewmodel(
        {
            "status": "ready",
            "result_dir": str(result_dir),
            "artifacts": [
                {"path": "case.dat", "suffix": ".dat"},
                {"path": "case.frd", "suffix": ".frd"},
            ],
            "diagnostics": [],
            "limitations": ["Parser summaries require human review."],
        },
        draft_mapping={
            "status": "ready",
            "dataset_id": "dialog_dataset",
            "source": "feaspec-calculix",
            "artifacts": [{"path": "case.dat"}],
            "scalar_candidates": [{"name": "total_energy"}],
            "table_candidates": [{"name": "displacements"}],
            "field_references": [{"name": "DISP"}],
            "diagnostics": [],
            "limitations": ["Field references are preview-only."],
        },
        write_plan={
            "status": "ready",
            "target": {
                "output_dir": str(output_dir),
                "parent_exists": True,
                "target_exists": False,
            },
            "planned_files": planned_files,
            "artifact_references": [{"path": "case.frd"}],
            "limitations_acknowledged": True,
            "copy_artifacts_requested": False,
            "diagnostics": [],
        },
        schema_payload={
            "status": "ready",
            "schema": {"schema_name": "ResultDataset", "schema_version": "0.1"},
            "dataset": {"dataset_id": "dialog_dataset"},
            "planned_files": planned_files,
            "limitations": ["Review before use."],
            "schema_diagnostics": [],
        },
        writer_result_summary=writer_result_summary,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )


def test_dialog_imports_from_module_and_dialog_package(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs import FEASpecCalculiXResultWriteDialog as PackageDialog
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_write_viewmodel(tmp_path))

    assert PackageDialog is FEASpecCalculiXResultWriteDialog
    assert dialog.objectName() == "oswFeaspecCalculixResultWriteDialog"
    assert dialog.windowTitle() == "FEASpec CalculiX ResultDataset Write"


def test_dialog_constructs_required_panels(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_write_viewmodel(tmp_path))

    assert dialog.header_label.objectName() == "oswFeaspecCalculixResultWriteHeader"
    assert dialog.tabs.objectName() == "oswFeaspecCalculixResultWriteTabs"
    assert set(dialog.panel_titles()) == {
        "Source",
        "Artifacts",
        "Diagnostics",
        "Draft Mapping",
        "Write Plan",
        "Schema / Manifest",
        "Safety / Limitations",
        "Actions",
        "Result",
    }
    assert dialog.source_panel.objectName() == (
        "oswFeaspecCalculixResultWriteSourcePanel"
    )
    assert dialog.actions_panel.objectName() == (
        "oswFeaspecCalculixResultWriteActionsPanel"
    )


def test_dialog_renders_viewmodel_summary(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_write_viewmodel(tmp_path))

    assert "dialog_dataset" in dialog.draft_mapping_panel.toPlainText()
    assert "ResultDataset 0.1" in dialog.schema_panel.toPlainText()
    assert "result_dataset.json" in dialog.planned_files_text()
    assert "Parser summaries require human review" in dialog.artifact_panel.toPlainText()
    assert "No diagnostics" in dialog.diagnostics_text()


def test_dialog_renders_safety_and_acknowledgements(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_write_viewmodel(tmp_path))
    safety = dialog.safety_text()

    assert "Experimental FEASpec CalculiX ResultDataset write dialog." in safety
    assert "directory-only QFileDialog" in safety
    assert "Writer calls require enabled gates" in safety
    assert "existing library writer" in safety
    assert "No directory creation during selection." in safety
    assert "No solver execution." in safety
    assert (
        "GitHub state verified 2026-07-14: Issue #8 is closed after bounded WSL "
        "CalculiX evidence; this workflow does not broaden that closure."
    ) in safety
    assert "External solvers are optional and not bundled." in safety
    assert "No industrial certification" in safety
    assert "Limitations acknowledged" in dialog.acknowledgement_text()
    assert "Human review required acknowledged" in dialog.acknowledgement_text()


def test_dialog_renders_writer_result_summary_without_invocation(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(
        _write_viewmodel(
            tmp_path,
            writer_result_summary={
                "status": "written",
                "target_dir": str(tmp_path / "dataset"),
                "written_files": [{"relative_path": "result_dataset.json"}],
            },
        )
    )

    assert '"status": "written"' in dialog.result_summary_text()
    assert "result_dataset.json" in dialog.result_summary_text()
    assert dialog.write_invocation_count() == 0
