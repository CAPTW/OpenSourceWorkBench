"""PySide reload review panel for optional solver plugin manifests.

This panel is a read-only/review-only surface over already-built
``OptionalSolverPluginManifestReloadViewModel`` records. It renders summary,
source/provenance, schema/migration, candidate lifecycle, acknowledgement,
redaction/privacy, stale-source, conflict/shared-stack, unsafe-claim,
evidence/history, diagnostic, action-state, trust, and safety information.

It implements no file dialog behavior, file reader/parser implementation,
runtime file reading, runtime state parsing, runtime reload behavior, default
reload path, background reload, reloadable bundle creation, export/report file
creation, clipboard behavior, report attachment, open-output-folder behavior,
CLI behavior, ProjectSchema mutation, live discovery, passive refresh, plugin
package import, directory scan, network fetch, validation execution, solver
execution, dependency installation or uninstall, solver uninstall, automatic
activation, trust restoration, issue/release/tag/asset mutation, version bump,
validation-pass/fail claim, issue-closure claim, bundled-solver claim, or
certification claim.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
    OptionalSolverPluginManifestReloadViewModel,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class OptionalSolverPluginManifestReloadPanel(_BaseDialog):
    """Read-only reload review panel over supplied view-model state."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestReloadViewModel | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestReloadPanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Reload")
        self.resize(1320, 900)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = view_model or OptionalSolverPluginManifestReloadViewModel.empty()
        self._disabled_action_reasons: dict[str, str] = {}
        self._action_buttons: dict[str, Any] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName("oswOptionalSolverPluginManifestReloadSummary")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestReloadTabs")
        root.addWidget(self.tabs, 1)

        self.summary_table = self._add_table_tab(
            "Summary",
            "oswOptionalSolverPluginManifestReloadSummaryTable",
            ("field", "value"),
        )
        self.sources_table = self._add_table_tab(
            "Source / Provenance",
            "oswOptionalSolverPluginManifestReloadSourcesTable",
            (
                "source_id",
                "source_type",
                "source_display",
                "source_reference_redacted",
                "provenance_label",
                "trust_label",
                "trust_label_is_certification",
                "user_plugin_sources_untrusted_by_default",
                "built_ins_authoritative_by_default",
                "fingerprint_not_trust_signal",
            ),
        )
        self.schema_table = self._add_table_tab(
            "Schema / Migration",
            "oswOptionalSolverPluginManifestReloadSchemaTable",
            (
                "payload_kind",
                "payload_schema_version",
                "payload_kind_required",
                "payload_schema_version_required",
                "supported_schema",
                "migration_required",
                "blocker",
                "schema_mismatch_not_validation_failure",
                "schema_model_separate_from_project_schema",
            ),
        )
        self.candidates_table = self._add_table_tab(
            "Candidates",
            "oswOptionalSolverPluginManifestReloadCandidatesTable",
            (
                "candidate_id",
                "display_name",
                "source_id",
                "source_type",
                "lifecycle_state",
                "reload_review_state",
                "requires_future_activation_review",
                "requires_future_discovery_refresh",
                "no_automatic_activation",
                "no_trust_restoration",
                "skipped_missing_remains_skipped_missing",
            ),
        )
        self.acknowledgements_table = self._add_table_tab(
            "Acknowledgements / Expiry",
            "oswOptionalSolverPluginManifestReloadAcknowledgementsTable",
            (
                "acknowledgement_id",
                "label",
                "required",
                "satisfied",
                "expired",
                "blocker",
                "expiry_reasons",
            ),
        )
        self.redaction_table = self._add_table_tab(
            "Redaction / Privacy",
            "oswOptionalSolverPluginManifestReloadRedactionTable",
            (
                "redaction_required",
                "redaction_review_required",
                "raw_paths_hidden_by_default",
                "unredacted_path_blocked",
                "secret_like_content_blocked",
                "fingerprints_not_trust_signals",
                "redaction_review_before_activation_review",
            ),
        )
        self.stale_sources_table = self._add_table_tab(
            "Stale Sources / Re-preview",
            "oswOptionalSolverPluginManifestReloadStaleSourcesTable",
            (
                "source_id",
                "stale_source_state",
                "repreview_required",
                "old_preview_not_silently_trusted",
                "no_source_file_io",
                "stale_source_not_validation_failure",
            ),
        )
        self.conflicts_table = self._add_table_tab(
            "Conflicts / Shared Stack",
            "oswOptionalSolverPluginManifestReloadConflictsTable",
            (
                "conflict_id",
                "candidate_id",
                "conflict_type",
                "built_ins_win_by_default",
                "persisted_state_overrides_built_ins",
                "shared_stack_warning_visible",
                "reload_resolves_conflict",
                "blocker",
            ),
        )
        self.unsafe_claims_table = self._add_table_tab(
            "Unsafe Claims",
            "oswOptionalSolverPluginManifestReloadUnsafeClaimsTable",
            (
                "claim_id",
                "candidate_id",
                "claim_type",
                "claim_text",
                "blocked",
                "not_reloaded_as_truth",
            ),
        )
        self.evidence_history_table = self._add_table_tab(
            "Evidence / History",
            "oswOptionalSolverPluginManifestReloadEvidenceHistoryTable",
            (
                "evidence_id",
                "candidate_id",
                "evidence_type",
                "deactivation_history_retained",
                "reactivation_history_retained",
                "historical_evidence_reference_only",
                "skipped_missing_remains_skipped_missing",
                "reload_is_not_validation_evidence",
                "evidence_deleted_or_rewritten",
                "issue_closure_implied",
            ),
        )
        self.trust_panel = self._add_text_tab(
            "Trust",
            "oswOptionalSolverPluginManifestReloadTrust",
        )
        self.diagnostics_table = self._add_table_tab(
            "Diagnostics",
            "oswOptionalSolverPluginManifestReloadDiagnosticsTable",
            (
                "severity",
                "code",
                "message",
                "blocker",
                "related",
                "suggested_fix",
            ),
        )
        self.actions_table = self._add_actions_tab()
        self.safety_panel = self._add_text_tab(
            "Safety Guidance",
            "oswOptionalSolverPluginManifestReloadSafety",
        )

        close_button = QtWidgets.QPushButton("Close", self)
        close_button.setObjectName("oswOptionalSolverPluginManifestReloadClose")
        close_button.clicked.connect(self.close)
        root.addWidget(close_button)

        self._apply_theme()
        self.refresh()

    def set_view_model(
        self,
        view_model: OptionalSolverPluginManifestReloadViewModel,
    ) -> None:
        self._view_model = view_model
        self.refresh()

    def refresh(self) -> None:
        self._populate_all()

    def summary_text(self) -> str:
        return self.summary_label.text()

    def summary_rows_text(self) -> str:
        return _table_text(self.summary_table, empty_text="No reload summary.")

    def source_rows_text(self) -> str:
        return _table_text(self.sources_table, empty_text="No reload sources.")

    def schema_migration_rows_text(self) -> str:
        return _table_text(self.schema_table, empty_text="No schema rows.")

    def candidate_rows_text(self) -> str:
        return _table_text(self.candidates_table, empty_text="No reload candidates.")

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table,
            empty_text="No reload acknowledgements.",
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

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def diagnostics_text(self) -> str:
        return _table_text(self.diagnostics_table, empty_text="No reload diagnostics.")

    def action_state_text(self) -> str:
        return _table_text(self.actions_table, empty_text="No reload action states.")

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def redacted_summary_text(self) -> str:
        return _mapping_text(self._view_model.to_mapping())

    def available_action_names(self) -> list[str]:
        return [
            name
            for name, button in self._action_buttons.items()
            if bool(button.isEnabled())
        ]

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

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

    def _add_actions_tab(self) -> object:
        panel = QtWidgets.QWidget(self.tabs)
        panel.setObjectName("oswOptionalSolverPluginManifestReloadActionsPanel")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        table = _readonly_table(
            "oswOptionalSolverPluginManifestReloadActionsTable",
            panel,
            ("action", "enabled", "future_only", "reason"),
        )
        layout.addWidget(table, 1)
        self._action_button_container = QtWidgets.QWidget(panel)
        self._action_button_container.setObjectName(
            "oswOptionalSolverPluginManifestReloadActionButtons"
        )
        self._action_button_layout = QtWidgets.QGridLayout(
            self._action_button_container
        )
        self._action_button_layout.setContentsMargins(0, 0, 0, 0)
        self._action_button_layout.setSpacing(4)
        layout.addWidget(self._action_button_container)
        self.tabs.addTab(panel, "Actions")
        return table

    def _populate_all(self) -> None:
        mapping = self._view_model.to_mapping()
        self.summary_label.setText(_summary_label_text(mapping))
        _populate_table(self.summary_table, _summary_rows(mapping))
        _populate_table(
            self.sources_table,
            _mapping_rows(mapping.get("sources"), _SOURCE_COLUMNS),
        )
        _populate_table(
            self.schema_table,
            _mapping_rows(mapping.get("schema"), _SCHEMA_COLUMNS),
        )
        _populate_table(
            self.candidates_table,
            _mapping_rows(mapping.get("candidates"), _CANDIDATE_COLUMNS),
        )
        _populate_table(
            self.acknowledgements_table,
            _mapping_rows(mapping.get("acknowledgements"), _ACK_COLUMNS),
        )
        _populate_table(
            self.redaction_table,
            _mapping_rows(mapping.get("redaction_privacy"), _REDACTION_COLUMNS),
        )
        _populate_table(
            self.stale_sources_table,
            _mapping_rows(mapping.get("stale_sources"), _STALE_COLUMNS),
        )
        _populate_table(
            self.conflicts_table,
            _mapping_rows(mapping.get("conflicts"), _CONFLICT_COLUMNS),
        )
        _populate_table(
            self.unsafe_claims_table,
            _mapping_rows(mapping.get("unsafe_claims"), _UNSAFE_COLUMNS),
        )
        _populate_table(
            self.evidence_history_table,
            _mapping_rows(mapping.get("evidence_history"), _EVIDENCE_COLUMNS),
        )
        _populate_table(
            self.diagnostics_table,
            _mapping_rows(mapping.get("diagnostics"), _DIAGNOSTIC_COLUMNS),
        )
        actions = _mapping_rows(mapping.get("actions"), _ACTION_COLUMNS)
        _populate_table(self.actions_table, actions)
        self._populate_action_buttons(mapping.get("actions"))
        self.trust_panel.setPlainText(_trust_text(mapping))
        self.safety_panel.setPlainText(_safety_text(mapping))

    def _populate_action_buttons(self, actions: object) -> None:
        self._disabled_action_reasons = {}
        self._action_buttons = {}
        while self._action_button_layout.count():
            item = self._action_button_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        action_rows = _normalised_rows(actions)
        for index, row in enumerate(action_rows):
            action = str(row.get("action", "unknown_action"))
            reason = str(row.get("reason", "disabled/future-only"))
            button = QtWidgets.QPushButton(_label_from_action(action), self)
            button.setObjectName(_action_button_object_name(action))
            button.setEnabled(bool(row.get("enabled", False)))
            if not button.isEnabled():
                self._disabled_action_reasons[action] = reason
            self._action_buttons[action] = button
            self._action_button_layout.addWidget(button, index // 3, index % 3)

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
            QPushButton:disabled {{
                color: {tokens.text_muted};
            }}
            """
        )


_SOURCE_COLUMNS = (
    "source_id",
    "source_type",
    "source_display",
    "source_reference_redacted",
    "provenance_label",
    "trust_label",
    "trust_label_is_certification",
    "user_plugin_sources_untrusted_by_default",
    "built_ins_authoritative_by_default",
    "fingerprint_not_trust_signal",
)
_SCHEMA_COLUMNS = (
    "payload_kind",
    "payload_schema_version",
    "payload_kind_required",
    "payload_schema_version_required",
    "supported_schema",
    "migration_required",
    "blocker",
    "schema_mismatch_not_validation_failure",
    "schema_model_separate_from_project_schema",
)
_CANDIDATE_COLUMNS = (
    "candidate_id",
    "display_name",
    "source_id",
    "source_type",
    "lifecycle_state",
    "reload_review_state",
    "requires_future_activation_review",
    "requires_future_discovery_refresh",
    "no_automatic_activation",
    "no_trust_restoration",
    "skipped_missing_remains_skipped_missing",
)
_ACK_COLUMNS = (
    "acknowledgement_id",
    "label",
    "required",
    "satisfied",
    "expired",
    "blocker",
    "expiry_reasons",
)
_REDACTION_COLUMNS = (
    "redaction_required",
    "redaction_review_required",
    "raw_paths_hidden_by_default",
    "unredacted_path_blocked",
    "secret_like_content_blocked",
    "fingerprints_not_trust_signals",
    "redaction_review_before_activation_review",
)
_STALE_COLUMNS = (
    "source_id",
    "stale_source_state",
    "repreview_required",
    "old_preview_not_silently_trusted",
    "no_source_file_io",
    "stale_source_not_validation_failure",
)
_CONFLICT_COLUMNS = (
    "conflict_id",
    "candidate_id",
    "conflict_type",
    "built_ins_win_by_default",
    "persisted_state_overrides_built_ins",
    "shared_stack_warning_visible",
    "reload_resolves_conflict",
    "blocker",
)
_UNSAFE_COLUMNS = (
    "claim_id",
    "candidate_id",
    "claim_type",
    "claim_text",
    "blocked",
    "not_reloaded_as_truth",
)
_EVIDENCE_COLUMNS = (
    "evidence_id",
    "candidate_id",
    "evidence_type",
    "deactivation_history_retained",
    "reactivation_history_retained",
    "historical_evidence_reference_only",
    "skipped_missing_remains_skipped_missing",
    "reload_is_not_validation_evidence",
    "evidence_deleted_or_rewritten",
    "issue_closure_implied",
)
_DIAGNOSTIC_COLUMNS = (
    "severity",
    "code",
    "message",
    "blocker",
    "related",
    "suggested_fix",
)
_ACTION_COLUMNS = ("action", "enabled", "future_only", "reason")


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


def _summary_label_text(mapping: Mapping[str, object]) -> str:
    summary = _mapping_value(mapping.get("summary"))
    fields = (
        "state",
        "readiness",
        "payload_kind",
        "payload_schema_version",
        "writer_version",
        "source_display",
        "source_reference_redacted",
        "source_count",
        "candidate_count",
        "acknowledgement_count",
        "diagnostic_count",
        "blocker_count",
        "warning_count",
        "reload_is_validation_evidence",
        "reload_is_validation_failure",
        "reload_restores_trust",
        "reload_automatically_activates",
        "reload_runs_discovery",
        "reload_imports_plugin_package",
        "reload_runs_validation",
        "reload_executes_solver",
        "reload_mutates_project_schema",
        "reload_closes_issue",
        "reload_mutates_release",
        "reload_certifies_manifest",
    )
    return "Optional solver plugin manifest reload: " + "; ".join(
        f"{field}={_summary_cell(summary.get(field, ''))}" for field in fields
    )


def _summary_rows(mapping: Mapping[str, object]) -> list[tuple[str, ...]]:
    summary = _mapping_value(mapping.get("summary"))
    return [(key, _summary_cell(value)) for key, value in summary.items()]


def _mapping_rows(
    rows_value: object,
    columns: tuple[str, ...],
) -> list[tuple[str, ...]]:
    return [
        tuple(_cell_text(row.get(column, "")) for column in columns)
        for row in _normalised_rows(rows_value)
    ]


def _normalised_rows(rows_value: object) -> list[Mapping[str, object]]:
    if not isinstance(rows_value, Sequence) or isinstance(rows_value, str):
        return []
    rows: list[Mapping[str, object]] = []
    for row in rows_value:
        if isinstance(row, Mapping):
            rows.append(row)
    return rows


def _mapping_value(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _summary_cell(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    return _cell_text(value)


def _cell_text(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Sequence) and not isinstance(value, str):
        return ", ".join(_cell_text(item) for item in value) or "none"
    return str(value) if str(value) else "none"


def _trust_text(mapping: Mapping[str, object]) -> str:
    lines = [
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-in manifests are authoritative by default.",
        "Trust label is not certification.",
        "Reloaded state is not validation evidence.",
        "Reloaded state is not validation success.",
        "Reloaded state is not validation failure.",
        "Reload is not trust restoration.",
        "Reload is not automatic activation.",
        "Reloaded state is not ProjectSchema state.",
        "Reload does not close issues or mutate releases.",
    ]
    for row in _normalised_rows(mapping.get("sources")):
        lines.append(
            "source="
            f"{_cell_text(row.get('source_id', ''))}; "
            f"type={_cell_text(row.get('source_type', ''))}; "
            f"trust={_cell_text(row.get('trust_label', ''))}; "
            "trust_label_is_certification="
            f"{_summary_cell(row.get('trust_label_is_certification', False))}"
        )
    return "\n".join(lines)


def _safety_text(mapping: Mapping[str, object]) -> str:
    lines = [
        "Reload GUI is read-only and review-only.",
        "No file dialog.",
        "No file reader/parser.",
        "No file reading or parsing.",
        "No runtime reload.",
        "No default reload path.",
        "No background reload.",
        "No reloadable bundle creation.",
        "No export/report file creation.",
        "No clipboard/report/open-folder behavior.",
        "No CLI behavior.",
        "No ProjectSchema mutation.",
        "No live discovery.",
        "No passive refresh.",
        "No plugin package import.",
        "No directory scan.",
        "No network fetch.",
        "No validation execution.",
        "No solver execution.",
        "No dependency installation or uninstall.",
        "No solver uninstall.",
        "No automatic activation.",
        "No trust restoration.",
        "No issue/release/tag/asset mutation.",
        "No version bump.",
        "No validation-pass claim.",
        "No validation-fail claim.",
        "No issue-closure claim.",
        "No bundled-solver claim.",
        "No certification claim.",
    ]
    safety_rows = mapping.get("safety_text")
    if isinstance(safety_rows, Sequence) and not isinstance(safety_rows, str):
        lines.extend(str(row) for row in safety_rows if str(row))
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


def _label_from_action(action: str) -> str:
    return action.replace("_", " ").title()


def _action_button_object_name(action: str) -> str:
    return "oswOptionalSolverPluginManifestReloadAction" + "".join(
        part.title() for part in action.split("_")
    )


__all__ = [
    "OptionalSolverPluginManifestReloadPanel",
]
