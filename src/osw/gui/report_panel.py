"""Report export panel for the OSW GUI shell."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.core.project_schema import Project, ProjectMetadata
from osw.post.report_generator import DEFAULT_REPORT_FILENAME, export_report_html

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


def default_report_project() -> Project:
    return Project(metadata=ProjectMetadata(name="Untitled OSW Project"))


class ReportPanel(_BaseWidget):
    """Small report panel that exports a minimal HTML project report."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        project: Project | None = None,
        export_directory: str | Path | None = None,
    ) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("reportPanel")
        self.project = project or default_report_project()
        self.export_directory = (
            Path(export_directory) if export_directory is not None else Path("reports")
        )

        self.export_button = QtWidgets.QPushButton("Export HTML Report", self)
        self.export_button.setObjectName("reportExportButton")
        self.status_label = QtWidgets.QLabel("Report not exported.", self)
        self.status_label.setObjectName("reportExportStatus")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Report"))
        layout.addWidget(self.export_button)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.export_button.clicked.connect(self.export_report)

    def export_report(self) -> Path:
        output_path = export_report_html(
            self.project,
            self.export_directory / DEFAULT_REPORT_FILENAME,
        )
        self.status_label.setText(f"Exported {output_path.name}")
        return output_path


def build_report_panel(parent: object | None = None) -> object:
    return ReportPanel(parent)
