"""FEASpec human review dialog bound to view-model state."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from osw.experimental.feaspec.human_review import (
    FEASpecHumanReviewRecord,
    validate_human_review_record,
)
from osw.experimental.feaspec.human_review_errors import FEASpecHumanReviewError
from osw.experimental.feaspec.human_review_io import dump_human_review_record
from osw.experimental.feaspec.human_review_viewmodel import (
    HumanReviewDialogAction,
    HumanReviewDialogState,
    build_human_review_dialog_state,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class FEASpecHumanReviewDialog(_BaseDialog):
    """Read-only review surface for existing FEASpec human-review state."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        state: HumanReviewDialogState | Mapping[str, Any] | None = None,
        save_path: object | None = None,
        overwrite: bool = False,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswFeaspecHumanReviewDialog")
        self.setWindowTitle("FEASpec Human Review")
        self.resize(980, 720)
        self._tokens = theme_tokens or DARK_TOKENS
        self._save_path = save_path
        self._overwrite_enabled = bool(overwrite)
        self._last_save_status = "idle"
        self._last_save_error = ""
        self._saved_record_path = ""
        self._state = _normalize_state(
            state,
            save_path=self._save_path,
            overwrite=self._overwrite_enabled,
        )
        self._buttons: dict[HumanReviewDialogAction, Any] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.header_label = QtWidgets.QLabel(
            "Experimental FEASpec human review - read-only preview",
            self,
        )
        self.header_label.setObjectName("oswFeaspecHumanReviewHeader")
        root.addWidget(self.header_label)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswFeaspecHumanReviewTabs")
        root.addWidget(self.tabs, 1)

        self.source_panel = _readonly_plain_text(
            "oswFeaspecHumanReviewSourcePanel",
            self.tabs,
        )
        self.diagnostics_panel = QtWidgets.QWidget(self.tabs)
        self.diagnostics_panel.setObjectName("oswFeaspecHumanReviewDiagnosticsPanel")
        diagnostics_layout = QtWidgets.QVBoxLayout(self.diagnostics_panel)
        diagnostics_layout.setContentsMargins(0, 0, 0, 0)
        diagnostics_layout.setSpacing(8)
        self.diagnostics_table = _diagnostics_table(
            "oswFeaspecHumanReviewDiagnosticsTable",
            self.diagnostics_panel,
        )
        diagnostics_layout.addWidget(self.diagnostics_table, 2)
        self.warning_list = QtWidgets.QListWidget(self.diagnostics_panel)
        self.warning_list.setObjectName("oswFeaspecHumanReviewWarningList")
        diagnostics_layout.addWidget(self.warning_list, 1)
        self.engineering_panel = _readonly_plain_text(
            "oswFeaspecHumanReviewEngineeringPanel",
            self.tabs,
        )
        self.export_preview_panel = _readonly_plain_text(
            "oswFeaspecHumanReviewExportPreviewPanel",
            self.tabs,
        )
        self.review_actions_panel = QtWidgets.QWidget(self.tabs)
        self.review_actions_panel.setObjectName("oswFeaspecHumanReviewActionsPanel")
        self.safety_panel = _readonly_plain_text(
            "oswFeaspecHumanReviewSafetyPanel",
            self.tabs,
        )
        self.record_preview_panel = _readonly_plain_text(
            "oswFeaspecHumanReviewRecordPreviewPanel",
            self.tabs,
        )

        self.tabs.addTab(self.source_panel, "Source/Evidence")
        self.tabs.addTab(self.diagnostics_panel, "Diagnostics")
        self.tabs.addTab(self.engineering_panel, "Engineering Summary")
        self.tabs.addTab(self.export_preview_panel, "Export Preview")
        self.tabs.addTab(self.review_actions_panel, "Review Actions")
        self.tabs.addTab(self.safety_panel, "Safety/Limitations")
        self.tabs.addTab(self.record_preview_panel, "Record Preview")

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswFeaspecHumanReviewCloseButton")
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.set_state(self._state)
        self.set_theme_tokens(self._tokens)

    def set_state(self, state: HumanReviewDialogState | Mapping[str, Any]) -> None:
        self._state = _normalize_state(
            state,
            save_path=self._save_path,
            overwrite=self._overwrite_enabled,
        )
        self.source_panel.setPlainText(_source_text(self._state))
        self._populate_diagnostics()
        self.engineering_panel.setPlainText(_engineering_text(self._state))
        self.export_preview_panel.setPlainText(_export_preview_text(self._state))
        self.safety_panel.setPlainText(_safety_text())
        self.record_preview_panel.setPlainText(_record_preview_text(self._state))
        self._populate_action_state()

    def set_save_path(self, path: object | None) -> None:
        self._save_path = path
        self._saved_record_path = ""
        self._set_save_status("idle", "")
        self.set_state(self._state)

    def set_overwrite_enabled(self, enabled: bool) -> None:
        self._overwrite_enabled = bool(enabled)
        self._set_save_status("idle", "")
        self.set_state(self._state)

    def trigger_save_record(self) -> bool:
        availability = self._state.availability_for(HumanReviewDialogAction.SAVE_RECORD)
        if not availability.enabled:
            reason = availability.disabled_reason or "save record action is disabled"
            self._set_save_status("blocked", reason)
            return False
        preview = self._state.record_preview
        if preview is None:
            self._set_save_status("error", "record preview is required")
            return False
        try:
            record = FEASpecHumanReviewRecord.from_dict(preview.json_payload)
            validation = validate_human_review_record(record)
            if not validation.is_valid:
                self._set_save_status("error", "; ".join(validation.errors))
                return False
            dump_human_review_record(
                record,
                self._state.save_plan.path,
                overwrite=self._overwrite_enabled,
            )
        except FEASpecHumanReviewError as exc:
            self._set_save_status("error", str(exc))
            return False
        self._saved_record_path = self._state.save_plan.path
        saved_path = self._saved_record_path
        self.set_state(self._state)
        self._set_save_status("saved", f"Saved human review record: {saved_path}")
        return True

    def last_save_status(self) -> str:
        return self._last_save_status

    def last_save_error(self) -> str:
        return self._last_save_error

    def saved_record_path(self) -> str:
        return self._saved_record_path

    def panel_names(self) -> tuple[str, ...]:
        return tuple(panel.value for panel in self._state.panels)

    def diagnostic_row_count(self) -> int:
        return self.diagnostics_table.rowCount()

    def warning_row_count(self) -> int:
        return self.warning_list.count()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def record_preview_text(self) -> str:
        return self.record_preview_panel.toPlainText()

    def action_enabled(self, action: HumanReviewDialogAction | str) -> bool:
        button = self._button_for(action)
        return bool(button and button.isEnabled())

    def action_disabled_reason(self, action: HumanReviewDialogAction | str) -> str:
        button = self._button_for(action)
        return "" if button is None else str(button.toolTip())

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswFeaspecHumanReviewDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswFeaspecHumanReviewHeader {"
            f"color: {tokens.accent};"
            "font-weight: 700;"
            "}"
            "QPlainTextEdit, QTableWidget, QListWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 4px;"
            "}"
            "QPushButton {"
            f"background-color: {tokens.accent};"
            f"color: {tokens.bg_app};"
            f"border: 1px solid {tokens.primary_hover};"
            "padding: 6px 12px;"
            "}"
            "QPushButton:disabled {"
            f"color: {tokens.text_muted};"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "}"
        )

    def _build_actions_panel(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.review_actions_panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.action_summary = QtWidgets.QListWidget(self.review_actions_panel)
        self.action_summary.setObjectName("oswFeaspecHumanReviewActionSummary")
        layout.addWidget(self.action_summary, 1)

        button_grid = QtWidgets.QGridLayout()
        action_labels = (
            (HumanReviewDialogAction.MARK_NEEDS_CHANGES, "Needs Changes"),
            (HumanReviewDialogAction.REJECT, "Reject"),
            (HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT, "Approve No-Run Export"),
            (
                HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN,
                "Request Installed-Only Run",
            ),
            (HumanReviewDialogAction.PREVIEW_RECORD, "Preview Record"),
            (HumanReviewDialogAction.SAVE_RECORD, "Save Record"),
        )
        for index, (action, label) in enumerate(action_labels):
            button = QtWidgets.QPushButton(label, self.review_actions_panel)
            button.setObjectName(_button_object_name(action))
            self._buttons[action] = button
            button_grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(button_grid)

        save_button = self._buttons[HumanReviewDialogAction.SAVE_RECORD]
        save_button.clicked.connect(lambda: self.trigger_save_record())
        self.save_status_label = QtWidgets.QLabel("", self.review_actions_panel)
        self.save_status_label.setObjectName("oswFeaspecHumanReviewSaveStatus")
        layout.addWidget(self.save_status_label)

    def _populate_diagnostics(self) -> None:
        rows = list(self._state.diagnostics)
        self.diagnostics_table.setRowCount(len(rows))
        for row_index, diagnostic in enumerate(rows):
            values = (
                diagnostic.severity,
                diagnostic.code,
                diagnostic.message,
                diagnostic.target_ref,
                "yes" if diagnostic.accept_away_eligible else "no",
            )
            for column, value in enumerate(values):
                self.diagnostics_table.setItem(
                    row_index,
                    column,
                    _readonly_item(value),
                )
        self.diagnostics_table.resizeColumnsToContents()
        self.warning_list.clear()
        for warning in self._state.warnings:
            reason_state = "reason provided" if warning.reason.strip() else "reason required"
            acceptance_state = "accepted" if warning.accepted else "not accepted"
            self.warning_list.addItem(
                f"{warning.diagnostic.code}: {warning.diagnostic.message} "
                f"({reason_state}; {acceptance_state})"
            )

    def _populate_action_state(self) -> None:
        self.action_summary.clear()
        for availability in self._state.actions:
            reason = availability.disabled_reason
            suffix = "enabled" if availability.enabled else f"disabled: {reason}"
            self.action_summary.addItem(f"{availability.action.value}: {suffix}")
            button = self._buttons.get(availability.action)
            if button is None:
                continue
            button.setEnabled(availability.enabled)
            button.setToolTip("" if availability.enabled else reason)

    def _set_save_status(self, status: str, message: str) -> None:
        self._last_save_status = status
        self._last_save_error = "" if status == "saved" else message
        if hasattr(self, "save_status_label"):
            self.save_status_label.setText(message)

    def _button_for(self, action: HumanReviewDialogAction | str) -> object | None:
        try:
            dialog_action = (
                action
                if isinstance(action, HumanReviewDialogAction)
                else HumanReviewDialogAction(str(action))
            )
        except ValueError:
            return None
        return self._buttons.get(dialog_action)


def _normalize_state(
    state: HumanReviewDialogState | Mapping[str, Any] | None,
    *,
    save_path: object | None = None,
    overwrite: bool = False,
) -> HumanReviewDialogState:
    if isinstance(state, HumanReviewDialogState) and save_path is None and not overwrite:
        return state
    if state is None:
        return build_human_review_dialog_state(save_path=save_path, overwrite=overwrite)
    if isinstance(state, HumanReviewDialogState):
        kwargs = _state_kwargs(state)
    else:
        kwargs = dict(state)
    if save_path is not None:
        kwargs["save_path"] = save_path
    elif "save_path" not in kwargs and isinstance(state, HumanReviewDialogState):
        kwargs["save_path"] = state.save_plan.path
    kwargs["overwrite"] = overwrite
    return build_human_review_dialog_state(**kwargs)


def _state_kwargs(state: HumanReviewDialogState) -> dict[str, Any]:
    record_payload = (
        state.record_preview.json_payload if state.record_preview is not None else None
    )
    return {
        "record": record_payload,
        "source_feaspec_id": state.source_feaspec_id,
        "reviewer": state.reviewer,
        "reviewed_at": state.reviewed_at,
        "desired_action": state.desired_action,
        "notes": state.notes,
        "validator_summary": state.validator_summary,
        "validator_report_hash": state.validator_report_hash,
        "bridge_summary": state.bridge_summary,
        "case_plan_summary": state.case_plan_summary,
        "export_preview_summary": state.export_preview_summary,
        "export_write_summary": state.export_write_summary,
        "limitations_acknowledged": state.limitations_acknowledged,
        "no_run_export_review_acknowledged": state.no_run_export_review_acknowledged,
        "run_gate_separation_acknowledged": state.run_gate_separation_acknowledged,
    }


def _readonly_plain_text(object_name: str, parent: object) -> object:
    widget = QtWidgets.QPlainTextEdit(parent)
    widget.setObjectName(object_name)
    widget.setReadOnly(True)
    return widget


def _diagnostics_table(object_name: str, parent: object) -> object:
    table = QtWidgets.QTableWidget(parent)
    table.setObjectName(object_name)
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(
        ["Severity", "Code", "Message", "Target", "Accept away"]
    )
    table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    return table


def _readonly_item(value: object) -> object:
    item = QtWidgets.QTableWidgetItem(str(value))
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item


def _source_text(state: HumanReviewDialogState) -> str:
    return "\n".join(
        [
            f"Source FEASpec ID: {state.source_feaspec_id or '<missing>'}",
            f"Reviewer: {state.reviewer or '<missing>'}",
            f"Reviewed at: {state.reviewed_at or '<missing>'}",
            f"Validator hash: {state.validator_report_hash or '<missing>'}",
        ]
    )


def _engineering_text(state: HumanReviewDialogState) -> str:
    return "\n\n".join(
        [
            "Bridge summary:",
            _json_text(state.bridge_summary),
            "Case-plan summary:",
            _json_text(state.case_plan_summary),
        ]
    )


def _export_preview_text(state: HumanReviewDialogState) -> str:
    return "\n\n".join(
        [
            "Export preview summary:",
            _json_text(state.export_preview_summary),
            "Export write summary:",
            _json_text(state.export_write_summary),
        ]
    )


def _record_preview_text(state: HumanReviewDialogState) -> str:
    if state.record_preview is None:
        return "No record preview available."
    return _json_text(state.record_preview.to_dict())


def _safety_text() -> str:
    return "\n".join(
        [
            "Experimental prerelease human-review dialog.",
            "No solver execution.",
            "No ccx invocation.",
            "No result import or installed-only run gate implementation.",
            "External solvers are optional and not bundled.",
            "Issue #8 live validation remains separate.",
            "No industrial certification or production accuracy claim.",
            "Record save uses an explicit JSON path only; no file dialog.",
            "Record save does not write export bundles, .inp files, or solver outputs.",
        ]
    )


def _json_text(value: Mapping[str, Any]) -> str:
    if not value:
        return "{}"
    return json.dumps(value, indent=2, sort_keys=True)


def _button_object_name(action: HumanReviewDialogAction) -> str:
    names = {
        HumanReviewDialogAction.MARK_NEEDS_CHANGES: (
            "oswFeaspecHumanReviewNeedsChangesButton"
        ),
        HumanReviewDialogAction.REJECT: "oswFeaspecHumanReviewRejectButton",
        HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT: (
            "oswFeaspecHumanReviewApproveNoRunButton"
        ),
        HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN: (
            "oswFeaspecHumanReviewRequestRunButton"
        ),
        HumanReviewDialogAction.PREVIEW_RECORD: (
            "oswFeaspecHumanReviewPreviewRecordButton"
        ),
        HumanReviewDialogAction.SAVE_RECORD: "oswFeaspecHumanReviewSaveRecordButton",
    }
    return names[action]


__all__ = ["FEASpecHumanReviewDialog"]
