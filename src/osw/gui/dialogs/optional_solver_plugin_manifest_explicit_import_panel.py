"""PySide explicit JSON import panel for optional solver plugin manifests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestExplicitImportAction,
    OptionalSolverPluginManifestExplicitImportActionState,
    OptionalSolverPluginManifestExplicitImportDiagnosticViewModel,
    OptionalSolverPluginManifestExplicitImportGuiViewModel,
    OptionalSolverPluginManifestLoadReport,
    build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel,
    build_optional_solver_plugin_manifest_explicit_import_error_viewmodel,
    build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel,
    load_optional_solver_plugin_manifest_json,
)
from osw.experimental.optional_solvers.plugin_manifest_explicit_import_gui_viewmodel import (
    OSPMG_IMPORT_FILE_MISSING,
    OSPMG_IMPORT_FILE_TOO_LARGE,
    OSPMG_IMPORT_UNREADABLE,
    OSPMG_IMPORT_UNSUPPORTED_EXTENSION,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object

DEFAULT_PLUGIN_MANIFEST_JSON_MAX_BYTES = 1_048_576

FileChooser = Callable[[], object]
ManifestLoader = Callable[[str], OptionalSolverPluginManifestLoadReport]


class OptionalSolverPluginManifestExplicitImportPanel(_BaseDialog):
    """User-initiated local JSON preview panel for plugin manifest reports."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel | None = None,
        file_chooser: FileChooser | None = None,
        loader: ManifestLoader | None = None,
        max_file_size_bytes: int = DEFAULT_PLUGIN_MANIFEST_JSON_MAX_BYTES,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverPluginManifestExplicitImportPanel")
        self.setWindowTitle("Preview Plugin Manifest JSON")
        self.resize(1180, 820)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = (
            view_model
            or build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel()
        )
        self._file_chooser = file_chooser or self._choose_json_file_dialog
        self._loader = loader or (lambda path: load_optional_solver_plugin_manifest_json(path))
        self._max_file_size_bytes = max_file_size_bytes
        self._disabled_action_reasons: dict[str, str] = {}
        self._action_buttons: dict[str, Any] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        chooser_row = QtWidgets.QHBoxLayout()
        self.choose_button = QtWidgets.QPushButton("Choose plugin manifest JSON", self)
        self.choose_button.setObjectName(
            "oswOptionalSolverPluginManifestExplicitImportChooseButton"
        )
        self.choose_button.clicked.connect(self.choose_manifest_json)
        chooser_row.addWidget(self.choose_button)
        chooser_row.addStretch(1)
        root.addLayout(chooser_row)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName(
            "oswOptionalSolverPluginManifestExplicitImportSummary"
        )
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswOptionalSolverPluginManifestExplicitImportTabs")
        root.addWidget(self.tabs, 1)

        self.sources_table = _readonly_table(
            "oswOptionalSolverPluginManifestExplicitImportSourcesTable",
            self.tabs,
            (
                "Index",
                "Source Type",
                "Source Label",
                "Source Reference",
                "Trust Label",
                "Status",
                "Diagnostics",
                "Warning",
            ),
        )
        self.accepted_table = _readonly_table(
            "oswOptionalSolverPluginManifestExplicitImportAcceptedTable",
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
            "oswOptionalSolverPluginManifestExplicitImportRejectedTable",
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
            "oswOptionalSolverPluginManifestExplicitImportConflictTable",
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
            "oswOptionalSolverPluginManifestExplicitImportDiagnosticsTable",
            self.tabs,
            (
                "Layer",
                "Severity",
                "Code",
                "Message",
                "Source",
                "Stack ID",
                "Suggested Fix",
            ),
        )
        self.trust_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExplicitImportTrustPanel",
            self.tabs,
        )
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExplicitImportSafetyPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName(
            "oswOptionalSolverPluginManifestExplicitImportActionsPanel"
        )

        self.tabs.addTab(self.sources_table, "Sources")
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
        self.close_button.setObjectName(
            "oswOptionalSolverPluginManifestExplicitImportCloseButton"
        )
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.set_view_model(self._view_model)
        self.set_theme_tokens(self._tokens)

    def choose_manifest_json(self) -> None:
        """Choose and preview one local JSON manifest after an explicit click."""

        selection = self._file_chooser()
        selected = _single_selected_path(selection)
        if selected is None:
            return
        path_or_error = self._validated_json_path(selected)
        if isinstance(path_or_error, OptionalSolverPluginManifestExplicitImportDiagnosticViewModel):
            self.set_view_model(
                build_optional_solver_plugin_manifest_explicit_import_error_viewmodel(
                    (path_or_error,)
                )
            )
            return
        try:
            report = self._loader(str(path_or_error))
        except Exception as exc:  # noqa: BLE001 - shown as a preview diagnostic.
            self.set_view_model(
                build_optional_solver_plugin_manifest_explicit_import_error_viewmodel(
                    (
                        _import_diagnostic(
                            OSPMG_IMPORT_UNREADABLE,
                            "error",
                            f"Selected manifest file could not be loaded: {exc}",
                            str(path_or_error),
                            "Check the explicit JSON file path.",
                        ),
                    )
                )
            )
            return
        self.set_view_model(
            build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
                report,
                selected_source_count=1,
            )
        )

    def set_view_model(
        self,
        view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
    ) -> None:
        """Render supplied explicit-import state without activating manifests."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_sources_table()
        self._populate_accepted_table()
        self._populate_rejected_table()
        self._populate_conflict_table()
        self._populate_diagnostics_table()
        self.trust_panel.setPlainText(_trust_text(view_model))
        self.safety_panel.setPlainText(_safety_text(view_model))
        self._populate_action_state()

    def summary_text(self) -> str:
        return self.summary_label.text()

    def source_rows_text(self) -> str:
        return _table_text(self.sources_table, empty_text="No sources selected.")

    def accepted_rows_text(self) -> str:
        return _table_text(self.accepted_table, empty_text="No accepted manifests.")

    def rejected_rows_text(self) -> str:
        return _table_text(self.rejected_table, empty_text="No rejected manifests.")

    def conflict_rows_text(self) -> str:
        return _table_text(self.conflict_table, empty_text="No manifest conflicts.")

    def diagnostics_text(self) -> str:
        return _table_text(self.diagnostics_table, empty_text="No diagnostics.")

    def import_diagnostics_text(self) -> str:
        return "\n".join(
            f"{item.severity} | {item.code} | {item.message}"
            for item in self._view_model.import_diagnostics
        )

    def trust_text(self) -> str:
        return self.trust_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def available_action_names(self) -> tuple[str, ...]:
        return tuple(
            action.action.value
            for action in self._view_model.actions
            if _effective_action_available(action)
        )

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOptionalSolverPluginManifestExplicitImportPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverPluginManifestExplicitImportSummary {"
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

    def _choose_json_file_dialog(self) -> object:
        filename, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Choose plugin manifest JSON",
            "",
            "JSON files (*.json)",
        )
        return filename

    def _validated_json_path(
        self,
        selected: object,
    ) -> Path | OptionalSolverPluginManifestExplicitImportDiagnosticViewModel:
        text = str(selected).strip()
        display, _redacted = _redacted_reference(text)
        if not text:
            return _import_diagnostic(
                OSPMG_IMPORT_FILE_MISSING,
                "error",
                "No plugin manifest JSON file was selected.",
                display,
                "Choose one explicit local .json file.",
            )
        if "://" in text:
            return _import_diagnostic(
                OSPMG_IMPORT_UNREADABLE,
                "error",
                "Network manifest URLs are not supported.",
                display,
                "Choose one explicit local JSON file.",
            )
        path = Path(text)
        if path.suffix.lower() != ".json":
            return _import_diagnostic(
                OSPMG_IMPORT_UNSUPPORTED_EXTENSION,
                "error",
                "Optional solver plugin manifests must be .json files.",
                display,
                "Use a .json file.",
            )
        try:
            if not path.exists():
                return _import_diagnostic(
                    OSPMG_IMPORT_FILE_MISSING,
                    "error",
                    "Selected plugin manifest file does not exist.",
                    display,
                    "Check the explicit JSON file path.",
                )
            if not path.is_file():
                return _import_diagnostic(
                    OSPMG_IMPORT_UNREADABLE,
                    "error",
                    "Directory selection is out of scope for plugin manifest preview.",
                    display,
                    "Choose one explicit local JSON file.",
                )
            size = path.stat().st_size
        except OSError as exc:
            return _import_diagnostic(
                OSPMG_IMPORT_UNREADABLE,
                "error",
                f"Selected plugin manifest file is unreadable: {exc}",
                display,
                "Check file permissions and choose an explicit local JSON file.",
            )
        if size > self._max_file_size_bytes:
            return _import_diagnostic(
                OSPMG_IMPORT_FILE_TOO_LARGE,
                "error",
                (
                    "Selected plugin manifest file is too large for preview "
                    f"({size} bytes; limit {self._max_file_size_bytes} bytes)."
                ),
                display,
                "Choose a smaller declarative plugin manifest JSON file.",
            )
        return path

    def _build_actions_panel(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.actions_panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.action_state_panel = _readonly_plain_text(
            "oswOptionalSolverPluginManifestExplicitImportActionStatePanel",
            self.actions_panel,
        )
        layout.addWidget(self.action_state_panel, 1)
        button_grid = QtWidgets.QGridLayout()
        for index, action_state in enumerate(self._view_model.actions):
            action_name = action_state.action.value
            if (
                action_state.action
                == OptionalSolverPluginManifestExplicitImportAction.CHOOSE_EXPLICIT_JSON_FILES
            ):
                button = self.choose_button
            else:
                button = QtWidgets.QPushButton(action_state.label, self.actions_panel)
                button.setObjectName(_action_button_object_name(action_state))
                button.setEnabled(False)
            self._action_buttons[action_name] = button
            button_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(button_grid)

    def _populate_sources_table(self) -> None:
        rows = [
            (
                str(row.source_index + 1),
                row.source_type,
                row.source_label or "not supplied",
                row.source_reference_display or "not supplied",
                row.trust_label,
                row.status,
                row.diagnostics_summary,
                row.warning_text,
            )
            for row in self._view_model.source_rows
        ]
        _populate_table(self.sources_table, rows)

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
                "loader",
                row.severity,
                row.code,
                row.message,
                row.source_ref or "not supplied",
                row.stack_id or "not supplied",
                row.suggested_fix or "not supplied",
            )
            for row in self._view_model.diagnostic_rows
        ]
        rows.extend(
            (
                "import",
                item.severity,
                item.code,
                item.message,
                item.source_reference_display or "not supplied",
                "not supplied",
                item.suggested_fix or "not supplied",
            )
            for item in self._view_model.import_diagnostics
        )
        _populate_table(self.diagnostics_table, rows)

    def _populate_action_state(self) -> None:
        self._disabled_action_reasons = {}
        lines: list[str] = []
        for action_state in self._view_model.actions:
            action_name = action_state.action.value
            state_text = _action_state_status(action_state)
            reason = _effective_action_reason(action_state)
            lines.append(f"{action_name}: {state_text}")
            lines.append(f"  {reason}")
            if not _effective_action_enabled(action_state):
                self._disabled_action_reasons[action_name] = reason
            button = self._action_buttons.get(action_name)
            if button is not None:
                button.setEnabled(_effective_action_enabled(action_state))
                button.setToolTip(reason)
        self.action_state_panel.setPlainText("\n".join(lines))


def _single_selected_path(selection: object) -> object | None:
    if selection is None:
        return None
    if isinstance(selection, str):
        return selection if selection.strip() else None
    if isinstance(selection, Path):
        return selection
    if isinstance(selection, Sequence) and not isinstance(
        selection, (bytes, bytearray)
    ):
        values = [item for item in selection if str(item).strip()]
        if not values:
            return None
        if len(values) > 1:
            return ""
        return values[0]
    return selection


def _import_diagnostic(
    code: str,
    severity: str,
    message: str,
    source_reference: str,
    suggested_fix: str,
) -> OptionalSolverPluginManifestExplicitImportDiagnosticViewModel:
    display, redacted = _redacted_reference(source_reference)
    return OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
        code=code,
        severity=severity,
        message=message,
        source_reference_display=display,
        redacted=redacted,
        suggested_fix=suggested_fix,
    )


def _redacted_reference(reference: object) -> tuple[str, bool]:
    text = str(reference or "")
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        base = normalized.rsplit("/", 1)[-1] or normalized
        if base and base != text:
            return base, True
    return text, False


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


def _summary_text(
    view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest explicit import preview: "
        f"state={summary.state}; "
        f"selected_sources={summary.selected_sources}; "
        f"accepted={summary.accepted_count}; "
        f"rejected={summary.rejected_count}; "
        f"conflicts={summary.conflict_count}; "
        f"diagnostics={summary.diagnostic_count}; "
        f"untrusted_sources={summary.untrusted_source_count}. "
        f"{summary.status_text}"
    )


def _trust_text(
    view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> str:
    lines = [
        "Trust/source labels.",
        "User-selected manifests are untrusted by default.",
        "Third-party/plugin manifests are not trusted by default.",
        "Trust label is not certification.",
    ]
    if not view_model.trust_badges:
        lines.append("No trust/source labels.")
    for badge in view_model.trust_badges:
        lines.append(
            f"{badge.label} | source_type={badge.source_type} | "
            f"trust_label={badge.trust_label} | source_ref={badge.source_ref} | "
            f"{badge.warning_text}"
        )
    for row in view_model.source_rows:
        lines.append(
            f"selected_source={row.source_label or row.source_type} | "
            f"source_type={row.source_type} | trust_label={row.trust_label} | "
            f"source_ref={row.source_reference_display} | {row.warning_text}"
        )
    return "\n".join(lines)


def _safety_text(
    view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> str:
    lines = [
        "Optional solver plugin manifest explicit import safety boundary.",
        "User-initiated local JSON selection only.",
        "Preview is not activation.",
        "Preview is not validation.",
        "Preview is not installation.",
        "Preview is not solver execution.",
        "Trust label is not certification.",
        "User-selected manifests are untrusted by default.",
        "Third-party/plugin manifests are not trusted by default.",
        "External solvers are not bundled.",
        "No plugin activation.",
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


def _source_text(source_type: str, source_ref: str) -> str:
    return f"{source_type}: {source_ref or 'not supplied'}"


def _effective_action_available(
    action_state: OptionalSolverPluginManifestExplicitImportActionState,
) -> bool:
    if (
        action_state.action
        == OptionalSolverPluginManifestExplicitImportAction.CHOOSE_EXPLICIT_JSON_FILES
    ):
        return True
    if action_state.action in {
        OptionalSolverPluginManifestExplicitImportAction.PREVIEW_SELECTED_MANIFEST_JSON,
        OptionalSolverPluginManifestExplicitImportAction.EXPORT_REDACTED_SUMMARY,
    }:
        return action_state.available
    return False


def _effective_action_enabled(
    action_state: OptionalSolverPluginManifestExplicitImportActionState,
) -> bool:
    return (
        action_state.action
        == OptionalSolverPluginManifestExplicitImportAction.CHOOSE_EXPLICIT_JSON_FILES
    )


def _effective_action_reason(
    action_state: OptionalSolverPluginManifestExplicitImportActionState,
) -> str:
    if (
        action_state.action
        == OptionalSolverPluginManifestExplicitImportAction.CHOOSE_EXPLICIT_JSON_FILES
    ):
        return (
            "Opens an injected chooser or QFileDialog only after explicit user action; "
            "JSON files (*.json) only."
        )
    if (
        action_state.action
        == OptionalSolverPluginManifestExplicitImportAction.PREVIEW_SELECTED_MANIFEST_JSON
    ):
        return "Preview is rendered automatically from the supplied loader report."
    if (
        action_state.action
        == OptionalSolverPluginManifestExplicitImportAction.EXPORT_REDACTED_SUMMARY
    ):
        return "No GUI export, clipboard, shell, or browser action is implemented."
    return action_state.reason


def _action_state_status(
    action_state: OptionalSolverPluginManifestExplicitImportActionState,
) -> str:
    availability = "available" if _effective_action_available(action_state) else "unavailable"
    enabled = "enabled" if _effective_action_enabled(action_state) else "disabled"
    future = "current" if _effective_action_enabled(action_state) else "future"
    return f"{availability}; {enabled}; {future}; preview-only"


def _action_button_object_name(
    action_state: OptionalSolverPluginManifestExplicitImportActionState,
) -> str:
    return "oswOptionalSolverPluginManifestExplicitImportAction" + "".join(
        part.title() for part in action_state.action.value.split("_")
    )


__all__ = [
    "DEFAULT_PLUGIN_MANIFEST_JSON_MAX_BYTES",
    "OptionalSolverPluginManifestExplicitImportPanel",
]
