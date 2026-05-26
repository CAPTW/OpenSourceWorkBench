"""Workflow stepper for the OpenSolver Workbench run screen."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None


class StepState(StrEnum):
    """Visual state of a workflow step."""

    COMPLETED = "completed"
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """Import-safe workflow step contract."""

    id: str
    number: int
    label: str
    state: StepState

    @property
    def display_label(self) -> str:
        return f"{self.number} {self.label}"


DEFAULT_WORKFLOW_STEPS = (
    WorkflowStep("import", 1, "Import", StepState.COMPLETED),
    WorkflowStep("configure", 2, "Configure", StepState.COMPLETED),
    WorkflowStep("mesh", 3, "Mesh", StepState.COMPLETED),
    WorkflowStep("run", 4, "Run", StepState.ACTIVE),
    WorkflowStep("results", 5, "Results", StepState.INACTIVE),
    WorkflowStep("report", 6, "Report", StepState.INACTIVE),
)
WORKFLOW_STEP_LABELS = tuple(step.display_label for step in DEFAULT_WORKFLOW_STEPS)
STEP_OBJECT_NAMES = {
    "import": "oswWorkflowStepImport",
    "configure": "oswWorkflowStepConfigure",
    "mesh": "oswWorkflowStepMesh",
    "run": "oswWorkflowStepRun",
    "results": "oswWorkflowStepResults",
    "report": "oswWorkflowStepReport",
}

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class WorkflowStepper(_BaseWidget):
    """Compact theme-aware workflow stepper with Run active by default."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        steps: tuple[WorkflowStep, ...] = DEFAULT_WORKFLOW_STEPS,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswWorkflowStepper")
        self._steps = list(steps)
        self._tokens = DARK_TOKENS
        self._step_labels: dict[str, object] = {}
        self._connectors: list[object] = []

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._rebuild()

    def set_steps(self, steps: list[WorkflowStep] | tuple[WorkflowStep, ...]) -> None:
        self._steps = list(steps)
        self._rebuild()

    def set_active_step(self, step_id: str) -> None:
        ids = [step.id for step in self._steps]
        if step_id not in ids:
            raise ValueError(f"Unknown workflow step {step_id!r}.")
        active_index = ids.index(step_id)
        self._steps = [
            WorkflowStep(
                step.id,
                step.number,
                step.label,
                StepState.COMPLETED
                if index < active_index
                else StepState.ACTIVE
                if index == active_index
                else StepState.INACTIVE,
            )
            for index, step in enumerate(self._steps)
        ]
        self._apply_theme()

    def mark_completed(self, step_id: str) -> None:
        self._steps = [
            WorkflowStep(step.id, step.number, step.label, StepState.COMPLETED)
            if step.id == step_id
            else step
            for step in self._steps
        ]
        self._apply_theme()

    def current_step(self) -> str:
        for step in self._steps:
            if step.state is StepState.ACTIVE:
                return step.id
        return ""

    def step_state(self, step_id: str) -> StepState:
        for step in self._steps:
            if step.id == step_id:
                return step.state
        raise ValueError(f"Unknown workflow step {step_id!r}.")

    def step_names(self) -> list[str]:
        return [step.label for step in self._steps]

    def step_labels(self) -> list[str]:
        return [step.display_label for step in self._steps]

    def active_step_label(self) -> str:
        for step in self._steps:
            if step.state is StepState.ACTIVE:
                return step.display_label
        return ""

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._apply_theme()

    def _rebuild(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._step_labels.clear()
        self._connectors.clear()

        for index, step in enumerate(self._steps):
            step_label = QtWidgets.QLabel(self._format_label(step), self)
            step_label.setObjectName(STEP_OBJECT_NAMES[step.id])
            step_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            step_label.setMinimumWidth(104)
            step_label.setProperty("stepState", step.state.value)
            self._layout.addWidget(step_label, 0)
            self._step_labels[step.id] = step_label

            if index < len(self._steps) - 1:
                connector = QtWidgets.QFrame(self)
                connector.setObjectName(f"oswWorkflowConnector{index + 1}")
                connector.setFixedHeight(2)
                connector.setMinimumWidth(22)
                self._layout.addWidget(connector, 0)
                self._connectors.append(connector)

        self._layout.addStretch(1)
        self._apply_theme()

    def _apply_theme(self) -> None:
        tokens = self._tokens
        self.setStyleSheet(
            "QWidget#oswWorkflowStepper {"
            "background: transparent;"
            "}"
            "QLabel[stepState='completed'] {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.success};"
            "border-radius: 5px;"
            "padding: 5px 9px;"
            "font-weight: 600;"
            "}"
            "QLabel[stepState='active'] {"
            f"background-color: {tokens.primary};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.primary_hover};"
            "border-radius: 5px;"
            "padding: 6px 10px;"
            "font-weight: 700;"
            "}"
            "QLabel[stepState='inactive'] {"
            f"background-color: {tokens.bg_header};"
            f"color: {tokens.text_muted};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 5px;"
            "padding: 5px 9px;"
            "font-weight: 600;"
            "}"
        )
        for step in self._steps:
            label = self._step_labels[step.id]
            label.setText(self._format_label(step))
            label.setProperty("stepState", step.state.value)
            label.style().unpolish(label)
            label.style().polish(label)
        active_index = next(
            (index for index, step in enumerate(self._steps) if step.state is StepState.ACTIVE),
            0,
        )
        for index, connector in enumerate(self._connectors):
            color = tokens.success if index < active_index else tokens.border
            connector.setStyleSheet(f"QFrame {{ background-color: {color}; border: none; }}")

    @staticmethod
    def _format_label(step: WorkflowStep) -> str:
        prefix = "✓ " if step.state is StepState.COMPLETED else ""
        return f"{prefix}{step.number} {step.label}"
