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
)


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def test_gui_modules_import_without_requiring_pyside6() -> None:
    for module_name in GUI_MODULES:
        module = importlib.import_module(module_name)

        assert module is not None


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
