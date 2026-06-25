from __future__ import annotations

import importlib.util
import json
import os

import pytest
from tests.gui.test_optional_solver_gui_health_panel import (
    sample_optional_solver_health_view_model,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_export_action_exists_and_is_enabled_for_valid_view_model(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: "",
    )

    assert "export_summary" in panel.available_action_names()
    assert "export_summary: available; enabled; current" in panel.action_state_text()
    assert panel.export_action_enabled() is True
    assert "explicitly selected file" in panel.export_action_reason()


def test_json_export_writes_one_redacted_file_under_tmp_path(
    app: object,
    tmp_path,
) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.json"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: (target, "JSON (*.json)"),
        export_generated_at="2026-06-25T00:00:00Z",
        export_source_context="gui-export-test",
        export_package_version="0.1.5rc1",
    )

    panel.export_summary_button.click()

    assert sorted(path.name for path in tmp_path.iterdir()) == ["summary.json"]
    content = target.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert payload["not_validation_evidence"] is True
    assert payload["redaction_state"]["redacted_by_default"] is True
    assert payload["redaction_state"]["environment_values_exported"] is False
    assert payload["generated_at"] == "2026-06-25T00:00:00Z"
    assert payload["source_context"] == "gui-export-test"
    assert payload["package_version"] == "0.1.5rc1"
    assert "C:/Users/USER" not in content
    assert "Full paths are omitted by default." in content
    assert panel.last_export_path() == str(target)
    assert panel.last_export_format() == "json"
    assert panel.export_error_text() == ""
    assert "Exported redacted optional solver summary." in panel.export_status_text()
    assert "not_validation_evidence=true" in panel.exported_file_summary_text()
