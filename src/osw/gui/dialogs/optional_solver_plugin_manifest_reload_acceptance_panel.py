"""PySide reload acceptance review panel for optional solver manifests.

The panel is a view-model-only review surface over an already-built
``OptionalSolverPluginManifestReloadAcceptanceViewModel``. It renders readiness,
blockers, acknowledgements, expiry reasons, accepted-state scope, provenance,
diagnostics, non-action flags, disabled/future action states, and safety
guidance. It does not accept runtime reload state, mutate project state, invoke
readers, call CLI code, or create output artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel import (
    OptionalSolverPluginManifestReloadAcceptanceViewModel,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class OptionalSolverPluginManifestReloadAcceptancePanel(_BaseDialog):
    """Read-only review panel over supplied reload acceptance view-model state."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestReloadAcceptanceViewModel | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestReloadAcceptancePanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Reload Acceptance")
        self.resize(1380, 920)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model
            or OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable()
        )

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptanceSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestReloadAcceptanceTabs")
        root.addWidget(self.tabs, 1)

        self.summary_table = self._add_table_tab(
            "Summary",
            "oswOptionalSolverPluginManifestReloadAcceptanceSummaryTable",
            ("field", "value"),
        )
        self.blockers_table = self._add_table_tab(
            "Preconditions / Blockers",
            "oswOptionalSolverPluginManifestReloadAcceptanceBlockersTable",
            (
                "blocker_id",
                "diagnostic_code",
                "label",
                "required_action",
                "severity",
                "blocks_acceptance",
            ),
        )
        self.acknowledgements_table = self._add_table_tab(
            "Acknowledgements",
            "oswOptionalSolverPluginManifestReloadAcceptanceAcknowledgementsTable",
            (
                "acknowledgement_id",
                "required",
                "satisfied",
                "expired",
                "blocker",
                "not_validation_evidence",
                "not_trust_restoration",
                "expiry_reasons",
            ),
        )
        self.expiry_table = self._add_table_tab(
            "Acknowledgement Expiry",
            "oswOptionalSolverPluginManifestReloadAcceptanceExpiryTable",
            ("expiry_reason", "effect"),
        )
        self.accepted_state_table = self._add_table_tab(
            "Accepted-State Scope",
            "oswOptionalSolverPluginManifestReloadAcceptanceAcceptedStateTable",
            (
                "state_id",
                "accepted_for_session_review",
                "scope",
                "untrusted_by_default",
                "persisted_state",
                "project_schema_state",
                "validation_evidence",
                "validation_failure",
                "automatic_activation",
                "trust_restoration",
                "issue_closure",
                "release_mutation",
                "certification",
            ),
        )
        self.provenance_table = self._add_table_tab(
            "Reader / Preview Provenance",
            "oswOptionalSolverPluginManifestReloadAcceptanceProvenanceTable",
            (
                "source_id",
                "source_display",
                "source_reference_redacted",
                "provenance_label",
                "trust_label",
                "source_fingerprint_changed",
                "user_plugin_sources_untrusted_by_default",
                "built_ins_authoritative_by_default",
                "trust_label_is_certification",
            ),
        )
        self.schema_table = self._add_table_tab(
            "Schema / Migration",
            "oswOptionalSolverPluginManifestReloadAcceptanceSchemaTable",
            ("field", "state", "guidance"),
        )
        self.redaction_table = self._add_table_tab(
            "Redaction / Privacy",
            "oswOptionalSolverPluginManifestReloadAcceptanceRedactionTable",
            ("field", "state", "guidance"),
        )
        self.candidate_lifecycle_table = self._add_table_tab(
            "Candidate Lifecycle",
            "oswOptionalSolverPluginManifestReloadAcceptanceLifecycleTable",
            ("state", "policy", "guidance"),
        )
        self.stale_source_table = self._add_table_tab(
            "Stale Source / Re-preview",
            "oswOptionalSolverPluginManifestReloadAcceptanceStaleSourceTable",
            ("field", "state", "guidance"),
        )
        self.conflict_table = self._add_table_tab(
            "Conflict / Shared Stack",
            "oswOptionalSolverPluginManifestReloadAcceptanceConflictTable",
            ("field", "state", "guidance"),
        )
        self.unsafe_claim_table = self._add_table_tab(
            "Unsafe Claims",
            "oswOptionalSolverPluginManifestReloadAcceptanceUnsafeClaimTable",
            ("field", "state", "guidance"),
        )
        self.evidence_history_table = self._add_table_tab(
            "Evidence / History",
            "oswOptionalSolverPluginManifestReloadAcceptanceEvidenceTable",
            (
                "evidence_id",
                "candidate_id",
                "evidence_type",
                "retained_reference_only",
                "not_validation_evidence",
                "not_validation_failure",
                "issue_closure_implied",
                "release_mutation_implied",
            ),
        )
        self.trust_table = self._add_table_tab(
            "Trust / Provenance",
            "oswOptionalSolverPluginManifestReloadAcceptanceTrustTable",
            (
                "source_id",
                "trust_label",
                "trust_restored",
                "trust_label_is_certification",
                "certification_claimed",
            ),
        )
        self.diagnostics_table = self._add_table_tab(
            "Diagnostics",
            "oswOptionalSolverPluginManifestReloadAcceptanceDiagnosticsTable",
            ("severity", "code", "message", "blocker", "related", "suggested_fix"),
        )
        self.non_action_flags_table = self._add_table_tab(
            "Non-Action Flags",
            "oswOptionalSolverPluginManifestReloadAcceptanceNonActionFlagsTable",
            ("flag", "value", "review_state"),
        )
        self.actions_table = self._add_table_tab(
            "Disabled / Future Actions",
            "oswOptionalSolverPluginManifestReloadAcceptanceActionsTable",
            ("action", "enabled", "future_only", "reason"),
        )
        self.safety_panel = self._add_text_tab(
            "Safety Guidance",
            "oswOptionalSolverPluginManifestReloadAcceptanceSafety",
        )

        close_button = QtWidgets.QPushButton("Close", self)
        close_button.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptanceClose"
        )
        close_button.clicked.connect(self.close)
        root.addWidget(close_button)

        self._apply_theme()
        self.refresh()

    def set_view_model(
        self,
        view_model: OptionalSolverPluginManifestReloadAcceptanceViewModel,
    ) -> None:
        """Replace the supplied view-model and refresh rendered rows."""

        self._view_model = view_model
        self.refresh()

    def refresh(self) -> None:
        """Render supplied view-model records without mutating them."""

        mapping = self._view_model.to_mapping()
        self.summary_label.setText(_summary_label_text(mapping))
        _populate_table(self.summary_table, _summary_rows(mapping))
        _populate_table(
            self.blockers_table,
            _mapping_rows(mapping.get("blockers"), _BLOCKER_COLUMNS),
        )
        _populate_table(
            self.acknowledgements_table,
            _mapping_rows(mapping.get("acknowledgements"), _ACK_COLUMNS),
        )
        _populate_table(
            self.expiry_table,
            _expiry_rows(mapping.get("acknowledgement_expiry_reasons")),
        )
        _populate_table(
            self.accepted_state_table,
            _mapping_rows(mapping.get("accepted_state"), _ACCEPTED_COLUMNS),
        )
        _populate_table(
            self.provenance_table,
            _mapping_rows(mapping.get("source_provenance"), _PROVENANCE_COLUMNS),
        )
        _populate_table(self.schema_table, _schema_rows(mapping))
        _populate_table(self.redaction_table, _redaction_rows(mapping))
        _populate_table(
            self.candidate_lifecycle_table,
            _candidate_lifecycle_rows(mapping),
        )
        _populate_table(
            self.stale_source_table,
            _diagnostic_policy_rows(
                mapping,
                "stale_source_repreview",
                "Stale sources require re-preview; stale state is not validation failure.",
            ),
        )
        _populate_table(
            self.conflict_table,
            _diagnostic_policy_rows(
                mapping,
                "conflict",
                "Conflicts and shared-stack warnings remain visible; "
                "built-ins stay authoritative.",
            ),
        )
        _populate_table(
            self.unsafe_claim_table,
            _diagnostic_policy_rows(
                mapping,
                "unsafe_claim",
                "Unsafe validation, issue, release, trust, install, execution, "
                "or certification claims remain blocked.",
            ),
        )
        _populate_table(
            self.evidence_history_table,
            _mapping_rows(mapping.get("evidence_history"), _EVIDENCE_COLUMNS),
        )
        _populate_table(
            self.trust_table,
            _mapping_rows(mapping.get("trust_badges"), _TRUST_COLUMNS),
        )
        _populate_table(
            self.diagnostics_table,
            _mapping_rows(mapping.get("diagnostics"), _DIAGNOSTIC_COLUMNS),
        )
        _populate_table(self.non_action_flags_table, _non_action_flag_rows(mapping))
        _populate_table(
            self.actions_table,
            _mapping_rows(mapping.get("actions"), _ACTION_COLUMNS),
        )
        self.safety_panel.setPlainText(_safety_text(mapping))

    def summary_text(self) -> str:
        return self.summary_label.text()

    def summary_rows_text(self) -> str:
        return _table_text(self.summary_table, empty_text="No acceptance summary.")

    def blocker_rows_text(self) -> str:
        return _table_text(self.blockers_table, empty_text="No acceptance blockers.")

    def acknowledgement_rows_text(self) -> str:
        return _table_text(
            self.acknowledgements_table,
            empty_text="No acceptance acknowledgements.",
        )

    def expiry_rows_text(self) -> str:
        return _table_text(self.expiry_table, empty_text="No expiry reasons.")

    def accepted_state_text(self) -> str:
        return _table_text(
            self.accepted_state_table,
            empty_text="No accepted-state rows.",
        )

    def provenance_text(self) -> str:
        return _table_text(self.provenance_table, empty_text="No provenance rows.")

    def schema_migration_text(self) -> str:
        return _table_text(self.schema_table, empty_text="No schema rows.")

    def redaction_privacy_text(self) -> str:
        return _table_text(self.redaction_table, empty_text="No redaction rows.")

    def candidate_lifecycle_text(self) -> str:
        return _table_text(
            self.candidate_lifecycle_table,
            empty_text="No lifecycle rows.",
        )

    def stale_source_text(self) -> str:
        return _table_text(self.stale_source_table, empty_text="No stale-source rows.")

    def conflict_text(self) -> str:
        return _table_text(self.conflict_table, empty_text="No conflict rows.")

    def unsafe_claim_text(self) -> str:
        return _table_text(self.unsafe_claim_table, empty_text="No unsafe claims.")

    def evidence_history_text(self) -> str:
        return _table_text(
            self.evidence_history_table,
            empty_text="No evidence/history rows.",
        )

    def trust_text(self) -> str:
        return _table_text(self.trust_table, empty_text="No trust rows.")

    def diagnostics_text(self) -> str:
        return _table_text(
            self.diagnostics_table,
            empty_text="No acceptance diagnostics.",
        )

    def non_action_flags_text(self) -> str:
        return _table_text(
            self.non_action_flags_table,
            empty_text="No non-action flags.",
        )

    def action_state_text(self) -> str:
        return _table_text(self.actions_table, empty_text="No action states.")

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def available_action_names(self) -> list[str]:
        rows = _normalised_rows(self._view_model.to_mapping().get("actions"))
        return [
            str(row.get("action", ""))
            for row in rows
            if bool(row.get("enabled", False))
        ]

    def disabled_action_reasons(self) -> dict[str, str]:
        rows = _normalised_rows(self._view_model.to_mapping().get("actions"))
        return {
            str(row.get("action", "")): _safe_text(row.get("reason", ""))
            for row in rows
            if not bool(row.get("enabled", False))
        }

    def rendered_text(self) -> str:
        """Return all rendered text for focused assertions."""

        return "\n".join(
            value
            for value in (
                self.summary_text(),
                self.summary_rows_text(),
                self.blocker_rows_text(),
                self.acknowledgement_rows_text(),
                self.expiry_rows_text(),
                self.accepted_state_text(),
                self.provenance_text(),
                self.schema_migration_text(),
                self.redaction_privacy_text(),
                self.candidate_lifecycle_text(),
                self.stale_source_text(),
                self.conflict_text(),
                self.unsafe_claim_text(),
                self.evidence_history_text(),
                self.trust_text(),
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


_BLOCKER_COLUMNS = (
    "blocker_id",
    "diagnostic_code",
    "label",
    "required_action",
    "severity",
    "blocks_acceptance",
)
_ACK_COLUMNS = (
    "acknowledgement_id",
    "required",
    "satisfied",
    "expired",
    "blocker",
    "not_validation_evidence",
    "not_trust_restoration",
    "expiry_reasons",
)
_ACCEPTED_COLUMNS = (
    "state_id",
    "accepted_for_session_review",
    "scope",
    "untrusted_by_default",
    "persisted_state",
    "project_schema_state",
    "validation_evidence",
    "validation_failure",
    "automatic_activation",
    "trust_restoration",
    "issue_closure",
    "release_mutation",
    "certification",
)
_PROVENANCE_COLUMNS = (
    "source_id",
    "source_display",
    "source_reference_redacted",
    "provenance_label",
    "trust_label",
    "source_fingerprint_changed",
    "user_plugin_sources_untrusted_by_default",
    "built_ins_authoritative_by_default",
    "trust_label_is_certification",
)
_EVIDENCE_COLUMNS = (
    "evidence_id",
    "candidate_id",
    "evidence_type",
    "retained_reference_only",
    "not_validation_evidence",
    "not_validation_failure",
    "issue_closure_implied",
    "release_mutation_implied",
)
_TRUST_COLUMNS = (
    "source_id",
    "trust_label",
    "trust_restored",
    "trust_label_is_certification",
    "certification_claimed",
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


def _summary_label_text(mapping: Mapping[str, object]) -> str:
    summary = _mapping(mapping.get("summary"))
    values = {
        "state": summary.get("state", "unknown"),
        "readiness": summary.get("readiness", "unknown"),
        "requested": summary.get("requested", False),
        "preview_available": summary.get("preview_available", False),
        "ready_future_only": summary.get("ready_for_future_acceptance", False),
        "accepted_for_session_review": summary.get(
            "accepted_for_session_review", False
        ),
        "blocker_count": summary.get("blocker_count", 0),
        "missing_acknowledgement_count": summary.get(
            "missing_acknowledgement_count", 0
        ),
        "no_validation": not bool(
            summary.get("accepted_state_is_validation_evidence", False)
        ),
        "no_validation_failure": not bool(
            summary.get("accepted_state_is_validation_failure", False)
        ),
        "no_project_schema_mutation": not bool(
            summary.get("accepted_state_mutates_project_schema", False)
        ),
        "no_persistence_write": not bool(
            summary.get("accepted_state_is_persistence_write", False)
        ),
        "no_activation": not bool(
            summary.get("accepted_state_automatically_activates", False)
        ),
        "no_trust_restoration": not bool(
            summary.get("accepted_state_restores_trust", False)
        ),
        "no_discovery": not bool(summary.get("accepted_state_runs_discovery", False)),
        "no_solver_execution": not bool(
            summary.get("accepted_state_executes_solver", False)
        ),
        "no_issue_release_mutation": not bool(
            summary.get("accepted_state_closes_issue", False)
        )
        and not bool(summary.get("accepted_state_mutates_release", False)),
        "no_certification": not bool(
            summary.get("accepted_state_certifies_manifest", False)
        ),
        "future_activation_review_required": summary.get(
            "future_activation_review_required", False
        ),
        "future_discovery_refresh_required": summary.get(
            "future_discovery_refresh_required", False
        ),
    }
    return "; ".join(f"{key}={_safe_text(value)}" for key, value in values.items())


def _summary_rows(mapping: Mapping[str, object]) -> list[tuple[str, str]]:
    summary = _mapping(mapping.get("summary"))
    rows = [(str(key), _safe_text(value)) for key, value in summary.items()]
    rows.extend(
        (
            ("preview_success_is_acceptance", "no"),
            ("file_selection_is_acceptance", "no"),
            ("readiness_is_validation_evidence", "no"),
            ("readiness_is_validation_failure", "no"),
            ("trust_label_is_certification", "no"),
        )
    )
    return rows


def _mapping_rows(
    rows_value: object,
    columns: tuple[str, ...],
) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for row in _normalised_rows(rows_value):
        rows.append(tuple(_safe_text(row.get(column, "")) for column in columns))
    return rows


def _expiry_rows(value: object) -> list[tuple[str, str]]:
    return [
        (
            _safe_text(reason),
            "expires acknowledgements; requires re-review; not validation failure",
        )
        for reason in _sequence(value)
    ]


def _schema_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str]]:
    codes = _diagnostic_codes(mapping)
    unsupported = "OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED" in codes
    migration = "OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED" in codes
    return [
        ("payload_kind_required", "yes", "Payload kind is required for review."),
        (
            "schema_version_required",
            "yes",
            "Schema version is required for review.",
        ),
        (
            "unsupported_schema_blocks",
            _yes_no(unsupported),
            "Unsupported schema blocks future acceptance.",
        ),
        (
            "migration_required_blocks",
            _yes_no(migration),
            "Migration remains a separate future gate.",
        ),
        (
            "schema_mismatch_is_validation_failure",
            "no",
            "Schema mismatch is not validation failure.",
        ),
        (
            "persistence_schema_is_project_schema",
            "no",
            "Persistence schema remains separate from ProjectSchema.",
        ),
        ("gui_repairs_or_migrates_files", "no", "The panel never repairs files."),
    ]


def _redaction_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str]]:
    codes = _diagnostic_codes(mapping)
    return [
        ("raw_paths_hidden_by_default", "yes", "Basename or redacted display wins."),
        (
            "home_env_secret_token_api_key_values_blocked",
            "yes",
            "Private paths and secret-like values are redacted.",
        ),
        (
            "unredacted_path_blocked",
            _yes_no("OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED" in codes),
            "Unredacted path disclosure blocks future acceptance.",
        ),
        (
            "secret_like_value_blocked",
            _yes_no("OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED" in codes),
            "Secret-like values block future acceptance.",
        ),
        ("fingerprints_are_trust_signals", "no", "Fingerprints are not trust."),
        (
            "accepted_state_stores_secrets_as_truth",
            "no",
            "Accepted state must never store secrets as truth.",
        ),
    ]


