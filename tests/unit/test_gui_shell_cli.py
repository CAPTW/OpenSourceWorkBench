"""Tests for the optional GUI shell command surface."""

from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

GUI_MODULES = (
    "osw.gui.main_window",
    "osw.gui.project_tree",
    "osw.gui.properties_panel",
    "osw.gui.run_monitor",
    "osw.gui.result_viewer",
    "osw.gui.plot_viewer",
    "osw.gui.table_viewer",
)

EXPECTED_MENU_ACTIONS = {
    "File": ("New Project", "Open Project", "Save Project"),
    "Import": ("Import",),
    "Plugins": ("Plugin Manager",),
    "Run": ("Run",),
    "Reports": ("Report",),
}


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def test_gui_modules_import_without_requiring_pyside6() -> None:
    for module_name in GUI_MODULES:
        module = importlib.import_module(module_name)

        assert module is not None


def test_gui_layout_contract_names_are_available_without_pyside6() -> None:
    from osw.gui.main_window import MENU_ACTIONS, VIEWER_TAB_TITLES

    assert VIEWER_TAB_TITLES == ("3D Viewer", "Plot Viewer", "Table Viewer")
    assert MENU_ACTIONS == EXPECTED_MENU_ACTIONS


def test_properties_for_project_tree_nodes_are_available_without_pyside6() -> None:
    from osw.gui.project_tree import PROJECT_SECTIONS
    from osw.gui.properties_panel import properties_for_node

    for section in PROJECT_SECTIONS:
        rows = properties_for_node(section)

        assert rows["Selection"] == section
        assert rows["Workflow step"]


def test_run_monitor_append_helper_uses_stable_format_without_pyside6() -> None:
    from osw.gui.run_monitor import append_run_log

    class FakeMonitor:
        def __init__(self) -> None:
            self.lines: list[str] = []

        def appendPlainText(self, text: str) -> None:
            self.lines.append(text)

    monitor = FakeMonitor()
    append_run_log(monitor, "Project opened", level="info")

    assert monitor.lines == ["[INFO] Project opened"]


def test_cli_gui_help_is_available_without_pyside6() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "osw.cli", "gui", "--help"],
        cwd=REPO_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Launch the optional PySide6 GUI shell." in result.stdout


def test_cli_gui_reports_missing_pyside6_cleanly() -> None:
    if importlib.util.find_spec("PySide6") is not None:
        pytest.skip("PySide6 is installed; missing-dependency path is not active.")

    result = subprocess.run(
        [sys.executable, "-m", "osw.cli", "gui"],
        cwd=REPO_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "PySide6 is not installed" in result.stderr
    assert "python -m pip install -e .[gui]" in result.stderr
