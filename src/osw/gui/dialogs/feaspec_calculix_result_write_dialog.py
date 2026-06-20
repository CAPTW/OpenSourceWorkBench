"""Review-first FEASpec CalculiX ResultDataset write dialog."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from os import fspath
from pathlib import Path
from typing import Any

from osw.experimental.feaspec.calculix_result_dataset_writer import (
    FEASpecCalculiXResultDatasetWriteResult,
    explain_calculix_result_dataset_write_result,
    write_calculix_result_dataset,
)
from osw.experimental.feaspec.calculix_result_write_viewmodel import (
    FEASpecCalculiXResultWriteAction,
    FEASpecCalculiXResultWriteActionAvailability,
    FEASpecCalculiXResultWriteActionState,
    FEASpecCalculiXResultWritePanel,
    FEASpecCalculiXResultWriteRow,
    FEASpecCalculiXResultWriteViewModel,
    plan_calculix_result_write_save_path,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:  # pragma: no cover - exercised in environments with the optional GUI extra.
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback.
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class FEASpecCalculiXResultWriteDialog(_BaseDialog):
    """PySide6 surface for review-first ResultDataset writes."""

    def __init__(
        self,
        viewmodel: FEASpecCalculiXResultWriteViewModel,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
        output_directory_chooser: Callable[[str, str], object] | None = None,
        result_dataset_writer: Callable[..., object] | None = None,
        write_confirmation: Callable[[str], bool] | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message("result write dialog"))
        if not isinstance(viewmodel, FEASpecCalculiXResultWriteViewModel):
            msg = "viewmodel must be a FEASpecCalculiXResultWriteViewModel"
            raise TypeError(msg)
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._tokens = theme_tokens or DARK_TOKENS
        self._write_invocations = 0
        self._file_dialog_invocations = 0
        self._output_directory_chooser = output_directory_chooser
        self._result_dataset_writer = (
            result_dataset_writer or write_calculix_result_dataset
        )
        self._write_confirmation = write_confirmation
        self._selected_output_dir = viewmodel.output_dir
        self._selected_save_plan = viewmodel.save_plan
        self._write_completed = False
        self._writer_result_object: object | None = None
        self._writer_result_summary = self._mapping(viewmodel.writer_result_summary)
        self._last_writer_result_text = ""
        self._last_confirmation_text = ""
        self._action_buttons: dict[
            FEASpecCalculiXResultWriteAction,
            QtWidgets.QPushButton,
        ] = {}
        self._action_reason_texts: list[str] = []

        self.setObjectName("oswFeaspecCalculixResultWriteDialog")
        self.setWindowTitle("FEASpec CalculiX ResultDataset Write")
        self.setMinimumSize(880, 640)
        self._apply_theme()
        self._build_layout()

    def panel_titles(self) -> tuple[str, ...]:
        """Return current tab titles in display order."""

        return tuple(
            self.tabs.tabText(index) for index in range(self.tabs.count())
        )

    def action_labels(self) -> tuple[str, ...]:
        """Return visible action button labels."""

        return tuple(button.text() for button in self._action_buttons.values())

    def disabled_reason_texts(self) -> tuple[str, ...]:
        """Return visible disabled-reason text."""

        return tuple(text for text in self._action_reason_texts if text)

    def safety_text(self) -> str:
        """Return the safety and limitations panel text."""

        return self.safety_panel.toPlainText()

    def diagnostics_text(self) -> str:
        """Return the diagnostics panel text."""

        return self.diagnostics_panel.toPlainText()

    def planned_files_text(self) -> str:
        """Return the write-plan panel text."""

        return self.write_plan_panel.toPlainText()

    def save_plan_text(self) -> str:
        """Return the current save-plan display text."""

        return self.write_plan_panel.toPlainText()

    def output_directory_text(self) -> str:
        """Return the selected output-directory field text."""

        return self.output_directory_field.text()

    def selected_output_directory(self) -> str:
        """Return the currently selected output directory."""

        return self._selected_output_dir

    def choose_output_directory_enabled(self) -> bool:
        """Return whether output-directory selection is available."""

        button = self._action_buttons.get(
            FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY
        )
        return bool(button and button.isEnabled())

    def file_dialog_invocation_count(self) -> int:
        """Return how often the directory chooser was invoked."""

        return self._file_dialog_invocations

    def result_summary_text(self) -> str:
        """Return the result-summary panel text."""

        return self.result_panel.toPlainText()

    def acknowledgement_text(self) -> str:
        """Return rendered acknowledgement text."""

        return "\n".join(box.text() for box in self._acknowledgement_boxes)

    def has_write_enabled(self) -> bool:
        """Return true only if a write button is enabled."""

        return self.write_button_enabled()

    def write_button_enabled(self) -> bool:
        """Return whether the guarded write button is currently enabled."""

        button = self._action_buttons.get(
            FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
        )
        return bool(button and button.isEnabled())

    def has_file_dialog_controls(self) -> bool:
        """Return whether active directory-selection controls exist."""

        return self.choose_output_directory_enabled()

    def write_invocation_count(self) -> int:
        """Return the number of write invocations made by this dialog."""

        return self._write_invocations

    def trigger_write_for_test(self, *, confirm: bool = True) -> bool:
        """Run the guarded write path with an injected confirmation result."""

        original = self._write_confirmation
        self._write_confirmation = lambda _text: confirm
        try:
            return self._attempt_write()
        finally:
            self._write_confirmation = original

    def last_writer_result_text(self) -> str:
        """Return the latest writer-result panel text."""

        return self._last_writer_result_text

    def written_files_text(self) -> str:
        """Return a compact list of files reported by the writer result."""

        written_files = self._writer_result_summary.get("written_files", ())
        if not isinstance(written_files, Sequence) or isinstance(written_files, str):
            return ""
        lines: list[str] = []
        for item in written_files:
            if not isinstance(item, Mapping):
                continue
            relative_path = item.get("relative_path") or item.get("path") or "<unknown>"
            size = item.get("size_bytes") or item.get("size") or "<unknown>"
            sha256 = item.get("sha256") or "<missing>"
            lines.append(f"{relative_path} | {size} bytes | {sha256}")
        return "\n".join(lines)

    def write_confirmation_text(self) -> str:
        """Return the latest confirmation text shown or injected in tests."""

        return self._last_confirmation_text

    def action_button(
        self,
        action: FEASpecCalculiXResultWriteAction,
    ) -> object | None:
        """Return a rendered action button for focused GUI tests."""

        return self._action_buttons.get(action)

    def choose_output_directory(self) -> bool:
        """Select an output directory and refresh display-only save-plan state."""

        self._file_dialog_invocations += 1
        selected = self._select_output_directory()
        selected_text = _selected_directory_text(selected)
        if not selected_text:
            return False
        return self.select_output_directory_for_test(selected_text)

    def select_output_directory_for_test(self, path: object) -> bool:
        """Apply a selected output directory without opening a file dialog."""

        selected_text = _selected_directory_text(path)
        if not selected_text:
            return False
        self._selected_output_dir = _display_directory_text(selected_text)
        self._selected_save_plan = plan_calculix_result_write_save_path(
            self._viewmodel,
            self._selected_output_dir,
        )
        self._refresh_output_directory_display()
        return True

    def _build_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        self.header_label = QtWidgets.QLabel(
            "FEASpec CalculiX ResultDataset write - review first"
        )
        self.header_label.setObjectName("oswFeaspecCalculixResultWriteHeader")
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setObjectName("oswFeaspecCalculixResultWriteTabs")
        layout.addWidget(self.tabs, stretch=1)

        self.source_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteSourcePanel",
            self._source_text(),
        )
        self.tabs.addTab(self.source_panel, "Source")

        self.artifact_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteArtifactsPanel",
            self._rows_text(FEASpecCalculiXResultWritePanel.ARTIFACT_SUMMARY)
            + "\n\nImport summary:\n"
            + self._json_text(self._viewmodel.import_summary),
        )
        self.tabs.addTab(self.artifact_panel, "Artifacts")

        self.diagnostics_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteDiagnosticsPanel",
            self._diagnostics_text(),
        )
        self.tabs.addTab(self.diagnostics_panel, "Diagnostics")

        self.draft_mapping_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteDraftMappingPanel",
            self._rows_text(FEASpecCalculiXResultWritePanel.DRAFT_MAPPING)
            + "\n\nDraft mapping summary:\n"
            + self._json_text(self._viewmodel.draft_mapping_summary),
        )
        self.tabs.addTab(self.draft_mapping_panel, "Draft Mapping")

        self.write_plan_panel = self._read_only_text(
            "oswFeaspecCalculixResultWritePlanPanel",
            self._write_plan_text(),
        )
        self.tabs.addTab(self.write_plan_panel, "Write Plan")

        self.schema_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteSchemaPanel",
            self._rows_text(FEASpecCalculiXResultWritePanel.SCHEMA_MANIFEST)
            + "\n\nSchema summary:\n"
            + self._json_text(self._viewmodel.schema_summary),
        )
        self.tabs.addTab(self.schema_panel, "Schema / Manifest")

        self.safety_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteSafetyPanel",
            self._safety_text(),
        )
        self.tabs.addTab(self.safety_panel, "Safety / Limitations")

        self.actions_panel = QtWidgets.QWidget()
        self.actions_panel.setObjectName("oswFeaspecCalculixResultWriteActionsPanel")
        self._populate_actions_panel()
        self.tabs.addTab(self.actions_panel, "Actions")

        self._last_writer_result_text = self._result_text()
        self.result_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteResultPanel",
            self._last_writer_result_text,
        )
        self.tabs.addTab(self.result_panel, "Result")

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.setObjectName("oswFeaspecCalculixResultWriteClose")
        self.close_button.clicked.connect(self.reject)
        footer.addWidget(self.close_button)
        layout.addLayout(footer)

    def _populate_actions_panel(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.actions_panel)
        self.action_summary = QtWidgets.QListWidget()
        self.action_summary.setObjectName("oswFeaspecCalculixResultWriteActionSummary")
        layout.addWidget(self.action_summary)

        output_group = QtWidgets.QGroupBox("Output directory")
        output_group.setObjectName("oswFeaspecCalculixResultWriteOutputDirectoryGroup")
        output_layout = QtWidgets.QVBoxLayout(output_group)
        output_row = QtWidgets.QHBoxLayout()
        self.output_directory_field = QtWidgets.QLineEdit()
        self.output_directory_field.setObjectName(
            "oswFeaspecCalculixResultWriteOutputDirectory"
        )
        self.output_directory_field.setReadOnly(True)
        output_row.addWidget(self.output_directory_field, stretch=1)
        output_layout.addLayout(output_row)
        self.output_directory_status = QtWidgets.QPlainTextEdit()
        self.output_directory_status.setObjectName(
            "oswFeaspecCalculixResultWriteOutputDirectoryStatus"
        )
        self.output_directory_status.setReadOnly(True)
        self.output_directory_status.setMaximumHeight(120)
        output_layout.addWidget(self.output_directory_status)
        layout.addWidget(output_group)

        self._acknowledgement_boxes: list[object] = []
        ack_group = QtWidgets.QGroupBox("Acknowledgements")
        ack_layout = QtWidgets.QVBoxLayout(ack_group)
        for label, checked in (
            (
                "Limitations acknowledged",
                self._viewmodel.acknowledgements.limitations,
            ),
            (
                "Human review required acknowledged",
                self._viewmodel.acknowledgements.review_required,
            ),
            ("Overwrite acknowledged", self._viewmodel.acknowledgements.overwrite),
            (
                "Create directory acknowledged",
                self._viewmodel.acknowledgements.create_dir,
            ),
        ):
            box = QtWidgets.QCheckBox(label)
            box.setChecked(bool(checked))
            box.setEnabled(False)
            ack_layout.addWidget(box)
            self._acknowledgement_boxes.append(box)
        layout.addWidget(ack_group)

        buttons = QtWidgets.QGridLayout()
        for index, action in enumerate(self._viewmodel.actions):
            item_text = self._action_summary_text(action)
            self.action_summary.addItem(item_text)
            button = QtWidgets.QPushButton(action.label or action.action.value)
            button.setObjectName(
                f"oswFeaspecCalculixResultWriteAction_{action.action.value}"
            )
            reason = self._disabled_reason_text(action)
            if action.action is FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY:
                button.setEnabled(True)
                button.setToolTip(
                    "Choose an output directory; no files are written by selection."
                )
                button.clicked.connect(self.choose_output_directory)
            elif action.action is FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET:
                button.setEnabled(self._write_action_ready())
                button.setToolTip(reason or "Write after review confirmation.")
                button.clicked.connect(self._attempt_write)
            else:
                button.setEnabled(False)
                button.setToolTip(reason or "Not implemented in this gate.")
                button.clicked.connect(
                    lambda _checked=False, a=action.action: self._noop(a)
                )
            self._action_buttons[action.action] = button
            self._action_reason_texts.append(reason)
            buttons.addWidget(button, index // 2, index % 2)
        layout.addLayout(buttons)
        self._refresh_output_directory_display()
        self._refresh_action_buttons()
        layout.addStretch(1)

    def _noop(self, _action: FEASpecCalculiXResultWriteAction) -> None:
        return None

    def _select_output_directory(self) -> object:
        title = "Choose ResultDataset Output Directory"
        initial_dir = self._selected_output_dir or self._viewmodel.output_dir
        if self._output_directory_chooser is not None:
            return self._output_directory_chooser(title, initial_dir)
        return QtWidgets.QFileDialog.getExistingDirectory(
            self,
            title,
            initial_dir,
            QtWidgets.QFileDialog.Option.ShowDirsOnly
            | QtWidgets.QFileDialog.Option.DontResolveSymlinks,
        )

    def _refresh_output_directory_display(self) -> None:
        if not hasattr(self, "output_directory_field"):
            return
        self.output_directory_field.setText(self._selected_output_dir)
        status_lines = [
            f"Selected output directory: {self._selected_output_dir or '<missing>'}",
            "Selection updates the reviewed target state.",
            "Directory creation and file writes occur only after confirmation.",
            "The writer is not invoked by directory selection.",
            "",
            "Save target analysis:",
            self._json_text(self._selected_save_plan.to_dict()),
        ]
        if not self._selected_output_matches_write_plan():
            status_lines.extend(
                (
                    "",
                    "Write blocker: selected output does not match the reviewed write plan.",
                )
            )
        self.output_directory_status.setPlainText("\n".join(status_lines))
        if hasattr(self, "write_plan_panel"):
            self.write_plan_panel.setPlainText(self._write_plan_text())
        if hasattr(self, "action_summary"):
            self._refresh_action_buttons()

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            "\n".join(
                (
                    f"QDialog {{ background: {self._tokens.bg_app}; "
                    f"color: {self._tokens.text_primary}; }}",
                    f"QPlainTextEdit {{ background: {self._tokens.bg_panel}; "
                    f"color: {self._tokens.text_primary}; }}",
                    f"QTabWidget::pane {{ border: 1px solid {self._tokens.border}; }}",
                )
            )
        )

    def _read_only_text(self, object_name: str, text: str) -> object:
        widget = QtWidgets.QPlainTextEdit()
        widget.setObjectName(object_name)
        widget.setReadOnly(True)
        widget.setPlainText(text)
        return widget

    def _source_text(self) -> str:
        lines = [
            "ResultDataset write dialog state: review-first writer integration.",
            f"Result directory: {self._viewmodel.result_dir or '<missing>'}",
            f"Output directory: {self._selected_output_dir or '<missing>'}",
            f"Import status: {self._viewmodel.import_summary.get('status', '')}",
            f"Draft mapping status: {self._viewmodel.draft_mapping_summary.get('status', '')}",
            f"Write plan status: {self._viewmodel.write_plan_summary.get('status', '')}",
            f"Schema status: {self._viewmodel.schema_summary.get('status', '')}",
        ]
        return "\n".join(lines)

    def _diagnostics_text(self) -> str:
        rows = self._viewmodel.rows_for(FEASpecCalculiXResultWritePanel.DIAGNOSTICS)
        if not rows:
            return "No diagnostics reported by the view-model."
        return "\n".join(self._row_text(row) for row in rows)

    def _write_plan_text(self) -> str:
        lines = [
            self._rows_text(FEASpecCalculiXResultWritePanel.WRITE_PLAN),
            "",
            f"Selected output directory: {self._selected_output_dir or '<missing>'}",
            "",
            "Save target analysis:",
            self._json_text(self._selected_save_plan.to_dict()),
            "",
            "Planned files:",
            self._planned_files_text(),
        ]
        return "\n".join(lines)

    def _planned_files_text(self) -> str:
        payload = self._mapping(self._viewmodel.inputs.write_plan)
        planned_files = self._sequence_of_mappings(payload.get("planned_files"))
        if not planned_files:
            return "<none>"
        lines: list[str] = []
        for item in planned_files:
            relative = str(
                item.get("relative_path")
                or item.get("path")
                or item.get("name")
                or "<unnamed>"
            )
            exists = str(item.get("exists", False)).lower()
            lines.append(f"- {relative} (exists: {exists})")
        return "\n".join(lines)

    def _safety_text(self) -> str:
        lines = [
            "Experimental FEASpec CalculiX ResultDataset write dialog.",
            "Output-directory selection uses directory-only QFileDialog behavior.",
            "Writer calls require enabled gates, selected output, and confirmation.",
            "ResultDataset files are written only through the existing library writer.",
            "No artifact copying.",
            "No directory creation during selection.",
            "No solver execution.",
            "No command execution.",
            "No release, tag, asset, or issue mutation.",
            "Issue #8 live CalculiX validation remains separate and open.",
            "External solvers are optional and not bundled.",
            "No industrial certification or production accuracy claim.",
            "",
            "View-model safety messages:",
        ]
        lines.extend(
            f"- {message.code}: {message.message}"
            for message in self._viewmodel.safety_messages
        )
        limitations = self._viewmodel.rows_for(
            FEASpecCalculiXResultWritePanel.SAFETY_LIMITATIONS
        )
        if limitations:
            lines.append("")
            lines.append("Limitations:")
            lines.extend(f"- {row.value}" for row in limitations)
        return "\n".join(lines)

    def _result_text(self) -> str:
        if not self._writer_result_summary:
            return (
                "No writer result summary is present. The writer has not been "
                "invoked in this dialog session."
            )
        return self._json_text(self._writer_result_summary)

    def _rows_text(self, panel: FEASpecCalculiXResultWritePanel) -> str:
        rows = self._viewmodel.rows_for(panel)
        if not rows:
            return "<none>"
        return "\n".join(self._row_text(row) for row in rows)

    def _row_text(self, row: FEASpecCalculiXResultWriteRow) -> str:
        severity = f" [{row.severity}]" if row.severity else ""
        details = f" ({'; '.join(row.details)})" if row.details else ""
        return f"{row.label}: {row.value}{severity}{details}"

    def _action_summary_text(
        self,
        action: FEASpecCalculiXResultWriteActionAvailability,
    ) -> str:
        reason = self._disabled_reason_text(action)
        suffix = f" - {reason}" if reason else ""
        return f"{action.action.value}: {action.state.value}{suffix}"

    def _disabled_reason_text(
        self,
        action: FEASpecCalculiXResultWriteActionAvailability,
    ) -> str:
        if action.action is FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET:
            return "; ".join(self._current_write_disabled_reasons())
        reasons = [reason.value for reason in action.disabled_reasons]
        if action.action is FEASpecCalculiXResultWriteAction.OPEN_WRITTEN_OUTPUT:
            reasons.append("open_output_not_implemented")
        if not reasons and action.safety_note:
            reasons.append(action.safety_note)
        return "; ".join(reasons)

    def _refresh_action_buttons(self) -> None:
        self._action_reason_texts = []
        if hasattr(self, "action_summary"):
            self.action_summary.clear()
        for action in self._viewmodel.actions:
            button = self._action_buttons.get(action.action)
            if button is None:
                continue
            if action.action is FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY:
                enabled = action.enabled
            elif action.action is FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET:
                enabled = self._write_action_ready()
            else:
                enabled = False
            button.setEnabled(enabled)
            reason = self._disabled_reason_text(action)
            if reason:
                self._action_reason_texts.append(reason)
            button.setToolTip(reason or "Ready.")
            if hasattr(self, "action_summary"):
                self.action_summary.addItem(self._action_summary_text(action))

    def _write_action_ready(self) -> bool:
        action = self._viewmodel.action_for(
            FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
        )
        return (
            action.state is FEASpecCalculiXResultWriteActionState.ENABLED
            and not self._current_write_disabled_reasons()
        )

    def _current_write_disabled_reasons(self) -> list[str]:
        action = self._viewmodel.action_for(
            FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
        )
        reasons = [reason.value for reason in action.disabled_reasons]
        if action.state is not FEASpecCalculiXResultWriteActionState.ENABLED:
            reasons.append(action.state.value)
        if self._write_completed:
            reasons.append("write_completed")
        if not self._writer_inputs_are_callable():
            reasons.append("writer_inputs_not_callable")
        if not self._selected_output_dir:
            reasons.append("output_directory_not_selected")
        if not self._selected_save_plan.can_write_target:
            reasons.extend(
                reason.value for reason in self._selected_save_plan.disabled_reasons
            )
        if self._selected_output_dir and not self._selected_output_matches_write_plan():
            reasons.append("selected_output_mismatch")
        return _dedupe(reasons)

    def _writer_inputs_are_callable(self) -> bool:
        write_plan = self._viewmodel.inputs.write_plan
        schema_payload = self._viewmodel.inputs.schema_payload
        if write_plan is None or schema_payload is None:
            return False
        if isinstance(write_plan, Mapping) or isinstance(schema_payload, Mapping):
            return False
        return hasattr(write_plan, "target") and hasattr(schema_payload, "dataset")

    def _selected_output_matches_write_plan(self) -> bool:
        write_plan = self._viewmodel.inputs.write_plan
        target = getattr(write_plan, "target", None)
        target_dir = getattr(target, "output_dir", None)
        if target_dir is None or not self._selected_output_dir:
            return False
        try:
            return Path(self._selected_output_dir) == Path(fspath(target_dir))
        except (TypeError, ValueError):
            return False

    def _attempt_write(self, _checked: bool = False) -> bool:
        if not self._write_action_ready():
            self._refresh_action_buttons()
            return False
        confirmation_text = self._build_confirmation_text()
        self._last_confirmation_text = confirmation_text
        if not self._confirm_write(confirmation_text):
            return False

        self._write_invocations += 1
        try:
            result = self._result_dataset_writer(
                self._viewmodel.inputs.write_plan,
                self._viewmodel.inputs.schema_payload,
                overwrite=self._viewmodel.acknowledgements.overwrite,
            )
        except Exception as exc:  # pragma: no cover - defensive GUI boundary
            result = {
                "status": "failed",
                "diagnostics": [
                    {
                        "code": "FGW_WRITER_EXCEPTION",
                        "severity": "error",
                        "message": str(exc),
                    }
                ],
            }

        self._writer_result_object = result
        self._writer_result_summary = self._mapping(result)
        self._last_writer_result_text = self._format_writer_result(result)
        self.result_panel.setPlainText(self._last_writer_result_text)
        self._write_completed = self._writer_result_status() in {
            "written",
            "written-with-warnings",
            "completed",
        }
        self._refresh_action_buttons()
        return self._write_completed

    def _build_confirmation_text(self) -> str:
        write_plan = self._viewmodel.inputs.write_plan
        target = getattr(write_plan, "target", None)
        target_dir = getattr(target, "output_dir", self._selected_output_dir)
        planned_files = getattr(write_plan, "planned_files", ())
        file_names: list[str] = []
        if isinstance(planned_files, Sequence) and not isinstance(planned_files, str):
            for planned_file in planned_files:
                relative_path = getattr(planned_file, "relative_path", None)
                if relative_path is not None:
                    file_names.append(str(relative_path))
        files_text = "\n".join(f"- {name}" for name in file_names)
        if not files_text:
            files_text = "- standard ResultDataset files"
        return (
            "Write FEASpec CalculiX ResultDataset files?\n\n"
            f"Target directory: {target_dir}\n"
            f"Selected directory: {self._selected_output_dir}\n"
            f"Overwrite: {self._viewmodel.acknowledgements.overwrite}\n\n"
            "Planned files:\n"
            f"{files_text}\n\n"
            "This action writes ResultDataset review files only. It does not copy "
            "solver artifacts or execute CalculiX."
        )

    def _confirm_write(self, text: str) -> bool:
        if self._write_confirmation is not None:
            return bool(self._write_confirmation(text))
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm ResultDataset write",
            text,
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return reply == QtWidgets.QMessageBox.StandardButton.Yes

    def _format_writer_result(self, result: object) -> str:
        sections: list[str] = []
        if isinstance(result, FEASpecCalculiXResultDatasetWriteResult):
            sections.extend(explain_calculix_result_dataset_write_result(result))
        mapping = self._mapping(result)
        if mapping:
            sections.append(self._json_text(mapping))
        if not sections:
            sections.append(str(result))
        return "\n".join(sections)

    def _writer_result_status(self) -> str:
        status = self._writer_result_summary.get("status")
        return str(status) if status is not None else ""

    def _json_text(self, payload: Mapping[str, Any]) -> str:
        if not payload:
            return "{}"
        return json.dumps(dict(payload), indent=2, sort_keys=True, default=str)

    def _mapping(self, value: object) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            payload = to_dict()
            if isinstance(payload, Mapping):
                return dict(payload)
        return {}

    def _sequence_of_mappings(self, value: object) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, list | tuple):
            return ()
        records: list[Mapping[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                records.append(dict(item))
        return tuple(records)


def _selected_directory_text(selected: object) -> str:
    if selected is None:
        return ""
    if isinstance(selected, str):
        return selected.strip()
    if isinstance(selected, Path):
        return fspath(selected)
    if isinstance(selected, Sequence) and not isinstance(selected, str | bytes):
        if not selected:
            return ""
        return _selected_directory_text(selected[0])
    if hasattr(selected, "__fspath__"):
        return str(fspath(selected)).strip()
    return str(selected).strip()


def _display_directory_text(path_text: str) -> str:
    return str(Path(path_text))


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


__all__ = ["FEASpecCalculiXResultWriteDialog"]
