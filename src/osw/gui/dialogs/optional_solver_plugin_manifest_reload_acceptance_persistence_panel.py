"""Display-only PySide review panel for reload acceptance persistence.

The panel renders a supplied reload acceptance persistence view-model and an
optional supplied writer dry-run/result mapping. It is a GUI review surface
only: it does not invoke writers, choose targets, inspect files, call CLI code,
mutate project state, or perform runtime reload acceptance.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_persistence_viewmodel import (  # noqa: E501
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class OptionalSolverPluginManifestReloadAcceptancePersistencePanel(_BaseDialog):
    """Read-only panel over supplied persistence planning records."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: object | None = None,
        writer_result: object | None = None,
        writer_mapping: Mapping[str, object] | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptancePersistencePanel"
        )
        self.setWindowTitle(
            "Optional Solver Plugin Manifest Reload Acceptance Persistence Review"
        )
        self.resize(1480, 940)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model
            or OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.unavailable()
        )
        self._writer_mapping = _object_to_mapping(writer_result) or _mapping(
            writer_mapping
        )

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceTabs"
        )
        root.addWidget(self.tabs, 1)

        self.summary_table = self._add_table_tab(
            "Summary",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceSummaryTable",
            ("field", "value"),
        )
        self.target_storage_table = self._add_table_tab(
            "Target / Storage",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceTargetTable",
            ("field", "value", "guidance"),
        )
        self.write_plan_table = self._add_table_tab(
            "Dry-run / Write-plan",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistencePlanTable",
            ("field", "value", "guidance"),
        )
        self.writer_result_table = self._add_table_tab(
            "Writer Result",
            "oswReloadAcceptancePersistenceWriterResultTable",
            ("field", "value", "guidance"),
        )
        self.acknowledgements_table = self._add_table_tab(
            "Acknowledgements",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceAckTable",
            (
                "acknowledgement_id",
                "required",
                "satisfied",
                "expired",
                "blocking",
                "not_validation_evidence",
                "not_trust_restoration",
            ),
        )
        self.expiry_table = self._add_table_tab(
            "Acknowledgement Expiry",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceExpiryTable",
            ("reason_id", "active", "blocks_when_triggered", "guidance"),
        )
        self.schema_table = self._add_table_tab(
            "Schema / Migration",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceSchemaTable",
            ("field", "value", "guidance"),
        )
        self.redaction_table = self._add_table_tab(
            "Redaction / Privacy",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceRedactionTable",
            ("field", "value", "guidance"),
        )
        self.provenance_table = self._add_table_tab(
            "Provenance",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceProvenanceTable",
            (
                "provenance_id",
                "source_display",
                "source_kind",
                "preview_identifier",
                "payload_fingerprint",
                "untrusted_by_default",
                "non_authoritative",
                "trust_label_not_certification",
            ),
        )
        self.candidate_lifecycle_table = self._add_table_tab(
            "Candidate Lifecycle",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceLifecycleTable",
            ("state", "policy", "guidance"),
        )
        self.stale_source_table = self._add_table_tab(
            "Stale Source / Re-preview",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceStaleTable",
            ("field", "state", "guidance"),
        )
        self.conflict_table = self._add_table_tab(
            "Conflict / Shared Stack",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceConflictTable",
            ("field", "state", "guidance"),
        )
        self.unsafe_claim_table = self._add_table_tab(
            "Unsafe Claims",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceUnsafeTable",
            ("field", "state", "guidance"),
        )
        self.evidence_history_table = self._add_table_tab(
            "Evidence / History",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceEvidenceTable",
            (
                "evidence_id",
                "evidence_type",
                "retained_reference_only",
                "not_validation_evidence",
                "not_validation_failure",
                "issue_closure_implied",
            ),
        )
        self.diagnostics_table = self._add_table_tab(
            "Diagnostics",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceDiagnosticTable",
            ("severity", "code", "message", "section", "blocker", "suggested_fix"),
        )
        self.non_action_flags_table = self._add_table_tab(
            "Non-Action Flags",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceFlagsTable",
            ("flag", "value", "review_state"),
        )
        self.actions_table = self._add_table_tab(
            "Disabled / Future Actions",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceActionsTable",
            ("action", "enabled", "future_only", "reason"),
        )
        self.safety_panel = self._add_text_tab(
            "Safety Guidance",
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceSafety",
        )

        close_button = QtWidgets.QPushButton("Close", self)
        close_button.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceClose"
        )
        close_button.clicked.connect(self.close)
        root.addWidget(close_button)

        self._apply_theme()
        self.refresh()

    def set_view_model(self, view_model: object) -> None:
        """Replace the supplied persistence view-model and re-render."""

        self._view_model = view_model
        self.refresh()

    def set_writer_result(self, writer_result: object | None) -> None:
        """Replace the supplied writer result record and re-render."""

        self._writer_mapping = _object_to_mapping(writer_result)
        self.refresh()

    def set_writer_mapping(self, writer_mapping: Mapping[str, object] | None) -> None:
        """Replace the supplied writer result mapping and re-render."""

        self._writer_mapping = _mapping(writer_mapping)
        self.refresh()

    def refresh(self) -> None:
        """Render supplied records without side effects."""

        mapping = _object_to_mapping(self._view_model)
        writer = _mapping(self._writer_mapping)
        self.summary_label.setText(_summary_label_text(mapping, writer))
        _populate_table(self.summary_table, _summary_rows(mapping, writer))
        _populate_table(
            self.target_storage_table,
            _target_storage_rows(mapping, writer),
        )
        _populate_table(self.write_plan_table, _write_plan_rows(mapping, writer))
        _populate_table(
            self.writer_result_table,
            _writer_result_rows(writer),
        )
        _populate_table(
            self.acknowledgements_table,
            _mapping_rows(
                mapping.get("acknowledgements"),
                _ACKNOWLEDGEMENT_COLUMNS,
            ),
        )
        _populate_table(self.expiry_table, _expiry_rows(mapping))
        _populate_table(self.schema_table, _schema_rows(mapping, writer))
        _populate_table(self.redaction_table, _redaction_rows(mapping, writer))
        _populate_table(
            self.provenance_table,
            _mapping_rows(mapping.get("provenance"), _PROVENANCE_COLUMNS),
        )
        _populate_table(
            self.candidate_lifecycle_table,
            _candidate_lifecycle_rows(),
        )
        _populate_table(self.stale_source_table, _stale_source_rows(mapping))
        _populate_table(self.conflict_table, _conflict_rows(mapping))
        _populate_table(self.unsafe_claim_table, _unsafe_claim_rows(mapping))
        _populate_table(
            self.evidence_history_table,
            _mapping_rows(mapping.get("evidence_history"), _EVIDENCE_COLUMNS),
        )
        _populate_table(self.diagnostics_table, _diagnostic_rows(mapping, writer))
        _populate_table(
            self.non_action_flags_table,
            _non_action_flag_rows(mapping, writer),
        )
        _populate_table(self.actions_table, _action_rows(mapping))
        self.safety_panel.setPlainText(_safety_text(mapping, writer))

    def summary_text(self) -> str:
        return self.summary_label.text()

    def summary_rows_text(self) -> str:
        return _table_text(self.summary_table, empty_text="No persistence summary.")

    def target_storage_text(self) -> str:
        return _table_text(
            self.target_storage_table,
            empty_text="No target/storage rows.",
        )

    def dry_run_write_plan_text(self) -> str:
        return _table_text(self.write_plan_table, empty_text="No write-plan rows.")

    def writer_result_text(self) -> str:
        return _table_text(
            self.writer_result_table,
            empty_text="No supplied writer result.",
        )

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table,
            empty_text="No persistence acknowledgements.",
        )

    def expiry_rows_text(self) -> str:
        return _table_text(self.expiry_table, empty_text="No expiry rows.")

    def schema_migration_text(self) -> str:
        return _table_text(self.schema_table, empty_text="No schema rows.")

    def redaction_privacy_text(self) -> str:
        return _table_text(self.redaction_table, empty_text="No redaction rows.")

    def provenance_text(self) -> str:
        return _table_text(self.provenance_table, empty_text="No provenance rows.")

    def candidate_lifecycle_text(self) -> str:
        return _table_text(
            self.candidate_lifecycle_table,
            empty_text="No lifecycle rows.",
        )

    def stale_source_text(self) -> str:
        return _table_text(self.stale_source_table, empty_text="No stale rows.")

    def conflict_text(self) -> str:
        return _table_text(self.conflict_table, empty_text="No conflict rows.")

    def unsafe_claim_text(self) -> str:
        return _table_text(self.unsafe_claim_table, empty_text="No unsafe claims.")

    def evidence_history_text(self) -> str:
        return _table_text(
            self.evidence_history_table,
            empty_text="No evidence/history rows.",
        )

    def diagnostics_text(self) -> str:
        return _table_text(
            self.diagnostics_table,
            empty_text="No persistence diagnostics.",
        )

    def non_action_flags_text(self) -> str:
        return _table_text(
            self.non_action_flags_table,
            empty_text="No non-action flags.",
        )

    def action_state_text(self) -> str:
        return _table_text(self.actions_table, empty_text="No action rows.")

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def available_action_names(self) -> list[str]:
        return [
            str(row.get("action", ""))
            for row in _action_row_mappings(_object_to_mapping(self._view_model))
            if bool(row.get("enabled", False))
        ]

    def disabled_action_reasons(self) -> dict[str, str]:
        return {
            str(row.get("action", "")): _safe_text(row.get("reason", ""))
            for row in _action_row_mappings(_object_to_mapping(self._view_model))
            if not bool(row.get("enabled", False))
        }

    def rendered_text(self) -> str:
        """Return all rendered review text for focused assertions."""

        return "\n".join(
            value
            for value in (
                self.summary_text(),
                self.summary_rows_text(),
                self.target_storage_text(),
                self.dry_run_write_plan_text(),
                self.writer_result_text(),
                self.acknowledgement_rows_text(),
                self.expiry_rows_text(),
                self.schema_migration_text(),
                self.redaction_privacy_text(),
                self.provenance_text(),
                self.candidate_lifecycle_text(),
                self.stale_source_text(),
                self.conflict_text(),
                self.unsafe_claim_text(),
                self.evidence_history_text(),
                self.diagnostics_text(),
                self.non_action_flags_text(),
                self.action_state_text(),
                self.safety_text(),
            )
            if value
        )

    def _add_table_tab(
        self,
        title: str,
        object_name: str,
        headers: tuple[str, ...],
    ) -> object:
        table = _readonly_table(object_name, self.tabs, headers)
        self.tabs.addTab(table, title)
        return table

    def _add_text_tab(self, title: str, object_name: str) -> object:
        widget = _readonly_plain_text(object_name, self.tabs)
        self.tabs.addTab(widget, title)
        return widget

    def _apply_theme(self) -> None:
        tokens = self._tokens
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {tokens.bg_app};
                color: {tokens.text_primary};
            }}
            QLabel {{
                color: {tokens.text_primary};
            }}
            QTabWidget::pane {{
                border: 1px solid {tokens.border};
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
            """
        )


_ACKNOWLEDGEMENT_COLUMNS = (
    "acknowledgement_id",
    "required",
    "satisfied",
    "expired",
    "blocking",
    "acknowledgement_is_validation_evidence",
    "acknowledgement_restores_trust",
)
_PROVENANCE_COLUMNS = (
    "provenance_id",
    "source_display",
    "source_kind",
    "preview_identifier",
    "payload_fingerprint",
    "untrusted_by_default",
    "non_authoritative",
    "trust_label_not_certification",
)
_EVIDENCE_COLUMNS = (
    "evidence_id",
    "evidence_type",
    "retained_reference_only",
    "not_validation_evidence",
    "not_validation_failure",
    "issue_closure_implied",
)
_DIAGNOSTIC_COLUMNS = (
    "severity",
    "code",
    "message",
    "section",
    "blocker",
    "suggested_fix",
)
_ACTION_COLUMNS = ("action", "enabled", "future_only", "reason")

_GUI_DIAGNOSTIC_CODES = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_UNAVAILABLE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_NOT_REQUESTED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_PREVIEW_RENDERED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_PLAN_FUTURE_ONLY",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_FUTURE_ONLY",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_TARGET_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_TARGET_REDACTED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_ACK_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_DRY_RUN_NOT_WRITE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_NOT_RUNTIME_ACCEPTANCE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_NO_VALIDATION_CLAIM",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_NO_PROJECT_SCHEMA_MUTATION",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_ERROR",
)

_GUI_ACTIONS = (
    "choose_target",
    "plan_persistence_record",
    "write_persistence_record",
    "persist_acceptance_record",
    "write_acceptance_state",
    "accept_for_session_review",
    "accept_as_trusted",
    "activate_reloaded_candidate",
    "refresh_discovery",
    "validate_solver",
    "execute_solver",
    "install_dependency",
    "uninstall_dependency",
    "uninstall_solver",
    "mutate_project_schema",
    "create_export_summary",
    "create_report_file",
    "create_reloadable_bundle",
    "copy_to_clipboard",
    "attach_to_report",
    "open_output_folder",
    "close_issue",
    "mutate_release",
    "push_tag",
    "upload_asset",
    "claim_validation_success",
    "claim_validation_failure",
    "claim_certification",
)

_NON_ACTION_FLAGS = (
    "runtime_reload_acceptance_performed",
    "persistence_write_performed",
    "project_schema_mutated",
    "default_reload_path_used",
    "background_reload_performed",
    "directory_scan_performed",
    "network_fetch_performed",
    "plugin_package_imported",
    "cli_subprocess_used",
    "gui_subprocess_used",
    "reloadable_bundle_created",
    "export_file_created",
    "report_file_created",
    "clipboard_used",
    "report_attached",
    "output_folder_opened",
    "live_discovery_executed",
    "passive_refresh_executed",
    "validation_executed",
    "solver_executed",
    "dependency_installed",
    "dependency_uninstalled",
    "solver_uninstalled",
    "candidate_activated",
    "trust_restored",
    "issue_mutated",
    "release_mutated",
    "tag_mutated",
    "asset_mutated",
    "version_bumped",
    "validation_pass_claimed",
    "validation_fail_claimed",
    "issue_closure_claimed",
    "bundled_solver_claimed",
    "certification_claimed",
)


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
    table.horizontalHeader().setStretchLastSection(True)
    return table


def _readonly_plain_text(object_name: str, parent: object) -> object:
    widget = QtWidgets.QPlainTextEdit(parent)
    widget.setObjectName(object_name)
    widget.setReadOnly(True)
    return widget


def _populate_table(table: object, rows: Sequence[Sequence[object]]) -> None:
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            item = QtWidgets.QTableWidgetItem(_safe_text(value))
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_index, column_index, item)
    table.resizeColumnsToContents()


def _table_text(table: object, *, empty_text: str) -> str:
    lines: list[str] = []
    for row_index in range(table.rowCount()):
        values: list[str] = []
        for column_index in range(table.columnCount()):
            item = table.item(row_index, column_index)
            if item is not None:
                values.append(item.text())
        if values:
            lines.append(" | ".join(values))
    return "\n".join(lines) if lines else empty_text


def _summary_label_text(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> str:
    summary = _mapping(mapping.get("summary"))
    values = {
        "state": summary.get("state", "unknown"),
        "readiness": summary.get("readiness", "unknown"),
        "persistence_requested": summary.get("persistence_requested", False),
        "dry_run_plan_state": _dry_run_plan_state(mapping, writer),
        "writer_future_only": summary.get("future_writer_only", True),
        "ready_for_future_write_plan": summary.get(
            "ready_for_future_write_plan", False
        ),
        "blocker_count": summary.get("blocker_count", 0),
        "warning_count": summary.get("warning_count", 0),
        "diagnostic_count": summary.get("diagnostic_count", 0),
        "target_required": _target_required(mapping, writer),
        "no_runtime_acceptance": not bool(
            summary.get("persistence_readiness_is_runtime_acceptance", False)
        ),
        "no_project_schema_mutation": not bool(
            summary.get("persistence_readiness_mutates_project_schema", False)
        ),
        "no_validation_evidence": not bool(
            summary.get("persistence_readiness_is_validation_evidence", False)
        ),
        "no_validation_failure": not bool(
            summary.get("persistence_readiness_is_validation_failure", False)
        ),
        "no_activation": not bool(
            summary.get("persistence_readiness_activates_candidate", False)
        ),
        "no_trust_restoration": not bool(
            summary.get("persistence_readiness_restores_trust", False)
        ),
        "no_issue_release_mutation": not bool(
            summary.get("persistence_readiness_closes_issue", False)
        )
        and not bool(summary.get("persistence_readiness_mutates_release", False)),
        "no_certification": not bool(
            summary.get("persistence_readiness_certifies_manifest", False)
        ),
    }
    return "; ".join(f"{key}={_safe_text(value)}" for key, value in values.items())


def _summary_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, str]]:
    summary = _mapping(mapping.get("summary"))
    rows = [(str(key), _safe_text(value)) for key, value in summary.items()]
    rows.extend(
        (
            ("dry_run_plan_state", _dry_run_plan_state(mapping, writer)),
            ("target_required", _yes_no(_target_required(mapping, writer))),
            ("dry_run_success_is_validation_success", "no"),
            ("dry_run_success_is_runtime_acceptance", "no"),
            ("dry_run_success_mutates_project_schema", "no"),
            ("writer_result_display_is_runtime_acceptance", "no"),
            ("persisted_record_is_validation_evidence", "no"),
            ("persisted_record_is_validation_failure", "no"),
            ("trust_label_is_certification", "no"),
        )
    )
    return rows


def _target_storage_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    storage_options = _normalised_rows(mapping.get("storage_options"))
    storage = storage_options[0] if storage_options else {}
    writer_target = writer.get("target_display", "")
    return [
        (
            "storage_policy_id",
            _first_non_empty(
                storage.get("storage_policy_id"),
                _mapping(mapping.get("write_plan")).get("storage_policy_id"),
            ),
            "Storage policy is review metadata only.",
        ),
        (
            "storage_label",
            _first_non_empty(storage.get("label"), "supplied review record"),
            "Label does not authorize a target chooser.",
        ),
        (
            "redacted_target_display",
            _first_non_empty(
                writer_target,
                storage.get("target_display"),
                _mapping(mapping.get("write_plan")).get("target_display"),
                "",
            ),
            "Target display is redacted; raw paths stay hidden.",
        ),
        (
            "target_required",
            _yes_no(_target_required(mapping, writer)),
            "Future writes require explicit target review.",
        ),
        (
            "target_blocked",
            _yes_no(_has_code(mapping, writer, "TARGET")),
            "Blocked targets remain display-only.",
        ),
        (
            "parent_missing",
            _yes_no(_has_code(mapping, writer, "PARENT_MISSING")),
            "The panel never creates directories.",
        ),
        (
            "directory_target_blocked",
            _yes_no(_has_code(mapping, writer, "TARGET_DIRECTORY_BLOCKED")),
            "Directory targets remain blocked by writer policy.",
        ),
        (
            "symlink_blocked",
            _yes_no(_has_code(mapping, writer, "SYMLINK_BLOCKED")),
            "Symbolic links require a separate future policy.",
        ),
        (
            "existing_target_replacement_policy",
            "explicit_replace_required",
            "Existing targets require a future explicit replace policy.",
        ),
        ("default_target_path_used", "no", "No default target path is used."),
        ("background_path_used", "no", "No background target path exists."),
        ("directory_creation_performed", "no", "No directories are created."),
    ]


def _write_plan_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    plan = _mapping(mapping.get("write_plan"))
    return [
        (
            "dry_run",
            _first_non_empty(writer.get("dry_run"), plan.get("dry_run_required")),
            "Dry-run review is not a file write.",
        ),
        (
            "planned",
            _first_non_empty(writer.get("planned"), plan.get("dry_run_required")),
            "Planning is display-only.",
        ),
        (
            "writer_future_only",
            _first_non_empty(plan.get("writer_future_only"), True),
            "Writer access remains future-gated from GUI.",
        ),
        (
            "bytes_count",
            writer.get("bytes_count", ""),
            "Byte count is supplied writer-result metadata only.",
        ),
        (
            "sha256",
            writer.get("sha256", ""),
            "Hash is a fingerprint, not a trust signal.",
        ),
        (
            "payload_kind",
            _first_non_empty(writer.get("payload_kind"), plan.get("expected_payload_kind")),
            "Payload kind is required metadata.",
        ),
        (
            "payload_schema",
            _first_non_empty(writer.get("payload_schema_version"), plan.get("schema_version")),
            "Schema metadata is separate from ProjectSchema.",
        ),
        (
            "blocker_count",
            _first_non_empty(plan.get("blocker_count"), len(_sequence(writer.get("blockers")))),
            "Blockers remain visible.",
        ),
        (
            "warning_count",
            _first_non_empty(plan.get("warning_count"), len(_sequence(writer.get("warnings")))),
            "Warnings remain visible.",
        ),
        (
            "diagnostic_count",
            _first_non_empty(
                plan.get("diagnostic_count"),
                len(_normalised_rows(writer.get("diagnostics"))),
            ),
            "Diagnostics remain visible.",
        ),
        ("dry_run_is_write", "no", "Dry-run is not write."),
        (
            "dry_run_success_is_validation_success",
            "no",
            "Dry-run success is not validation success.",
        ),
        (
            "dry_run_success_is_runtime_acceptance",
            "no",
            "Dry-run success is not runtime acceptance.",
        ),
        (
            "dry_run_success_mutates_project_schema",
            "no",
            "Dry-run success is not ProjectSchema mutation.",
        ),
    ]


def _writer_result_rows(writer: Mapping[str, object]) -> list[tuple[str, str, str]]:
    if not writer:
        return [
            (
                "writer_result",
                "not_supplied",
                "The panel does not invoke the writer.",
            ),
            (
                "write_success_scope",
                "local_review_record_only",
                "Any supplied write result is still not runtime acceptance.",
            ),
        ]
    return [
        ("status", writer.get("status", ""), "Status was supplied by caller."),
        (
            "target_display",
            writer.get("target_display", ""),
            "Target display is redacted by display helpers.",
        ),
        ("planned", writer.get("planned", ""), "Planning is not mutation."),
        ("written", writer.get("written", ""), "Written means local review record only."),
        ("bytes_count", writer.get("bytes_count", ""), "Byte count is metadata only."),
        ("sha256", writer.get("sha256", ""), "Hash is not a trust signal."),
        (
            "cleanup_performed",
            writer.get("cleanup_performed", ""),
            "Cleanup status is supplied metadata only.",
        ),
        (
            "temp_file_used",
            writer.get("temp_file_used", ""),
            "Temporary-file state is supplied metadata only.",
        ),
        (
            "temp_file_left_behind",
            writer.get("temp_file_left_behind", ""),
            "Temporary-file state is supplied metadata only.",
        ),
        (
            "diagnostics",
            _diagnostic_code_text(writer.get("diagnostics")),
            "Writer diagnostics are surfaced without rewriting them as truth.",
        ),
        (
            "warnings",
            writer.get("warnings", ()),
            "Warnings remain visible.",
        ),
        (
            "blockers",
            writer.get("blockers", ()),
            "Blockers remain visible.",
        ),
        (
            "write_success_scope",
            "local_review_record_only",
            "Write success, if future-enabled, is not runtime acceptance.",
        ),
    ]


def _expiry_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str, str]]:
    rows = _mapping_rows(
        mapping.get("acknowledgement_expiry"),
        ("reason_id", "active", "blocks_when_triggered"),
    )
    if rows:
        return [
            (
                row[0],
                row[1],
                row[2],
                "Triggered expiry requires re-review; it is not validation failure.",
            )
            for row in rows
        ]
    return [
        (
            _safe_text(reason),
            "yes",
            "yes",
            "Triggered expiry requires re-review; it is not validation failure.",
        )
        for reason in _sequence(mapping.get("expiry_reasons"))
    ]


def _schema_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    schema_rows = _normalised_rows(mapping.get("schema"))
    schema = schema_rows[0] if schema_rows else {}
    return [
        (
            "payload_kind",
            _first_non_empty(
                writer.get("payload_kind"),
                schema.get("payload_kind"),
                _mapping(mapping.get("write_plan")).get("expected_payload_kind"),
            ),
            "Payload kind is required.",
        ),
        (
            "schema_version",
            _first_non_empty(
                writer.get("payload_schema_version"),
                schema.get("schema_version"),
                _mapping(mapping.get("write_plan")).get("schema_version"),
            ),
            "Schema version is required.",
        ),
        (
            "schema_mismatch",
            _yes_no(_has_code(mapping, writer, "SCHEMA_MISMATCH")),
            "Schema mismatch is not validation failure.",
        ),
        (
            "unsupported_schema",
            _yes_no(_has_code(mapping, writer, "SCHEMA_UNSUPPORTED")),
            "Unsupported schema blocks future persistence.",
        ),
        (
            "migration_required",
            _safe_text(schema.get("migration_required", False)),
            "Migration remains a separate future gate.",
        ),
        (
            "separate_from_project_schema",
            _safe_text(schema.get("separate_from_project_schema", True)),
            "Persistence schema is separate from ProjectSchema.",
        ),
        ("gui_repairs_or_migrates_files", "no", "The panel never repairs files."),
    ]


def _redaction_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    return [
        ("raw_paths_hidden_by_default", "yes", "Basename/redacted display wins."),
        (
            "secret_like_values_blocked",
            "yes",
            "Secret-like values are redacted from rendered text.",
        ),
        (
            "unredacted_path_blocked",
            _yes_no(_has_code(mapping, writer, "UNREDACTED_PATH_BLOCKED")),
            "Unredacted paths block future write policy.",
        ),
        (
            "fingerprints_are_trust_signals",
            "no",
            "Fingerprints are identifiers, not trust signals.",
        ),
        (
            "full_file_content_displayed",
            "no",
            "The panel displays supplied metadata, not full file contents.",
        ),
        (
            "plugin_code_displayed",
            "no",
            "The panel never displays plugin code.",
        ),
        (
            "diagnostics_use_redacted_context",
            "yes",
            "Diagnostic context is rendered through redaction helpers.",
        ),
    ]


def _candidate_lifecycle_rows() -> list[tuple[str, str, str]]:
    return [
        ("inactive_preview", "review_only", "Inactive preview remains review-only."),
        (
            "persisted_active",
            "future_activation_review_required",
            "Persisted active state is not automatic activation.",
        ),
        (
            "deactivated",
            "deactivated_review_state",
            "Deactivated state remains deactivated review state.",
        ),
        (
            "reactivation",
            "future_activation_review_required",
            "Reactivation routes to future activation review.",
        ),
        (
            "discovery_refresh",
            "review_state",
            "Discovery-refresh state remains review state.",
        ),
        ("automatic_activation", "no", "The panel never activates candidates."),
        ("trust_restoration", "no", "The panel never restores trust."),
        (
            "override_built_ins",
            "no",
            "Persisted records do not override built-ins.",
        ),
    ]


def _stale_source_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str]]:
    return [
        (
            "old_preview_silently_trusted",
            "no",
            "Old preview is not silently trusted.",
        ),
        (
            "missing_moved_changed_source_requires_repreview",
            _yes_no(_has_code(mapping, {}, "STALE_SOURCE_REPREVIEW_REQUIRED")),
            "Missing, moved, or changed sources require re-preview.",
        ),
        (
            "gui_inspects_referenced_source_files",
            "no",
            "Persistence GUI does not inspect referenced source files.",
        ),
        (
            "stale_source_is_validation_failure",
            "no",
            "Stale-source state is not validation failure.",
        ),
        ("repreview_future_gated", "yes", "Re-preview remains future-gated."),
    ]


def _conflict_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str]]:
    conflict_visible = _has_code(mapping, {}, "CONFLICT") or _has_code(
        mapping, {}, "SHARED_STACK"
    )
    return [
        ("conflicts_visible", _yes_no(conflict_visible), "Conflicts remain visible."),
        ("built_ins_win_by_default", "yes", "Built-ins remain authoritative."),
        (
            "persisted_record_overrides_built_ins",
            "no",
            "Persisted records do not override built-ins.",
        ),
        (
            "shared_stack_warnings_visible",
            _yes_no(_has_code(mapping, {}, "SHARED_STACK")),
            "Shared-stack warnings remain visible.",
        ),
        ("gui_resolves_conflicts", "no", "The panel does not resolve conflicts."),
        ("future_policy_required", "yes", "Conflict policy remains future-gated."),
    ]


def _unsafe_claim_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str]]:
    unsafe_visible = _has_code(mapping, {}, "UNSAFE_CLAIM")
    return [
        ("unsafe_claims_visible", _yes_no(unsafe_visible), "Unsafe claims are visible."),
        ("unsafe_claims_persisted_as_truth", "no", "Unsafe claims are not truth."),
        ("validation_success_claims_blocked", "yes", "Validation claims are blocked."),
        ("validation_failure_claims_blocked", "yes", "Validation claims are blocked."),
        ("issue_closure_claims_blocked", "yes", "Issue closure claims are blocked."),
        ("release_mutation_claims_blocked", "yes", "Release claims are blocked."),
        ("bundled_solver_claims_blocked", "yes", "Bundled solver claims are blocked."),
        (
            "dependency_installation_claims_blocked",
            "yes",
            "Dependency installation claims are blocked.",
        ),
        ("solver_execution_claims_blocked", "yes", "Solver execution is blocked."),
        ("trust_restoration_claims_blocked", "yes", "Trust claims are blocked."),
        ("certification_claims_blocked", "yes", "Certification claims are blocked."),
    ]


def _diagnostic_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, ...]]:
    rows = _mapping_rows(mapping.get("diagnostics"), _DIAGNOSTIC_COLUMNS)
    rows.extend(_mapping_rows(writer.get("diagnostics"), _DIAGNOSTIC_COLUMNS))
    rows.extend(
        (
            "info",
            code,
            _gui_diagnostic_message(code),
            "persistence_gui",
            "no",
            "Review supplied records only.",
        )
        for code in _GUI_DIAGNOSTIC_CODES
    )
    return rows


def _non_action_flag_rows(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    flags: dict[str, object] = {flag: False for flag in _NON_ACTION_FLAGS}
    flags.update(_mapping(mapping.get("non_action_flags")))
    flags.update(_mapping(writer.get("non_action_flags")))
    for key in (
        "runtime_reload_acceptance_performed",
        "project_schema_mutated",
        "validation_executed",
        "solver_executed",
        "candidate_activated",
        "trust_restored",
        "issue_mutated",
        "release_mutated",
        "certification_claimed",
    ):
        flags[key] = bool(flags.get(key, False))
    return [
        (
            flag,
            _safe_text(flags.get(flag, False)),
            _flag_guidance(flag, bool(flags.get(flag, False))),
        )
        for flag in _NON_ACTION_FLAGS
    ]


def _action_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str, str]]:
    rows: dict[str, Mapping[str, object]] = {
        action: {
            "action": action,
            "enabled": False,
            "future_only": True,
            "reason": "Requires a separate future gate.",
        }
        for action in _GUI_ACTIONS
    }
    for row in _normalised_rows(mapping.get("actions")):
        action = str(row.get("action", ""))
        if action:
            rows[action] = row
    return [
        (
            action,
            _safe_text(row.get("enabled", False)),
            _safe_text(row.get("future_only", True)),
            _safe_text(row.get("reason", "Requires a separate future gate.")),
        )
        for action, row in rows.items()
    ]


def _safety_text(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> str:
    supplied = tuple(_safe_text(item) for item in _sequence(mapping.get("safety_text")))
    fixed = (
        "Display-only persistence GUI review panel.",
        "Panel construction is not runtime reload acceptance.",
        "Refresh is not runtime reload acceptance.",
        "Target-display update is not target selection.",
        "Dry-run is not write.",
        "Dry-run success is not validation success.",
        "Dry-run success is not validation failure.",
        "Dry-run success is not runtime acceptance.",
        "Dry-run success is not ProjectSchema mutation.",
        "Writer result display is not runtime acceptance.",
        "Persisted review record is not validation evidence.",
        "Persisted review record is not validation failure.",
        "Persisted review record is not ProjectSchema mutation.",
        "Persisted review record is not trust restoration.",
        "Persisted review record is not automatic activation.",
        "Persisted review record does not close issues or mutate releases.",
        "Trust label is not certification.",
        "Skipped-missing remains skipped-missing.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence.",
        "Prepared-machine validation remains separate.",
        "No target chooser is exposed.",
        "No writer bridge is exposed.",
        "No CLI bridge or external process use.",
        "No reload file reader bridge.",
        "No discovery, validation, solver execution, install, or uninstall.",
        "No reloadable bundle, export file, report file, copy, attachment, "
        "or output-folder action.",
    )
    writer_lines = tuple(_safe_text(item) for item in _sequence(writer.get("warnings")))
    return "\n".join(fixed + writer_lines + supplied)


def _mapping_rows(
    rows_value: object,
    columns: tuple[str, ...],
) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for row in _normalised_rows(rows_value):
        rows.append(tuple(_safe_text(row.get(column, "")) for column in columns))
    return rows


def _action_row_mappings(mapping: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [
        {
            "action": row[0],
            "enabled": row[1] == "yes",
            "future_only": row[2] == "yes",
            "reason": row[3],
        }
        for row in _action_rows(mapping)
    ]


def _object_to_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    return {}


def _normalised_rows(rows_value: object) -> list[Mapping[str, object]]:
    if isinstance(rows_value, Mapping):
        return [rows_value]
    if isinstance(rows_value, Sequence) and not isinstance(rows_value, str):
        return [row for row in rows_value if isinstance(row, Mapping)]
    return []


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    if value is None:
        return ()
    return (value,)


def _first_non_empty(*values: object) -> object:
    for value in values:
        if value not in ("", None, ()):
            return value
    return ""


def _dry_run_plan_state(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> str:
    if writer:
        if bool(writer.get("written", False)):
            return "supplied_writer_result_written_local_review_record"
        if bool(writer.get("planned", False)):
            return "supplied_writer_result_dry_run_plan"
    plan = _mapping(mapping.get("write_plan"))
    if bool(plan.get("writer_future_only", True)):
        return "future_only"
    return "not_supplied"


def _target_required(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> bool:
    plan = _mapping(mapping.get("write_plan"))
    target = _first_non_empty(
        writer.get("target_display"),
        plan.get("target_display"),
    )
    return not bool(str(target).strip())


def _has_code(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
    fragment: str,
) -> bool:
    return any(fragment in code for code in _diagnostic_codes(mapping, writer))


def _diagnostic_codes(
    mapping: Mapping[str, object],
    writer: Mapping[str, object],
) -> set[str]:
    return set(_diagnostic_code_values(mapping.get("diagnostics"))) | set(
        _diagnostic_code_values(writer.get("diagnostics"))
    )


def _diagnostic_code_values(value: object) -> tuple[str, ...]:
    return tuple(
        str(row.get("code", ""))
        for row in _normalised_rows(value)
        if row.get("code")
    )


def _diagnostic_code_text(value: object) -> str:
    return ", ".join(_diagnostic_code_values(value))


def _gui_diagnostic_message(code: str) -> str:
    label = code.removeprefix("OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_")
    return f"GUI review diagnostic reserved: {label.lower()}."


def _flag_guidance(flag: str, value: bool) -> str:
    if flag == "persistence_write_performed" and value:
        return "explicit local review-record write only; not runtime acceptance"
    if value:
        return "supplied non-action flag requires review"
    return "safe false boundary"


def _safe_text(value: object) -> str:
    if isinstance(value, bool):
        return _yes_no(value)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return ", ".join(_safe_text(item) for item in value)
    if isinstance(value, Mapping):
        return "; ".join(
            f"{_safe_text(key)}={_safe_text(item)}"
            for key, item in sorted(value.items())
        )
    return _redact_string(str(value))


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _redact_string(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    secret_markers = (
        "api_key",
        "api-key",
        "token=",
        "password=",
        "credential=",
        "private key",
        "secret=",
        "sk-",
        "ghp_",
        "github_pat",
        "bearer ",
    )
    if any(marker in lowered for marker in secret_markers):
        return "<redacted-secret>"
    normalised = text.replace("\\", "/")
    if "://" in normalised:
        return "<redacted-external-url>"
    if _looks_like_path(text, normalised):
        leaf = normalised.rstrip("/").rsplit("/", 1)[-1]
        return leaf or "<redacted-path>"
    return text


def _looks_like_path(original: str, normalised: str) -> bool:
    if len(original) >= 3 and original[1] == ":" and original[2] in "\\/":
        return True
    if normalised.startswith("//"):
        return True
    if normalised.startswith("~"):
        return True
    if normalised.startswith("/") and "/" in normalised[1:]:
        return True
    if ":/" in normalised:
        return True
    if "$" in original and "/" in normalised:
        return True
    if "%" in original and "/" in normalised:
        return True
    return False


__all__ = ["OptionalSolverPluginManifestReloadAcceptancePersistencePanel"]
