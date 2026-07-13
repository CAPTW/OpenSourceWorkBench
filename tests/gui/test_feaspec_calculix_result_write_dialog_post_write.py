from __future__ import annotations

import importlib.util
import json
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


class _FakeWriter:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.calls: list[tuple[object, object, bool]] = []

    def __call__(
        self,
        write_plan: object,
        schema_payload: object,
        *,
        overwrite: bool = False,
    ) -> dict[str, object]:
        self.calls.append((write_plan, schema_payload, overwrite))
        return self.result


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_result_dir(root: Path) -> Path:
    root.mkdir(parents=True)
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": True,
            "exit_code": 0,
            "timed_out": False,
            "source_feaspec_id": "gui_post_write_feaspec",
            "case_id": "gui_post_write_case",
            "osw_version": "0.1.4rc1",
        },
    )
    _write_json(
        root / "gui_post_write_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "gui_post_write_feaspec",
            "case_id": "gui_post_write_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "gui_post_write_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "gui_post_write_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "gui_post_write_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "gui_post_write_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "gui_post_write_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "gui_post_write_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _viewmodel(tmp_path: Path, *, output_dir: Path | None = None):
    from osw.experimental.feaspec import (
        FEASpecCalculiXResultWriteAcknowledgementState,
        build_calculix_result_dataset_draft_mapping,
        build_calculix_result_dataset_schema_payload,
        build_calculix_result_write_viewmodel,
        plan_calculix_result_dataset_write,
        plan_calculix_result_import,
    )

    import_plan = plan_calculix_result_import(_write_result_dir(tmp_path / "result"))
    mapping = build_calculix_result_dataset_draft_mapping(import_plan)
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir or (tmp_path / "dataset"),
        acknowledge_limitations=True,
    )
    schema = build_calculix_result_dataset_schema_payload(mapping, write_plan)
    return build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )


def _written_result(tmp_path: Path, *, status: str = "written") -> dict[str, object]:
    return {
        "status": status,
        "target_dir": str(tmp_path / "dataset"),
        "written_files": [
            {
                "relative_path": "result_dataset.json",
                "payload_kind": "result_dataset",
                "size_bytes": 128,
                "sha256": "a" * 64,
            },
            {
                "relative_path": "README_REVIEW_FIRST.txt",
                "payload_kind": "readme",
                "size_bytes": 48,
                "sha256": "b" * 64,
            },
        ],
        "diagnostics": [
            {
                "code": "FDW_WRITE_COMPLETED",
                "severity": "info",
                "message": "ResultDataset files were written.",
            },
            {
                "code": "FDW_REVIEW_WARNING",
                "severity": "warning",
                "message": "Review limitations before use.",
            },
        ],
        "limitations": ["Review parser limitations before downstream use."],
        "solver_execution_performed": False,
        "artifact_copy_performed": False,
    }


def _dialog_with_result(app: object, tmp_path: Path, result: dict[str, object]):
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    writer = _FakeWriter(result)
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        result_dataset_writer=writer,
    )
    return dialog, writer


def test_successful_writer_result_displays_status(app: object, tmp_path: Path) -> None:
    dialog, _writer = _dialog_with_result(app, tmp_path, _written_result(tmp_path))

    assert dialog.trigger_write_for_test(confirm=True) is True

    assert "written:" in dialog.post_write_status_text()
    assert "Post-write status:" in dialog.last_writer_result_text()


def test_successful_writer_result_displays_written_file_table(
    app: object,
    tmp_path: Path,
) -> None:
    dialog, _writer = _dialog_with_result(app, tmp_path, _written_result(tmp_path))

    assert dialog.trigger_write_for_test(confirm=True) is True

    table = dialog.written_files_table_text()
    assert "File | Payload kind | Size | sha256" in table
    assert "result_dataset.json" in table
    assert "128 bytes" in table
    assert "a" * 64 in table
    assert "result_dataset" in table


def test_written_with_warnings_state_is_displayed(
    app: object,
    tmp_path: Path,
) -> None:
    dialog, _writer = _dialog_with_result(
        app,
        tmp_path,
        _written_result(tmp_path, status="written-with-warnings"),
    )

    assert dialog.trigger_write_for_test(confirm=True) is True

    assert "written-with-warnings" in dialog.post_write_status_text()
    assert "Warning diagnostics:" in dialog.diagnostics_group_text()


def test_failed_writer_result_displays_failure_details(
    app: object,
    tmp_path: Path,
) -> None:
    result = {
        "status": "failed",
        "target_dir": str(tmp_path / "dataset"),
        "written_files": [],
        "diagnostics": [
            {
                "code": "FDW_TARGET_REPLACE_FAILED",
                "severity": "error",
                "message": "Could not replace target file.",
                "path": str(tmp_path / "dataset" / "result_dataset.json"),
                "suggested_fix": "Inspect permissions and retry.",
            }
        ],
    }
    dialog, writer = _dialog_with_result(app, tmp_path, result)

    assert dialog.trigger_write_for_test(confirm=True) is False

    details = dialog.failure_details_text()
    assert len(writer.calls) == 1
    assert "failed" in details
    assert "FDW_TARGET_REPLACE_FAILED" in details
    assert "Inspect permissions and retry" in details


def test_partial_cleanup_failure_displays_dedicated_warning(
    app: object,
    tmp_path: Path,
) -> None:
    result = {
        "status": "partial-cleanup-failed",
        "target_dir": str(tmp_path / "dataset"),
        "diagnostics": [
            {
                "code": "FDW_WRITE_FAILED",
                "severity": "error",
                "message": "Temporary files remain.",
            }
        ],
    }
    dialog, _writer = _dialog_with_result(app, tmp_path, result)

    assert dialog.trigger_write_for_test(confirm=True) is False

    assert "Partial cleanup failed" in dialog.failure_details_text()
    assert "temporary files" in dialog.retry_guidance_text()


