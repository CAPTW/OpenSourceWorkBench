"""Dialogs for the optional PySide6 GUI."""

from __future__ import annotations

__all__ = [
    "BoundaryCurveDialog",
    "ExecutablePathDialog",
    "GmshMeshDialog",
    "MatPreviewDialog",
    "PluginManagerDialog",
    "ReportExportDialog",
    "ScriptPreviewDialog",
]


def __getattr__(name: str) -> object:
    if name in {"ExecutablePathDialog", "PluginManagerDialog"}:
        from osw.gui.dialogs.plugin_manager_dialog import (
            ExecutablePathDialog,
            PluginManagerDialog,
        )

        return {
            "ExecutablePathDialog": ExecutablePathDialog,
            "PluginManagerDialog": PluginManagerDialog,
        }[name]
    if name == "ScriptPreviewDialog":
        from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog

        return ScriptPreviewDialog
    if name == "MatPreviewDialog":
        from osw.gui.dialogs.mat_preview_dialog import MatPreviewDialog

        return MatPreviewDialog
    if name == "BoundaryCurveDialog":
        from osw.gui.dialogs.boundary_curve_dialog import BoundaryCurveDialog

        return BoundaryCurveDialog
    if name == "GmshMeshDialog":
        from osw.gui.dialogs.gmsh_mesh_dialog import GmshMeshDialog

        return GmshMeshDialog
    if name == "ReportExportDialog":
        from osw.gui.dialogs.report_export_dialog import ReportExportDialog

        return ReportExportDialog
    raise AttributeError(name)
