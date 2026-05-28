"""Theme-aware CalculiX input deck preview dialog."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class CalculixDeckDialog(_BaseDialog):
    """Preview, write, and explicitly run CalculiX `.inp` text through a runner."""

    if QtCore is not None:
        deckWritten = QtCore.Signal(str)
        calculixRunCompleted = QtCore.Signal(object)
        calculixResultsParsed = QtCore.Signal(object)

    def __init__(
        self,
        parent: object | None = None,
        *,
        result: object | None = None,
        theme_tokens: ThemeTokens | None = None,
        output_path: str | Path = Path("artifacts") / "calculix" / "cantilever.inp",
        runner: object | None = None,
        run_policy: object | None = None,
        run_case_dir: str | Path | None = None,
        result_parser: object | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswCalculixDeckDialog")
        self.setWindowTitle("Generate CalculiX Input Deck")
        self.resize(920, 720)
        self._tokens = theme_tokens or DARK_TOKENS
        self.output_path = Path(output_path)
        self.result = result
        self.runner = runner
        self.run_policy = run_policy
        self.run_case_dir = Path(run_case_dir) if run_case_dir is not None else None
        self.run_result: object | None = None
        self.result_parser = result_parser
        self.parsed_results: object | None = None

        layout = QtWidgets.QVBoxLayout(self)
        self.deck_preview = QtWidgets.QPlainTextEdit(self)
        self.deck_preview.setObjectName("oswCalculixDeckPreview")
        self.deck_preview.setReadOnly(True)
        layout.addWidget(self.deck_preview, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswCalculixReadinessDiagnostics")
        layout.addWidget(self.diagnostics_list)

        self.run_status_label = QtWidgets.QLabel("Run status: not run", self)
        self.run_status_label.setObjectName("oswCalculixRunStatusLabel")
        layout.addWidget(self.run_status_label)

        self.case_dir_label = QtWidgets.QLabel("Case directory: -", self)
        self.case_dir_label.setObjectName("oswCalculixCaseDirLabel")
        layout.addWidget(self.case_dir_label)

        self.run_log_preview = QtWidgets.QPlainTextEdit(self)
        self.run_log_preview.setObjectName("oswCalculixRunLogPreview")
        self.run_log_preview.setReadOnly(True)
        self.run_log_preview.setMaximumHeight(120)
        layout.addWidget(self.run_log_preview)

        self.run_artifacts_list = QtWidgets.QListWidget(self)
        self.run_artifacts_list.setObjectName("oswCalculixRunArtifactsList")
        self.run_artifacts_list.setMaximumHeight(90)
        layout.addWidget(self.run_artifacts_list)

        self.run_diagnostics_list = QtWidgets.QListWidget(self)
        self.run_diagnostics_list.setObjectName("oswCalculixRunDiagnosticsList")
        self.run_diagnostics_list.setMaximumHeight(90)
        layout.addWidget(self.run_diagnostics_list)

        self.result_summary_panel = QtWidgets.QWidget(self)
        self.result_summary_panel.setObjectName("oswCalculixResultSummaryPanel")
        result_layout = QtWidgets.QVBoxLayout(self.result_summary_panel)
        self.max_displacement_label = QtWidgets.QLabel("Max displacement: -", self)
        self.max_displacement_label.setObjectName("oswCalculixMaxDisplacementLabel")
        self.max_stress_label = QtWidgets.QLabel("Max stress: -", self)
        self.max_stress_label.setObjectName("oswCalculixMaxStressLabel")
        self.result_diagnostics_list = QtWidgets.QListWidget(self)
        self.result_diagnostics_list.setObjectName("oswCalculixResultDiagnosticsList")
        self.result_diagnostics_list.setMaximumHeight(90)
        result_layout.addWidget(self.max_displacement_label)
        result_layout.addWidget(self.max_stress_label)
        result_layout.addWidget(self.result_diagnostics_list)
        layout.addWidget(self.result_summary_panel)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.write_deck_button = QtWidgets.QPushButton("Write Deck", self)
        self.write_deck_button.setObjectName("oswCalculixWriteDeckButton")
        self.run_button = QtWidgets.QPushButton("Run with CalculiX", self)
        self.run_button.setObjectName("oswCalculixRunButton")
        self.parse_results_button = QtWidgets.QPushButton("Parse Results", self)
        self.parse_results_button.setObjectName("oswCalculixParseResultsButton")
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswCalculixCloseButton")
        buttons.addWidget(self.write_deck_button)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.parse_results_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.write_deck_button.clicked.connect(self.write_deck)
        self.run_button.clicked.connect(self.run_calculix)
        self.parse_results_button.clicked.connect(self.parse_results)
        self.close_button.clicked.connect(self.close)
        self.set_theme_tokens(self._tokens)
        if self.result is not None:
            self.set_deck_result(self.result)
        else:
            self.deck_preview.setPlainText("")
            self.diagnostics_list.addItem("INFO project: No CalculiX deck preview loaded.")
            self.write_deck_button.setEnabled(False)
            self.run_button.setEnabled(False)
            self.parse_results_button.setEnabled(False)

    def set_deck_result(self, result: object) -> None:
        self.result = result
        self.deck_preview.setPlainText(str(getattr(result, "input_text", "") or ""))
        self.diagnostics_list.clear()
        for item in getattr(result, "diagnostics", ()) or ():
            if isinstance(item, dict):
                severity = str(item.get("severity", "")).upper()
                path = str(item.get("path", ""))
                message = str(item.get("message", ""))
                self.diagnostics_list.addItem(f"{severity} {path}: {message}")
        self.write_deck_button.setEnabled(bool(getattr(result, "input_text", "")))
        self.run_button.setEnabled(bool(getattr(result, "input_text", "")))

    def write_deck(self) -> Path | None:
        text = str(self.deck_preview.toPlainText())
        if not text:
            return None
        output_path = self.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        self.deckWritten.emit(str(output_path))
        return output_path

    def run_calculix(self) -> object | None:
        """Run the written deck through the backend CalculiX runner."""

        deck_path = self.write_deck()
        if deck_path is None:
            return None
        self.run_status_label.setText("Run status: running")
        runner = self.runner
        policy = self.run_policy
        if runner is None:
            runner_module = import_module("osw.solvers.calculix.runner")
            runner = runner_module.CalculiXRunner()
            if policy is None:
                policy = runner_module.CalculiXRunPolicy(timeout_seconds=30.0)
        result = runner.run_input_deck(
            deck_path,
            policy=policy,
            case_dir=self.run_case_dir,
        )
        self.set_run_result(result)
        self.calculixRunCompleted.emit(result)
        return result

    def set_run_result(self, result: object) -> None:
        self.run_result = result
        self.parse_results_button.setEnabled(True)
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        self.run_status_label.setText(f"Run status: {status or 'unknown'}")
        self.case_dir_label.setText(f"Case directory: {getattr(result, 'case_dir', '-')}")
        self.run_log_preview.setPlainText(str(getattr(result, "combined_log", "") or ""))
        self.run_artifacts_list.clear()
        for artifact in getattr(result, "artifacts", ()) or ():
            role = str(getattr(artifact, "role", getattr(artifact, "kind", "")))
            path = str(getattr(artifact, "path", ""))
            self.run_artifacts_list.addItem(f"{role}: {path}")
        self.run_diagnostics_list.clear()
        diagnostics = getattr(result, "diagnostics", None)
        messages = getattr(diagnostics, "messages", ()) if diagnostics is not None else ()
        for message in messages:
            severity = str(getattr(getattr(message, "severity", ""), "value", ""))
            code = str(getattr(message, "code", ""))
            text = str(getattr(message, "message", ""))
            self.run_diagnostics_list.addItem(f"{severity.upper()} {code}: {text}")

    def parse_results(self) -> object | None:
        """Parse already-collected CalculiX artifacts without running ``ccx``."""

        parser = self.result_parser
        if callable(parser):
            source = self.run_result if self.run_result is not None else self.output_path.parent
            parsed = parser(source)
        else:
            parser_module = import_module("osw.solvers.calculix.result_parser")
            if self.run_result is not None:
                parsed = parser_module.parse_calculix_run_artifacts(self.run_result)
            else:
                parsed = parser_module.parse_calculix_case_directory(self.output_path.parent)
        self.set_parsed_results(parsed)
        self.calculixResultsParsed.emit(parsed)
        return parsed

    def set_parsed_results(self, parsed: object) -> None:
        self.parsed_results = parsed
        displacement = getattr(parsed, "displacement_summary", None)
        stress = getattr(parsed, "stress_summary", None)
        max_displacement = getattr(displacement, "max_magnitude", None)
        max_stress = getattr(stress, "max_von_mises", None)
        displacement_unit = getattr(displacement, "unit", "")
        stress_unit = getattr(stress, "unit", "")
        self.max_displacement_label.setText(
            "Max displacement: "
            f"{_format_result_value(max_displacement, displacement_unit)}"
        )
        self.max_stress_label.setText(
            f"Max stress: {_format_result_value(max_stress, stress_unit)}"
        )
        self.result_diagnostics_list.clear()
        diagnostics = getattr(parsed, "diagnostics", None)
        messages = getattr(diagnostics, "messages", ()) if diagnostics is not None else ()
        for message in messages:
            severity = str(getattr(getattr(message, "severity", ""), "value", ""))
            code = str(getattr(message, "code", ""))
            text = str(getattr(message, "message", ""))
            self.result_diagnostics_list.addItem(f"{severity.upper()} {code}: {text}")

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswCalculixDeckDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QPlainTextEdit, QListWidget, QLabel, QWidget#oswCalculixResultSummaryPanel {"
            f"background-color: {tokens.bg_panel_alt};"
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
        )


def _format_result_value(value: object, unit: object) -> str:
    if value is None:
        return "-"
    try:
        text = f"{float(value):.6g}"
    except (TypeError, ValueError):
        text = str(value)
    return f"{text} {unit}".strip()
