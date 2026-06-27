"""PySide deactivation review panel for optional solver plugin manifests.

This panel is a view-model-driven review/control surface over the OSW-EXP-085
pure deactivation view-model. It renders deactivation readiness, deactivation
state, candidate inclusion/exclusion, acknowledgements, blockers, diagnostics,
shared-stack/conflict rows, evidence retention, trust/provenance badges, safety
guidance, and disabled/future action states.

It implements no runtime deactivation behavior and no deactivation persistence.
It does not delete files, uninstall dependencies or solvers, run discovery, run
validation, install dependencies, execute solvers, import plugin packages, scan
directories, fetch network manifests, mutate activation/discovery/plugin state, or
mutate issues/releases. Acknowledgement interaction is widget-local and
non-persistent, driven by an injected pure callback that rebuilds a supplied
view-model.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestDeactivationAction,
    OptionalSolverPluginManifestDeactivationActionState,
    OptionalSolverPluginManifestDeactivationViewModel,
    render_optional_solver_plugin_manifest_deactivation_summary,
)
from osw.experimental.optional_solvers.plugin_manifest_deactivation_viewmodel import (
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_SOLVER_EXECUTION,
    ACK_NOT_DEPENDENCY_UNINSTALL,
    ACK_NOT_FILE_DELETION,
    ACK_NOT_ISSUE_CLOSURE,
    ACK_NOT_RELEASE_MUTATION,
    ACK_NOT_SOLVER_UNINSTALL,
    ACK_NOT_VALIDATION_EVIDENCE_DELETION,
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
    [Mapping[str, bool]], OptionalSolverPluginManifestDeactivationViewModel
]

_Action = OptionalSolverPluginManifestDeactivationAction

# Map the acknowledge_* actions to their acknowledgement identifiers. Only the
# acknowledgements that have a dedicated future action are mapped here; the
# remaining required acknowledgements (deactivation_history_visible,
# conflict_or_shared_stack_warning) are still rendered and can be toggled via
# apply_acknowledgement(<id>) directly (widget-local, non-persistent).
_ACK_ACTION_TO_ID: dict[str, str] = {
    _Action.ACKNOWLEDGE_NOT_FILE_DELETION.value: ACK_NOT_FILE_DELETION,
    _Action.ACKNOWLEDGE_NOT_DEPENDENCY_UNINSTALL.value: ACK_NOT_DEPENDENCY_UNINSTALL,
    _Action.ACKNOWLEDGE_NOT_SOLVER_UNINSTALL.value: ACK_NOT_SOLVER_UNINSTALL,
    _Action.ACKNOWLEDGE_NOT_ISSUE_CLOSURE.value: ACK_NOT_ISSUE_CLOSURE,
    _Action.ACKNOWLEDGE_NOT_RELEASE_MUTATION.value: ACK_NOT_RELEASE_MUTATION,
    _Action.ACKNOWLEDGE_NOT_VALIDATION_EVIDENCE_DELETION.value: (
        ACK_NOT_VALIDATION_EVIDENCE_DELETION
    ),
    _Action.ACKNOWLEDGE_NO_DISCOVERY_EXECUTION.value: ACK_NO_DISCOVERY_EXECUTION,
    _Action.ACKNOWLEDGE_NO_SOLVER_EXECUTION.value: ACK_NO_SOLVER_EXECUTION,
}

_ACTION_REASON_OVERRIDES: dict[str, str] = {
    _Action.REQUEST_DEACTIVATION.value: (
        "Request deactivation is display/preview-only; deactivation persistence is "
        "a future gate and nothing is persisted here."
    ),
    _Action.DEACTIVATE_CANDIDATE.value: (
        "Deactivate is disabled; deactivation persistence requires a separate "
        "future gate and deletes/uninstalls nothing."
    ),
    _Action.REACTIVATE_CANDIDATE.value: (
        "Reactivation is a future gate; this panel reactivates nothing."
    ),
    _Action.RUN_DISCOVERY.value: (
        "Discovery execution is unavailable from the deactivation GUI."
    ),
    _Action.RUN_VALIDATION.value: "Validation requires a separate OSW-VALID gate.",
    _Action.UNINSTALL_DEPENDENCY.value: (
        "Dependency uninstall is unavailable from the deactivation GUI."
    ),
    _Action.UNINSTALL_SOLVER.value: (
        "Solver uninstall is unavailable from the deactivation GUI."
    ),
    _Action.EXECUTE_SOLVER.value: (
        "Solver execution is unavailable from the deactivation GUI."
    ),
    _Action.CLOSE_ISSUE.value: (
        "Issue closure requires separate validation and closure gates."
    ),
    _Action.EXPORT_REDACTED_SUMMARY.value: (
        "Only the in-memory redacted summary accessor is implemented; no file, "
        "clipboard, shell, or browser export action is available."
    ),
}


class OptionalSolverPluginManifestDeactivationPanel(_BaseDialog):
    """View-model-driven deactivation review panel (non-persistent, non-mutating)."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestDeactivationViewModel | None = None,
        acknowledgement_callback: AcknowledgementCallback | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestDeactivationPanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Deactivation")
        self.resize(1240, 840)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model
            or OptionalSolverPluginManifestDeactivationViewModel.unavailable()
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
            "oswOptionalSolverPluginManifestDeactivationSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestDeactivationTabs")
        root.addWidget(self.tabs, 1)

        self.candidates_table = _readonly_table(
            "oswOptionalSolverPluginManifestDeactivationCandidatesTable",
            self.tabs,
            (
                "Stack ID",
                "Display Name",
                "Source Type",
                "Source Label",
                "Source Reference",
                "Trust Label",
                "Activation State",
                "Deactivation State",
                "Readiness",
                "Blockers",
                "Warnings",
                "Required Acks",
                "Built-in Relationship",
                "Shared-stack Indicators",
                "Historical Evidence",
                "Redacted",
            ),
        )
        self.acknowledgements_table = _readonly_table(
            "oswOptionalSolverPluginManifestDeactivationAcknowledgementsTable",
            self.tabs,
            (
                "Acknowledgement",
                "Label",
                "Required",
                "Satisfied",
                "Blocking",
                "Reason",
                "Related",
                "Warning",
            ),
        )
        self.diagnostics_table = _readonly_table(
            "oswOptionalSolverPluginManifestDeactivationDiagnosticsTable",
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
        self.shared_stacks_table = _readonly_table(
            "oswOptionalSolverPluginManifestDeactivationSharedStacksTable",
            self.tabs,
            (
                "Stack ID",
                "Built-in Source",
                "User/Plugin Source",
                "Active State",
                "Deactivated State",
                "Built-ins Win",
                "Keeps Built-ins",
                "Required Future Policy",
            ),
        )
        self.evidence_table = _readonly_table(
            "oswOptionalSolverPluginManifestDeactivationEvidenceTable",
            self.tabs,
            (
                "Stack ID",
                "Historical Evidence",
                "Evidence Retained",
                "Not Validation Failure",
                "Skipped-missing Remains",
                "Issue Closure Not Implied",
                "Evidence Not Deleted",
            ),
        )
        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestDeactivationTrustPanel",
            self.tabs,
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestDeactivationSafetyPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName(
            "oswOptionalSolverPluginManifestDeactivationActionsPanel"
        )

        self.tabs.addTab(self.candidates_table, "Candidates")
        self.tabs.addTab(self.acknowledgements_table, "Acknowledgements")
        self.tabs.addTab(self.diagnostics_table, "Diagnostics")
        self.tabs.addTab(self.shared_stacks_table, "Shared Stacks")
        self.tabs.addTab(self.evidence_table, "Evidence")
        self.tabs.addTab(self.trust_panel, "Trust")
        self.tabs.addTab(self.safety_panel, "Safety")
        self.tabs.addTab(self.actions_panel, "Actions")

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName(
            "oswOptionalSolverPluginManifestDeactivationCloseButton"
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
        view_model: OptionalSolverPluginManifestDeactivationViewModel,
    ) -> None:
        """Render the supplied deactivation view-model without side effects."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_candidates_table()
        self._populate_acknowledgements_table()
        self._populate_diagnostics_table()
        self._populate_shared_stacks_table()
        self._populate_evidence_table()
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
        return _table_text(self.candidates_table, empty_text="No deactivation candidates.")

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table, empty_text="No required acknowledgements."
        )

    def diagnostics_text(self) -> str:
        return _table_text(self.diagnostics_table, empty_text="No diagnostics.")

    def shared_stack_rows_text(self) -> str:
        return _table_text(self.shared_stacks_table, empty_text="No shared-stack conflicts.")

    def evidence_rows_text(self) -> str:
        return _table_text(self.evidence_table, empty_text="No evidence records.")

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def redacted_summary_text(self) -> str:
        """Return an in-memory redacted summary; writes no files."""

        payload = render_optional_solver_plugin_manifest_deactivation_summary(
            self._view_model
        )
        lines: list[str] = []
        for key, value in payload.items():
            if isinstance(value, list):
                lines.append(f"{key}: {len(value)} item(s)")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def available_action_names(self) -> tuple[str, ...]:
        return tuple(
            action.action.value
            for action in self._view_model.actions
            if self._effective_action_enabled(action)
        )

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOptionalSolverPluginManifestDeactivationPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverPluginManifestDeactivationSummary {"
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
            "oswOptionalSolverPluginManifestDeactivationActionStatePanel",
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
                row.deactivation_state,
                row.readiness,
                "; ".join(row.blockers) or "none",
                "; ".join(row.warnings) or "none",
                "; ".join(row.required_acknowledgements) or "none",
                row.built_in_relationship or "not supplied",
                "; ".join(row.shared_stack_indicators) or "none",
                row.historical_evidence_state,
                "yes" if row.redacted_source_reference else "no",
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
                row.related,
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

    def _populate_shared_stacks_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.built_in_source,
                row.user_plugin_source or "not supplied",
                row.active_source_state,
                row.deactivated_source_state,
                "yes" if row.built_ins_win_default else "no",
                row.deactivating_user_source_keeps_built_ins,
                row.required_future_policy,
            )
            for row in self._view_model.shared_stack_rows
        ]
        _populate_table(self.shared_stacks_table, rows)

    def _populate_evidence_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.historical_evidence_state,
                "yes" if row.evidence_retained else "no",
                row.not_validation_failure_text,
                row.skipped_missing_remains_text,
                row.issue_closure_not_implied_text,
                row.evidence_not_deleted_text,
            )
            for row in self._view_model.evidence_rows
        ]
        _populate_table(self.evidence_table, rows)

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
        action_state: OptionalSolverPluginManifestDeactivationActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            # Acknowledge toggles are widget-local and require an injected
            # callback; they never persist anything.
            return self._acknowledgement_callback is not None
        # Every other action (request/deactivate/reactivate/discovery/validation/
        # uninstall/execute/close-issue/export) stays disabled in this gate.
        return False

    def _effective_action_available(
        self,
        action_state: OptionalSolverPluginManifestDeactivationActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        # Reflect the view-model's availability: unsafe actions (run discovery,
        # run validation, uninstall dependency/solver, execute solver, close
        # issue) are unavailable; other future actions render available-but-disabled.
        return bool(action_state.available)

    def _effective_action_reason(
        self,
        action_state: OptionalSolverPluginManifestDeactivationActionState,
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
    view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest deactivation: "
        f"readiness={summary.readiness}; "
        f"state={summary.state}; "
        f"active={summary.active_candidate_count}; "
        f"deactivation_candidates={summary.deactivation_candidate_count}; "
        f"deactivation_ready={summary.deactivation_ready_count}; "
        f"deactivation_blocked={summary.deactivation_blocked_count}; "
        f"deactivated={summary.deactivated_count}; "
        f"shared_stack={summary.shared_stack_count}; "
        f"state_conflict={summary.state_conflict_count}; "
        f"acknowledgements_required={summary.acknowledgement_required_count}; "
        f"diagnostics={summary.diagnostic_count}; "
        f"evidence_retained={summary.evidence_retained}; "
        f"evidence_retained_count={summary.evidence_retained_count}; "
        f"deactivation_performed={summary.deactivation_performed}; "
        f"file_deletion_performed={summary.file_deletion_performed}; "
        f"dependency_uninstall_performed={summary.dependency_uninstall_performed}; "
        f"solver_uninstall_performed={summary.solver_uninstall_performed}; "
        f"discovery_execution_performed={summary.discovery_execution_performed}; "
        f"validation_execution_performed={summary.validation_execution_performed}; "
        f"solver_execution_performed={summary.solver_execution_performed}; "
        f"issue_mutation_performed={summary.issue_mutation_performed}; "
        f"release_mutation_performed={summary.release_mutation_performed}; "
        f"certification_claimed={summary.certification_claimed}. "
        f"{summary.status_text}"
    )


def _trust_text(
    view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> str:
    lines = [
        "Trust/provenance labels.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "A deactivated state is not validation evidence.",
    ]
    if not view_model.trust_badges:
        lines.append("No trust/provenance badges.")
    for badge in view_model.trust_badges:
        lines.append(
            f"source_type={badge.source_type} | trust_label={badge.trust_label} | "
            f"source_label={badge.source_label or 'not supplied'} | "
            f"activation_state={badge.activation_state} | "
            f"deactivation_state={badge.deactivation_state} | {badge.warning_text} | "
            f"{badge.trust_label_is_not_certification} | "
            f"{badge.deactivated_is_not_validation_evidence}"
        )
    return "\n".join(lines)


def _safety_text(
    view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> str:
    lines = [
        "Optional solver plugin manifest deactivation safety boundary.",
        "Deactivation GUI is view-model driven and non-mutating.",
        "Deactivation is not file deletion.",
        "Deactivation is not dependency uninstall.",
        "Deactivation is not solver uninstall.",
        "Deactivation is not a validation failure.",
        "Deactivation is not discovery execution.",
        "Deactivation is not solver execution.",
        "Deactivation is not issue closure.",
        "Deactivation is not release mutation.",
        "Deactivation is not certification.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "A deactivated state is not validation evidence.",
        "No deactivation persistence.",
        "No activation/discovery/plugin state mutation.",
        "No issue mutation.",
        "No release mutation.",
        "No tag mutation.",
        "No asset mutation.",
    ]
    lines.extend(view_model.guidance_text)
    lines.extend(view_model.safety_text)
    lines.extend(view_model.blocked_transitions)
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
    action_state: OptionalSolverPluginManifestDeactivationActionState,
) -> str:
    return "oswOptionalSolverPluginManifestDeactivationAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


__all__ = [
    "OptionalSolverPluginManifestDeactivationPanel",
]