def _candidate_lifecycle_rows(
    mapping: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    summary = _mapping(mapping.get("summary"))
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
            "future_discovery_refresh_required",
            "Discovery refresh remains a separate future review.",
        ),
        (
            "future_activation_review_required",
            _safe_text(summary.get("future_activation_review_required", False)),
            "No automatic activation occurs.",
        ),
        (
            "future_discovery_refresh_required",
            _safe_text(summary.get("future_discovery_refresh_required", False)),
            "No live discovery or passive refresh occurs.",
        ),
        (
            "skipped_missing",
            "skipped_missing_remains_skipped_missing",
            "Skipped-missing is not success.",
        ),
    ]


def _diagnostic_policy_rows(
    mapping: Mapping[str, object],
    marker: str,
    guidance: str,
) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for diagnostic in _normalised_rows(mapping.get("diagnostics")):
        code = str(diagnostic.get("code", ""))
        if marker in code.lower():
            rows.append((code, _safe_text(diagnostic.get("blocker", "")), guidance))
    if not rows:
        rows.append((marker, "not-present", guidance))
    return rows


def _non_action_flag_rows(mapping: Mapping[str, object]) -> list[tuple[str, str, str]]:
    flags = _mapping(mapping.get("non_action_flags"))
    return [
        (
            str(flag),
            _safe_text(value),
            "safe false boundary" if value is False else "review boundary failure",
        )
        for flag, value in flags.items()
    ]


