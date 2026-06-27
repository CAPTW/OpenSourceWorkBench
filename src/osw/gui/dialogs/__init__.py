"""Dialogs for the optional PySide6 GUI."""

from __future__ import annotations

__all__ = [
    "BoundaryCurveDialog",
    "ChmPropertyDialog",
    "ChmReactorDialog",
    "CalculixDeckDialog",
    "ExecutablePathDialog",
    "FEASpecCalculiXResultWriteDialog",
    "FEASpecHumanReviewDialog",
    "GmshMeshDialog",
    "MatPreviewDialog",
    "OpenFOAMTemplateDialog",
    "OptionalSolverHealthPanel",
    "OptionalSolverPluginManifestActivationPanel",
    "OptionalSolverPluginManifestDiscoveryRefreshPanel",
    "OptionalSolverPluginManifestExplicitImportPanel",
    "OptionalSolverPluginManifestPanel",
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
    if name == "ChmPropertyDialog":
        from osw.gui.dialogs.chm_property_dialog import ChmPropertyDialog

        return ChmPropertyDialog
    if name == "ChmReactorDialog":
        from osw.gui.dialogs.chm_reactor_dialog import ChmReactorDialog

        return ChmReactorDialog
    if name == "OpenFOAMTemplateDialog":
        from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog

        return OpenFOAMTemplateDialog
    if name == "OptionalSolverHealthPanel":
        from osw.gui.dialogs.optional_solver_health_panel import (
            OptionalSolverHealthPanel,
        )

        return OptionalSolverHealthPanel
    if name == "OptionalSolverPluginManifestPanel":
        from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
            OptionalSolverPluginManifestPanel,
        )

        return OptionalSolverPluginManifestPanel
    if name == "OptionalSolverPluginManifestActivationPanel":
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )

        return OptionalSolverPluginManifestActivationPanel
    if name == "OptionalSolverPluginManifestDiscoveryRefreshPanel":
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel,
        )

        return OptionalSolverPluginManifestDiscoveryRefreshPanel
    if name == "OptionalSolverPluginManifestExplicitImportPanel":
        from osw.gui.dialogs.optional_solver_plugin_manifest_explicit_import_panel import (
            OptionalSolverPluginManifestExplicitImportPanel,
        )

        return OptionalSolverPluginManifestExplicitImportPanel
    if name == "FEASpecHumanReviewDialog":
        from osw.gui.dialogs.feaspec_human_review_dialog import FEASpecHumanReviewDialog

        return FEASpecHumanReviewDialog
    if name == "FEASpecCalculiXResultWriteDialog":
        from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
            FEASpecCalculiXResultWriteDialog,
        )

        return FEASpecCalculiXResultWriteDialog
    if name == "ReportExportDialog":
        from osw.gui.dialogs.report_export_dialog import ReportExportDialog

        return ReportExportDialog
    raise AttributeError(name)
