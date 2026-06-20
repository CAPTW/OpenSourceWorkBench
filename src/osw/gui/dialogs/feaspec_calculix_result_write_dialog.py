"""Display-only FEASpec CalculiX ResultDataset write dialog."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from osw.experimental.feaspec.calculix_result_write_viewmodel import (
    FEASpecCalculiXResultWriteAction,
    FEASpecCalculiXResultWriteActionAvailability,
    FEASpecCalculiXResultWritePanel,
    FEASpecCalculiXResultWriteRow,
    FEASpecCalculiXResultWriteViewModel,
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
    """Read-only PySide6 surface for the ResultDataset write view-model."""

    def __init__(
        self,
        viewmodel: FEASpecCalculiXResultWriteViewModel,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
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

    def result_summary_text(self) -> str:
        """Return the result-summary panel text."""

        return self.result_panel.toPlainText()

    def acknowledgement_text(self) -> str:
        """Return rendered acknowledgement text."""

        return "\n".join(box.text() for box in self._acknowledgement_boxes)

    def has_write_enabled(self) -> bool:
        """Return true only if a write button is enabled."""

        button = self._action_buttons.get(
            FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
        )
        return bool(button and button.isEnabled())

    def has_file_dialog_controls(self) -> bool:
        """Return whether active directory-selection controls exist."""

        return False

    def write_invocation_count(self) -> int:
        """Return the number of write invocations made by this dialog."""

        return self._write_invocations

    def action_button(
        self,
        action: FEASpecCalculiXResultWriteAction,
    ) -> object | None:
        """Return a rendered action button for focused GUI tests."""

        return self._action_buttons.get(action)

    def _build_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        self.header_label = QtWidgets.QLabel(
            "FEASpec CalculiX ResultDataset write - display only"
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

        self.result_panel = self._read_only_text(
            "oswFeaspecCalculixResultWriteResultPanel",
            self._result_text(),
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
            button.setEnabled(False)
            reason = self._disabled_reason_text(action)
            button.setToolTip(reason or "Display-only in this implementation gate.")
            button.clicked.connect(lambda _checked=False, a=action.action: self._noop(a))
            self._action_buttons[action.action] = button
            self._action_reason_texts.append(reason)
            buttons.addWidget(button, index // 2, index % 2)
        layout.addLayout(buttons)
        layout.addStretch(1)

    def _noop(self, _action: FEASpecCalculiXResultWriteAction) -> None:
        return None

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
            "ResultDataset write dialog state: display-only.",
            f"Result directory: {self._viewmodel.result_dir or '<missing>'}",
            f"Output directory: {self._viewmodel.output_dir or '<missing>'}",
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
            "Save target analysis:",
            self._json_text(self._viewmodel.save_plan.to_dict()),
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
            "Display-only FEASpec CalculiX ResultDataset write dialog.",
            "No file dialog.",
            "No writer call.",
            "No ResultDataset file write.",
            "No artifact copying.",
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
        if not self._viewmodel.writer_result_summary:
            return (
                "No writer result summary is present. This dialog does not invoke "
                "the writer."
            )
        return self._json_text(self._viewmodel.writer_result_summary)

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
        reasons = [reason.value for reason in action.disabled_reasons]
        if action.action in {
            FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY,
            FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET,
            FEASpecCalculiXResultWriteAction.OPEN_WRITTEN_OUTPUT,
        }:
            reasons.append("display_only_dialog")
        if not reasons and action.safety_note:
            reasons.append(action.safety_note)
        return "; ".join(reasons)

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


__all__ = ["FEASpecCalculiXResultWriteDialog"]
