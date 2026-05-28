"""Dialogs for the optional PySide6 GUI."""

from __future__ import annotations

__all__ = [
    "BoundaryCurveDialog",
    "CalculixDeckDialog",
    "ExecutablePathDialog",
    "GmshMeshDialog",
    "MatPreviewDialog",
    "OpenFOAMTemplateDialog",
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
    if name == "CalculixDeckDialog":
        from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog

        return CalculixDeckDialog
    if name == "OpenFOAMTemplateDialog":
        from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog

        return OpenFOAMTemplateDialog
    if name == "ReportExportDialog":
        from osw.gui.dialogs.report_export_dialog import ReportExportDialog

        return ReportExportDialog
    raise AttributeError(name)
