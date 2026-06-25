"""PySide display panel for optional solver plugin manifest previews."""

from __future__ import annotations

from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestActionState,
    OptionalSolverPluginManifestGuiViewModel,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class OptionalSolverPluginManifestPanel(_BaseDialog):
    """Render an already-built plugin manifest preview view-model."""

    def __init__(
        self,
        view_model: OptionalSolverPluginManifestGuiViewModel,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestPanel")
        self.setWindowTitle("Optional Solver Plugin Manifest Preview")
        self.resize(1120, 760)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = view_model
        self._disabled_action_reasons: dict[str, str] = {}
        self._action_buttons: dict[str, Any] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName("oswOptionalSolverPluginManifestSummary")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestTabs")
        root.addWidget(self.tabs, 1)

        self.accepted_table = _readonly_table(
            "oswOptionalSolverPluginManifestAcceptedTable",
            self.tabs,
            (
                "Stack ID",
                "Display Name",
                "Source Type",
                "Trust Label",
                "Issue",
                "Support",
                "Capabilities",
                "Notice",
            ),
        )
        self.rejected_table = _readonly_table(
            "oswOptionalSolverPluginManifestRejectedTable",
            self.tabs,
            (
                "Stack ID",
                "Source",
                "Trust Label",
                "Reason",
                "Diagnostics",
                "Suggested Fix",
                "Unsafe Claims",
            ),
        )
        self.conflict_table = _readonly_table(
            "oswOptionalSolverPluginManifestConflictTable",
            self.tabs,
            (
                "Stack ID",
                "Winning Source",
                "Rejected Source",
                "Message",
                "Policy",
                "Override",
            ),
        )
        self.diagnostics_table = _readonly_table(
            "oswOptionalSolverPluginManifestDiagnosticsTable",
            self.tabs,
            (
                "Severity",
                "Category",
                "Code",
                "Message",
                "Source",
                "Stack ID",
                "Suggested Fix",
            ),
        )
        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestTrustPanel",
            self.tabs,
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestSafetyPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName("oswOptionalSolverPluginManifestActionsPanel")

        self.tabs.addTab(self.accepted_table, "Accepted")
        self.tabs.addTab(self.rejected_table, "Rejected")
        self.tabs.addTab(self.conflict_table, "Conflicts")
        self.tabs.addTab(self.diagnostics_table, "Diagnostics")
        self.tabs.addTab(self.trust_panel, "Trust")
        self.tabs.addTab(self.safety_panel, "Safety")
        self.tabs.addTab(self.actions_panel, "Actions")

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswOptionalSolverPluginManifestCloseButton")
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.set_view_model(view_model)
        self.set_theme_tokens(self._tokens)

    def set_view_model(
        self,
        view_model: OptionalSolverPluginManifestGuiViewModel,
    ) -> None:
        """Render a supplied view-model without loading or activating manifests."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_accepted_table()
        self._populate_rejected_table()
        self._populate_conflict_table()
        self._populate_diagnostics_table()
        self.trust_panel.setPlainText(_trust_text(view_model))
        self.safety_panel.setPlainText(_safety_text(view_model))
        self._populate_action_state()

    def summary_text(self) -> str:
        return self.summary_label.text()

    def accepted_rows_text(self) -> str:
        return _table_text(self.accepted_table, empty_text="No accepted manifests.")

    def rejected_rows_text(self) -> str:
        return _table_text(self.rejected_table, empty_text="No rejected manifests.")

    def conflict_rows_text(self) -> str:
        return _table_text(self.conflict_table, empty_text="No manifest conflicts.")

    def diagnostics_text(self) -> str:
        return _table_text(self.diagnostics_table, empty_text="No diagnostics.")

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def available_action_names(self) -> tuple[str, ...]:
        return tuple(
            action.action.value for action in self._view_model.actions if action.available
        )

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOptionalSolverPluginManifestPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverPluginManifestSummary {"
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

    def _build_actions_panel(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.actions_panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.action_state_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestActionStatePanel",
            self.actions_panel,
        )
        layout.addWidget(self.action_state_panel, 1)
        button_grid = QtWidgets.QGridLayout()
        for index, action_state in enumerate(self._view_model.actions):
            button = QtWidgets.QPushButton(action_state.label, self.actions_panel)
            button.setObjectName(_action_button_object_name(action_state))
            button.setEnabled(False)
            self._action_buttons[action_state.action.value] = button
            button_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(button_grid)

    def _populate_accepted_table(self) -> None:
        rows = [
            (
                row.stack_id,
                row.display_name,
                row.source_type,
                row.trust_label,
                row.related_issue,
                row.support_status,
                row.capabilities_summary,
                row.not_validation_evidence_text,
            )
            for row in self._view_model.accepted_rows
        ]
        _populate_table(self.accepted_table, rows)

    def _populate_rejected_table(self) -> None:
        rows = [
            (
                row.stack_id,
                _source_text(row.source_type, row.source_ref),
                row.trust_label,
                row.rejection_reason,
                "; ".join(row.diagnostics) or "none",
                row.suggested_fix or "not supplied",
                "; ".join(row.unsafe_claim_indicators) or "none",
            )
            for row in self._view_model.rejected_rows
        ]
        _populate_table(self.rejected_table, rows)

    def _populate_conflict_table(self) -> None:
        rows = [
            (
                row.stack_id,
                _source_text(row.winning_source_type, row.winning_source_ref),
                _source_text(row.rejected_source_type, row.rejected_source_ref),
                row.message,
                row.built_in_wins_text,
                row.plugin_override_disabled_text,
            )
            for row in self._view_model.conflict_rows
        ]
        _populate_table(self.conflict_table, rows)

    def _populate_diagnostics_table(self) -> None:
        rows = [
            (
                row.severity,
                row.category,
                row.code,
                row.message,
                row.source_ref or "not supplied",
                row.stack_id or "not supplied",
                row.suggested_fix or "not supplied",
            )
            for row in self._view_model.diagnostic_rows
        ]
        _populate_table(self.diagnostics_table, rows)

    def _populate_action_state(self) -> None:
        self._disabled_action_reasons = {}
        lines: list[str] = []
        for action_state in self._view_model.actions:
            action_name = action_state.action.value
            state_text = _action_state_status(action_state)
            lines.append(f"{action_name}: {state_text}")
            lines.append(f"  {action_state.reason}")
            self._disabled_action_reasons[action_name] = action_state.reason
            button = self._action_buttons.get(action_name)
            if button is not None:
                button.setEnabled(bool(action_state.enabled))
                button.setToolTip(action_state.reason)
        self.action_state_panel.setPlainText("\n".join(lines))


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


def _summary_text(view_model: OptionalSolverPluginManifestGuiViewModel) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest preview: "
        f"accepted={summary.accepted_count}; "
        f"rejected={summary.rejected_count}; "
        f"conflicts={summary.conflict_count}; "
        f"diagnostics={summary.diagnostic_count}; "
        f"visible_accepted={summary.visible_accepted_count}; "
        f"visible_rejected={summary.visible_rejected_count}; "
        f"visible_conflicts={summary.visible_conflict_count}; "
        f"visible_diagnostics={summary.visible_diagnostic_count}. "
        f"{summary.status_text}"
    )


def _trust_text(view_model: OptionalSolverPluginManifestGuiViewModel) -> str:
    lines = [
        "Trust/source labels.",
        "Third-party/plugin manifests are not trusted by default.",
        "Trust label is not certification.",
    ]
    if not view_model.trust_badges:
        lines.append("No trust/source labels.")
        return "\n".join(lines)
    for badge in view_model.trust_badges:
        lines.append(
            f"{badge.label} | source_type={badge.source_type} | "
            f"trust_label={badge.trust_label} | source_ref={badge.source_ref} | "
            f"{badge.warning_text}"
        )
    return "\n".join(lines)


def _safety_text(view_model: OptionalSolverPluginManifestGuiViewModel) -> str:
    lines = [
        "Optional solver plugin manifest GUI preview safety boundary.",
        "View-model driven display only.",
        "Plugin manifest preview is not validation evidence.",
        "Third-party/plugin manifests are not trusted by default.",
        "Trust label is not certification.",
        "External solvers are not bundled.",
        "No file dialog.",
        "No file loading.",
        "No plugin loading.",
        "No plugin activation.",
        "No plugin code execution.",
        "No plugin package import.",
        "No directory scan.",
        "No network fetch.",
        "No discovery execution.",
        "No solver execution.",
        "No dependency installation.",
        "No install action.",
        "No issue closure action.",
        "No issue mutation.",
        "No release mutation.",
    ]
    lines.extend(view_model.guidance_text)
    lines.extend(view_model.safety_text)
    return "\n".join(dict.fromkeys(lines))


def _source_text(source_type: str, source_ref: str) -> str:
    return f"{source_type}: {source_ref or 'not supplied'}"


def _action_state_status(action_state: OptionalSolverPluginManifestActionState) -> str:
    availability = "available" if action_state.available else "unavailable"
    enabled = "enabled" if action_state.enabled else "disabled"
    future = "future" if action_state.future_action else "current"
    return f"{availability}; {enabled}; {future}; display-only"


def _action_button_object_name(
    action_state: OptionalSolverPluginManifestActionState,
) -> str:
    return "oswOptionalSolverPluginManifestAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


__all__ = ["OptionalSolverPluginManifestPanel"]
