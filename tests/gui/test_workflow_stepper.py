"""Tests for the UI-004 workflow stepper."""

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

EXPECTED_LABELS = ("Import", "Configure", "Mesh", "Run", "Results", "Report")


def test_workflow_step_contract_is_import_safe_without_pyside6() -> None:
    from osw.gui.widgets.workflow_stepper import (
        DEFAULT_WORKFLOW_STEPS,
        WORKFLOW_STEP_LABELS,
        StepState,
    )

    assert tuple(step.label for step in DEFAULT_WORKFLOW_STEPS) == EXPECTED_LABELS
    assert WORKFLOW_STEP_LABELS == (
        "1 Import",
        "2 Configure",
        "3 Mesh",
        "4 Run",
        "5 Results",
        "6 Report",
    )
    assert [step.state for step in DEFAULT_WORKFLOW_STEPS[:3]] == [StepState.COMPLETED] * 3
    assert DEFAULT_WORKFLOW_STEPS[3].state is StepState.ACTIVE
    assert [step.state for step in DEFAULT_WORKFLOW_STEPS[4:]] == [StepState.INACTIVE] * 2


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_workflow_stepper_instantiates_with_run_active(app: object) -> None:
    from osw.gui.widgets.workflow_stepper import StepState, WorkflowStepper

    stepper = WorkflowStepper()

    assert stepper.objectName() == "oswWorkflowStepper"
    assert stepper.step_names() == list(EXPECTED_LABELS)
    assert stepper.current_step() == "run"
    assert stepper.step_state("import") is StepState.COMPLETED
    assert stepper.step_state("configure") is StepState.COMPLETED
    assert stepper.step_state("mesh") is StepState.COMPLETED
    assert stepper.step_state("run") is StepState.ACTIVE
    assert stepper.step_state("results") is StepState.INACTIVE
    assert stepper.step_state("report") is StepState.INACTIVE


def test_workflow_stepper_can_change_active_step(app: object) -> None:
    from osw.gui.widgets.workflow_stepper import StepState, WorkflowStepper

    stepper = WorkflowStepper()
    stepper.set_active_step("results")

    assert stepper.current_step() == "results"
    assert stepper.step_state("results") is StepState.ACTIVE
    assert stepper.step_state("run") is StepState.COMPLETED


def test_workflow_stepper_accepts_dark_and_light_tokens(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.widgets.workflow_stepper import WorkflowStepper

    stepper = WorkflowStepper()
    manager = ThemeManager(auto_load=False)

    manager.set_mode("dark", save=False)
    stepper.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    stepper.set_theme_tokens(manager.current_tokens)

    assert stepper.styleSheet()
