"""Tests for the UI-004 top bar."""

from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None

EXPECTED_ACTIONS = (
    "New",
    "Open",
    "Save",
    "Save As",
    "Import",
    "Export",
    "Terminal",
    "Preferences",
    "Help",
    "About",
)


def test_top_bar_contract_is_import_safe_without_pyside6() -> None:
    from osw.gui.widgets.top_bar import (
        APP_SUBTITLE,
        APP_TITLE,
        TOOLBAR_ACTION_LABELS,
        UTILITY_ACTION_LABELS,
    )

    assert APP_TITLE == "OpenSolver Workbench"
    assert APP_SUBTITLE == "Open Source CAE / CFD / CHM / MATLAB-Octave"
    assert TOOLBAR_ACTION_LABELS == EXPECTED_ACTIONS[:6]
    assert UTILITY_ACTION_LABELS == EXPECTED_ACTIONS[6:]


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_top_bar_instantiates_with_title_subtitle_and_actions(app: object) -> None:
    from osw.gui.widgets.top_bar import TopBar

    top_bar = TopBar()

    assert top_bar.objectName() == "oswTopRegion"
    assert top_bar.title_label.objectName() == "oswAppTitle"
    assert top_bar.subtitle_label.objectName() == "oswAppSubtitle"
    assert top_bar.title_label.text() == "OpenSolver Workbench"
    assert top_bar.subtitle_label.text() == "Open Source CAE / CFD / CHM / MATLAB-Octave"
    assert top_bar.action_labels() == list(EXPECTED_ACTIONS)
    assert top_bar.utility_actions.objectName() == "oswTopUtilityActions"


def test_top_bar_placeholder_actions_do_not_crash(app: object) -> None:
    from osw.gui.widgets.top_bar import TopBar

    observed: list[str] = []
    top_bar = TopBar()
    top_bar.actionTriggered.connect(observed.append)

    top_bar.trigger_action("Terminal")
    top_bar.trigger_action("Help")
    top_bar.trigger_action("About")

    assert observed == ["Terminal", "Help", "About"]


def test_top_bar_preferences_signal_can_be_triggered(app: object) -> None:
    from osw.gui.widgets.top_bar import TopBar

    observed: list[str] = []
    top_bar = TopBar()
    top_bar.actionTriggered.connect(observed.append)

    top_bar.trigger_action("Preferences")

    assert observed == ["Preferences"]