def _safety_text(mapping: Mapping[str, object]) -> str:
    supplied = tuple(_safe_text(item) for item in _sequence(mapping.get("safety_text")))
    fixed = (
        "Review-only panel.",
        "Preview success is not acceptance.",
        "File selection is not acceptance.",
        "Panel construction is not acceptance.",
        "Acceptance readiness is not validation evidence.",
        "Acceptance readiness is not validation failure.",
        "Accepted state is not trust restoration.",
        "Accepted state is not automatic activation.",
        "Accepted state is not ProjectSchema state.",
        "Accepted state is not persistence.",
        "Accepted state does not close issues or mutate releases.",
        "Trust label is not certification.",
        "User/plugin sources remain untrusted by default.",
        "Built-ins remain authoritative by default.",
        "No persisted state file access.",
        "No reader call.",
        "No CLI bridge.",
        "No discovery, validation, solver execution, install, or uninstall.",
        "No reloadable bundle, export file, report file, copy, attachment, "
        "or output-folder action.",
        "Issues #6 through #11 remain open.",
    )
    return "\n".join(fixed + supplied)


def _diagnostic_codes(mapping: Mapping[str, object]) -> set[str]:
    return {
        str(row.get("code", ""))
        for row in _normalised_rows(mapping.get("diagnostics"))
        if row.get("code")
    }


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
        "sk-",
        "ghp_",
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


__all__ = ["OptionalSolverPluginManifestReloadAcceptancePanel"]
