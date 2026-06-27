"""PySide persistence review panel for optional solver plugin manifests.

This panel is a view-model-driven review surface over the OSW-EXP-092 pure
persistence view-model and, when supplied, the OSW-EXP-093 in-memory schema
model. It renders persistence readiness, sources, candidates, acknowledgements,
diagnostics, redaction/privacy rows, schema/migration rows, stale-source rows,
conflicts, unsafe claims, evidence/history retention, trust/provenance badges,
non-action flags, safety guidance, and disabled/future action states.

It implements no runtime persistence behavior. It does not create settings files,
runtime state files, schema files, reloadable bundles, ProjectSchema mutations,
file dialog behavior, save dialog behavior, reload behavior, export behavior,
clipboard behavior, folder actions, CLI behavior, automatic activation, trust
restoration, file restoration/rewrite/deletion, dependency installation or
uninstall, solver uninstall, discovery execution, validation execution, solver
execution, plugin package import, directory scan, network fetch, issue/release
mutation, tag/asset mutation, version bump, validation-pass/fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

Acknowledgement interaction is widget-local and non-persistent, driven by an
injected pure callback that rebuilds a supplied view-model.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_persistence_schema_model import (
    OptionalSolverPluginManifestPersistenceSchemaModel,
)
from osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel import (
    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
    ACK_LOCAL_PATH_REDACTION_REVIEWED,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
    ACK_PERSISTENCE_NO_SOLVER_EXECUTION,
    ACK_PERSISTENCE_NOT_INSTALL,
    ACK_PERSISTENCE_NOT_ISSUE_CLOSURE,
    ACK_PERSISTENCE_NOT_RELEASE_MUTATION,
    ACK_PERSISTENCE_NOT_TRUST_RESTORATION,
    ACK_PERSISTENCE_NOT_VALIDATION,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    OptionalSolverPluginManifestPersistenceAction,
    OptionalSolverPluginManifestPersistenceActionState,
    OptionalSolverPluginManifestPersistenceViewModel,
    render_optional_solver_plugin_manifest_persistence_summary,
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
    [Mapping[str, bool]], OptionalSolverPluginManifestPersistenceViewModel
]

_Action = OptionalSolverPluginManifestPersistenceAction

_ACK_ACTION_TO_ID: dict[str, str] = {
    _Action.ACKNOWLEDGE_PERSISTENCE_NOT_VALIDATION.value: (
        ACK_PERSISTENCE_NOT_VALIDATION
    ),
    _Action.ACKNOWLEDGE_PERSISTENCE_NOT_TRUST_RESTORATION.value: (
        ACK_PERSISTENCE_NOT_TRUST_RESTORATION
    ),
    _Action.ACKNOWLEDGE_NO_INSTALL.value: ACK_PERSISTENCE_NOT_INSTALL,
    _Action.ACKNOWLEDGE_NO_SOLVER_EXECUTION.value: (
        ACK_PERSISTENCE_NO_SOLVER_EXECUTION
    ),
    _Action.ACKNOWLEDGE_NO_ISSUE_CLOSURE.value: ACK_PERSISTENCE_NOT_ISSUE_CLOSURE,
    _Action.ACKNOWLEDGE_NO_RELEASE_MUTATION.value: (
        ACK_PERSISTENCE_NOT_RELEASE_MUTATION
    ),
    _Action.ACKNOWLEDGE_LOCAL_PATH_REDACTION_REVIEWED.value: (
        ACK_LOCAL_PATH_REDACTION_REVIEWED
    ),
    _Action.ACKNOWLEDGE_ACKNOWLEDGEMENTS_MAY_EXPIRE.value: (
        ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE
    ),
    _Action.ACKNOWLEDGE_STALE_SOURCE_REQUIRES_REPREVIEW.value: (
        ACK_STALE_SOURCE_REQUIRES_REPREVIEW
    ),
    _Action.ACKNOWLEDGE_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED.value: (
        ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED
    ),
    _Action.ACKNOWLEDGE_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD.value: (
        ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD
    ),
    _Action.ACKNOWLEDGE_NO_DISCOVERY_EXECUTION.value: ACK_NO_DISCOVERY_EXECUTION,
    _Action.ACKNOWLEDGE_NO_PLUGIN_PACKAGE_IMPORT.value: (
        ACK_NO_PLUGIN_PACKAGE_IMPORT
    ),
    _Action.ACKNOWLEDGE_TRUST_LABEL_NOT_CERTIFICATION.value: (
        ACK_TRUST_LABEL_NOT_CERTIFICATION
    ),
}

_ACTION_REASON_OVERRIDES: dict[str, str] = {
    _Action.REQUEST_PERSISTENCE.value: (
        "Persistence request is display/preview-only; persistence writes are a "
        "future gate and no state is saved."
    ),
    _Action.REVIEW_REDACTION.value: (
        "Redaction review is display-only here; future persistence gates must "
        "decide how reviewed paths are handled."
    ),
    _Action.SAVE_STATE.value: (
        "Saving persistence state is disabled; file persistence is a future gate."
    ),
    _Action.CREATE_SETTINGS_FILE.value: (
        "Settings file creation is disabled; settings integration is a future gate."
    ),
    _Action.MUTATE_PROJECT_SCHEMA.value: (
        "ProjectSchema mutation is disabled; schema integration is a future gate."
    ),
    _Action.RELOAD_STATE.value: (
        "Reload behavior is disabled; persisted-state reload is a future gate."
    ),
    _Action.EXPORT_SUMMARY.value: (
        "Export behavior is disabled; this panel exposes only in-memory redacted "
        "summary text."
    ),
    _Action.CREATE_RELOADABLE_BUNDLE.value: (
        "Reloadable bundle creation is disabled; bundle behavior is a future gate."
    ),
    _Action.AUTOMATIC_ACTIVATION.value: (
        "Automatic activation is unavailable from the persistence GUI."
    ),
    _Action.TRUST_RESTORATION.value: (
        "Trust restoration is unavailable from the persistence GUI."
    ),
    _Action.RUN_DISCOVERY.value: (
        "Discovery execution is unavailable from the persistence GUI."
    ),
    _Action.RUN_VALIDATION.value: "Validation requires a separate OSW-VALID gate.",
    _Action.INSTALL_DEPENDENCY.value: (
        "Dependency installation is unavailable from the persistence GUI."
    ),
    _Action.UNINSTALL_DEPENDENCY.value: (
        "Dependency uninstall is unavailable from the persistence GUI."
    ),
    _Action.UNINSTALL_SOLVER.value: (
        "Solver uninstall is unavailable from the persistence GUI."
    ),
    _Action.EXECUTE_SOLVER.value: (
        "Solver execution is unavailable from the persistence GUI."
    ),
    _Action.CLOSE_ISSUE.value: (
        "Issue closure requires separate validation and closure gates."
    ),
    _Action.MUTATE_RELEASE.value: (
        "Release, tag, and asset mutation require separate release gates."
    ),
}


class OptionalSolverPluginManifestPersistencePanel(_BaseDialog):
    """View-model/schema-model persistence review panel (non-writing)."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestPersistenceViewModel | None = None,
        schema_model: OptionalSolverPluginManifestPersistenceSchemaModel | None = None,
        acknowledgement_callback: AcknowledgementCallback | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestPersistencePanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Persistence")
        self.resize(1300, 900)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model
            or OptionalSolverPluginManifestPersistenceViewModel.unavailable()
        )
        self._schema_model = schema_model
        self._acknowledgement_callback = acknowledgement_callback
        self._acknowledgements: dict[str, bool] = {}
        self._disabled_action_reasons: dict[str, str] = {}
        self._action_buttons: dict[str, Any] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName(
            "oswOptionalSolverPluginManifestPersistenceSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestPersistenceTabs")
        root.addWidget(self.tabs, 1)

        self.sources_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceSourcesTable",
            self.tabs,
            (
                "Source ID",
                "Source Type",
                "Source Label",
                "Source Reference",
                "Trust Label",
                "Persistence Kind",
                "Redaction Status",
                "Raw Path Blocked",
                "Fingerprint",
                "Stale Source",
                "Re-preview Required",
                "Blockers",
                "Warnings",
                "Redacted",
            ),
        )
        self.candidates_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceCandidatesTable",
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
                "Reactivation State",
                "Discovery Refresh State",
                "Persistence State",
                "Readiness",
                "Blockers",
                "Warnings",
                "Required Acks",
                "Diagnostics",
                "Built-in Relationship",
                "Shared-stack Indicators",
                "Stale Source",
                "Re-preview Required",
                "Deactivation History",
                "Reactivation History",
                "Historical Evidence",
                "Redaction",
                "Redacted",
                "Untrusted",
            ),
        )
        self.acknowledgements_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceAcknowledgementsTable",
            self.tabs,
            (
                "Acknowledgement",
                "Label",
                "Required",
                "Satisfied",
                "Persisted",
                "Expires Reload",
                "Expires Source",
                "Expires Schema",
                "Expires Unsafe Claim",
                "Blocking",
                "Reason",
                "Related",
                "Warning",
            ),
        )
        self.diagnostics_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceDiagnosticsTable",
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
        self.redaction_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceRedactionTable",
            self.tabs,
            (
                "Raw Reference",
                "Display Reference",
                "Redaction Status",
                "Unredacted Path Blocked",
                "Redaction Reviewed",
                "Secret-like Blocked",
                "Privacy Warning",
            ),
        )
        self.schema_migration_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceSchemaMigrationTable",
            self.tabs,
            (
                "Schema Version",
                "Present",
                "Migration Required",
                "Migration Status",
                "Migration Notes",
                "Blocker",
                "Warning",
                "Creates Schema File",
            ),
        )
        self.schema_model_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestPersistenceSchemaModel",
            self.tabs,
        )
        self.stale_sources_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceStaleSourcesTable",
            self.tabs,
            (
                "Stale Source",
                "Re-preview Required",
                "Source Reference",
                "Redacted",
                "Not Silently Trusted",
                "File IO Performed",
                "File Restoration",
                "File Rewrite",
                "File Deletion",
                "Future Policy",
            ),
        )
        self.conflicts_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceConflictsTable",
            self.tabs,
            (
                "Stack ID",
                "Built-in Source",
                "User/Plugin Source",
                "Activation State",
                "Deactivation State",
                "Reactivation State",
                "Persistence State",
                "Built-ins Win",
                "User/Plugin Does Not Override",
                "Conflict Visible",
                "Required Future Policy",
            ),
        )
        self.unsafe_claims_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceUnsafeClaimsTable",
            self.tabs,
            (
                "Claim ID",
                "Related",
                "Claim Text",
                "Blocked",
                "Warning",
                "Not Accepted",
            ),
        )
        self.evidence_history_table = _readonly_table(
            "oswOptionalSolverPluginManifestPersistenceEvidenceHistoryTable",
            self.tabs,
            (
                "Stack ID",
                "Deactivation History",
                "Deactivation Retained",
                "Reactivation History",
                "Reactivation Retained",
                "Historical Evidence",
                "Historical Evidence Retained",
                "Not Validation Success",
                "Not Validation Failure",
                "Skipped-missing Remains",
                "Issue Closure Not Implied",
                "Evidence Not Deleted/Rewritten",
            ),
        )

        self.schema_tab = QtWidgets.QWidget(self.tabs)
        schema_layout = QtWidgets.QVBoxLayout(self.schema_tab)
        schema_layout.setContentsMargins(0, 0, 0, 0)
        schema_layout.setSpacing(6)
        schema_layout.addWidget(self.schema_migration_table, 2)
        schema_layout.addWidget(self.schema_model_panel, 1)

        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestPersistenceTrust", self.tabs
        )
        self.non_action_flags_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestPersistenceNonActions", self.tabs
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestPersistenceSafety", self.tabs
        )
        self.action_state_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestPersistenceActionState", self.tabs
        )

        self.tabs.addTab(self.sources_table, "Sources")
        self.tabs.addTab(self.candidates_table, "Candidates")
        self.tabs.addTab(self.acknowledgements_table, "Acknowledgements")
        self.tabs.addTab(self.diagnostics_table, "Diagnostics")
        self.tabs.addTab(self.redaction_table, "Redaction")
        self.tabs.addTab(self.schema_tab, "Schema")
        self.tabs.addTab(self.stale_sources_table, "Stale Sources")
        self.tabs.addTab(self.conflicts_table, "Conflicts")
        self.tabs.addTab(self.unsafe_claims_table, "Unsafe Claims")
        self.tabs.addTab(self.evidence_history_table, "Evidence")
        self.tabs.addTab(self.trust_panel, "Trust")
        self.tabs.addTab(self.non_action_flags_panel, "Non-actions")
        self.tabs.addTab(self.safety_panel, "Safety")
        self.tabs.addTab(self._build_actions_panel(), "Actions")

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.setObjectName("oswOptionalSolverPluginManifestPersistenceButtons")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.set_theme_tokens(self._tokens)
        self._populate_all()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {tokens.bg_panel};
                color: {tokens.text_primary};
            }}
            QTabWidget::pane {{
                border: 1px solid {tokens.border};
            }}
            QHeaderView::section {{
                background: {tokens.bg_panel_alt};
                color: {tokens.text_primary};
                border: 1px solid {tokens.border};
                padding: 4px;
            }}
            QTableWidget, QPlainTextEdit {{
                background: {tokens.bg_viewport};
                color: {tokens.text_primary};
                border: 1px solid {tokens.border};
            }}
            QPushButton {{
                background: {tokens.bg_panel_alt};
                color: {tokens.text_primary};
                border: 1px solid {tokens.border};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:disabled {{
                color: {tokens.text_muted};
            }}
            """
        )

    def set_view_model(
        self,
        view_model: OptionalSolverPluginManifestPersistenceViewModel,
        *,
        schema_model: OptionalSolverPluginManifestPersistenceSchemaModel | None = None,
    ) -> None:
        self._view_model = view_model
        if schema_model is not None:
            self._schema_model = schema_model
        self._populate_all()

    def set_schema_model(
        self,
        schema_model: OptionalSolverPluginManifestPersistenceSchemaModel | None,
    ) -> None:
        self._schema_model = schema_model
        self.schema_model_panel.setPlainText(_schema_model_text(schema_model))
        self.non_action_flags_panel.setPlainText(
            _non_action_flags_text(self._view_model, self._schema_model)
        )

    def apply_acknowledgement(
        self,
        acknowledgement_id: str,
        satisfied: bool = True,
    ) -> None:
        if self._acknowledgement_callback is None:
            return
        self._acknowledgements[str(acknowledgement_id)] = bool(satisfied)
        self._view_model = self._acknowledgement_callback(dict(self._acknowledgements))
        self._populate_all()

    def acknowledgement_state(self) -> dict[str, bool]:
        return dict(self._acknowledgements)

    def summary_text(self) -> str:
        return self.summary_label.text()

    def source_rows_text(self) -> str:
        return _table_text(self.sources_table, empty_text="No persistence sources.")

    def candidate_rows_text(self) -> str:
        return _table_text(self.candidates_table, empty_text="No persistence candidates.")

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table,
            empty_text="No persistence acknowledgements.",
        )

    def diagnostics_text(self) -> str:
        return _table_text(
            self.diagnostics_table,
            empty_text="No persistence diagnostics.",
        )

    def redaction_rows_text(self) -> str:
        return _table_text(self.redaction_table, empty_text="No redaction rows.")

    def schema_migration_rows_text(self) -> str:
        return _table_text(
            self.schema_migration_table,
            empty_text="No schema/migration rows.",
        )

    def schema_model_text(self) -> str:
        return self.schema_model_panel.toPlainText()

    def stale_source_rows_text(self) -> str:
        return _table_text(self.stale_sources_table, empty_text="No stale sources.")

    def conflict_rows_text(self) -> str:
        return _table_text(self.conflicts_table, empty_text="No conflicts.")

    def unsafe_claim_rows_text(self) -> str:
        return _table_text(self.unsafe_claims_table, empty_text="No unsafe claims.")

    def evidence_history_rows_text(self) -> str:
        return _table_text(
            self.evidence_history_table,
            empty_text="No evidence/history rows.",
        )

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def non_action_flags_text(self) -> str:
        return self.non_action_flags_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def redacted_summary_text(self) -> str:
        summary = render_optional_solver_plugin_manifest_persistence_summary(
            self._view_model
        )
        lines: list[str] = []
        for key in sorted(summary):
            value = summary[key]
            if isinstance(value, list):
                lines.append(f"{key}: {len(value)} item(s)")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def available_action_names(self) -> list[str]:
        return [
            action_state.action.value
            for action_state in self._view_model.actions
            if self._effective_action_enabled(action_state)
        ]

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def _build_actions_panel(self) -> object:
        panel = QtWidgets.QWidget(self.tabs)
        panel.setObjectName("oswOptionalSolverPluginManifestPersistenceActions")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        button_grid = QtWidgets.QGridLayout()
        button_grid.setSpacing(4)
        for index, action_state in enumerate(self._view_model.actions):
            action_name = action_state.action.value
            button = QtWidgets.QPushButton(action_state.label, panel)
            button.setObjectName(_action_button_object_name(action_state))
            button.clicked.connect(
                lambda _checked=False, name=action_name: self._handle_action(name)
            )
            self._action_buttons[action_name] = button
            button_grid.addWidget(button, index // 3, index % 3)

        layout.addLayout(button_grid)
        layout.addWidget(self.action_state_panel, 1)
        return panel

    def _handle_action(self, action_name: str) -> None:
        acknowledgement_id = _ACK_ACTION_TO_ID.get(action_name)
        if acknowledgement_id is not None:
            current = self._acknowledgements.get(acknowledgement_id, False)
            self.apply_acknowledgement(acknowledgement_id, not current)

    def _populate_all(self) -> None:
        self.summary_label.setText(_summary_text(self._view_model))
        self._populate_sources()
        self._populate_candidates()
        self._populate_acknowledgements()
        self._populate_diagnostics()
        self._populate_redaction()
        self._populate_schema_migration()
        self.schema_model_panel.setPlainText(_schema_model_text(self._schema_model))
        self._populate_stale_sources()
        self._populate_conflicts()
        self._populate_unsafe_claims()
        self._populate_evidence_history()
        self.trust_panel.setPlainText(_trust_text(self._view_model))
        self.non_action_flags_panel.setPlainText(
            _non_action_flags_text(self._view_model, self._schema_model)
        )
        self.safety_panel.setPlainText(_safety_text(self._view_model))
        self._populate_action_state()

    def _populate_sources(self) -> None:
        rows = [
            (
                row.source_id,
                row.source_type,
                row.source_label,
                row.source_reference_display or "not supplied",
                row.trust_label,
                row.persistence_source_kind,
                row.redaction_status,
                _yes_no(row.raw_path_blocked),
                row.source_fingerprint_display or "not supplied",
                row.stale_source_state or "fresh",
                _yes_no(row.repreview_required),
                _joined(row.blockers),
                _joined(row.warnings),
                _yes_no(row.redacted_source_reference),
            )
            for row in self._view_model.source_rows
        ]
        _populate_table(self.sources_table, rows)

    def _populate_candidates(self) -> None:
        rows = [
            (
                row.stack_id,
                row.display_name,
                row.source_type,
                row.source_label,
                row.source_reference_display or "not supplied",
                row.trust_label,
                row.activation_state,
                row.deactivation_state,
                row.reactivation_state,
                row.discovery_refresh_state,
                row.persistence_state,
                row.readiness,
                _joined(row.blockers),
                _joined(row.warnings),
                _joined(row.required_acknowledgements),
                _joined(row.diagnostics),
                row.built_in_relationship,
                _joined(row.shared_stack_indicators),
                row.stale_source_state,
                _yes_no(row.repreview_required),
                row.deactivation_history_state,
                row.reactivation_history_state,
                row.historical_evidence_state,
                row.redaction_status,
                _yes_no(row.redacted_source_reference),
                _yes_no(row.is_untrusted),
            )
            for row in self._view_model.candidate_rows
        ]
        _populate_table(self.candidates_table, rows)

    def _populate_acknowledgements(self) -> None:
        rows = [
            (
                row.acknowledgement_id,
                row.label,
                _yes_no(row.required),
                _yes_no(row.satisfied),
                _yes_no(row.persisted),
                _yes_no(row.expires_on_reload),
                _yes_no(row.expires_on_source_change),
                _yes_no(row.expires_on_schema_change),
                _yes_no(row.expires_on_unsafe_claim),
                _yes_no(row.blocking),
                row.reason,
                row.related,
                row.warning_text,
            )
            for row in self._view_model.acknowledgement_rows
        ]
        _populate_table(self.acknowledgements_table, rows)

    def _populate_diagnostics(self) -> None:
        rows = [
            (
                row.severity,
                row.category,
                row.code,
                row.message,
                row.source_reference_display,
                row.stack_id,
                row.suggested_fix,
                _yes_no(row.blocker),
            )
            for row in self._view_model.diagnostics
        ]
        _populate_table(self.diagnostics_table, rows)

    def _populate_redaction(self) -> None:
        rows = [
            (
                _yes_no(row.raw_reference_supplied),
                row.display_reference or "not supplied",
                row.redaction_status,
                _yes_no(row.unredacted_path_blocked),
                _yes_no(row.redaction_reviewed),
                _yes_no(row.secret_like_content_blocked),
                row.privacy_warning_text,
            )
            for row in self._view_model.redaction_rows
        ]
        _populate_table(self.redaction_table, rows)

    def _populate_schema_migration(self) -> None:
        rows = [
            (
                row.schema_version_display or "not supplied",
                _yes_no(row.schema_version_present),
                _yes_no(row.migration_required),
                row.migration_status,
                row.migration_notes_display,
                row.blocker_text,
                row.warning_text,
                _yes_no(not row.this_gate_creates_no_schema_file),
            )
            for row in self._view_model.schema_migration_rows
        ]
        _populate_table(self.schema_migration_table, rows)

    def _populate_stale_sources(self) -> None:
        rows = [
            (
                row.stale_source_state or "fresh",
                _yes_no(row.repreview_required),
                row.source_reference_display or "not supplied",
                _yes_no(row.redacted_source_reference),
                row.missing_moved_changed_not_silently_trusted,
                _yes_no(row.file_io_performed),
                _yes_no(row.file_restoration_performed),
                _yes_no(row.file_rewrite_performed),
                _yes_no(row.file_deletion_performed),
                row.future_policy_required_if_source_cannot_be_repreviewed,
            )
            for row in self._view_model.stale_source_rows
        ]
        _populate_table(self.stale_sources_table, rows)

    def _populate_conflicts(self) -> None:
        rows = [
            (
                row.stack_id,
                row.built_in_source,
                row.user_plugin_source,
                row.activation_state,
                row.deactivation_state,
                row.reactivation_state,
                row.persistence_state,
                _yes_no(row.built_ins_win_default),
                row.persisted_user_plugin_state_does_not_override_built_ins_silently,
                row.conflicts_remain_visible_after_reload,
                row.required_future_policy,
            )
            for row in self._view_model.conflict_rows
        ]
        _populate_table(self.conflicts_table, rows)

    def _populate_unsafe_claims(self) -> None:
        rows = [
            (
                row.claim_id,
                row.related,
                row.claim_text,
                _yes_no(row.blocked),
                row.warning_text,
                row.unsafe_claims_not_accepted_by_persistence,
            )
            for row in self._view_model.unsafe_claim_rows
        ]
        _populate_table(self.unsafe_claims_table, rows)

    def _populate_evidence_history(self) -> None:
        rows = [
            (
                row.stack_id,
                row.deactivation_history_state,
                _yes_no(row.deactivation_history_retained),
                row.reactivation_history_state,
                _yes_no(row.reactivation_history_retained),
                row.historical_evidence_state,
                _yes_no(row.historical_validation_evidence_retained),
                row.persisted_state_not_validation_success,
                row.persisted_state_not_validation_failure,
                row.skipped_missing_remains_text,
                row.issue_closure_not_implied_text,
                row.evidence_not_deleted_or_rewritten_text,
            )
            for row in self._view_model.evidence_history_rows
        ]
        _populate_table(self.evidence_history_table, rows)

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
            scope_text = (
                "widget-local; non-persistent"
                if enabled
                else "non-writing; non-persistent"
            )
            lines.append(
                f"{action_name}: {availability}; {enabled_text}; {future_text}; "
                f"{scope_text}"
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
        action_state: OptionalSolverPluginManifestPersistenceActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        return False

    def _effective_action_available(
        self,
        action_state: OptionalSolverPluginManifestPersistenceActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        return bool(action_state.available)

    def _effective_action_reason(
        self,
        action_state: OptionalSolverPluginManifestPersistenceActionState,
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
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest persistence: "
        f"readiness={summary.readiness}; "
        f"state={summary.persistence_state}; "
        f"state_scope={summary.state_scope}; "
        f"schema_version={summary.schema_version_display}; "
        f"candidates={summary.candidate_count}; "
        f"sources={summary.source_count}; "
        f"acknowledgements={summary.acknowledgement_count}; "
        f"acknowledgements_required={summary.acknowledgement_required_count}; "
        f"diagnostics={summary.diagnostic_count}; "
        f"warnings={summary.warning_count}; "
        f"errors={summary.error_count}; "
        f"conflicts={summary.conflict_count}; "
        f"unsafe_claims={summary.unsafe_claim_count}; "
        f"stale_sources={summary.stale_source_count}; "
        f"redaction_required={summary.redaction_required_count}; "
        f"migration_required={summary.migration_required_count}; "
        f"evidence_retained={summary.evidence_retained_count}; "
        f"history_retained={summary.history_retained_count}; "
        f"persistence_ready={summary.persistence_ready_count}; "
        f"persistence_blocked={summary.persistence_blocked_count}; "
        f"persistence_performed={summary.persistence_performed}; "
        f"file_write_performed={summary.file_write_performed}; "
        f"settings_file_created={summary.settings_file_created}; "
        "runtime_state_file_created=False; "
        "schema_file_created=False; "
        f"project_schema_mutation_performed={summary.project_schema_mutation_performed}; "
        f"automatic_activation_performed={summary.automatic_activation_performed}; "
        f"trust_restoration_performed={summary.trust_restoration_performed}; "
        f"file_restore_performed={summary.file_restore_performed}; "
        f"file_rewrite_performed={summary.file_rewrite_performed}; "
        f"file_deletion_performed={summary.file_deletion_performed}; "
        f"dependency_installation_performed={summary.dependency_installation_performed}; "
        f"dependency_uninstall_performed={summary.dependency_uninstall_performed}; "
        f"solver_uninstall_performed={summary.solver_uninstall_performed}; "
        f"plugin_package_import_performed={summary.plugin_package_import_performed}; "
        f"directory_scan_performed={summary.directory_scan_performed}; "
        f"network_fetch_performed={summary.network_fetch_performed}; "
        f"discovery_execution_performed={summary.discovery_execution_performed}; "
        f"validation_execution_performed={summary.validation_execution_performed}; "
        f"solver_execution_performed={summary.solver_execution_performed}; "
        f"export_performed={summary.export_performed}; "
        f"reload_performed={summary.reload_performed}; "
        f"reloadable_bundle_created={summary.reloadable_bundle_created}; "
        f"issue_mutation_performed={summary.issue_mutation_performed}; "
        f"issue_closure_claimed={summary.issue_closure_claimed}; "
        f"release_mutation_performed={summary.release_mutation_performed}; "
        f"tag_mutation_performed={summary.tag_mutation_performed}; "
        f"asset_mutation_performed={summary.asset_mutation_performed}; "
        f"version_bump_performed={summary.version_bump_performed}; "
        f"validation_pass_claimed={summary.validation_pass_claimed}; "
        f"validation_fail_claimed={summary.validation_fail_claimed}; "
        f"certification_claimed={summary.certification_claimed}; "
        f"not_validation_evidence={summary.not_validation_evidence}; "
        "file_dialog_behavior=False; save_dialog_behavior=False; "
        "clipboard_behavior=False; open_output_folder_behavior=False; "
        "cli_behavior=False. "
        f"{summary.status_text}"
    )


def _schema_model_text(
    schema_model: OptionalSolverPluginManifestPersistenceSchemaModel | None,
) -> str:
    if schema_model is None:
        return "No persistence schema model supplied."
    header = schema_model.header
    lines = [
        "Persistence schema model records (in-memory only).",
        f"schema_model_schema_version={header.schema_version or 'not supplied'}",
        f"schema_model_supported={header.schema_version_supported}",
        f"schema_model_state_scope={header.state_scope}",
        f"schema_model_state_kind={header.state_kind}",
        f"schema_model_migration_required={header.migration_required}",
        f"schema_model_source_count={len(schema_model.sources)}",
        f"schema_model_candidate_count={len(schema_model.candidates)}",
        f"schema_model_acknowledgement_count={len(schema_model.acknowledgements)}",
        f"schema_model_diagnostic_count={len(schema_model.diagnostics)}",
        f"schema_model_conflict_count={len(schema_model.conflicts)}",
        f"schema_model_unsafe_claim_count={len(schema_model.unsafe_claims)}",
        f"redaction_policy_id={header.redaction_policy_id}",
        f"raw_absolute_paths_allowed={schema_model.redaction_policy.raw_absolute_paths_allowed}",
        f"this_gate_creates_schema_file={schema_model.this_gate_creates_schema_file}",
        f"not_validation_evidence={schema_model.not_validation_evidence}",
        "Schema model non-action flags:",
    ]
    for name in _SCHEMA_NON_ACTION_FLAG_NAMES:
        lines.append(f"schema_model_{name}={getattr(schema_model.non_action_flags, name)}")
    return "\n".join(lines)


def _trust_text(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
) -> str:
    lines = [
        "Trust/provenance labels.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Persisted state is not validation evidence.",
        "Persistence is not trust restoration.",
        "Persistence is not automatic activation.",
    ]
    if not view_model.trust_badges:
        lines.append("No trust/provenance badges.")
    for badge in view_model.trust_badges:
        lines.append(
            f"source_type={badge.source_type} | trust_label={badge.trust_label} | "
            f"source_label={badge.source_label or 'not supplied'} | "
            f"activation_state={badge.activation_state} | "
            f"deactivation_state={badge.deactivation_state} | "
            f"reactivation_state={badge.reactivation_state} | "
            f"discovery_refresh_state={badge.discovery_refresh_state} | "
            f"persistence_state={badge.persistence_state} | {badge.warning_text} | "
            f"{badge.trust_label_is_not_certification} | "
            f"{badge.persisted_state_is_not_validation_evidence} | "
            f"{badge.user_plugin_manifests_untrusted_by_default}"
        )
    return "\n".join(lines)


def _non_action_flags_text(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
    schema_model: OptionalSolverPluginManifestPersistenceSchemaModel | None,
) -> str:
    summary = view_model.summary
    lines = [
        "Persistence GUI non-actions.",
        f"persistence_performed={summary.persistence_performed}",
        f"file_write_performed={summary.file_write_performed}",
        f"settings_file_created={summary.settings_file_created}",
        "runtime_state_file_created=False",
        "schema_file_created=False",
        f"project_schema_mutation_performed={summary.project_schema_mutation_performed}",
        "file_dialog_behavior=False",
        "save_dialog_behavior=False",
        f"reload_performed={summary.reload_performed}",
        f"export_performed={summary.export_performed}",
        "clipboard_behavior=False",
        "open_output_folder_behavior=False",
        "cli_behavior=False",
        "source_behavior_mutation=False",
        f"automatic_activation_performed={summary.automatic_activation_performed}",
        f"trust_restoration_performed={summary.trust_restoration_performed}",
        f"file_restore_performed={summary.file_restore_performed}",
        f"file_rewrite_performed={summary.file_rewrite_performed}",
        f"file_deletion_performed={summary.file_deletion_performed}",
        f"dependency_installation_performed={summary.dependency_installation_performed}",
        f"dependency_uninstall_performed={summary.dependency_uninstall_performed}",
        f"solver_uninstall_performed={summary.solver_uninstall_performed}",
        f"plugin_package_import_performed={summary.plugin_package_import_performed}",
        f"directory_scan_performed={summary.directory_scan_performed}",
        f"network_fetch_performed={summary.network_fetch_performed}",
        f"discovery_execution_performed={summary.discovery_execution_performed}",
        f"validation_execution_performed={summary.validation_execution_performed}",
        f"solver_execution_performed={summary.solver_execution_performed}",
        f"issue_mutation_performed={summary.issue_mutation_performed}",
        f"release_mutation_performed={summary.release_mutation_performed}",
        f"tag_mutation_performed={summary.tag_mutation_performed}",
        f"asset_mutation_performed={summary.asset_mutation_performed}",
        f"version_bump_performed={summary.version_bump_performed}",
        f"validation_pass_claimed={summary.validation_pass_claimed}",
        f"validation_fail_claimed={summary.validation_fail_claimed}",
        f"issue_closure_claimed={summary.issue_closure_claimed}",
        f"certification_claimed={summary.certification_claimed}",
        f"not_validation_evidence={summary.not_validation_evidence}",
        (
            "third_party_manifests_trusted_by_default="
            f"{summary.third_party_manifests_trusted_by_default}"
        ),
    ]
    if schema_model is not None:
        lines.append(
            "schema_model_non_action_flags_all_false="
            f"{_schema_non_action_flags_all_false(schema_model)}"
        )
    return "\n".join(lines)


def _safety_text(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
) -> str:
    lines = [
        "Optional solver plugin manifest persistence GUI safety boundary.",
        "Persistence GUI is view-model/schema-model driven and non-writing.",
        "Persisted state is not validation evidence.",
        "Persistence is not trust restoration.",
        "Persistence is not automatic activation.",
        "Persistence is not dependency installation.",
        "Persistence is not solver execution.",
        "Persistence is not issue closure.",
        "Persistence is not release mutation.",
        "Persistence is not certification.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Stale, missing, moved, or changed sources require re-preview.",
        "Unsafe claims are blocked and not accepted by persistence.",
        "No runtime persistence behavior.",
        "No file writes.",
        "No settings file creation.",
        "No runtime state file creation.",
        "No schema file creation.",
        "No ProjectSchema mutation.",
        "No file dialog behavior.",
        "No save dialog behavior.",
        "No reload behavior.",
        "No export behavior.",
        "No clipboard behavior.",
        "No open-output-folder behavior.",
        "No CLI behavior.",
        "No source behavior mutation.",
        "No plugin package import.",
        "No directory scan.",
        "No network fetch.",
        "No discovery execution.",
        "No validation execution.",
        "No solver execution.",
        "No dependency install.",
        "No dependency uninstall.",
        "No solver uninstall.",
        "No issue mutation.",
        "No release mutation.",
        "No tag mutation.",
        "No asset mutation.",
        "No validation-pass claim.",
        "No validation-fail claim.",
        "No bundled-solver claim.",
        "No certification claim.",
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


def _yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _joined(values: object) -> str:
    if not isinstance(values, tuple):
        return str(values) if values else "none"
    joined = ", ".join(str(value) for value in values if str(value))
    return joined or "none"


def _schema_non_action_flags_all_false(
    schema_model: OptionalSolverPluginManifestPersistenceSchemaModel,
) -> bool:
    return all(
        not bool(getattr(schema_model.non_action_flags, name))
        for name in _SCHEMA_NON_ACTION_FLAG_NAMES
    )


def _action_button_object_name(
    action_state: OptionalSolverPluginManifestPersistenceActionState,
) -> str:
    return "oswOptionalSolverPluginManifestPersistenceAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


_SCHEMA_NON_ACTION_FLAG_NAMES: tuple[str, ...] = (
    "persistence_performed",
    "file_write_performed",
    "settings_file_created",
    "runtime_state_file_created",
    "project_schema_mutation_performed",
    "gui_behavior_added",
    "cli_behavior_added",
    "reload_behavior_added",
    "export_behavior_added",
    "automatic_activation_performed",
    "trust_restoration_performed",
    "file_restoration_performed",
    "file_rewrite_performed",
    "file_deletion_performed",
    "dependency_installation_performed",
    "dependency_uninstall_performed",
    "solver_uninstall_performed",
    "discovery_execution_performed",
    "validation_execution_performed",
    "solver_execution_performed",
    "issue_mutation_performed",
    "release_mutation_performed",
    "tag_mutation_performed",
    "asset_mutation_performed",
    "certification_claimed",
)


__all__ = [
    "OptionalSolverPluginManifestPersistencePanel",
]
