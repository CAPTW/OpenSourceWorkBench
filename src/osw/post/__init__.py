"""Post-processing, figures, and report package."""

from __future__ import annotations

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
    build_report_model,
    export_report_html,
    render_report_html,
)

__all__ = [
    "DEFAULT_REPORT_FILENAME",
    "DEFAULT_REPORT_LIMITATIONS",
    "PyVistaScene",
    "PyVistaSceneConfig",
    "PyVistaSceneState",
    "PyVistaUnavailableError",
    "ReportModel",
    "build_report_model",
    "build_scene_state",
    "export_report_html",
    "is_pyvista_available",
    "render_report_html",
]