def test_diagnostics_are_grouped(app: object, tmp_path: Path) -> None:
    result = _written_result(tmp_path)
    result["diagnostics"] = [
        {"code": "FDW_INFO", "severity": "info", "message": "Informational."},
        {"code": "FDW_WARN", "severity": "warning", "message": "Warning."},
        {"code": "FDW_ERROR", "severity": "error", "message": "Error."},
        {
            "code": "FDW_BLOCK",
            "severity": "warning",
            "message": "Blocker.",
            "blocks_write": True,
        },
    ]
    dialog, _writer = _dialog_with_result(app, tmp_path, result)

    assert dialog.trigger_write_for_test(confirm=True) is True

    text = dialog.diagnostics_group_text()
    assert "Info diagnostics:" in text
    assert "Warning diagnostics:" in text
    assert "Error diagnostics:" in text
    assert "Blocker diagnostics:" in text


def test_limitations_are_grouped(app: object, tmp_path: Path) -> None:
    dialog, _writer = _dialog_with_result(app, tmp_path, _written_result(tmp_path))

    assert dialog.trigger_write_for_test(confirm=True) is True

    text = dialog.limitations_group_text()
    assert "Review parser limitations" in text
    assert "Result import model only" in text


def test_retry_guidance_is_shown_after_failure(app: object, tmp_path: Path) -> None:
    dialog, _writer = _dialog_with_result(
        app,
        tmp_path,
        {"status": "failed", "target_dir": str(tmp_path / "dataset")},
    )

    assert dialog.trigger_write_for_test(confirm=True) is False

    text = dialog.retry_guidance_text()
    assert "Refresh the write plan" in text
    assert "selected output directory" in text
    assert "No automatic retry" not in text
    assert "no automatic retry" in text.casefold()


def test_copy_ready_summary_is_deterministic_without_clipboard(
    app: object,
    tmp_path: Path,
) -> None:
    dialog, _writer = _dialog_with_result(app, tmp_path, _written_result(tmp_path))

    assert dialog.trigger_write_for_test(confirm=True) is True

    first = dialog.copy_ready_summary_text()
    second = dialog.copy_ready_summary_text()
    assert first == second
    assert "FEASpec CalculiX ResultDataset write summary" in first
    assert (
        "Safety: no solver execution; no artifact copying; GitHub state verified "
        "2026-07-14: issue #8 is closed after bounded WSL CalculiX evidence, and "
        "this workflow does not broaden that closure."
    ) in first


def test_disabled_reason_text_remains_clear(app: object, tmp_path: Path) -> None:
    from osw.experimental.feaspec import (
        FEASpecCalculiXResultWriteAcknowledgementState,
        build_calculix_result_dataset_draft_mapping,
        build_calculix_result_dataset_schema_payload,
        build_calculix_result_write_viewmodel,
        plan_calculix_result_dataset_write,
        plan_calculix_result_import,
    )
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    import_plan = plan_calculix_result_import(_write_result_dir(tmp_path / "blocked"))
    mapping = build_calculix_result_dataset_draft_mapping(import_plan)
    output_dir = tmp_path / "dataset"
    output_dir.mkdir()
    (output_dir / "result_dataset.json").write_text("existing", encoding="utf-8")
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir,
        acknowledge_limitations=True,
    )
    schema = build_calculix_result_dataset_schema_payload(mapping, write_plan)
    viewmodel = build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=False,
        ),
    )
    dialog = FEASpecCalculiXResultWriteDialog(viewmodel)

    text = "\n".join(dialog.disabled_reason_texts())
    assert "missing_review_acknowledgement" in text
    assert "overwrite_required" in text


def test_write_enablement_semantics_unchanged(app: object, tmp_path: Path) -> None:
    dialog, _writer = _dialog_with_result(app, tmp_path, _written_result(tmp_path))

    assert dialog.write_button_enabled() is True
    assert dialog.trigger_write_for_test(confirm=True) is True
    assert dialog.write_button_enabled() is False


def test_confirmation_cancel_still_writes_nothing(app: object, tmp_path: Path) -> None:
    dialog, writer = _dialog_with_result(app, tmp_path, _written_result(tmp_path))

    assert dialog.trigger_write_for_test(confirm=False) is False

    assert writer.calls == []
    assert dialog.write_invocation_count() == 0


def test_real_writer_success_stays_under_tmp_path(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    output_dir = tmp_path / "dataset"
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path, output_dir=output_dir)
    )

    assert dialog.trigger_write_for_test(confirm=True) is True

    assert (output_dir / "result_dataset.json").exists()
    assert not (output_dir / "gui_post_write_case.dat").exists()
    assert str(output_dir) in dialog.post_write_status_text()


def test_source_adds_no_post_write_forbidden_paths() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "osw"
        / "gui"
        / "dialogs"
        / "feaspec_calculix_result_write_dialog.py"
    )
    source = module_path.read_text(encoding="utf-8")
    forbidden = (
        "clipboard",
        "pyperclip",
        "QDesktopServices",
        "startfile",
        "Popen",
        "run_calculix",
        "SolverAdapter",
        "CalculiXRunner",
        "ProjectSchema",
        "shutil.copy",
        "copy2",
    )

    for token in forbidden:
        assert token not in source
