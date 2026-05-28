"""Post-processing, figures, and report package."""

from __future__ import annotations

from osw.post.matplotlib_scene import (
    MatplotlibUnavailableError,
    export_line_plot_dataset,
    is_matplotlib_available,
)
from osw.post.pyvista_scene import (
    PyVistaScene,
    PyVistaSceneConfig,
    PyVistaSceneState,
    PyVistaUnavailableError,
    build_scene_state,
    is_pyvista_available,
)
from osw.post.report_generator import (
    DEFAULT_REPORT_FILENAME,
    DEFAULT_REPORT_LIMITATIONS,
    ReportModel,
    build_report,
    build_report_model,
    build_report_summary,
    export_report_html,
    render_report_html,
    render_report_markdown,
    render_report_summary_html,
)
from osw.post.report_model import (
    ReportAsset,
    ReportBuildRequest,
    ReportBuildResult,
    ReportFigure,
    ReportFormat,
    ReportSection,
    ReportSummary,
    ReportTable,
)
from osw.post.result_view_model import (
    ResultViewModel,
    boundary_curve_to_view_dataset,
    figure_dataset_to_view_dataset,
    mat_summary_to_view_dataset,
    mesh_info_to_view_dataset,
    result_catalog_from_project,
    result_catalog_from_result_datasets,
    result_dataset_summary,
    result_dataset_to_view_model,
)

__all__ = [
    "DEFAULT_REPORT_FILENAME",
    "DEFAULT_REPORT_LIMITATIONS",
    "MatplotlibUnavailableError",
    "PyVistaScene",
    "PyVistaSceneConfig",
    "PyVistaSceneState",
    "PyVistaUnavailableError",
    "ReportModel",
    "ReportAsset",
    "ReportBuildRequest",
    "ReportBuildResult",
    "ReportFigure",
    "ReportFormat",
    "ReportSection",
    "ReportSummary",
    "ReportTable",
    "ResultViewModel",
    "boundary_curve_to_view_dataset",
    "build_report",
    "build_report_model",
    "build_report_summary",
    "build_scene_state",
    "export_report_html",
    "export_line_plot_dataset",
    "figure_dataset_to_view_dataset",
    "is_matplotlib_available",
    "is_pyvista_available",
    "mat_summary_to_view_dataset",
    "mesh_info_to_view_dataset",
    "render_report_markdown",
    "render_report_html",
    "render_report_summary_html",
    "result_catalog_from_project",
    "result_catalog_from_result_datasets",
    "result_dataset_summary",
    "result_dataset_to_view_model",
]
