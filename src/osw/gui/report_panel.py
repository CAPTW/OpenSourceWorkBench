"""Report export panel for the OSW GUI shell."""

from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
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
        self.figure_datasets: tuple[object, ...] = ()
        self.mesh_infos: tuple[object, ...] = ()
        self.result_tables: tuple[object, ...] = ()
        self.warnings: tuple[str, ...] = ()
        self.export_directory = (
            Path(export_directory)
            if export_directory is not None
            else Path(gettempdir()) / "osw-reports"
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

    def set_report_state(
        self,
        *,
        project: Project,
        figure_datasets: tuple[object, ...] = (),
        mesh_infos: tuple[object, ...] = (),
        result_tables: tuple[object, ...] = (),
        warnings: tuple[str, ...] = (),
    ) -> None:
        self.project = project
        self.figure_datasets = tuple(figure_datasets)
        self.mesh_infos = tuple(mesh_infos)
        self.result_tables = tuple(result_tables)
        self.warnings = tuple(warnings)

    def export_report(self, output_path: str | Path | bool | None = None) -> Path:
        if isinstance(output_path, bool):
            output_path = None
        target = (
            Path(output_path)
            if output_path is not None
            else self.export_directory / DEFAULT_REPORT_FILENAME
        )
        output_path = export_report_html(
            self.project,
            target,
            figure_datasets=self.figure_datasets,
            mesh_infos=self.mesh_infos,
            result_tables=self.result_tables,
            warnings=self.warnings,
        )
        self.status_label.setText(f"Exported {output_path.name}")
        return output_path


def build_report_panel(parent: object | None = None) -> object:
    return ReportPanel(parent)
