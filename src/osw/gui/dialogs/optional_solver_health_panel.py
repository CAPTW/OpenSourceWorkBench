"""PySide display panel for optional solver health view-models."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from osw.experimental.optional_solvers import (
    OptionalSolverDiagnosticRowViewModel,
    OptionalSolverDiscoveryOptions,
    OptionalSolverDiscoveryReport,
    OptionalSolverExportSummaryFormat,
    OptionalSolverExportSummaryOptions,
    OptionalSolverExportSummaryRenderResult,
    OptionalSolverHealthPanelAction,
    OptionalSolverHealthPanelActionState,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverManifest,
    OptionalSolverRefreshApplyResult,
    OptionalSolverRefreshDiagnostic,
    OptionalSolverRefreshRequest,
    OptionalSolverRefreshResult,
    OptionalSolverRefreshState,
    OptionalSolverRequirementRowViewModel,
    OptionalSolverStackCardViewModel,
    OptionalSolverStackDetailsViewModel,
    OptionalSolverValidationHistoryRowViewModel,
    apply_optional_solver_refresh_canceled,
    apply_optional_solver_refresh_failure,
    apply_optional_solver_refresh_success,
    build_optional_solver_export_summary_payload,
    build_optional_solver_refresh_plan,
    builtin_optional_solver_manifests,
    discovery_service,
    ignore_optional_solver_stale_refresh_result,
    plan_optional_solver_export_summary_save,
    render_optional_solver_export_summary_json,
    render_optional_solver_export_summary_markdown,
    render_optional_solver_export_summary_text,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object
_EXPORT_ACTION_NAME = "export_summary"
_SavePathSelection = str | Path | tuple[str | Path, str] | None
_SavePathChooser = Callable[[object], _SavePathSelection]
_OverwriteConfirmer = Callable[[str], bool]
_RefreshRunnerResult = OptionalSolverRefreshResult | OptionalSolverDiscoveryReport | None
_RefreshRunner = Callable[[OptionalSolverRefreshRequest], _RefreshRunnerResult]


class OptionalSolverHealthPanel(_BaseDialog):
    """Display-only optional solver health panel bound to a pure view-model."""

    def __init__(
        self,
        view_model: OptionalSolverHealthPanelViewModel,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
        save_path_chooser: _SavePathChooser | None = None,
        overwrite_confirmer: _OverwriteConfirmer | None = None,
        export_generated_at: str = "",
        export_source_context: str = "optional_solver_gui_health_panel",
        export_package_version: str = "",
        refresh_runner: _RefreshRunner | None = None,
        allow_default_refresh_runner: bool = True,
        refresh_generated_at: str = "",
        refresh_source: str = "optional_solver_gui_passive_refresh",
        refresh_manifests: Sequence[OptionalSolverManifest] | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOptionalSolverHealthPanel")
        self.setWindowTitle("Optional Solver Health")
        self.resize(1120, 760)
        self._tokens = theme_tokens or DARK_TOKENS
        self._view_model = view_model
        self._save_path_chooser = save_path_chooser
        self._overwrite_confirmer = overwrite_confirmer
        self._export_generated_at = export_generated_at
        self._export_source_context = export_source_context
        self._export_package_version = export_package_version
        self._refresh_runner = refresh_runner
        self._allow_default_refresh_runner = allow_default_refresh_runner
        self._refresh_generated_at = refresh_generated_at
        self._refresh_source = refresh_source
        self._refresh_manifests = (
            tuple(refresh_manifests) if refresh_manifests is not None else None
        )
        self._action_buttons: dict[OptionalSolverHealthPanelAction, Any] = {}
        self._disabled_action_reasons: dict[str, str] = {}
        self._export_action_available = False
        self._export_action_reason = "Export summary has not been initialized."
        self._export_status_text = "No export attempted."
        self._export_error_text = ""
        self._last_export_path = ""
        self._last_export_format = ""
        self._exported_file_summary_text = ""
        self._refresh_action_reason = "Refresh action has not been initialized."
        self._refresh_status_text = "Refresh idle."
        self._refresh_error_text = ""
        self._refresh_active_request_id = ""
        self._refresh_result_summary_text = "No refresh attempted."
        self._refresh_runner_call_count = 0

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.summary_label = QtWidgets.QLabel(self)
        self.summary_label.setObjectName("oswOptionalSolverHealthSummary")
        root.addWidget(self.summary_label)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        root.addWidget(splitter, 1)

        self.stack_list = QtWidgets.QListWidget(splitter)
        self.stack_list.setObjectName("oswOptionalSolverHealthStackList")
        self.stack_list.setMinimumWidth(300)

        self.tabs = QtWidgets.QTabWidget(splitter)
        self.tabs.setObjectName("oswOptionalSolverHealthTabs")
        self.details_panel = _readonly_plain_text(
            "oswOptionalSolverHealthDetailsPanel",
            self.tabs,
        )
        self.diagnostics_panel = _readonly_plain_text(
            "oswOptionalSolverHealthDiagnosticsPanel",
            self.tabs,
        )
        self.guidance_panel = _readonly_plain_text(
            "oswOptionalSolverHealthGuidancePanel",
            self.tabs,
        )
        self.validation_history_panel = _readonly_plain_text(
            "oswOptionalSolverHealthValidationHistoryPanel",
            self.tabs,
        )
        self.actions_panel = QtWidgets.QWidget(self.tabs)
        self.actions_panel.setObjectName("oswOptionalSolverHealthActionsPanel")
        self.safety_panel = _readonly_plain_text(
            "oswOptionalSolverHealthSafetyPanel",
            self.tabs,
        )
        self.tabs.addTab(self.details_panel, "Details")
        self.tabs.addTab(self.diagnostics_panel, "Diagnostics")
        self.tabs.addTab(self.guidance_panel, "Guidance")
        self.tabs.addTab(self.validation_history_panel, "Validation History")
        self.tabs.addTab(self.actions_panel, "Actions")
        self.tabs.addTab(self.safety_panel, "Safety")
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self._build_actions_panel()

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswOptionalSolverHealthCloseButton")
        self.close_button.clicked.connect(self.reject)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.set_view_model(view_model)
        self.set_theme_tokens(self._tokens)

    def set_view_model(self, view_model: OptionalSolverHealthPanelViewModel) -> None:
        """Render a new already-built view-model without performing discovery."""

        self._view_model = view_model
        self.summary_label.setText(_summary_text(view_model))
        self._populate_stack_cards()
        self.details_panel.setPlainText(_details_text(view_model.details))
        self.diagnostics_panel.setPlainText(_diagnostics_text(view_model.diagnostics))
        self.guidance_panel.setPlainText(_guidance_text(view_model))
        self.validation_history_panel.setPlainText(
            _validation_history_text(view_model.validation_history)
        )
        self._refresh_export_action_state()
        self._populate_action_state()
        self.safety_panel.setPlainText(_safety_text(view_model))

    def summary_text(self) -> str:
        return self.summary_label.text()

    def stack_card_texts(self) -> tuple[str, ...]:
        return tuple(
            self.stack_list.item(index).text()
            for index in range(self.stack_list.count())
        )

    def selected_stack_details_text(self) -> str:
        return self.details_panel.toPlainText()

    def diagnostics_text(self) -> str:
        return self.diagnostics_panel.toPlainText()

    def guidance_text(self) -> str:
        return self.guidance_panel.toPlainText()

    def validation_history_text(self) -> str:
        return self.validation_history_panel.toPlainText()

    def action_state_text(self) -> str:
        return self.action_state_panel.toPlainText()

    def safety_text(self) -> str:
        return self.safety_panel.toPlainText()

    def available_action_names(self) -> tuple[str, ...]:
        names = [
            action.action.value
            for action in self._view_model.actions
            if action.available
        ]
        if self.export_action_enabled():
            names.append(_EXPORT_ACTION_NAME)
        return tuple(names)

    def disabled_action_reasons(self) -> dict[str, str]:
        return dict(self._disabled_action_reasons)

    def export_status_text(self) -> str:
        return self._export_status_text

    def export_error_text(self) -> str:
        return self._export_error_text

    def last_export_path(self) -> str:
        return self._last_export_path

    def last_export_format(self) -> str:
        return self._last_export_format

    def exported_file_summary_text(self) -> str:
        return self._exported_file_summary_text

    def export_action_enabled(self) -> bool:
        return bool(self.export_summary_button.isEnabled())

    def export_action_reason(self) -> str:
        return self._export_action_reason

    def refresh_action_enabled(self) -> bool:
        return bool(self.refresh_passive_discovery_button.isEnabled())

    def refresh_action_reason(self) -> str:
        return self._refresh_action_reason

    def refresh_status_text(self) -> str:
        return self._refresh_status_text

    def refresh_error_text(self) -> str:
        return self._refresh_error_text

    def refresh_request_id(self) -> str:
        return self._refresh_active_request_id

    def refresh_result_summary_text(self) -> str:
        return self._refresh_result_summary_text

    def refresh_runner_call_count(self) -> int:
        return self._refresh_runner_call_count

    def current_stack_card_texts(self) -> tuple[str, ...]:
        return self.stack_card_texts()

    def current_summary_text(self) -> str:
        return self.summary_text()

    def set_refresh_runner_for_test(self, runner: _RefreshRunner | None) -> None:
        self._refresh_runner = runner
        self._refresh_action_reason = self._compute_refresh_action_reason()
        self._populate_action_state()

    def trigger_refresh_for_test(self) -> None:
        self._trigger_refresh()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOptionalSolverHealthPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverHealthSummary {"
            f"color: {tokens.accent};"
            "font-weight: 700;"
            "}"
            "QLabel#oswOptionalSolverHealthExportStatus {"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverHealthExportError {"
            f"color: {tokens.danger};"
            "}"
            "QLabel#oswOptionalSolverHealthRefreshStatus {"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel#oswOptionalSolverHealthRefreshError {"
            f"color: {tokens.danger};"
            "}"
            "QPlainTextEdit, QListWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 4px;"
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
            "oswOptionalSolverHealthActionStatePanel",
            self.actions_panel,
        )
        layout.addWidget(self.action_state_panel, 1)
        button_grid = QtWidgets.QGridLayout()
        for index, action in enumerate(OptionalSolverHealthPanelAction):
            button = QtWidgets.QPushButton(_action_label(action), self.actions_panel)
            button.setObjectName(_action_button_object_name(action))
            button.setEnabled(False)
            self._action_buttons[action] = button
            button_grid.addWidget(button, index // 2, index % 2)
        self.refresh_passive_discovery_button = self._action_buttons[
            OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY
        ]
        self.refresh_passive_discovery_button.clicked.connect(self._trigger_refresh)
        export_row = len(tuple(OptionalSolverHealthPanelAction)) // 2
        self.export_summary_button = QtWidgets.QPushButton(
            "Export Summary",
            self.actions_panel,
        )
        self.export_summary_button.setObjectName(
            "oswOptionalSolverHealthExportSummaryButton"
        )
        self.export_summary_button.clicked.connect(self._export_summary)
        button_grid.addWidget(self.export_summary_button, export_row, 0, 1, 2)
        layout.addLayout(button_grid)
        self.refresh_status_label = QtWidgets.QLabel(self._refresh_status_text, self)
        self.refresh_status_label.setObjectName("oswOptionalSolverHealthRefreshStatus")
        self.refresh_status_label.setWordWrap(True)
        layout.addWidget(self.refresh_status_label)
        self.refresh_error_label = QtWidgets.QLabel(self._refresh_error_text, self)
        self.refresh_error_label.setObjectName("oswOptionalSolverHealthRefreshError")
        self.refresh_error_label.setWordWrap(True)
        layout.addWidget(self.refresh_error_label)
        self.export_status_label = QtWidgets.QLabel(self._export_status_text, self)
        self.export_status_label.setObjectName("oswOptionalSolverHealthExportStatus")
        self.export_status_label.setWordWrap(True)
        layout.addWidget(self.export_status_label)
        self.export_error_label = QtWidgets.QLabel(self._export_error_text, self)
        self.export_error_label.setObjectName("oswOptionalSolverHealthExportError")
        self.export_error_label.setWordWrap(True)
        layout.addWidget(self.export_error_label)

    def _populate_stack_cards(self) -> None:
        self.stack_list.clear()
        for card in self._view_model.cards:
            item = QtWidgets.QListWidgetItem(_stack_card_text(card))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, card.stack_id)
            self.stack_list.addItem(item)
            if card.selected:
                self.stack_list.setCurrentItem(item)

    def _populate_action_state(self) -> None:
        self._disabled_action_reasons = {}
        lines: list[str] = []
        for action_state in self._view_model.actions:
            action_name = action_state.action.value
            if (
                action_state.action
                == OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY
            ):
                refresh_enabled = self._refresh_action_enabled()
                self._refresh_action_reason = self._compute_refresh_action_reason()
                state_text = (
                    "available; enabled; current; passive-only"
                    if refresh_enabled
                    else "unavailable; disabled; current; passive-only"
                )
                lines.append(f"{action_name}: {state_text}")
                lines.append(f"  {self._refresh_action_reason}")
                self._disabled_action_reasons[action_name] = self._refresh_action_reason
                button = self._action_buttons.get(action_state.action)
                if button is not None:
                    button.setEnabled(refresh_enabled)
                    button.setToolTip(self._refresh_action_reason)
                continue
            state_text = _action_state_status(action_state)
            reason = _gui_disabled_reason(action_state)
            lines.append(f"{action_name}: {state_text}")
            lines.append(f"  {reason}")
            self._disabled_action_reasons[action_name] = reason
            button = self._action_buttons.get(action_state.action)
            if button is not None:
                button.setEnabled(False)
                button.setToolTip(reason)
        export_state = (
            "available; enabled; current"
            if self._export_action_available
            else "unavailable; disabled; current"
        )
        lines.append(f"{_EXPORT_ACTION_NAME}: {export_state}; gui write-limited")
        lines.append(f"  {self._export_action_reason}")
        self._disabled_action_reasons[_EXPORT_ACTION_NAME] = self._export_action_reason
        self.action_state_panel.setPlainText("\n".join(lines))

    def _refresh_export_action_state(self) -> None:
        try:
            options = OptionalSolverExportSummaryOptions(
                export_format=OptionalSolverExportSummaryFormat.JSON,
                package_version=self._export_package_version,
                generated_at=self._export_generated_at,
                source_context=self._export_source_context,
            )
            build_optional_solver_export_summary_payload(self._view_model, options)
        except Exception as exc:
            self._export_action_available = False
            self._export_action_reason = (
                "Export unavailable: payload rendering failed with "
                f"{type(exc).__name__}."
            )
        else:
            self._export_action_available = True
            self._export_action_reason = (
                "Redacted JSON, Markdown, or plain-text summary export writes "
                "exactly one explicitly selected file."
            )
        self.export_summary_button.setEnabled(self._export_action_available)
        self.export_summary_button.setToolTip(self._export_action_reason)

    def _refresh_action_enabled(self) -> bool:
        if self._refresh_runner is None and not self._allow_default_refresh_runner:
            return False
        return not self._refresh_status_text.endswith("running.")

    def _compute_refresh_action_reason(self) -> str:
        if self._refresh_runner is None and not self._allow_default_refresh_runner:
            return (
                "Passive refresh runner is not configured and the default built-in "
                "passive discovery runner is disabled."
            )
        if not self._refresh_action_enabled():
            return "Passive discovery refresh is already running."
        runner_kind = (
            "injected runner"
            if self._refresh_runner is not None
            else "default built-in passive runner"
        )
        return (
            f"Refresh Passive Discovery uses the {runner_kind} only after an "
            "explicit user action; it is passive discovery only and is not "
            "validation evidence."
        )

    def _trigger_refresh(self) -> None:
        if not self._refresh_action_enabled():
            self._set_refresh_result(
                status="Passive discovery refresh unavailable.",
                error=self._compute_refresh_action_reason(),
                summary="No refresh was run.",
            )
            return

        plan = build_optional_solver_refresh_plan(
            self._view_model,
            state=OptionalSolverRefreshState.RUNNING,
            selected_stack_id=self._view_model.selected_stack_id,
            filter_text=self._view_model.filter_text,
            health_state_filters=self._view_model.health_state_filters,
            requested_at=self._refresh_generated_at,
            source=self._refresh_source,
        )
        if plan.request is None:
            self._set_refresh_result(
                status="Passive discovery refresh unavailable.",
                error="Refresh request could not be created.",
                summary="No refresh was run.",
            )
            return
        request = plan.request
        self._refresh_active_request_id = request.request_id
        self._set_refresh_result(
            status=plan.status.status_text,
            error="",
            summary=(
                f"refresh_state={plan.state.value}; request_id={request.request_id}; "
                "not_validation_evidence=true"
            ),
        )

        try:
            self._refresh_runner_call_count += 1
            raw_result = self._active_refresh_runner()(request)
            result = _normalize_refresh_runner_result(raw_result, request)
            applied = self._apply_refresh_runner_result(request, result)
        except Exception as exc:
            failure = OptionalSolverRefreshResult(
                request_id=request.request_id,
                state=OptionalSolverRefreshState.FAILED,
                generated_at=self._refresh_generated_at,
                source=self._refresh_source,
                error_text=f"{type(exc).__name__}: {exc}",
                diagnostics=(
                    OptionalSolverRefreshDiagnostic(
                        severity="error",
                        code="OSR_REFRESH_RUNNER_ERROR",
                        message="Passive refresh runner raised an exception.",
                        field="refresh_runner",
                        suggested_fix=(
                            "Inspect the injected runner or passive discovery service."
                        ),
                    ),
                ),
            )
            applied = apply_optional_solver_refresh_failure(
                self._view_model,
                result=failure,
                active_request_id=request.request_id,
            )
        self._apply_refresh_result(applied)

    def _active_refresh_runner(self) -> _RefreshRunner:
        return self._refresh_runner or self._default_passive_refresh_runner

    def _default_passive_refresh_runner(
        self,
        request: OptionalSolverRefreshRequest,
    ) -> OptionalSolverRefreshResult:
        options = OptionalSolverDiscoveryOptions(
            generated_at=self._refresh_generated_at,
            source=self._refresh_source,
        )
        report = discovery_service.discover_builtin_optional_solvers(options=options)
        return OptionalSolverRefreshResult(
            request_id=request.request_id,
            state=OptionalSolverRefreshState.COMPLETED,
            discovery_reports=report,
            generated_at=report.generated_at,
            source=report.source,
            status_text="Default passive discovery completed.",
        )

    def _apply_refresh_runner_result(
        self,
        request: OptionalSolverRefreshRequest,
        result: OptionalSolverRefreshResult,
    ) -> OptionalSolverRefreshApplyResult:
        if result.state == OptionalSolverRefreshState.FAILED:
            return apply_optional_solver_refresh_failure(
                self._view_model,
                request=request,
                result=result,
                active_request_id=request.request_id,
            )
        if result.state == OptionalSolverRefreshState.CANCELED:
            return apply_optional_solver_refresh_canceled(
                self._view_model,
                request=request,
                result=result,
                active_request_id=request.request_id,
            )
        if result.state == OptionalSolverRefreshState.STALE_IGNORED:
            return ignore_optional_solver_stale_refresh_result(
                self._view_model,
                active_request_id=request.request_id,
                result_request_id=result.request_id,
                timestamp=result.generated_at,
                source=result.source,
            )
        return apply_optional_solver_refresh_success(
            self._view_model,
            manifests=self._refresh_manifests or builtin_optional_solver_manifests(),
            result=result,
            active_request_id=request.request_id,
        )

    def _apply_refresh_result(
        self,
        result: OptionalSolverRefreshApplyResult,
    ) -> None:
        self._refresh_active_request_id = result.active_request_id
        self._refresh_status_text = result.status_text
        self._refresh_error_text = result.error_text
        self._refresh_result_summary_text = _refresh_apply_summary_text(result)
        if result.applied:
            self.set_view_model(result.panel)
        else:
            self._populate_action_state()
        self._sync_refresh_labels()

    def _set_refresh_result(self, *, status: str, error: str, summary: str) -> None:
        self._refresh_status_text = status
        self._refresh_error_text = error
        self._refresh_result_summary_text = summary
        self._sync_refresh_labels()
        self._populate_action_state()

    def _sync_refresh_labels(self) -> None:
        self.refresh_status_label.setText(self._refresh_status_text)
        self.refresh_error_label.setText(self._refresh_error_text)

    def _export_summary(self) -> None:
        if not self._export_action_available:
            self._set_export_result(
                status="Export unavailable.",
                error=self._export_action_reason,
            )
            return

        selected_path, selected_filter = self._choose_export_path()
        if not selected_path.strip():
            self._set_export_result(status="Export cancelled.", error="")
            return

        format_hint = _format_hint_from_filter(selected_filter)
        plan = plan_optional_solver_export_summary_save(
            selected_path,
            export_format=format_hint,
            allow_overwrite=False,
        )
        if _only_overwrite_blocked(plan.diagnostics):
            if not self._confirm_overwrite(plan.normalized_path):
                self._set_export_result(
                    status="Export not written.",
                    error="OSE_OVERWRITE_BLOCKED: overwrite was not confirmed.",
                )
                return
            plan = plan_optional_solver_export_summary_save(
                selected_path,
                export_format=format_hint,
                allow_overwrite=True,
            )
        if not plan.can_save or plan.export_format is None:
            self._set_export_result(
                status="Export not written.",
                error=_export_diagnostics_text(plan.diagnostics),
            )
            return

        try:
            render_result = _render_export_summary(
                self._view_model,
                plan.export_format,
                generated_at=self._export_generated_at,
                source_context=self._export_source_context,
                package_version=self._export_package_version,
            )
            target = Path(plan.normalized_path)
            target.write_text(render_result.content, encoding="utf-8", newline="\n")
        except Exception as exc:
            self._set_export_result(
                status="Export failed.",
                error=f"{type(exc).__name__}: {exc}",
            )
            return

        self._last_export_path = plan.normalized_path
        self._last_export_format = render_result.export_format.value
        byte_count = len(render_result.content.encode("utf-8"))
        self._exported_file_summary_text = (
            f"{render_result.export_format.value} export wrote {byte_count} bytes "
            f"to {plan.normalized_path}; redacted_by_default=true; "
            "not_validation_evidence=true"
        )
        self._set_export_result(
            status="Exported redacted optional solver summary.",
            error="",
        )

    def _choose_export_path(self) -> tuple[str, str]:
        if self._save_path_chooser is not None:
            selection = self._save_path_chooser(self)
        else:
            selection = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Export Optional Solver Summary",
                "",
                "JSON (*.json);;Markdown (*.md);;Plain text (*.txt)",
            )
        return _normalize_save_path_selection(selection)

    def _confirm_overwrite(self, normalized_path: str) -> bool:
        if self._overwrite_confirmer is not None:
            return self._overwrite_confirmer(normalized_path)
        result = QtWidgets.QMessageBox.question(
            self,
            "Overwrite export?",
            f"The export target already exists:\n{normalized_path}\n\nReplace it?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return result == QtWidgets.QMessageBox.StandardButton.Yes

    def _set_export_result(self, *, status: str, error: str) -> None:
        self._export_status_text = status
        self._export_error_text = error
        self.export_status_label.setText(status)
        self.export_error_label.setText(error)
        self._populate_action_state()


def _normalize_refresh_runner_result(
    result: _RefreshRunnerResult,
    request: OptionalSolverRefreshRequest,
) -> OptionalSolverRefreshResult:
    if isinstance(result, OptionalSolverRefreshResult):
        return result
    if isinstance(result, OptionalSolverDiscoveryReport):
        return OptionalSolverRefreshResult(
            request_id=request.request_id,
            state=OptionalSolverRefreshState.COMPLETED,
            discovery_reports=result,
            generated_at=result.generated_at,
            source=result.source,
        )
    return OptionalSolverRefreshResult(
        request_id=request.request_id,
        state=OptionalSolverRefreshState.CANCELED,
        generated_at=request.requested_at,
        source=request.source,
        status_text="Passive discovery refresh canceled.",
    )


def _refresh_apply_summary_text(result: OptionalSolverRefreshApplyResult) -> str:
    return (
        f"refresh_state={result.state.value}; applied={result.applied}; "
        f"ignored={result.ignored}; request_id={result.result_request_id}; "
        f"source={result.source or 'not supplied'}; "
        f"timestamp={result.last_refresh_timestamp or 'not supplied'}; "
        "not_validation_evidence=true"
    )


def _readonly_plain_text(object_name: str, parent: object) -> object:
    widget = QtWidgets.QPlainTextEdit(parent)
    widget.setObjectName(object_name)
    widget.setReadOnly(True)
    return widget


def _normalize_save_path_selection(selection: _SavePathSelection) -> tuple[str, str]:
    if selection is None:
        return "", ""
    if isinstance(selection, tuple):
        selected_path = selection[0] if selection else ""
        selected_filter = selection[1] if len(selection) > 1 else ""
        return str(selected_path or ""), str(selected_filter or "")
    return str(selection or ""), ""


def _format_hint_from_filter(
    selected_filter: str,
) -> OptionalSolverExportSummaryFormat | None:
    normalized = selected_filter.lower()
    if ".json" in normalized or "json" in normalized:
        return OptionalSolverExportSummaryFormat.JSON
    if ".md" in normalized or "markdown" in normalized:
        return OptionalSolverExportSummaryFormat.MARKDOWN
    if ".txt" in normalized or "plain text" in normalized:
        return OptionalSolverExportSummaryFormat.TEXT
    return None


def _only_overwrite_blocked(
    diagnostics: tuple[Any, ...],
) -> bool:
    codes = {
        getattr(diagnostic, "code", "")
        for diagnostic in diagnostics
        if getattr(diagnostic, "severity", "") == "error"
    }
    return codes == {"OSE_OVERWRITE_BLOCKED"}


def _export_diagnostics_text(diagnostics: tuple[Any, ...]) -> str:
    if not diagnostics:
        return "Export path or payload is not valid."
    return "; ".join(
        f"{diagnostic.code}: {diagnostic.message}" for diagnostic in diagnostics
    )


def _render_export_summary(
    view_model: OptionalSolverHealthPanelViewModel,
    export_format: OptionalSolverExportSummaryFormat,
    *,
    generated_at: str,
    source_context: str,
    package_version: str,
) -> OptionalSolverExportSummaryRenderResult:
    options = OptionalSolverExportSummaryOptions(
        export_format=export_format,
        package_version=package_version,
        generated_at=generated_at,
        source_context=source_context,
    )
    payload = build_optional_solver_export_summary_payload(view_model, options)
    if export_format == OptionalSolverExportSummaryFormat.JSON:
        return render_optional_solver_export_summary_json(payload)
    if export_format == OptionalSolverExportSummaryFormat.MARKDOWN:
        return render_optional_solver_export_summary_markdown(payload)
    return render_optional_solver_export_summary_text(payload)


def _summary_text(view_model: OptionalSolverHealthPanelViewModel) -> str:
    summary = view_model.summary
    state_counts = ", ".join(
        f"{state}={count}"
        for state, count in sorted(summary.counts_by_health_state.items())
    )
    return (
        f"Optional solver health: total={summary.total_stacks}; "
        f"missing={summary.missing_count}; partial={summary.partial_count}; "
        f"discovered={summary.discovered_count}; "
        f"open_issues={summary.open_issue_count}; "
        f"warnings={summary.validation_warning_count}; "
        f"states={state_counts or 'none'}"
    )


def _stack_card_text(card: OptionalSolverStackCardViewModel) -> str:
    selected = "selected" if card.selected else "not selected"
    disclaimer = "non-bundled" if card.has_non_bundled_disclaimer else "no disclaimer"
    return (
        f"{card.stack_id} | {card.display_name} | {card.issue_reference or 'no issue'} | "
        f"health={card.health_state} | support={card.support_status} | "
        f"missing={card.missing_requirements_count} | "
        f"diagnostics={card.diagnostics_count} | {disclaimer} | {selected}"
    )


def _details_text(details: OptionalSolverStackDetailsViewModel | None) -> str:
    if details is None:
        return "No stack selected."
    sections = [
        f"Stack: {details.display_name} ({details.stack_id})",
        _section("Capabilities", details.capabilities),
        _requirement_section("Executable requirements", details.executable_requirements),
        _requirement_section(
            "Python package requirements",
            details.python_package_requirements,
        ),
        _requirement_section("Environment hints", details.environment_hints),
        _section("Prepared-machine notes", details.prepared_machine_notes),
        _section("Safety notes", details.safety_notes),
        _section("Documentation refs", details.documentation_refs),
    ]
    if details.version_probe_text:
        sections.append(f"Version probe: {details.version_probe_text}")
    if details.help_probe_text:
        sections.append(f"Help probe: {details.help_probe_text}")
    return "\n\n".join(sections)


def _requirement_section(
    title: str,
    rows: tuple[OptionalSolverRequirementRowViewModel, ...],
) -> str:
    if not rows:
        return f"{title}:\n- none"
    return "\n".join([f"{title}:"] + [_requirement_line(row) for row in rows])


def _requirement_line(row: OptionalSolverRequirementRowViewModel) -> str:
    requirement = "required" if row.required else "optional"
    found = "not checked" if row.found is None else ("found" if row.found else "missing")
    parts = [
        f"- {row.identifier}",
        f"display={row.display_name}",
        requirement,
        f"status={row.status_text}",
        f"found={found}",
    ]
    if row.detail_text:
        parts.append(f"detail={row.detail_text}")
    if row.notes:
        parts.append("notes=" + "; ".join(row.notes))
    return " | ".join(parts)


def _diagnostics_text(rows: tuple[OptionalSolverDiagnosticRowViewModel, ...]) -> str:
    if not rows:
        return "No diagnostics."
    lines: list[str] = []
    for row in rows:
        parts = [
            f"{row.stack_id}",
            row.severity,
            row.code,
            row.message,
        ]
        if row.path:
            parts.append(f"path={row.path}")
        if row.suggested_fix:
            parts.append(f"fix={row.suggested_fix}")
        if row.redaction_notice:
            parts.append(row.redaction_notice)
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _guidance_text(view_model: OptionalSolverHealthPanelViewModel) -> str:
    if not view_model.guidance:
        return "No guidance."
    return "\n".join(
        f"{row.category} [{row.severity}]: {row.text}"
        for row in view_model.guidance
    )


def _validation_history_text(
    rows: tuple[OptionalSolverValidationHistoryRowViewModel, ...],
) -> str:
    if not rows:
        return "No validation history."
    lines: list[str] = []
    for row in rows:
        issue = f"#{row.related_issue}" if row.related_issue is not None else "no issue"
        pass_state = "pass evidence" if row.is_pass_evidence else "not pass evidence"
        closure = (
            "closure review required"
            if row.closure_review_required
            else "closure review not required"
        )
        lines.append(
            f"{row.source}: {row.status} | {issue} | {pass_state} | "
            f"{closure} | {row.summary}"
        )
    return "\n".join(lines)


def _action_state_status(action_state: OptionalSolverHealthPanelActionState) -> str:
    availability = "available" if action_state.available else "unavailable"
    enabled = "view-model enabled" if action_state.enabled else "disabled"
    future = "future" if action_state.future_action else "current"
    return f"{availability}; {enabled}; {future}; gui disabled"


def _gui_disabled_reason(action_state: OptionalSolverHealthPanelActionState) -> str:
    action = action_state.action
    if action == OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY:
        return (
            "Refresh is explicit passive discovery only and is not validation "
            "evidence."
        )
    if action == OptionalSolverHealthPanelAction.COPY_SUMMARY:
        return (
            "Display-only placeholder: this panel does not access the clipboard."
        )
    if action == OptionalSolverHealthPanelAction.OPEN_DOCS:
        return (
            "Display-only placeholder: this panel does not open shells or browsers."
        )
    return action_state.reason


def _safety_text(view_model: OptionalSolverHealthPanelViewModel) -> str:
    return "\n".join(
        [
            "Optional solver GUI health panel safety boundary.",
            "No automatic startup refresh.",
            "Refresh Passive Discovery runs passive presence checks only after "
            "an explicit user action.",
            "Refresh output is not validation evidence.",
            "No active smoke validation.",
            "No solver execution.",
            "No external command execution.",
            "No subprocess usage.",
            "No solver or dependency installation.",
            "No optional solver package import.",
            "No issue closure action.",
            "No release mutation.",
            "External solvers and optional science packages are not bundled.",
            "Skipped-missing validation history is not pass evidence.",
            "Issues #6 through #11 remain separate validation work.",
            "No certification claim.",
            f"Selected stack: {view_model.selected_stack_id or 'none'}",
        ]
    )


def _section(title: str, rows: tuple[str, ...]) -> str:
    if not rows:
        return f"{title}:\n- none"
    return "\n".join([f"{title}:"] + [f"- {row}" for row in rows])


def _action_label(action: OptionalSolverHealthPanelAction) -> str:
    labels = {
        OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY: "Refresh",
        OptionalSolverHealthPanelAction.RUN_VALIDATION_GATE: "Run Validation",
        OptionalSolverHealthPanelAction.INSTALL_SOLVER: "Install Solver",
        OptionalSolverHealthPanelAction.CLOSE_ISSUE: "Close Issue",
        OptionalSolverHealthPanelAction.COPY_SUMMARY: "Copy Summary",
        OptionalSolverHealthPanelAction.OPEN_DOCS: "Open Docs",
    }
    return labels[action]


def _action_button_object_name(action: OptionalSolverHealthPanelAction) -> str:
    return "oswOptionalSolverHealthAction" + "".join(
        part.title() for part in action.value.split("_")
    )


__all__ = ["OptionalSolverHealthPanel"]
