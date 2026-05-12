from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from osw.core.project_schema import Project, ProjectMetadata, ReportConfig

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


def test_report_panel_triggers_export(app: object, tmp_path: Path) -> None:
    from osw.gui.report_panel import ReportPanel

    project = Project(
        metadata=ProjectMetadata(name="Panel Project"),
        report=ReportConfig(title="Panel Report"),
    )
    panel = ReportPanel(project=project, export_directory=tmp_path)

    output_path = panel.export_report()

    assert output_path == tmp_path / "report.html"
    assert output_path.exists()
    assert "Panel Project" in output_path.read_text(encoding="utf-8")
    assert "report.html" in panel.status_label.text()

    del app
