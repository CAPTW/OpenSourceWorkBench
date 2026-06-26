"""PySide activation review panel for optional solver plugin manifests.

This panel is a view-model-driven review/control surface over the OSW-EXP-079
pure activation view-model. It renders activation readiness, acknowledgements,
blockers, diagnostics, conflicts, trust/provenance badges, and disabled/future
action states. It does not persist activation, run discovery, run validation,
install dependencies, execute solvers, import plugin packages, scan directories,
fetch network manifests, or mutate issues/releases. Acknowledgement interaction
is widget-local and non-persistent, driven by an injected pure callback that
rebuilds a supplied view-model.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestActivationAction,
    OptionalSolverPluginManifestActivationActionState,
    OptionalSolverPluginManifestActivationViewModel,
    render_optional_solver_plugin_manifest_activation_summary,
)
from osw.experimental.optional_solvers.plugin_manifest_activation_viewmodel import (
    ACK_NO_CERTIFICATION,
    ACK_NO_DEPENDENCY_INSTALL,
    ACK_NO_SOLVER_EXECUTION,
    ACK_NO_VALIDATION_PASS,
    ACK_UNTRUSTED_SOURCE,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object

AcknowledgementCallback = Callable[
    [Mapping[str, bool]], OptionalSolverPluginManifestActivationViewModel
]

# Map the acknowledge_* actions to their acknowledgement identifiers.
_ACK_ACTION_TO_ID: dict[str, str] = {
    OptionalSolverPluginManifestActivationAction.ACKNOWLEDGE_UNTRUSTED_SOURCE.value: (
        ACK_UNTRUSTED_SOURCE
    ),
    OptionalSolverPluginManifestActivationAction.ACKNOWLEDGE_NO_VALIDATION_PASS.value: (
        ACK_NO_VALIDATION_PASS
    ),
    OptionalSolverPluginManifestActivationAction.ACKNOWLEDGE_NO_INSTALL.value: (
        ACK_NO_DEPENDENCY_INSTALL
    ),
    OptionalSolverPluginManifestActivationAction.ACKNOWLEDGE_NO_SOLVER_EXECUTION.value: (
        ACK_NO_SOLVER_EXECUTION
    ),
    OptionalSolverPluginManifestActivationAction.ACKNOWLEDGE_NO_CERTIFICATION.value: (
        ACK_NO_CERTIFICATION
    ),
}

# Actions that must always remain disabled in this GUI gate.
_ALWAYS_DISABLED_ACTIONS: frozenset[str] = frozenset(
    {
        OptionalSolverPluginManifestActivationAction.REQUEST_ACTIVATION.value,
        OptionalSolverPluginManifestActivationAction.ACTIVATE_CANDIDATE.value,
        OptionalSolverPluginManifestActivationAction.DEACTIVATE_CANDIDATE.value,
        OptionalSolverPluginManifestActivationAction.RUN_DISCOVERY_WITH_ACTIVATED_MANIFESTS.value,
        OptionalSolverPluginManifestActivationAction.RUN_VALIDATION.value,
        OptionalSolverPluginManifestActivationAction.INSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestActivationAction.EXECUTE_SOLVER.value,
        OptionalSolverPluginManifestActivationAction.CLOSE_ISSUE.value,
        OptionalSolverPluginManifestActivationAction.EXPORT_REDACTED_SUMMARY.value,
    }
)

_ACTION_REASON_OVERRIDES: dict[str, str] = {
    OptionalSolverPluginManifestActivationAction.REQUEST_ACTIVATION.value: (
        "Request activation is displayed for review only; persistent activation "
        "is not implemented in this GUI gate."
    ),
    OptionalSolverPluginManifestActivationAction.ACTIVATE_CANDIDATE.value: (
        "Activate candidate is disabled; activation persistence requires a "
        "separate future gate."
    ),
    OptionalSolverPluginManifestActivationAction.DEACTIVATE_CANDIDATE.value: (
        "Deactivation workflow is a future gate (OSW-EXP-081)."
    ),
    OptionalSolverPluginManifestActivationAction.RUN_DISCOVERY_WITH_ACTIVATED_MANIFESTS.value: (
        "Discovery with activated manifests is a future integration gate."
    ),
    OptionalSolverPluginManifestActivationAction.RUN_VALIDATION.value: (
        "Validation requires a separate OSW-VALID gate."
    ),
    OptionalSolverPluginManifestActivationAction.INSTALL_DEPENDENCY.value: (
        "Dependency installation is unavailable from the activation GUI."
    ),
    OptionalSolverPluginManifestActivationAction.EXECUTE_SOLVER.value: (
        "Solver execution is unavailable from the activation GUI."
    ),
    OptionalSolverPluginManifestActivationAction.CLOSE_ISSUE.value: (
        "Issue closure requires separate validation and closure gates."
    ),
    OptionalSolverPluginManifestActivationAction.EXPORT_REDACTED_SUMMARY.value: (
        "Only the in-memory redacted summary accessor is implemented; no file, "
        "clipboard, shell, or browser export action is available."
    ),
}


class OptionalSolverPluginManifestActivationPanel(_BaseDialog):
    """View-model-driven activation review panel (non-persistent)."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestActivationViewModel | None = None,
        acknowledgement_callback: AcknowledgementCallback | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestActivationPanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Activation")
        self.resize(1180, 820)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model or OptionalSolverPluginManifestActivationViewModel.empty()
        )
        self._acknowledgement_callback = acknowledgement_callback
        self._acknowledgements: dict[str, bool] = {}
        self._disabled_action_reasons: dict[str, str] = {}
        self._action_buttons: dict[str, Any] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName(
            "oswOptionalSolverPluginManifestActivationSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestActivationTabs")
        root.addWidget(self.tabs, 1)

        self.candidates_table = _readonly_table(
            "oswOptionalSolverPluginManifestActivationCandidatesTable",
            self.tabs,
            (
                "Stack ID",
                "Display Name",
                "Source Type",
                "Source Label",
                "Source Reference",
                "Trust Label",
                "Activation State",
                "Readiness",
                "Blockers",
                "Warnings",
                "Required Acks",
                "Unsafe Claims",
                "Built-in Relationship",
            ),
        )
        self.acknowledgements_table = _readonly_table(
            "oswOptionalSolverPluginManifestActivationAcknowledgementsTable",
            self.tabs,
            (
                "Acknowledgement",
                "Label",
                "Required",
                "Satisfied",
                "Blocking",
                "Reason",
                "Warning",
            ),
        )
        self.diagnostics_table = _readonly_table(
            "oswOptionalSolverPluginManifestActivationDiagnosticsTable",
            self.tabs,
            (
                "Severity",
                "Category",
                "Code",
                "Message",
                "Source",
                "Stack ID",
                "Suggested Fix",
                "Blocker",
            ),
        )
        self.conflicts_table = _readonly_table(
            "oswOptionalSolverPluginManifestActivationConflictsTable",
            self.tabs,
            (
                "Stack ID",
                "Built-in Source",
                "User/Plugin Source",
                "Policy",
                "Built-ins Win",
                "Activation State",
            ),
        )
        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestActivationTrustPanel",
            self.tabs,
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestActivationSafetyPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName(
            "oswOptionalSolverPluginManifestActivationActionsPanel"
        )

        self.tabs.addTab(self.candidates_table, "Candidates")
        self.tabs.addTab(self.acknowledgements_table, "Acknowledgements")
        self.tabs.addTab(self.diagnostics_table, "Diagnostics")
        self.tabs.addTab(self.conflicts_table, "Conflicts")
        self.tabs.addTab(self.trust_panel, "Trust")
        self.tabs.addTab(self.safety_panel, "Safety")
        self.tabs.addTab(self.actions_panel, "Actions")

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName(
            "oswOptionalSolverPluginManifestActivationCloseButton"
        )
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.set_view_model(self._view_model)
        self.set_theme_tokens(self._tokens)

    # ------------------------------------------------------------------
    # Public API.
    # ------------------------------------------------------------------
    def set_view_model(
        self,
        view_model: OptionalSolverPluginManifestActivationViewModel,
    ) -> None:
        """Render the supplied activation view-model without side effects."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_candidates_table()
        self._populate_acknowledgements_table()
        self._populate_diagnostics_table()
        self._populate_conflicts_table()
        self.trust_panel.setPlainText(_trust_text(view_model))
        self.safety_panel.setPlainText(_safety_text(view_model))
        self._populate_action_state()

    def apply_acknowledgement(self, acknowledgement_id: str, satisfied: bool = True) -> None:
        """Update a widget-local acknowledgement and rebuild via the callback.

        This is non-persistent: it updates only in-memory widget state and a
        caller-supplied pure callback that returns a fresh view-model. If no
        callback was injected, the panel stays display-only and nothing changes.
        """

        if self._acknowledgement_callback is None:
            return
        self._acknowledgements[str(acknowledgement_id)] = bool(satisfied)
        new_view_model = self._acknowledgement_callback(dict(self._acknowledgements))
        self.set_view_model(new_view_model)

    def acknowledgement_state(self) -> dict[str, bool]:
        return dict(self._acknowledgements)

    def summary_text(self) -> str:
        return self.summary_label.text()

    def candidate_rows_text(self) -> str:
        return _table_text(self.candidates_table, empty_text="No activation candidates.")

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table, empty_text="No required acknowledgements."
        )

    def diagnostics_text(self) -> str:
        return _table_text(self.diagnostics_table, empty_text="No diagnostics.")

    def conflict_rows_text(self) -> str:
        return _table_text(self.conflicts_table, empty_text="No activation conflicts.")

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def redacted_summary_text(self) -> str:
        """Return an in-memory redacted summary; writes no files."""

        payload = render_optional_solver_plugin_manifest_activation_summary(
            self._view_model
        )
        return "\n".join(f"{key}: {value}" for key, value in payload.items())

    def available_action_names(self) -> tuple[str, ...]:
        return tuple(
            action.action.value
            for action in self._view_model.actions
            if self._effective_action_available(action)
        )

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOptionalSolverPluginManifestActivationPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverPluginManifestActivationSummary {"
            f"color: {tokens.accent};"
            "font-weight: 700;"
            "}"
            "QPlainTextEdit, QTableWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton:disabled {"
            f"color: {tokens.text_muted};"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "}"
        )

    # ------------------------------------------------------------------
    # Internal rendering.
    # ------------------------------------------------------------------
    def _build_actions_panel(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.actions_panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.action_state_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestActivationActionStatePanel",
            self.actions_panel,
        )
        layout.addWidget(self.action_state_panel, 1)
        button_grid = QtWidgets.QGridLayout()
        for index, action_state in enumerate(self._view_model.actions):
            action_name = action_state.action.value
            button = QtWidgets.QPushButton(action_state.label, self.actions_panel)
            button.setObjectName(_action_button_object_name(action_state))
            button.setEnabled(False)
            if action_name in _ACK_ACTION_TO_ID:
                ack_id = _ACK_ACTION_TO_ID[action_name]
                button.clicked.connect(
                    lambda _checked=False, ack=ack_id: self.apply_acknowledgement(ack, True)
                )
            self._action_buttons[action_name] = button
            button_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(button_grid)

    def _populate_candidates_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.display_name,
                row.source_type,
                row.source_label or "not supplied",
                row.source_reference_display or "not supplied",
                row.trust_label,
                row.activation_state,
                row.readiness,
                "; ".join(row.blockers) or "none",
                "; ".join(row.warnings) or "none",
                "; ".join(row.required_acknowledgements) or "none",
                "; ".join(row.unsafe_claim_indicators) or "none",
                row.built_in_relationship or "not supplied",
            )
            for row in self._view_model.candidate_rows
        ]
        _populate_table(self.candidates_table, rows)

    def _populate_acknowledgements_table(self) -> None:
        rows = [
            (
                row.acknowledgement_id,
                row.label,
                "yes" if row.required else "no",
                "yes" if row.satisfied else "no",
                "yes" if row.blocking else "no",
                row.reason,
                row.warning_text,
            )
            for row in self._view_model.acknowledgement_rows
        ]
        _populate_table(self.acknowledgements_table, rows)

    def _populate_diagnostics_table(self) -> None:
        rows = [
            (
                row.severity,
                row.category,
                row.code,
                row.message,
                row.source_reference_display or "not supplied",
                row.stack_id or "not supplied",
                row.suggested_fix or "not supplied",
                "yes" if row.blocker else "no",
            )
            for row in self._view_model.diagnostics
        ]
        _populate_table(self.diagnostics_table, rows)

    def _populate_conflicts_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.built_in_source,
                row.user_plugin_source or "not supplied",
                row.conflict_policy,
                "yes" if row.built_ins_win_default else "no",
                row.activation_state,
            )
            for row in self._view_model.conflict_rows
        ]
        _populate_table(self.conflicts_table, rows)

    def _populate_action_state(self) -> None:
        self._disabled_action_reasons = {}
        lines: list[str] = []
        for action_state in self._view_model.actions:
            action_name = action_state.action.value
            enabled = self._effective_action_enabled(action_state)
            available = self._effective_action_available(action_state)
            reason = self._effective_action_reason(action_state)
            availability = "available" if available else "unavailable"
            enabled_text = "enabled" if enabled else "disabled"
            future_text = "current" if enabled else "future"
            lines.append(
                f"{action_name}: {availability}; {enabled_text}; {future_text}; "
                "non-persistent"
            )
            lines.append(f"  {reason}")
            if not enabled:
                self._disabled_action_reasons[action_name] = reason
            button = self._action_buttons.get(action_name)
            if button is not None:
                button.setEnabled(enabled)
                button.setToolTip(reason)
        self.action_state_panel.setPlainText("\n".join(lines))

    def _effective_action_enabled(
        self,
        action_state: OptionalSolverPluginManifestActivationActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            # Acknowledge toggles are widget-local and require an injected
            # callback; they never persist anything.
            return self._acknowledgement_callback is not None
        # Every other action (request/activate/deactivate/discovery/validation/
        # install/execute/close-issue/export) stays disabled in this gate.
        return False

    def _effective_action_available(
        self,
        action_state: OptionalSolverPluginManifestActivationActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        return False

    def _effective_action_reason(
        self,
        action_state: OptionalSolverPluginManifestActivationActionState,
    ) -> str:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            if self._acknowledgement_callback is None:
                return (
                    "Acknowledgement is display-only here; inject a callback to "
                    "toggle it (widget-local, non-persistent)."
                )
            return (
                "Toggles a widget-local acknowledgement and rebuilds the supplied "
                "view-model; nothing is persisted."
            )
        return _ACTION_REASON_OVERRIDES.get(action_name, action_state.reason)


def _summary_text(
    view_model: OptionalSolverPluginManifestActivationViewModel,
) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest activation: "
        f"preview_available={view_model.preview_available}; "
        f"preview_sources={summary.preview_sources_count}; "
        f"candidates={summary.activation_candidates_count}; "
        f"ready={summary.activation_ready_count}; "
        f"blocked={summary.activation_blocked_count}; "
        f"active={summary.active_candidate_count}; "
        f"deactivated={summary.deactivated_count}; "
        f"diagnostics={summary.diagnostic_count}; "
        f"acknowledgements_required={summary.acknowledgement_required_count}; "
        f"preview_required={summary.preview_required_count}; "
        f"activation_performed={summary.activation_performed}; "
        f"validation_execution_performed={summary.validation_execution_performed}; "
        f"discovery_execution_performed={summary.discovery_execution_performed}; "
        f"solver_execution_performed={summary.solver_execution_performed}; "
        f"dependency_installation_performed={summary.dependency_installation_performed}; "
        f"issue_mutation_performed={summary.issue_mutation_performed}; "
        f"release_mutation_performed={summary.release_mutation_performed}; "
        f"certification_claimed={summary.certification_claimed}. "
        f"{summary.status_text}"
    )


def _trust_text(
    view_model: OptionalSolverPluginManifestActivationViewModel,
) -> str:
    lines = [
        "Trust/provenance labels.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Trust label is not certification.",
        "Active candidate is not validation evidence.",
    ]
    if not view_model.trust_badges:
        lines.append("No trust/provenance badges.")
    for badge in view_model.trust_badges:
        lines.append(
            f"source_type={badge.source_type} | trust_label={badge.trust_label} | "
            f"source_label={badge.source_label or 'not supplied'} | "
            f"activation_state={badge.activation_state} | {badge.warning_text} | "
            f"{badge.trust_label_is_not_certification} | "
            f"{badge.active_candidate_is_not_validation_evidence}"
        )
    return "\n".join(lines)


def _safety_text(
    view_model: OptionalSolverPluginManifestActivationViewModel,
) -> str:
    lines = [
        "Optional solver plugin manifest activation safety boundary.",
        "Activation GUI is view-model driven and non-persistent.",
        "Activation is not validation.",
        "Activation is not dependency installation.",
        "Activation is not solver execution.",
        "Activation is not certification.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Trust label is not certification.",
        "Active candidate is not validation evidence.",
        "No activation persistence.",
        "No plugin package import.",
        "No directory scan.",
        "No network fetch.",
        "No discovery execution.",
        "No validation execution.",
        "No solver execution.",
        "No dependency installation.",
        "No issue mutation.",
        "No release mutation.",
        "No tag mutation.",
        "No asset mutation.",
    ]
    lines.extend(view_model.guidance_text)
    lines.extend(view_model.safety_text)
    return "\n".join(dict.fromkeys(lines))


def _readonly_table(
    object_name: str,
    parent: object,
    headers: tuple[str, ...],
) -> object:
    table = QtWidgets.QTableWidget(parent)
    table.setObjectName(object_name)
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(list(headers))
    table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
    table.verticalHeader().setVisible(False)
    return table


def _readonly_plain_text(object_name: str, parent: object) -> object:
    widget = QtWidgets.QPlainTextEdit(parent)
    widget.setObjectName(object_name)
    widget.setReadOnly(True)
    return widget


def _readonly_item(text: object) -> object:
    item = QtWidgets.QTableWidgetItem(str(text))
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item


def _populate_table(table: object, rows: list[tuple[str, ...]]) -> None:
    table.setRowCount(len(rows))
    for row_index, row_values in enumerate(rows):
        for column_index, value in enumerate(row_values):
            table.setItem(row_index, column_index, _readonly_item(value))
    table.resizeColumnsToContents()


def _table_text(table: object, *, empty_text: str) -> str:
    if table.rowCount() == 0:
        return empty_text
    lines: list[str] = []
    for row in range(table.rowCount()):
        values: list[str] = []
        for column in range(table.columnCount()):
            item = table.item(row, column)
            values.append(item.text() if item is not None else "")
        lines.append(" | ".join(values))
    return "\n".join(lines)


def _action_button_object_name(
    action_state: OptionalSolverPluginManifestActivationActionState,
) -> str:
    return "oswOptionalSolverPluginManifestActivationAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


__all__ = [
    "OptionalSolverPluginManifestActivationPanel",
]
