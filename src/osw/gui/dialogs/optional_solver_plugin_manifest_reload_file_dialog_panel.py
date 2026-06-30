"""Explicit file-dialog wrapper for optional solver manifest reload preview.

The panel is a GUI shell around the reload file reader and review panel. It
does not choose a path during construction, does not keep recent paths, and
does not mutate project state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from osw.experimental.optional_solvers.plugin_manifest_reload_file_reader import (
    OptionalSolverPluginManifestReloadFileReader,
    OptionalSolverPluginManifestReloadFileReaderDiagnostic,
    OptionalSolverPluginManifestReloadFileReadRequest,
    OptionalSolverPluginManifestReloadFileReadResult,
)
from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
    OptionalSolverPluginManifestReloadViewModel,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

from .optional_solver_plugin_manifest_reload_panel import (
    OptionalSolverPluginManifestReloadPanel,
)

try:  # pragma: no cover - exercised when PySide6 is installed.
    from PySide6 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - exercised in minimal environments.
    QtCore = None
    QtWidgets = None


FilePicker = Callable[[], str | Path | Sequence[str | Path] | None]
RequestFactory = Callable[
    [str | Path | None], OptionalSolverPluginManifestReloadFileReadRequest
]
ViewModelFactory = Callable[
    [Mapping[str, object], str | None], OptionalSolverPluginManifestReloadViewModel
]


_DISABLED_RELOAD_ACTIONS: tuple[tuple[str, str], ...] = (
    ("accept_reload", "Runtime reload acceptance is outside this preview panel."),
    ("validate_plugins", "Validation execution is outside this preview panel."),
    ("run_solver", "Solver execution is outside this preview panel."),
    ("activate_candidate", "Automatic activation is outside this preview panel."),
    ("restore_trust", "Trust restoration is outside this preview panel."),
    ("create_export_file", "Export file creation is outside this preview panel."),
    ("create_report_file", "Report file creation is outside this preview panel."),
    ("create_reloadable_bundle", "Reloadable bundle creation is outside this preview panel."),
    ("attach_report", "Report attachment is outside this preview panel."),
    ("copy_to_clipboard", "Clipboard behavior is outside this preview panel."),
    ("open_output_folder", "Output-folder actions are outside this preview panel."),
    ("scan_directories", "Directory scanning is outside this preview panel."),
    ("fetch_network_manifest", "Network manifest fetching is outside this preview panel."),
    ("import_plugin_package", "Plugin package import is outside this preview panel."),
)


if QtWidgets is None:  # pragma: no cover - simple fallback type.
    _BaseDialog = object
else:
    _BaseDialog = QtWidgets.QDialog


class OptionalSolverPluginManifestReloadFileDialogPanel(_BaseDialog):
    """File-dialog wrapper for read-only reload preview."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        file_picker: FilePicker | None = None,
        reader: object | None = None,
        request_factory: RequestFactory | None = None,
        view_model_factory: ViewModelFactory | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtWidgets is None or QtCore is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self._tokens = theme_tokens or DARK_TOKENS
        self._file_picker = file_picker or self._choose_reload_state_file
        self._reader = reader or OptionalSolverPluginManifestReloadFileReader()
        self._request_factory = request_factory or self._build_read_request
        self._view_model_factory = (
            view_model_factory or self._build_view_model_preview
        )
        self._reader_result: OptionalSolverPluginManifestReloadFileReadResult | None = (
            None
        )
        self._view_model_preview: (
            OptionalSolverPluginManifestReloadViewModel | None
        ) = None
        self._last_selected_display = "<none>"
        self._file_dialog_invocation_count = 0

        self.setWindowTitle("Optional Solver Plugin Manifest Reload")
        self.setObjectName("oswOptionalSolverPluginManifestReloadFileDialogPanel")
        self.resize(1120, 820)
        self._build_layout()
        self._render_idle_state()

    def open_file_dialog(self) -> bool:
        """Ask the picker for one explicit path, then preview it if selected."""

        self._file_dialog_invocation_count += 1
        try:
            selected = self._normalise_picker_value(self._file_picker())
        except Exception:  # pragma: no cover - defensive GUI boundary.
            self._render_internal_error("OSPMG_RELOAD_GUI_FILE_PICKER_ERROR")
            return False
        if selected is None:
            self._render_cancelled_state()
            return False
        return self.load_selected_file(selected)

    def load_selected_file(self, path: str | Path | None) -> bool:
        """Read one explicitly supplied path and update diagnostics/preview."""

        try:
            request = self._request_factory(path)
            result = self._reader.read(request)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - defensive GUI boundary.
            self._render_internal_error("OSPMG_RELOAD_GUI_READER_ERROR")
            return False

        self._reader_result = result
        self._last_selected_display = result.redacted_target_display
        self._render_reader_result(result)

        if not result.ready_for_viewmodel or result.safe_mapping is None:
            return False

        try:
            view_model = self._view_model_factory(
                result.safe_mapping,
                result.redacted_target_display,
            )
        except Exception:  # pragma: no cover - defensive GUI boundary.
            self._render_internal_error("OSPMG_RELOAD_GUI_VIEWMODEL_ERROR")
            return False

        self._view_model_preview = view_model
        self._reload_panel.set_view_model(view_model)
        self._status_label.setText(
            "Ready for review: reader diagnostics completed before preview."
        )
        self._selected_file_label.setText(
            f"Selected file: {self._last_selected_display}"
        )
        return True

    def clear_preview(self) -> None:
        """Clear the displayed preview without touching any selected file."""

        self._reader_result = None
        self._view_model_preview = None
        self._last_selected_display = "<none>"
        self._reload_panel.set_view_model(
            OptionalSolverPluginManifestReloadViewModel.empty()
        )
        self._render_idle_state()

    def has_view_model_preview(self) -> bool:
        return self._view_model_preview is not None

    def file_dialog_invocation_count(self) -> int:
        return self._file_dialog_invocation_count

    def selected_file_text(self) -> str:
        return self._selected_file_label.text()

    def reader_status_text(self) -> str:
        return self._status_label.text()

    def reader_diagnostics_text(self) -> str:
        return self._table_text(self._reader_diagnostics_table)

    def action_state_text(self) -> str:
        return self._table_text(self._action_state_table)

    def safety_text(self) -> str:
        return self._safety_text.toPlainText()

    def preview_summary_text(self) -> str:
        return self._reload_panel.summary_text()

    def preview_diagnostics_text(self) -> str:
        return self._reload_panel.diagnostics_text()

    def summary_text(self) -> str:
        return "\n".join(
            line
            for line in (
                self.reader_status_text(),
                self.selected_file_text(),
                self.reader_diagnostics_text(),
                self.action_state_text(),
                self.safety_text(),
                self.preview_summary_text(),
            )
            if line
        )

    def last_reader_result(
        self,
    ) -> OptionalSolverPluginManifestReloadFileReadResult | None:
        return self._reader_result

    def _build_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._status_label = QtWidgets.QLabel(self)
        self._status_label.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogStatus"
        )
        layout.addWidget(self._status_label)

        self._selected_file_label = QtWidgets.QLabel(self)
        self._selected_file_label.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogSelectedFile"
        )
        layout.addWidget(self._selected_file_label)

        button_row = QtWidgets.QHBoxLayout()
        self._open_button = QtWidgets.QPushButton("Open reload state...", self)
        self._open_button.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogOpenButton"
        )
        self._open_button.clicked.connect(self.open_file_dialog)
        button_row.addWidget(self._open_button)

        self._clear_button = QtWidgets.QPushButton("Clear preview", self)
        self._clear_button.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogClearButton"
        )
        self._clear_button.clicked.connect(self.clear_preview)
        button_row.addWidget(self._clear_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._reader_diagnostics_table = QtWidgets.QTableWidget(0, 5, self)
        self._reader_diagnostics_table.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogDiagnosticsTable"
        )
        self._reader_diagnostics_table.setHorizontalHeaderLabels(
            ["Severity", "Code", "Message", "Blocking", "Suggested fix"]
        )
        self._reader_diagnostics_table.horizontalHeader().setStretchLastSection(
            True
        )
        self._reader_diagnostics_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self._reader_diagnostics_table, 2)

        self._action_state_table = QtWidgets.QTableWidget(0, 2, self)
        self._action_state_table.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogActionStateTable"
        )
        self._action_state_table.setHorizontalHeaderLabels(["Action", "State"])
        self._action_state_table.horizontalHeader().setStretchLastSection(True)
        self._action_state_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self._action_state_table, 1)

        self._safety_text = QtWidgets.QPlainTextEdit(self)
        self._safety_text.setObjectName(
            "oswOptionalSolverPluginManifestReloadFileDialogSafetyText"
        )
        self._safety_text.setReadOnly(True)
        self._safety_text.setPlainText(
            "\n".join(
                (
                    "Preview only.",
                    "No default reload path.",
                    "No background reload.",
                    "No directory scan.",
                    "No network fetch.",
                    "No plugin package import.",
                    "No CLI bridge.",
                    "No project mutation.",
                    "No validation or solver execution.",
                )
            )
        )
        layout.addWidget(self._safety_text, 1)

        self._reload_panel = OptionalSolverPluginManifestReloadPanel(
            parent=self,
            view_model=OptionalSolverPluginManifestReloadViewModel.empty(),
            theme_tokens=self._tokens,
        )
        self._reload_panel.setWindowFlag(QtCore.Qt.WindowType.Widget, True)
        layout.addWidget(self._reload_panel, 5)

    def _choose_reload_state_file(self) -> str | None:
        selected, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open optional solver reload state",
            "",
            "JSON files (*.json);;All files (*)",
            options=QtWidgets.QFileDialog.Option.DontResolveSymlinks,
        )
        return selected or None

    def _build_read_request(
        self, path: str | Path | None
    ) -> OptionalSolverPluginManifestReloadFileReadRequest:
        return OptionalSolverPluginManifestReloadFileReadRequest(
            target_path=path,
            caller_context="gui_file_dialog",
        )

    def _build_view_model_preview(
        self, mapping: Mapping[str, object], source_label: str | None
    ) -> OptionalSolverPluginManifestReloadViewModel:
        return OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(
            mapping,
            source_label=source_label,
        )

    def _render_idle_state(self) -> None:
        self._status_label.setText("No reload state file selected.")
        self._selected_file_label.setText("Selected file: <none>")
        self._set_reader_diagnostics_rows(
            [
                (
                    "info",
                    "OSPMG_RELOAD_GUI_NO_FILE_SELECTED",
                    "Use the explicit file action to preview one state file.",
                    "no",
                    "Select a bounded state-writer UX state file.",
                )
            ]
        )
        self._set_action_state_rows(_DISABLED_RELOAD_ACTIONS)

    def _render_cancelled_state(self) -> None:
        self._status_label.setText(
            "File selection cancelled; previous preview was preserved."
        )
        self._selected_file_label.setText(
            f"Selected file: {self._last_selected_display}"
        )
        self._set_reader_diagnostics_rows(
            [
                (
                    "info",
                    "OSPMG_RELOAD_GUI_SELECTION_CANCELLED",
                    "No file was selected and no file was read.",
                    "no",
                    "Select a file to update the preview.",
                )
            ]
        )
        self._set_action_state_rows(_DISABLED_RELOAD_ACTIONS)

    def _render_reader_result(
        self, result: OptionalSolverPluginManifestReloadFileReadResult
    ) -> None:
        self._status_label.setText(
            f"{result.status.value}: {result.summary}"
        )
        self._selected_file_label.setText(
            f"Selected file: {result.redacted_target_display}"
        )
        self._set_reader_diagnostics_rows(
            [
                (
                    diagnostic.severity,
                    diagnostic.code,
                    diagnostic.message,
                    "yes" if diagnostic.blocker else "no",
                    diagnostic.suggested_fix,
                )
                for diagnostic in result.diagnostics
            ]
        )
        action_rows = tuple(
            (state.action, state.reason)
            for state in result.action_states
            if not state.enabled
        )
        self._set_action_state_rows(action_rows or _DISABLED_RELOAD_ACTIONS)

    def _render_internal_error(self, code: str) -> None:
        self._status_label.setText(
            "Internal GUI diagnostic: reload preview did not proceed."
        )
        self._selected_file_label.setText(
            f"Selected file: {self._last_selected_display}"
        )
        diagnostic = OptionalSolverPluginManifestReloadFileReaderDiagnostic(
            severity="error",
            code=code,
            message="Internal GUI diagnostic; no reload preview was accepted.",
            blocker=True,
            suggested_fix="Review the injected GUI dependency and retry.",
        )
        self._set_reader_diagnostics_rows(
            [
                (
                    diagnostic.severity,
                    diagnostic.code,
                    diagnostic.message,
                    "yes",
                    diagnostic.suggested_fix,
                )
            ]
        )
        self._set_action_state_rows(_DISABLED_RELOAD_ACTIONS)

    def _set_reader_diagnostics_rows(
        self, rows: Sequence[tuple[str, str, str, str, str]]
    ) -> None:
        self._reader_diagnostics_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self._reader_diagnostics_table.setItem(
                    row_index,
                    column_index,
                    self._read_only_item(value),
                )
        self._reader_diagnostics_table.resizeColumnsToContents()

    def _set_action_state_rows(
        self, rows: Sequence[tuple[str, str]]
    ) -> None:
        self._action_state_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self._action_state_table.setItem(
                    row_index,
                    column_index,
                    self._read_only_item(value),
                )
        self._action_state_table.resizeColumnsToContents()

    def _read_only_item(self, value: object) -> object:
        item = QtWidgets.QTableWidgetItem(str(value))
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        return item

    def _normalise_picker_value(
        self, selected: str | Path | Sequence[str | Path] | None
    ) -> str | Path | None:
        if selected is None or selected == "":
            return None
        if isinstance(selected, (str, Path)):
            return selected
        if not selected:
            return None
        first = selected[0]
        return first if first else None

    def _table_text(self, table: object) -> str:
        lines: list[str] = []
        for row_index in range(table.rowCount()):
            values: list[str] = []
            for column_index in range(table.columnCount()):
                item = table.item(row_index, column_index)
                if item is not None:
                    values.append(item.text())
            if values:
                lines.append(" | ".join(values))
        return "\n".join(lines)


__all__ = ["OptionalSolverPluginManifestReloadFileDialogPanel"]
