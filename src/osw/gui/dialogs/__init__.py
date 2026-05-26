"""Dialogs for the optional PySide6 GUI."""

from __future__ import annotations

__all__ = ["ExecutablePathDialog", "PluginManagerDialog", "ScriptPreviewDialog"]


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
    raise AttributeError(name)
