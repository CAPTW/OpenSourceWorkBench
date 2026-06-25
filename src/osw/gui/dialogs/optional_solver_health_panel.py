"""PySide display panel for optional solver health view-models."""

from __future__ import annotations

from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverDiagnosticRowViewModel,
    OptionalSolverHealthPanelAction,
    OptionalSolverHealthPanelActionState,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverRequirementRowViewModel,
    OptionalSolverStackCardViewModel,
    OptionalSolverStackDetailsViewModel,
    OptionalSolverValidationHistoryRowViewModel,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class OptionalSolverHealthPanel(_BaseDialog):
    """Display-only optional solver health panel bound to a pure view-model."""

    def __init__(
        self,
        view_model: OptionalSolverHealthPanelViewModel,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverHealthPanel")
        self.setWindowTitle("Optional Solver Health")
        self.resize(1120, 760)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = view_model
        self._action_buttons: dict[OptionalSolverHealthPanelAction, Any] = {}
        self._disabled_action_reasons: dict[str, str] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName("oswOptionalSolverHealthSummary")
        root.addWidget(self.summary_label)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        root.addWidget(splitter, 1)

        self.stack_list = QtWidgets.QListWidget(splitter)
        self.stack_list.setObjectName("oswOptionalSolverHealthStackList")
        self.stack_list.setMinimumWidth(300)

        self.tabs = QtWidgets.QTabWidget(splitter)
        self.tabs.setObjectName("oswOptionalSolverHealthTabs")
        self.details_panel = _readonly_plain_text(
            "oswOptionalSolverHealthDetailsPanel",
            self.tabs,
        )
        self.diagnostics_panel = _readonly_plain_text(
            "oswOptionalSolverHealthDiagnosticsPanel",
            self.tabs,
        )
        self.guidance_panel = _readonly_plain_text(
            "oswOptionalSolverHealthGuidancePanel",
            self.tabs,
        )
        self.validation_history_panel = _readonly_plain_text(
            "oswOptionalSolverHealthValidationHistoryPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName("oswOptionalSolverHealthActionsPanel")
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverHealthSafetyPanel",
            self.tabs,
        )
        self.tabs.addTab(self.details_panel, "Details")
        self.tabs.addTab(self.diagnostics_panel, "Diagnostics")
        self.tabs.addTab(self.guidance_panel, "Guidance")
        self.tabs.addTab(self.validation_history_panel, "Validation History")
        self.tabs.addTab(self.actions_panel, "Actions")
        self.tabs.addTab(self.safety_panel, "Safety")
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswOptionalSolverHealthCloseButton")
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.set_view_model(view_model)
        self.set_theme_tokens(self._tokens)

    def set_view_model(self, view_model: OptionalSolverHealthPanelViewModel) -> None:
        """Render a new already-built view-model without performing discovery."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_stack_cards()
        self.details_panel.setPlainText(_details_text(view_model.details))
        self.diagnostics_panel.setPlainText(_diagnostics_text(view_model.diagnostics))
        self.guidance_panel.setPlainText(_guidance_text(view_model))
        self.validation_history_panel.setPlainText(
            _validation_history_text(view_model.validation_history)
        )
        self._populate_action_state()
        self.safety_panel.setPlainText(_safety_text(view_model))

    def summary_text(self) -> str:
        return self.summary_label.text()

    def stack_card_texts(self) -> tuple[str, ...]:
        return tuple(
            self.stack_list.item(index).text()
            for index in range(self.stack_list.count())
        )

    def selected_stack_details_text(self) -> str:
        return self.details_panel.toPlainText()

    def diagnostics_text(self) -> str:
        return self.diagnostics_panel.toPlainText()

    def guidance_text(self) -> str:
        return self.guidance_panel.toPlainText()

    def validation_history_text(self) -> str:
        return self.validation_history_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def available_action_names(self) -> tuple[str, ...]:
        return tuple(
            action.action.value
            for action in self._view_model.actions
            if action.available
        )

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOptionalSolverHealthPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverHealthSummary {"
            f"color: {tokens.accent};"
            "font-weight: 700;"
            "}"
            "QPlainTextEdit, QListWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 4px;"
            "}"
            "QPushButton:disabled {"
            f"color: {tokens.text_muted};"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "}"
        )

    def _build_actions_panel(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.actions_panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.action_state_panel = _readonly_plain_text(
            "oswOptionalSolverHealthActionStatePanel",
            self.actions_panel,
        )
        layout.addWidget(self.action_state_panel, 1)
        button_grid = QtWidgets.QGridLayout()
        for index, action in enumerate(OptionalSolverHealthPanelAction):
            button = QtWidgets.QPushButton(_action_label(action), self.actions_panel)
            button.setObjectName(_action_button_object_name(action))
            button.setEnabled(False)
            self._action_buttons[action] = button
            button_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(button_grid)

    def _populate_stack_cards(self) -> None:
        self.stack_list.clear()
        for card in self._view_model.cards:
            item = QtWidgets.QListWidgetItem(_stack_card_text(card))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, card.stack_id)
            self.stack_list.addItem(item)
            if card.selected:
                self.stack_list.setCurrentItem(item)

    def _populate_action_state(self) -> None:
        self._disabled_action_reasons = {}
        lines: list[str] = []
        for action_state in self._view_model.actions:
            action_name = action_state.action.value
            state_text = _action_state_status(action_state)
            reason = _gui_disabled_reason(action_state)
            lines.append(f"{action_name}: {state_text}")
            lines.append(f"  {reason}")
            self._disabled_action_reasons[action_name] = reason
            button = self._action_buttons.get(action_state.action)
            if button is not None:
                button.setEnabled(False)
                button.setToolTip(reason)
        self.action_state_panel.setPlainText("\n".join(lines))


def _readonly_plain_text(object_name: str, parent: object) -> object:
    widget = QtWidgets.QPlainTextEdit(parent)
    widget.setObjectName(object_name)
    widget.setReadOnly(True)
    return widget


def _summary_text(view_model: OptionalSolverHealthPanelViewModel) -> str:
    summary = view_model.summary
    state_counts = ", ".join(
        f"{state}={count}"
        for state, count in sorted(summary.counts_by_health_state.items())
    )
    return (
        f"Optional solver health: total={summary.total_stacks}; "
        f"missing={summary.missing_count}; partial={summary.partial_count}; "
        f"discovered={summary.discovered_count}; "
        f"open_issues={summary.open_issue_count}; "
        f"warnings={summary.validation_warning_count}; "
        f"states={state_counts or 'none'}"
    )


def _stack_card_text(card: OptionalSolverStackCardViewModel) -> str:
    selected = "selected" if card.selected else "not selected"
    disclaimer = "non-bundled" if card.has_non_bundled_disclaimer else "no disclaimer"
    return (
        f"{card.stack_id} | {card.display_name} | {card.issue_reference or 'no issue'} | "
        f"health={card.health_state} | support={card.support_status} | "
        f"missing={card.missing_requirements_count} | "
        f"diagnostics={card.diagnostics_count} | {disclaimer} | {selected}"
    )


def _details_text(details: OptionalSolverStackDetailsViewModel | None) -> str:
    if details is None:
        return "No stack selected."
    sections = [
        f"Stack: {details.display_name} ({details.stack_id})",
        _section("Capabilities", details.capabilities),
        _requirement_section("Executable requirements", details.executable_requirements),
        _requirement_section(
            "Python package requirements",
            details.python_package_requirements,
        ),
        _requirement_section("Environment hints", details.environment_hints),
        _section("Prepared-machine notes", details.prepared_machine_notes),
        _section("Safety notes", details.safety_notes),
        _section("Documentation refs", details.documentation_refs),
    ]
    if details.version_probe_text:
        sections.append(f"Version probe: {details.version_probe_text}")
    if details.help_probe_text:
        sections.append(f"Help probe: {details.help_probe_text}")
    return "\n\n".join(sections)


def _requirement_section(
    title: str,
    rows: tuple[OptionalSolverRequirementRowViewModel, ...],
) -> str:
    if not rows:
        return f"{title}:\n- none"
    return "\n".join([f"{title}:"] + [_requirement_line(row) for row in rows])


def _requirement_line(row: OptionalSolverRequirementRowViewModel) -> str:
    requirement = "required" if row.required else "optional"
    found = "not checked" if row.found is None else ("found" if row.found else "missing")
    parts = [
        f"- {row.identifier}",
        f"display={row.display_name}",
        requirement,
        f"status={row.status_text}",
        f"found={found}",
    ]
    if row.detail_text:
        parts.append(f"detail={row.detail_text}")
    if row.notes:
        parts.append("notes=" + "; ".join(row.notes))
    return " | ".join(parts)


def _diagnostics_text(rows: tuple[OptionalSolverDiagnosticRowViewModel, ...]) -> str:
    if not rows:
        return "No diagnostics."
    lines: list[str] = []
    for row in rows:
        parts = [
            f"{row.stack_id}",
            row.severity,
            row.code,
            row.message,
        ]
        if row.path:
            parts.append(f"path={row.path}")
        if row.suggested_fix:
            parts.append(f"fix={row.suggested_fix}")
        if row.redaction_notice:
            parts.append(row.redaction_notice)
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _guidance_text(view_model: OptionalSolverHealthPanelViewModel) -> str:
    if not view_model.guidance:
        return "No guidance."
    return "\n".join(
        f"{row.category} [{row.severity}]: {row.text}"
        for row in view_model.guidance
    )


def _validation_history_text(
    rows: tuple[OptionalSolverValidationHistoryRowViewModel, ...],
) -> str:
    if not rows:
        return "No validation history."
    lines: list[str] = []
    for row in rows:
        issue = f"#{row.related_issue}" if row.related_issue is not None else "no issue"
        pass_state = "pass evidence" if row.is_pass_evidence else "not pass evidence"
        closure = (
            "closure review required"
            if row.closure_review_required
            else "closure review not required"
        )
        lines.append(
            f"{row.source}: {row.status} | {issue} | {pass_state} | "
            f"{closure} | {row.summary}"
        )
    return "\n".join(lines)


def _action_state_status(action_state: OptionalSolverHealthPanelActionState) -> str:
    availability = "available" if action_state.available else "unavailable"
    enabled = "view-model enabled" if action_state.enabled else "disabled"
    future = "future" if action_state.future_action else "current"
    return f"{availability}; {enabled}; {future}; gui disabled"


def _gui_disabled_reason(action_state: OptionalSolverHealthPanelActionState) -> str:
    action = action_state.action
    if action == OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY:
        return (
            "Display-only placeholder: GUI refresh wiring is a future gate and "
            "this panel does not run discovery."
        )
    if action == OptionalSolverHealthPanelAction.COPY_SUMMARY:
        return (
            "Display-only placeholder: this panel does not access the clipboard."
        )
    if action == OptionalSolverHealthPanelAction.OPEN_DOCS:
        return (
            "Display-only placeholder: this panel does not open shells or browsers."
        )
    return action_state.reason


def _safety_text(view_model: OptionalSolverHealthPanelViewModel) -> str:
    return "\n".join(
        [
            "Optional solver GUI health panel safety boundary.",
            "No discovery execution from this panel.",
            "No solver execution.",
            "No external command execution.",
            "No subprocess usage.",
            "No solver or dependency installation.",
            "No optional solver package import.",
            "No issue closure action.",
            "No release mutation.",
            "External solvers and optional science packages are not bundled.",
            "Skipped-missing validation history is not pass evidence.",
            "Issues #6 through #11 remain separate validation work.",
            "No certification claim.",
            f"Selected stack: {view_model.selected_stack_id or 'none'}",
        ]
    )


def _section(title: str, rows: tuple[str, ...]) -> str:
    if not rows:
        return f"{title}:\n- none"
    return "\n".join([f"{title}:"] + [f"- {row}" for row in rows])


def _action_label(action: OptionalSolverHealthPanelAction) -> str:
    labels = {
        OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY: "Refresh",
        OptionalSolverHealthPanelAction.RUN_VALIDATION_GATE: "Run Validation",
        OptionalSolverHealthPanelAction.INSTALL_SOLVER: "Install Solver",
        OptionalSolverHealthPanelAction.CLOSE_ISSUE: "Close Issue",
        OptionalSolverHealthPanelAction.COPY_SUMMARY: "Copy Summary",
        OptionalSolverHealthPanelAction.OPEN_DOCS: "Open Docs",
    }
    return labels[action]


def _action_button_object_name(action: OptionalSolverHealthPanelAction) -> str:
    return "oswOptionalSolverHealthAction" + "".join(
        part.title() for part in action.value.split("_")
    )


__all__ = ["OptionalSolverHealthPanel"]
