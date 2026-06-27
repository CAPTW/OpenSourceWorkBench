"""PySide discovery-refresh review panel for optional solver plugin manifests.

This panel is a view-model-driven review/control surface over the OSW-EXP-083
pure discovery-refresh view-model. It renders refresh readiness, refresh
mode/state, discovery source inclusion/exclusion, deactivated candidates,
acknowledgements, blockers, diagnostics, conflicts, unsafe claims,
trust/provenance badges, safety guidance, and disabled/future action states.

It implements no runtime discovery integration and changes no passive discovery
behavior. It does not run discovery, run validation, install dependencies,
execute solvers, import plugin packages, scan directories, fetch network
manifests, persist activation/deactivation state, or mutate issues/releases.
Acknowledgement interaction is widget-local and non-persistent, driven by an
injected pure callback that rebuilds a supplied view-model.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestDiscoveryRefreshAction,
    OptionalSolverPluginManifestDiscoveryRefreshActionState,
    OptionalSolverPluginManifestDiscoveryRefreshViewModel,
    render_optional_solver_plugin_manifest_discovery_refresh_summary,
)
from osw.experimental.optional_solvers.plugin_manifest_discovery_refresh_viewmodel import (
    ACK_NO_NETWORK_FETCH,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_REFRESH_NOT_INSTALL,
    ACK_REFRESH_NOT_ISSUE_CLOSURE,
    ACK_REFRESH_NOT_SOLVER_EXECUTION,
    ACK_REFRESH_NOT_VALIDATION,
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
    [Mapping[str, bool]], OptionalSolverPluginManifestDiscoveryRefreshViewModel
]

_Action = OptionalSolverPluginManifestDiscoveryRefreshAction

# Map the acknowledge_* actions to their acknowledgement identifiers. Only the
# acknowledgements that have a dedicated future action are mapped here; the
# remaining required acknowledgements are still rendered and can be toggled via
# apply_acknowledgement(<id>) directly (widget-local, non-persistent).
_ACK_ACTION_TO_ID: dict[str, str] = {
    _Action.ACKNOWLEDGE_REFRESH_NOT_VALIDATION.value: ACK_REFRESH_NOT_VALIDATION,
    _Action.ACKNOWLEDGE_NO_INSTALL.value: ACK_REFRESH_NOT_INSTALL,
    _Action.ACKNOWLEDGE_NO_SOLVER_EXECUTION.value: ACK_REFRESH_NOT_SOLVER_EXECUTION,
    _Action.ACKNOWLEDGE_NO_ISSUE_CLOSURE.value: ACK_REFRESH_NOT_ISSUE_CLOSURE,
    _Action.ACKNOWLEDGE_NO_NETWORK_FETCH.value: ACK_NO_NETWORK_FETCH,
    _Action.ACKNOWLEDGE_NO_PLUGIN_IMPORT.value: ACK_NO_PLUGIN_PACKAGE_IMPORT,
}

_ACTION_REASON_OVERRIDES: dict[str, str] = {
    _Action.REQUEST_REFRESH.value: (
        "Request refresh is display/preview-only; runtime discovery refresh is a "
        "future integration gate and runs nothing here."
    ),
    _Action.BUILT_IN_ONLY_REFRESH.value: (
        "Built-in-only refresh is future-only; no discovery runs from this GUI."
    ),
    _Action.INCLUDE_ACTIVATED_CANDIDATES.value: (
        "Including activated candidates in discovery is a future integration gate."
    ),
    _Action.EXCLUDE_DEACTIVATED_CANDIDATES.value: (
        "Deactivated candidates are excluded by default; this is display-only."
    ),
    _Action.RUN_DISCOVERY.value: (
        "Discovery execution is unavailable from the discovery-refresh GUI."
    ),
    _Action.RUN_VALIDATION.value: "Validation requires a separate OSW-VALID gate.",
    _Action.INSTALL_DEPENDENCY.value: (
        "Dependency installation is unavailable from the discovery-refresh GUI."
    ),
    _Action.EXECUTE_SOLVER.value: (
        "Solver execution is unavailable from the discovery-refresh GUI."
    ),
    _Action.CLOSE_ISSUE.value: (
        "Issue closure requires separate validation and closure gates."
    ),
    _Action.EXPORT_REDACTED_SUMMARY.value: (
        "Only the in-memory redacted summary accessor is implemented; no file, "
        "clipboard, shell, or browser export action is available."
    ),
}


class OptionalSolverPluginManifestDiscoveryRefreshPanel(_BaseDialog):
    """View-model-driven discovery-refresh review panel (non-executing)."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel | None = None,
        acknowledgement_callback: AcknowledgementCallback | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestDiscoveryRefreshPanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Discovery Refresh")
        self.resize(1240, 840)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model
            or OptionalSolverPluginManifestDiscoveryRefreshViewModel.unavailable()
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
            "oswOptionalSolverPluginManifestDiscoveryRefreshSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestDiscoveryRefreshTabs")
        root.addWidget(self.tabs, 1)

        self.sources_table = _readonly_table(
            "oswOptionalSolverPluginManifestDiscoveryRefreshSourcesTable",
            self.tabs,
            (
                "Stack ID",
                "Display Name",
                "Source Type",
                "Source Label",
                "Source Reference",
                "Trust Label",
                "Discovery State",
                "Activation State",
                "Refresh Mode",
                "Included",
                "Exclusion Reason",
                "Readiness",
                "Blockers",
                "Warnings",
                "Required Acks",
                "Unsafe Claims",
                "Built-in Relationship",
                "Redacted",
            ),
        )
        self.deactivated_table = _readonly_table(
            "oswOptionalSolverPluginManifestDiscoveryRefreshDeactivatedTable",
            self.tabs,
            (
                "Stack ID",
                "Source Label",
                "Trust Label",
                "Deactivated State",
                "Excluded By Default",
                "Source Reference",
                "Not Validation Failure",
                "Not Uninstall",
                "Not File Deletion",
            ),
        )
        self.acknowledgements_table = _readonly_table(
            "oswOptionalSolverPluginManifestDiscoveryRefreshAcknowledgementsTable",
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
            "oswOptionalSolverPluginManifestDiscoveryRefreshDiagnosticsTable",
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
            "oswOptionalSolverPluginManifestDiscoveryRefreshConflictsTable",
            self.tabs,
            (
                "Stack ID",
                "Built-in Source",
                "User/Plugin Source",
                "Policy",
                "Built-ins Win",
                "Refresh State",
                "Required Future Policy",
            ),
        )
        self.unsafe_claims_table = _readonly_table(
            "oswOptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimsTable",
            self.tabs,
            (
                "Stack ID",
                "Source Label",
                "Trust Label",
                "Unsafe Claim Indicators",
                "Blocked",
                "Reason",
            ),
        )
        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestDiscoveryRefreshTrustPanel",
            self.tabs,
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestDiscoveryRefreshSafetyPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName(
            "oswOptionalSolverPluginManifestDiscoveryRefreshActionsPanel"
        )

        self.tabs.addTab(self.sources_table, "Sources")
        self.tabs.addTab(self.deactivated_table, "Deactivated")
        self.tabs.addTab(self.acknowledgements_table, "Acknowledgements")
        self.tabs.addTab(self.diagnostics_table, "Diagnostics")
        self.tabs.addTab(self.conflicts_table, "Conflicts")
        self.tabs.addTab(self.unsafe_claims_table, "Unsafe Claims")
        self.tabs.addTab(self.trust_panel, "Trust")
        self.tabs.addTab(self.safety_panel, "Safety")
        self.tabs.addTab(self.actions_panel, "Actions")

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName(
            "oswOptionalSolverPluginManifestDiscoveryRefreshCloseButton"
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
        view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
    ) -> None:
        """Render the supplied discovery-refresh view-model without side effects."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_sources_table()
        self._populate_deactivated_table()
        self._populate_acknowledgements_table()
        self._populate_diagnostics_table()
        self._populate_conflicts_table()
        self._populate_unsafe_claims_table()
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

    def source_rows_text(self) -> str:
        return _table_text(self.sources_table, empty_text="No discovery sources.")

    def deactivated_rows_text(self) -> str:
        return _table_text(
            self.deactivated_table, empty_text="No deactivated candidates."
        )

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table, empty_text="No required acknowledgements."
        )

    def diagnostics_text(self) -> str:
        return _table_text(self.diagnostics_table, empty_text="No diagnostics.")

    def conflict_rows_text(self) -> str:
        return _table_text(self.conflicts_table, empty_text="No discovery conflicts.")

    def unsafe_claim_rows_text(self) -> str:
        return _table_text(self.unsafe_claims_table, empty_text="No unsafe claims.")

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def redacted_summary_text(self) -> str:
        """Return an in-memory redacted summary; writes no files."""

        payload = render_optional_solver_plugin_manifest_discovery_refresh_summary(
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
            "QDialog#oswOptionalSolverPluginManifestDiscoveryRefreshPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverPluginManifestDiscoveryRefreshSummary {"
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
            "oswOptionalSolverPluginManifestDiscoveryRefreshActionStatePanel",
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

    def _populate_sources_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.display_name,
                row.source_type,
                row.source_label or "not supplied",
                row.source_reference_display or "not supplied",
                row.trust_label,
                row.discovery_source_state,
                row.activation_state,
                row.refresh_mode,
                "included" if row.included else "excluded",
                row.exclusion_reason or "none",
                row.readiness,
                "; ".join(row.blockers) or "none",
                "; ".join(row.warnings) or "none",
                "; ".join(row.required_acknowledgements) or "none",
                "; ".join(row.unsafe_claim_indicators) or "none",
                row.built_in_relationship or "not supplied",
                "yes" if row.redacted_source_reference else "no",
            )
            for row in self._view_model.source_rows
        ]
        _populate_table(self.sources_table, rows)

    def _populate_deactivated_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.source_label,
                row.trust_label,
                row.deactivated_state,
                "yes" if row.excluded_by_default else "no",
                row.source_reference_display or "not supplied",
                row.not_validation_failure_text,
                row.not_uninstall_text,
                row.not_file_deletion_text,
            )
            for row in self._view_model.deactivated_rows
        ]
        _populate_table(self.deactivated_table, rows)

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

    def _populate_conflicts_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.built_in_source,
                row.user_plugin_source or "not supplied",
                row.conflict_policy,
                "yes" if row.built_ins_win_default else "no",
                row.refresh_state,
                row.required_future_policy,
            )
            for row in self._view_model.conflict_rows
        ]
        _populate_table(self.conflicts_table, rows)

    def _populate_unsafe_claims_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.source_label,
                row.trust_label,
                "; ".join(row.unsafe_claim_indicators) or "none",
                "yes" if row.blocked else "no",
                row.reason,
            )
            for row in self._view_model.unsafe_claim_rows
        ]
        _populate_table(self.unsafe_claims_table, rows)

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
        action_state: OptionalSolverPluginManifestDiscoveryRefreshActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            # Acknowledge toggles are widget-local and require an injected
            # callback; they never persist anything.
            return self._acknowledgement_callback is not None
        # Every other action (request/built-in-only/include/exclude/discovery/
        # validation/install/execute/close-issue/export) stays disabled here.
        return False

    def _effective_action_available(
        self,
        action_state: OptionalSolverPluginManifestDiscoveryRefreshActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        # Reflect the view-model's availability: unsafe actions (run discovery,
        # run validation, install, execute solver, close issue) are unavailable;
        # other future actions render as available-but-disabled (future-only).
        return bool(action_state.available)

    def _effective_action_reason(
        self,
        action_state: OptionalSolverPluginManifestDiscoveryRefreshActionState,
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
    view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest discovery refresh: "
        f"mode={summary.refresh_mode}; "
        f"state={summary.refresh_state}; "
        f"readiness={summary.readiness}; "
        f"refresh_ready={summary.refresh_ready}; "
        f"built_in={summary.built_in_source_count}; "
        f"active={summary.active_candidate_count}; "
        f"included={summary.included_candidate_count}; "
        f"deactivated_excluded={summary.deactivated_excluded_count}; "
        f"deactivated_visible={summary.deactivated_visible_count}; "
        f"conflict_blocked={summary.conflict_blocked_count}; "
        f"unsafe_claim_blocked={summary.unsafe_claim_blocked_count}; "
        f"acknowledgements_required={summary.acknowledgement_required_count}; "
        f"diagnostics={summary.diagnostic_count}; "
        f"discovery_execution_performed={summary.discovery_execution_performed}; "
        f"validation_execution_performed={summary.validation_execution_performed}; "
        f"solver_execution_performed={summary.solver_execution_performed}; "
        f"dependency_installation_performed={summary.dependency_installation_performed}; "
        f"network_fetch_performed={summary.network_fetch_performed}; "
        f"plugin_package_import_performed={summary.plugin_package_import_performed}; "
        f"issue_mutation_performed={summary.issue_mutation_performed}; "
        f"release_mutation_performed={summary.release_mutation_performed}; "
        f"certification_claimed={summary.certification_claimed}. "
        f"{summary.status_text}"
    )


def _trust_text(
    view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
) -> str:
    lines = [
        "Trust/provenance labels.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Discovery inclusion is not validation evidence.",
    ]
    if not view_model.trust_badges:
        lines.append("No trust/provenance badges.")
    for badge in view_model.trust_badges:
        lines.append(
            f"source_type={badge.source_type} | trust_label={badge.trust_label} | "
            f"source_label={badge.source_label or 'not supplied'} | "
            f"discovery_source_state={badge.discovery_source_state} | "
            f"activation_state={badge.activation_state} | {badge.warning_text} | "
            f"{badge.trust_label_is_not_certification} | "
            f"{badge.discovery_inclusion_is_not_validation_evidence}"
        )
    return "\n".join(lines)


def _safety_text(
    view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
) -> str:
    lines = [
        "Optional solver plugin manifest discovery-refresh safety boundary.",
        "Discovery-refresh GUI is view-model driven and non-executing.",
        "Discovery refresh is not validation.",
        "Discovery refresh is not dependency installation.",
        "Discovery refresh is not solver execution.",
        "Discovery refresh is not issue closure.",
        "Discovery refresh is not certification.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Discovery inclusion is not validation evidence.",
        "Refresh-ready is not validation evidence.",
        "No runtime discovery integration.",
        "No passive discovery behavior change.",
        "No activation persistence.",
        "No deactivation persistence.",
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
    action_state: OptionalSolverPluginManifestDiscoveryRefreshActionState,
) -> str:
    return "oswOptionalSolverPluginManifestDiscoveryRefreshAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


__all__ = [
    "OptionalSolverPluginManifestDiscoveryRefreshPanel",
]
