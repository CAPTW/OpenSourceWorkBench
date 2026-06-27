"""PySide export-summary review panel for optional solver plugin manifests.

This panel is a view-model-driven review surface over the OSW-EXP-097 pure
export-summary view-model. It renders header, section, source/provenance,
candidate, acknowledgement, diagnostic, redaction/privacy, stale-source,
conflict/shared-stack, unsafe-claim, evidence/history, limitation, trust,
non-action, safety, and disabled/future action-state records.

It implements no file export, file writes, export file creation, report file
creation, reloadable bundle creation, clipboard behavior, report attachment,
open-output-folder behavior, runtime persistence behavior, settings file
creation, runtime state file creation, schema file creation, ProjectSchema
mutation, CLI behavior, reload behavior, automatic activation, trust
restoration, file restoration/rewrite/deletion, dependency installation or
uninstall, solver uninstall, plugin package import, directory scan, network
fetch, discovery execution, validation execution, solver execution,
issue/release mutation, tag/asset mutation, version bump, validation-pass/fail
claim, issue-closure claim, bundled-solver claim, or certification claim.

Acknowledgement interaction is optional, widget-local, non-persistent, and
driven by an injected pure callback that rebuilds a supplied view-model.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_export_summary_viewmodel import (
    ACK_EXPORT_NO_SOLVER_EXECUTION,
    ACK_EXPORT_NOT_INSTALL,
    ACK_EXPORT_NOT_ISSUE_CLOSURE,
    ACK_EXPORT_NOT_PERSISTENCE,
    ACK_EXPORT_NOT_RELEASE_MUTATION,
    ACK_EXPORT_NOT_RELOADABLE_BUNDLE,
    ACK_EXPORT_NOT_TRUST_RESTORATION,
    ACK_EXPORT_NOT_VALIDATION,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_REDACTION_REVIEWED,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_UNREDACTED_PATHS_BLOCKED,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    OptionalSolverPluginManifestExportSummaryAction,
    OptionalSolverPluginManifestExportSummaryActionState,
    OptionalSolverPluginManifestExportSummaryViewModel,
    render_optional_solver_plugin_manifest_export_summary,
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
    [Mapping[str, bool]], OptionalSolverPluginManifestExportSummaryViewModel
]

_Action = OptionalSolverPluginManifestExportSummaryAction

_ACK_ACTION_TO_ID: dict[str, str] = {
    _Action.ACKNOWLEDGE_EXPORT_NOT_VALIDATION.value: ACK_EXPORT_NOT_VALIDATION,
    _Action.ACKNOWLEDGE_EXPORT_NOT_PERSISTENCE.value: ACK_EXPORT_NOT_PERSISTENCE,
    _Action.ACKNOWLEDGE_EXPORT_NOT_RELOADABLE_BUNDLE.value: (
        ACK_EXPORT_NOT_RELOADABLE_BUNDLE
    ),
    _Action.ACKNOWLEDGE_EXPORT_NOT_TRUST_RESTORATION.value: (
        ACK_EXPORT_NOT_TRUST_RESTORATION
    ),
    _Action.ACKNOWLEDGE_NO_INSTALL.value: ACK_EXPORT_NOT_INSTALL,
    _Action.ACKNOWLEDGE_NO_SOLVER_EXECUTION.value: ACK_EXPORT_NO_SOLVER_EXECUTION,
    _Action.ACKNOWLEDGE_NO_ISSUE_CLOSURE.value: ACK_EXPORT_NOT_ISSUE_CLOSURE,
    _Action.ACKNOWLEDGE_NO_RELEASE_MUTATION.value: ACK_EXPORT_NOT_RELEASE_MUTATION,
    _Action.ACKNOWLEDGE_REDACTION_REVIEWED.value: ACK_REDACTION_REVIEWED,
    _Action.ACKNOWLEDGE_UNREDACTED_PATHS_BLOCKED.value: (
        ACK_UNREDACTED_PATHS_BLOCKED
    ),
    _Action.ACKNOWLEDGE_STALE_SOURCE_REQUIRES_REPREVIEW.value: (
        ACK_STALE_SOURCE_REQUIRES_REPREVIEW
    ),
    _Action.ACKNOWLEDGE_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED.value: (
        ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED
    ),
    _Action.ACKNOWLEDGE_NO_DISCOVERY_EXECUTION.value: ACK_NO_DISCOVERY_EXECUTION,
    _Action.ACKNOWLEDGE_NO_PLUGIN_PACKAGE_IMPORT.value: ACK_NO_PLUGIN_PACKAGE_IMPORT,
    _Action.ACKNOWLEDGE_TRUST_LABEL_NOT_CERTIFICATION.value: (
        ACK_TRUST_LABEL_NOT_CERTIFICATION
    ),
}

_ACTION_REASON_OVERRIDES: dict[str, str] = {
    _Action.REVIEW_EXPORT_SUMMARY.value: (
        "Review is available through the rendered tables; no export is performed."
    ),
    _Action.REVIEW_REDACTION.value: (
        "Redaction review is display-only here; no raw path is accepted."
    ),
    _Action.WRITE_EXPORT_FILE.value: (
        "File export is disabled; file export requires a future explicit gate."
    ),
    _Action.COPY_TO_CLIPBOARD.value: (
        "Clipboard behavior is disabled; clipboard integration is a future gate."
    ),
    _Action.ATTACH_TO_REPORT.value: (
        "Report attachment is disabled; report integration is a future gate."
    ),
    _Action.CREATE_RELOADABLE_BUNDLE.value: (
        "Reloadable bundle creation is disabled; bundle behavior is a future gate."
    ),
    _Action.PERSIST_STATE.value: (
        "Persistence is disabled; persistence writers require a future gate."
    ),
    _Action.RELOAD_STATE.value: "Reload behavior is disabled; reload is a future gate.",
    _Action.MUTATE_PROJECT_SCHEMA.value: (
        "ProjectSchema mutation is disabled; ProjectSchema integration is a "
        "future gate."
    ),
    _Action.RUN_DISCOVERY.value: "Discovery execution is disabled.",
    _Action.RUN_VALIDATION.value: "Validation execution is disabled.",
    _Action.INSTALL_DEPENDENCY.value: "Dependency installation is disabled.",
    _Action.UNINSTALL_DEPENDENCY.value: "Dependency uninstall is disabled.",
    _Action.UNINSTALL_SOLVER.value: "Solver uninstall is disabled.",
    _Action.EXECUTE_SOLVER.value: "Solver execution is disabled.",
    _Action.CLOSE_ISSUE.value: "Issue closure is disabled.",
    _Action.MUTATE_RELEASE.value: "Release mutation is disabled.",
    _Action.PUSH_TAG.value: "Tag mutation is disabled.",
    _Action.UPLOAD_ASSET.value: "Asset upload is disabled.",
}


class OptionalSolverPluginManifestExportSummaryPanel(_BaseDialog):
    """View-model driven export-summary review panel (non-exporting)."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestExportSummaryViewModel | None = None,
        acknowledgement_callback: AcknowledgementCallback | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestExportSummaryPanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Export Summary")
        self.resize(1320, 900)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model or OptionalSolverPluginManifestExportSummaryViewModel.unavailable()
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
            "oswOptionalSolverPluginManifestExportSummarySummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestExportSummaryTabs")
        root.addWidget(self.tabs, 1)

        self.sections_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummarySectionsTable",
            self.tabs,
            (
                "Section ID",
                "Title",
                "Severity",
                "Visible",
                "Collapsed",
                "Limitation",
                "Blocker",
                "Lines",
                "Row Count",
                "Diagnostics",
            ),
        )
        self.sources_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummarySourcesTable",
            self.tabs,
            (
                "Source ID",
                "Source Type",
                "Source Label",
                "Source Reference",
                "Reference Redacted",
                "Trust Label",
                "Export Summary Kind",
                "Persisted State Kind",
                "Fingerprint",
                "Stale Source",
                "Re-preview Required",
                "Raw Reference Blocked",
                "Trust Label Not Certification",
                "Not Validation Evidence",
                "Built-in Authoritative",
                "Secret-like Blocked",
                "Diagnostics",
            ),
        )
        self.candidates_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryCandidatesTable",
            self.tabs,
            (
                "Stack ID",
                "Display Name",
                "Source ID",
                "Source Type",
                "Trust Label",
                "Activation State",
                "Deactivation State",
                "Reactivation State",
                "Discovery Refresh State",
                "Persistence State",
                "Export Summary State",
                "Readiness",
                "Blockers",
                "Warnings",
                "Required Acks",
                "Diagnostics",
                "Stale Source",
                "Re-preview Required",
                "Redaction",
                "Built-in Relationship",
                "Shared-stack Indicators",
                "Deactivation History",
                "Reactivation History",
                "Historical Evidence",
                "Validation Evidence",
                "Issue Closure Implied",
                "Automatic Activation Implied",
                "Trusted Source Implied",
                "Validation Evidence Implied",
                "Untrusted",
                "Built-in Authoritative",
            ),
        )
        self.acknowledgements_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryAcknowledgementsTable",
            self.tabs,
            (
                "Acknowledgement",
                "Label",
                "Required",
                "Satisfied",
                "Persisted",
                "Blocking",
                "Reason",
                "Related Candidate",
                "Related Source",
                "Warning",
            ),
        )
        self.diagnostics_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryDiagnosticsTable",
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
            "oswOptionalSolverPluginManifestExportSummaryRedactionTable",
            self.tabs,
            (
                "Raw Reference",
                "Display Reference",
                "Redaction Status",
                "Redaction Required",
                "Unredacted Path Blocked",
                "Redaction Reviewed",
                "Secret-like Blocked",
                "Privacy Warning",
                "Fingerprint Not Trust Signal",
            ),
        )
        self.stale_sources_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryStaleSourcesTable",
            self.tabs,
            (
                "Stale Source",
                "Re-preview Required",
                "Source Reference",
                "Redacted",
                "Old Preview Data",
                "File IO",
                "File Restoration",
                "File Rewrite",
                "File Deletion",
                "Future Policy",
            ),
        )
        self.conflicts_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryConflictsTable",
            self.tabs,
            (
                "Stack ID",
                "Built-in Source",
                "User/Plugin Source",
                "Active State",
                "Deactivated State",
                "Reactivation State",
                "Persistence State",
                "Export Summary State",
                "Built-ins Win",
                "Conflict Visible",
                "Exported State Does Not Override",
                "Future Policy",
            ),
        )
        self.unsafe_claims_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryUnsafeClaimsTable",
            self.tabs,
            (
                "Claim ID",
                "Related Candidate",
                "Related Source",
                "Claim Text",
                "Blocked",
                "Warning",
                "Accepted By Export Summary",
            ),
        )
        self.evidence_history_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryEvidenceHistoryTable",
            self.tabs,
            (
                "Stack ID",
                "Deactivation History Retained",
                "Reactivation History Retained",
                "Historical Evidence Retained",
                "Skipped Missing Remains",
                "Issue Closure Implied",
                "Validation Success Claimed",
                "Validation Failure Claimed",
                "Evidence Deleted/Rewritten",
                "Not Validation Evidence",
            ),
        )
        self.limitations_table = _readonly_table(
            "oswOptionalSolverPluginManifestExportSummaryLimitationsTable",
            self.tabs,
            (
                "Limitation ID",
                "Title",
                "Message",
                "Severity",
                "Related Section",
                "Related Source",
                "Related Candidate",
                "Must Show",
            ),
        )
        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExportSummaryTrust",
            self.tabs,
        )
        self.non_action_flags_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExportSummaryNonActions",
            self.tabs,
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExportSummarySafety",
            self.tabs,
        )

        self.tabs.addTab(self.sections_table, "Sections")
        self.tabs.addTab(self.sources_table, "Sources")
        self.tabs.addTab(self.candidates_table, "Candidates")
        self.tabs.addTab(self.acknowledgements_table, "Acknowledgements")
        self.tabs.addTab(self.diagnostics_table, "Diagnostics")
        self.tabs.addTab(self.redaction_table, "Redaction")
        self.tabs.addTab(self.stale_sources_table, "Stale Sources")
        self.tabs.addTab(self.conflicts_table, "Conflicts")
        self.tabs.addTab(self.unsafe_claims_table, "Unsafe Claims")
        self.tabs.addTab(self.evidence_history_table, "Evidence")
        self.tabs.addTab(self.limitations_table, "Limitations")
        self.tabs.addTab(self.trust_panel, "Trust")
        self.tabs.addTab(self.non_action_flags_panel, "Non-actions")
        self.tabs.addTab(self.safety_panel, "Safety")
        self.tabs.addTab(self._build_actions_panel(), "Actions")

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.setObjectName("oswOptionalSolverPluginManifestExportSummaryButtons")
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
        view_model: OptionalSolverPluginManifestExportSummaryViewModel,
    ) -> None:
        self._view_model = view_model
        self._populate_all()

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

    def section_rows_text(self) -> str:
        return _table_text(self.sections_table, empty_text="No export-summary sections.")

    def source_rows_text(self) -> str:
        return _table_text(self.sources_table, empty_text="No export-summary sources.")

    def candidate_rows_text(self) -> str:
        return _table_text(
            self.candidates_table,
            empty_text="No export-summary candidates.",
        )

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table,
            empty_text="No export-summary acknowledgements.",
        )

    def diagnostics_text(self) -> str:
        return _table_text(
            self.diagnostics_table,
            empty_text="No export-summary diagnostics.",
        )

    def redaction_rows_text(self) -> str:
        return _table_text(self.redaction_table, empty_text="No redaction rows.")

    def stale_source_rows_text(self) -> str:
        return _table_text(
            self.stale_sources_table,
            empty_text="No stale-source rows.",
        )

    def conflict_rows_text(self) -> str:
        return _table_text(self.conflicts_table, empty_text="No conflict rows.")

    def unsafe_claim_rows_text(self) -> str:
        return _table_text(
            self.unsafe_claims_table,
            empty_text="No unsafe-claim rows.",
        )

    def evidence_history_rows_text(self) -> str:
        return _table_text(
            self.evidence_history_table,
            empty_text="No evidence/history rows.",
        )

    def limitation_rows_text(self) -> str:
        return _table_text(self.limitations_table, empty_text="No limitation rows.")

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def non_action_flags_text(self) -> str:
        return self.non_action_flags_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def redacted_summary_text(self) -> str:
        return _mapping_text(
            render_optional_solver_plugin_manifest_export_summary(self._view_model)
        )

    def available_action_names(self) -> list[str]:
        return [
            name
            for name, button in self._action_buttons.items()
            if bool(button.isEnabled())
        ]

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def _build_actions_panel(self) -> object:
        panel = QtWidgets.QWidget(self.tabs)
        panel.setObjectName("oswOptionalSolverPluginManifestExportSummaryActionsPanel")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.action_state_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExportSummaryActionState",
            panel,
        )
        layout.addWidget(self.action_state_panel, 1)
        grid_widget = QtWidgets.QWidget(panel)
        grid = QtWidgets.QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        for index, action_state in enumerate(self._view_model.actions):
            button = QtWidgets.QPushButton(action_state.label, grid_widget)
            button.setObjectName(_action_button_object_name(action_state))
            action_name = action_state.action.value
            if action_name in _ACK_ACTION_TO_ID:
                ack_id = _ACK_ACTION_TO_ID[action_name]
                button.clicked.connect(
                    lambda _checked=False, acknowledgement_id=ack_id: (
                        self.apply_acknowledgement(acknowledgement_id)
                    )
                )
            self._action_buttons[action_name] = button
            grid.addWidget(button, index // 3, index % 3)
        layout.addWidget(grid_widget)
        return panel

    def _populate_all(self) -> None:
        self.summary_label.setText(_summary_text(self._view_model))
        self._populate_sections()
        self._populate_sources()
        self._populate_candidates()
        self._populate_acknowledgements()
        self._populate_diagnostics()
        self._populate_redaction()
        self._populate_stale_sources()
        self._populate_conflicts()
        self._populate_unsafe_claims()
        self._populate_evidence_history()
        self._populate_limitations()
        self.trust_panel.setPlainText(_trust_text(self._view_model))
        self.non_action_flags_panel.setPlainText(_non_action_flags_text(self._view_model))
        self.safety_panel.setPlainText(_safety_text(self._view_model))
        self._populate_action_state()

    def _populate_sections(self) -> None:
        rows = [
            (
                row.section_id,
                row.title,
                row.severity,
                _yes_no(row.visible),
                _yes_no(row.collapsed_by_default),
                _yes_no(row.limitation),
                _yes_no(row.blocker),
                _joined(row.lines),
                str(len(row.rows)),
                _joined(row.diagnostics),
            )
            for row in self._view_model.sections
        ]
        _populate_table(self.sections_table, rows)

    def _populate_sources(self) -> None:
        rows = [
            (
                row.source_id,
                row.source_type,
                row.source_label,
                row.source_reference_display,
                _yes_no(row.source_reference_redacted),
                row.trust_label,
                row.export_summary_kind,
                row.persisted_state_kind,
                row.source_fingerprint_display,
                row.stale_source_state,
                _yes_no(row.repreview_required),
                _yes_no(row.raw_reference_blocked),
                _yes_no(row.trust_label_not_certification),
                _yes_no(row.not_validation_evidence),
                _yes_no(row.built_in_authoritative),
                _yes_no(row.secret_like_content_blocked),
                _joined(row.diagnostics),
            )
            for row in self._view_model.source_rows
        ]
        _populate_table(self.sources_table, rows)

    def _populate_candidates(self) -> None:
        rows = [
            (
                row.stack_id,
                row.display_name,
                row.source_id,
                row.source_type,
                row.trust_label,
                row.activation_state,
                row.deactivation_state,
                row.reactivation_state,
                row.discovery_refresh_state,
                row.persistence_state,
                row.export_summary_state,
                row.readiness,
                _joined(row.blockers),
                _joined(row.warnings),
                _joined(row.required_acknowledgements),
                _joined(row.diagnostics),
                row.stale_source_state,
                _yes_no(row.repreview_required),
                row.redaction_status,
                row.built_in_relationship,
                _joined(row.shared_stack_indicators),
                row.deactivation_history_state,
                row.reactivation_history_state,
                row.historical_evidence_state,
                row.validation_evidence_state,
                _yes_no(row.issue_closure_implied),
                _yes_no(row.automatic_activation_implied),
                _yes_no(row.trusted_source_implied),
                _yes_no(row.validation_evidence_implied),
                _yes_no(row.is_untrusted),
                _yes_no(row.built_in_authoritative),
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
                _yes_no(row.blocking),
                row.reason,
                row.related_candidate_id,
                row.related_source_id,
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
                row.display_reference,
                row.redaction_status,
                _yes_no(row.redaction_required),
                _yes_no(row.unredacted_path_blocked),
                _yes_no(row.redaction_reviewed),
                _yes_no(row.secret_like_content_blocked),
                row.privacy_warning,
                _yes_no(row.fingerprint_is_not_trust_signal),
            )
            for row in self._view_model.redaction_rows
        ]
        _populate_table(self.redaction_table, rows)

    def _populate_stale_sources(self) -> None:
        rows = [
            (
                row.stale_source_state,
                _yes_no(row.repreview_required),
                row.source_reference_display,
                _yes_no(row.source_reference_redacted),
                "old preview data is not silently trusted"
                if row.old_preview_not_silently_trusted
                else "old preview data trusted",
                "no file IO performed" if row.no_file_io_performed else "file IO",
                "no file restoration performed"
                if row.no_file_restoration_performed
                else "file restoration",
                "no file rewrite performed" if row.no_file_rewrite_performed else "file rewrite",
                "no file deletion performed"
                if row.no_file_deletion_performed
                else "file deletion",
                _yes_no(row.future_policy_required),
            )
            for row in self._view_model.stale_source_rows
        ]
        _populate_table(self.stale_sources_table, rows)

    def _populate_conflicts(self) -> None:
        rows = [
            (
                row.stack_id,
                row.built_in_source_id,
                row.user_or_plugin_source_id,
                row.active_source_state,
                row.deactivated_source_state,
                row.reactivation_source_state,
                row.persistence_state,
                row.export_summary_state,
                _yes_no(row.built_ins_win_by_default),
                _yes_no(row.conflict_visible),
                _yes_no(row.exported_state_does_not_override_builtin),
                _yes_no(row.future_policy_required),
            )
            for row in self._view_model.conflict_rows
        ]
        _populate_table(self.conflicts_table, rows)

    def _populate_unsafe_claims(self) -> None:
        rows = [
            (
                row.claim_id,
                row.related_candidate_id,
                row.related_source_id,
                row.claim_text,
                _yes_no(row.blocked),
                row.warning_text,
                _yes_no(row.accepted_by_export_summary),
            )
            for row in self._view_model.unsafe_claim_rows
        ]
        _populate_table(self.unsafe_claims_table, rows)

    def _populate_evidence_history(self) -> None:
        rows = [
            (
                row.stack_id,
                _yes_no(row.deactivation_history_retained),
                _yes_no(row.reactivation_history_retained),
                _yes_no(row.historical_validation_evidence_retained),
                _yes_no(row.skipped_missing_remains_skipped_missing),
                _yes_no(row.issue_closure_implied),
                _yes_no(row.validation_success_claimed),
                _yes_no(row.validation_failure_claimed),
                _yes_no(row.evidence_deleted_or_rewritten),
                _yes_no(row.export_summary_is_not_validation_evidence),
            )
            for row in self._view_model.evidence_history_rows
        ]
        _populate_table(self.evidence_history_table, rows)

    def _populate_limitations(self) -> None:
        rows = [
            (
                row.limitation_id,
                row.title,
                row.message,
                row.severity,
                row.related_section,
                row.related_source_id,
                row.related_candidate_id,
                _yes_no(row.must_show),
            )
            for row in self._view_model.limitation_rows
        ]
        _populate_table(self.limitations_table, rows)

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
            future_text = "future-only" if action_state.future_action else "review-only"
            scope_text = (
                "widget-local; non-persistent"
                if enabled
                else "non-exporting; non-writing; non-persistent"
            )
            lines.append(
                f"{action_name}: {availability}; {enabled_text}; "
                f"{future_text}; {scope_text}"
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
        action_state: OptionalSolverPluginManifestExportSummaryActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        return False

    def _effective_action_available(
        self,
        action_state: OptionalSolverPluginManifestExportSummaryActionState,
    ) -> bool:
        action_name = action_state.action.value
        if action_name in _ACK_ACTION_TO_ID:
            return self._acknowledgement_callback is not None
        return bool(action_state.available)

    def _effective_action_reason(
        self,
        action_state: OptionalSolverPluginManifestExportSummaryActionState,
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
                "view-model; nothing is exported or persisted."
            )
        return _ACTION_REASON_OVERRIDES.get(action_name, action_state.reason)


def _summary_text(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> str:
    h = view_model.header
    flags = view_model.non_action_flags
    return (
        "Optional solver plugin manifest export summary: "
        f"readiness={h.readiness}; "
        f"state={h.export_summary_state}; "
        f"summary_kind={h.summary_kind}; "
        f"state_scope={h.state_scope}; "
        f"generated_by={h.generated_by_display}; "
        f"schema_version={h.schema_version_display}; "
        f"sources={h.source_count}; "
        f"candidates={h.candidate_count}; "
        f"acknowledgements={h.acknowledgement_count}; "
        f"diagnostics={h.diagnostic_count}; "
        f"warnings={h.warning_count}; "
        f"errors={h.error_count}; "
        f"conflicts={h.conflict_count}; "
        f"unsafe_claims={h.unsafe_claim_count}; "
        f"stale_sources={h.stale_source_count}; "
        f"redaction_required={h.redaction_required_count}; "
        f"evidence_retained={h.evidence_retained_count}; "
        f"history_retained={h.history_retained_count}; "
        f"limitations={h.limitations_count}; "
        f"export_performed={h.export_performed}; "
        f"file_write_performed={h.file_write_performed}; "
        f"export_file_created={h.export_file_created}; "
        f"clipboard_performed={h.clipboard_performed}; "
        f"report_attachment_performed={h.report_attachment_performed}; "
        f"reloadable_bundle_created={h.reloadable_bundle_created}; "
        f"persistence_performed={h.persistence_performed}; "
        f"settings_file_created={flags.settings_file_created}; "
        f"runtime_state_file_created={flags.runtime_state_file_created}; "
        f"schema_file_created={flags.schema_file_created}; "
        f"project_schema_mutation_performed={flags.project_schema_mutation_performed}; "
        f"cli_behavior_added={flags.cli_behavior_added}; "
        f"reload_behavior_added={flags.reload_behavior_added}; "
        f"automatic_activation_performed={flags.automatic_activation_performed}; "
        f"trust_restoration_performed={flags.trust_restoration_performed}; "
        f"file_restoration_performed={flags.file_restoration_performed}; "
        f"file_rewrite_performed={flags.file_rewrite_performed}; "
        f"file_deletion_performed={flags.file_deletion_performed}; "
        f"dependency_installation_performed={flags.dependency_installation_performed}; "
        f"dependency_uninstall_performed={flags.dependency_uninstall_performed}; "
        f"solver_uninstall_performed={flags.solver_uninstall_performed}; "
        f"plugin_package_import_performed={flags.plugin_package_import_performed}; "
        f"directory_scan_performed={flags.directory_scan_performed}; "
        f"network_fetch_performed={flags.network_fetch_performed}; "
        f"discovery_execution_performed={flags.discovery_execution_performed}; "
        f"validation_execution_performed={flags.validation_execution_performed}; "
        f"solver_execution_performed={flags.solver_execution_performed}; "
        f"issue_mutation_performed={flags.issue_mutation_performed}; "
        f"release_mutation_performed={flags.release_mutation_performed}; "
        f"tag_mutation_performed={flags.tag_mutation_performed}; "
        f"asset_mutation_performed={flags.asset_mutation_performed}; "
        f"version_bump_performed={flags.version_bump_performed}; "
        f"validation_success_claimed={h.validation_success_claimed}; "
        f"validation_failure_claimed={h.validation_failure_claimed}; "
        f"issue_closure_claimed={h.issue_closure_claimed}; "
        f"certification_claimed={h.certification_claimed}; "
        f"not_validation_evidence={h.not_validation_evidence}; "
        f"not_persistence={h.not_persistence}; "
        f"not_reloadable_bundle={h.not_reloadable_bundle}; "
        "file_dialog_behavior=False; save_dialog_behavior=False; "
        "clipboard_behavior=False; report_attachment_behavior=False; "
        "open_output_folder_behavior=False. "
        f"{h.status_text}"
    )


def _trust_text(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> str:
    lines = [
        "Trust/provenance labels.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Export summary is not validation evidence.",
        "Export summary is not validation success.",
        "Export summary is not validation failure.",
        "Export summary is not persistence.",
        "Export summary is not a reloadable bundle.",
        "Export summary is not automatic activation.",
        "Export summary is not trust restoration.",
    ]
    if not view_model.source_rows and not view_model.candidate_rows:
        lines.append("No trust/provenance rows.")
    for source in view_model.source_rows:
        lines.append(
            f"source_id={source.source_id} | source_type={source.source_type} | "
            f"trust_label={source.trust_label} | "
            f"source_label={source.source_label or 'not supplied'} | "
            f"export_summary_kind={source.export_summary_kind} | "
            f"trust_label_not_certification={source.trust_label_not_certification} | "
            f"not_validation_evidence={source.not_validation_evidence} | "
            f"built_in_authoritative={source.built_in_authoritative}"
        )
    for candidate in view_model.candidate_rows:
        lines.append(
            f"stack_id={candidate.stack_id} | source_type={candidate.source_type} | "
            f"trust_label={candidate.trust_label} | "
            f"export_summary_state={candidate.export_summary_state} | "
            f"user_plugin_manifests_untrusted_by_default={candidate.is_untrusted} | "
            f"built_in_authoritative={candidate.built_in_authoritative} | "
            f"issue_closure_implied={candidate.issue_closure_implied}"
        )
    return "\n".join(lines)


def _non_action_flags_text(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> str:
    flags = view_model.non_action_flags
    lines = [
        "Export-summary GUI non-actions.",
        f"export_performed={flags.export_performed}",
        f"file_write_performed={flags.file_write_performed}",
        f"export_file_created={flags.export_file_created}",
        f"clipboard_performed={flags.clipboard_performed}",
        f"report_attachment_performed={flags.report_attachment_performed}",
        f"reloadable_bundle_created={flags.reloadable_bundle_created}",
        f"persistence_performed={flags.persistence_performed}",
        f"settings_file_created={flags.settings_file_created}",
        f"runtime_state_file_created={flags.runtime_state_file_created}",
        f"schema_file_created={flags.schema_file_created}",
        f"project_schema_mutation_performed={flags.project_schema_mutation_performed}",
        f"gui_behavior_added={flags.gui_behavior_added}",
        f"cli_behavior_added={flags.cli_behavior_added}",
        f"reload_behavior_added={flags.reload_behavior_added}",
        f"automatic_activation_performed={flags.automatic_activation_performed}",
        f"trust_restoration_performed={flags.trust_restoration_performed}",
        f"file_restoration_performed={flags.file_restoration_performed}",
        f"file_rewrite_performed={flags.file_rewrite_performed}",
        f"file_deletion_performed={flags.file_deletion_performed}",
        f"dependency_installation_performed={flags.dependency_installation_performed}",
        f"dependency_uninstall_performed={flags.dependency_uninstall_performed}",
        f"solver_uninstall_performed={flags.solver_uninstall_performed}",
        f"plugin_package_import_performed={flags.plugin_package_import_performed}",
        f"directory_scan_performed={flags.directory_scan_performed}",
        f"network_fetch_performed={flags.network_fetch_performed}",
        f"discovery_execution_performed={flags.discovery_execution_performed}",
        f"validation_execution_performed={flags.validation_execution_performed}",
        f"solver_execution_performed={flags.solver_execution_performed}",
        f"issue_mutation_performed={flags.issue_mutation_performed}",
        f"issue_closure_claimed={flags.issue_closure_claimed}",
        f"release_mutation_performed={flags.release_mutation_performed}",
        f"tag_mutation_performed={flags.tag_mutation_performed}",
        f"asset_mutation_performed={flags.asset_mutation_performed}",
        f"version_bump_performed={flags.version_bump_performed}",
        f"validation_success_claimed={flags.validation_success_claimed}",
        f"validation_failure_claimed={flags.validation_failure_claimed}",
        f"bundled_solver_claimed={flags.bundled_solver_claimed}",
        f"certification_claimed={flags.certification_claimed}",
        "file_dialog_behavior=False",
        "save_dialog_behavior=False",
        "source_behavior_mutation=False",
        "report_attachment_behavior=False",
        "open_output_folder_behavior=False",
    ]
    return "\n".join(lines)


def _safety_text(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> str:
    lines = [
        "Optional solver plugin manifest export-summary GUI safety boundary.",
        "Export-summary GUI is view-model driven and non-exporting.",
        "Export summary is not validation evidence.",
        "Export summary is not validation success.",
        "Export summary is not validation failure.",
        "Export summary is not persistence.",
        "Export summary is not reloadable bundle.",
        "Export-summary GUI is not automatic activation.",
        "Export-summary GUI is not trust restoration.",
        "Export-summary GUI is not dependency installation.",
        "Export-summary GUI is not solver execution.",
        "Export-summary GUI is not issue closure.",
        "Export-summary GUI is not release mutation.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Fingerprints are not trust signals.",
        "Old preview data is not silently trusted.",
        "Stale, missing, moved, or changed sources require re-preview.",
        "Unsafe claims are blocked and not accepted by export summaries.",
        "Limitations remain visible.",
        "Skipped-missing remains skipped-missing.",
        "No file export.",
        "No file writes.",
        "No export file creation.",
        "No report file creation.",
        "No clipboard behavior.",
        "No report attachment.",
        "No open-output-folder behavior.",
        "No reloadable bundle creation.",
        "No runtime persistence behavior.",
        "No settings file creation.",
        "No runtime state file creation.",
        "No schema file creation.",
        "No ProjectSchema mutation.",
        "No CLI behavior.",
        "No reload behavior.",
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
        "No issue-closure claim.",
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


def _mapping_text(value: object, *, prefix: str = "") -> str:
    lines: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = f"{prefix}{key}"
            if isinstance(item, Mapping):
                lines.append(f"{key_text}:")
                lines.append(_mapping_text(item, prefix=f"{key_text}."))
            elif isinstance(item, list):
                lines.append(f"{key_text}: {len(item)} item(s)")
                for index, nested in enumerate(item):
                    if isinstance(nested, Mapping):
                        lines.append(_mapping_text(nested, prefix=f"{key_text}.{index}."))
                    else:
                        lines.append(f"{key_text}.{index}: {nested}")
            else:
                lines.append(f"{key_text}: {item}")
    else:
        lines.append(str(value))
    return "\n".join(line for line in lines if line)


def _yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _joined(values: object) -> str:
    if not isinstance(values, tuple):
        return str(values) if values else "none"
    joined = ", ".join(str(value) for value in values if str(value))
    return joined or "none"


def _action_button_object_name(
    action_state: OptionalSolverPluginManifestExportSummaryActionState,
) -> str:
    return "oswOptionalSolverPluginManifestExportSummaryAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


__all__ = [
    "OptionalSolverPluginManifestExportSummaryPanel",
]
