"""Dialogs for the optional PySide6 GUI."""

from __future__ import annotations

__all__ = ["ExecutablePathDialog", "PluginManagerDialog"]


def __getattr__(name: str) -> object:
    if name in __all__:
        from osw.gui.dialogs.plugin_manager_dialog import (
            ExecutablePathDialog,
            PluginManagerDialog,
        )

        return {
            "ExecutablePathDialog": ExecutablePathDialog,
            "PluginManagerDialog": PluginManagerDialog,
        }[name]
    raise AttributeError(name)
