"""Explicit GUI write panel for reload acceptance persistence review records.

The panel is intentionally inert until callers provide a target path and invoke
explicit methods. It writes only through the OSW-EXP-126 reload acceptance
persistence writer after target, dry-run, acknowledgement, and confirmation
gates pass.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_persistence_writer import (  # noqa: E501
    RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND,
    RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION,
    OptionalSolverPluginManifestReloadAcceptancePersistenceWriter,
    ReloadAcceptancePersistenceWriteRequest,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

from .optional_solver_plugin_manifest_reload_acceptance_persistence_panel import (
    OptionalSolverPluginManifestReloadAcceptancePersistencePanel,
)

try:  # pragma: no cover - exercised only when PySide6 is installed.
    from PySide6 import QtWidgets
except ImportError:  # pragma: no cover - exercised in minimal environments.
    QtWidgets = None


WriterFactory = Callable[[], object]

_NO_TARGET = "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_TARGET_REQUIRED"
_DRY_RUN_REQUIRED = "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_DRY_RUN_REQUIRED"
_STALE_DRY_RUN = "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_STALE_DRY_RUN"
_ACK_REQUIRED = "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_ACK_REQUIRED"
_CONFIRM_REQUIRED = "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_WRITE_CONFIRM_REQUIRED"

_NON_ACTION_FLAGS: tuple[str, ...] = (
    "runtime_reload_acceptance_performed",
    "project_schema_mutated",
    "default_reload_path_used",
    "background_reload_performed",
    "directory_scan_performed",
    "network_fetch_performed",
    "plugin_package_imported",
    "cli_subprocess_used",
    "gui_subprocess_used",
    "reloadable_bundle_created",
    "export_file_created",
    "report_file_created",
    "clipboard_used",
    "report_attached",
    "output_folder_opened",
    "live_discovery_executed",
    "passive_refresh_executed",
    "validation_executed",
    "solver_executed",
    "dependency_installed",
    "dependency_uninstalled",
    "solver_uninstalled",
    "candidate_activated",
    "trust_restored",
    "issue_mutated",
    "release_mutated",
    "tag_mutated",
    "asset_mutated",
    "version_bumped",
    "validation_pass_claimed",
    "validation_fail_claimed",
    "issue_closure_claimed",
    "bundled_solver_claimed",
    "certification_claimed",
)

_DISABLED_FUTURE_ACTIONS: tuple[tuple[str, str], ...] = (
    ("choose_target", "Target assignment is explicit and does not write."),
    ("plan_persistence_record", "Planning requires explicit dry-run."),
    ("write_persistence_record", "Writing requires all explicit gates."),
    ("accept_runtime_reload", "Runtime reload acceptance is out of scope."),
    ("mutate_project_schema", "ProjectSchema mutation is out of scope."),
    ("refresh_discovery", "Live discovery is out of scope."),
    ("validate_solver", "Validation execution is out of scope."),
    ("execute_solver", "Solver execution is out of scope."),
    ("install_dependency", "Dependency installation is out of scope."),
    ("activate_reloaded_candidate", "Automatic activation is out of scope."),
    ("restore_trust", "Trust restoration is out of scope."),
    ("close_issue", "Issue mutation is out of scope."),
    ("mutate_release", "Release mutation is out of scope."),
    ("claim_certification", "Certification claims are out of scope."),
)

_SAFETY_TEXT: tuple[str, ...] = (
    "GUI write success is not runtime reload acceptance.",
    "GUI write success is not validation evidence.",
    "GUI write success is not validation failure.",
    "GUI write success is not ProjectSchema mutation.",
    "GUI write success is not trust restoration or automatic activation.",
    "GUI write success does not close issues or mutate releases.",
    "Trust label is not certification.",
    "Writes are explicit local review-record persistence only.",
    "No default target path is selected.",
    "No background write is performed.",
    "No reload file reader, CLI bridge, or subprocess is used.",
)


class OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel(
    OptionalSolverPluginManifestReloadAcceptancePersistencePanel
):
    """Explicit-target, dry-run-first GUI write panel."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        view_model: object | None = None,
        writer: object | None = None,
        writer_factory: WriterFactory | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        self._target_path: str | None = None
        self._target_display = ""
        self._allow_replace = False
        self._acknowledged = False
        self._confirmed = False
        self._generation = 0
        self._dry_run_generation: int | None = None
        self._last_dry_run: Mapping[str, object] = {}
        self._writer_source = writer if writer is not None else writer_factory
        super().__init__(
            parent,
            view_model=view_model,
            theme_tokens=theme_tokens or DARK_TOKENS,
        )
        self.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel"
        )
        self.setWindowTitle(
            "Optional Solver Plugin Manifest Reload Acceptance Persistence Write"
        )
        self._insert_write_controls()
        self._refresh_write_controls()

    def set_view_model(self, view_model: object) -> None:
        """Replace the supplied persistence view-model and invalidate planning."""

        self._invalidate_dry_run()
        super().set_view_model(view_model)
        self._refresh_write_controls()

    def set_target_path(self, target_path: object) -> None:
        """Assign an explicit caller-supplied target path without writing."""

        raw = str(target_path).strip()
        self._target_path = raw or None
        self._target_display = _redacted_target(raw) if raw else ""
        self._invalidate_dry_run()
        self.set_writer_mapping(None)
        self._refresh_write_controls()

    def clear_target(self) -> None:
        """Clear the explicit target and invalidate the latest dry-run."""

        self._target_path = None
        self._target_display = ""
        self._invalidate_dry_run(clear=True)
        self.set_writer_mapping(None)
        self._refresh_write_controls()

    def set_allow_replace(self, enabled: bool) -> None:
        """Enable existing-target replacement only when explicitly requested."""

        self._allow_replace = bool(enabled)
        self._invalidate_dry_run()
        self.set_writer_mapping(None)
        self._refresh_write_controls()

    def set_acknowledged(self, enabled: bool) -> None:
        """Set the explicit caller acknowledgement gate."""

        self._acknowledged = bool(enabled)
        self._refresh_write_controls()

    def set_confirmed(self, enabled: bool) -> None:
        """Set the explicit caller confirmation gate."""

        self._confirmed = bool(enabled)
        self._refresh_write_controls()

    def run_dry_run(self) -> Mapping[str, object]:
        """Plan the write through the injected writer without creating files."""

        if not self._target_path:
            mapping = _blocked_result(
                code=_NO_TARGET,
                message="Explicit target path is required before dry-run.",
                target_display="",
                dry_run=True,
            )
            self.set_writer_mapping(mapping)
            self._last_dry_run = {}
            self._dry_run_generation = None
            self._refresh_write_controls()
            return mapping

        request = self._build_request(dry_run=True, acknowledged=False)
        result = self._writer().write(request)
        mapping = _object_to_mapping(result)
        self._last_dry_run = mapping
        self._dry_run_generation = self._generation
        self.set_writer_mapping(mapping)
        self._refresh_write_controls()
        return mapping

    plan_write = run_dry_run

    def write_persistence_record(self) -> Mapping[str, object]:
        """Write an explicit local review record after all gates pass."""

        blocked = self._write_gate_blocker()
        if blocked is not None:
            self.set_writer_mapping(blocked)
            self._refresh_write_controls()
            return blocked

        request = self._build_request(dry_run=False, acknowledged=True)
        result = self._writer().write(request)
        mapping = _object_to_mapping(result)
        self.set_writer_mapping(mapping)
        self._refresh_write_controls()
        return mapping

    def target_text(self) -> str:
        return (
            f"target_required={_yes_no(not self._target_path)}; "
            f"target_display={self._target_display or 'not_set'}; "
            f"allow_replace={_yes_no(self._allow_replace)}; "
            "default_target_path_used=no; background_write_performed=no"
        )

    def write_gate_text(self) -> str:
        return (
            f"dry_run_fresh={_yes_no(self._dry_run_is_fresh())}; "
            f"acknowledged={_yes_no(self._acknowledged)}; "
            f"confirmed={_yes_no(self._confirmed)}; "
            f"write_ready={_yes_no(self._write_gate_blocker() is None)}"
        )

    def write_result_text(self) -> str:
        return self.writer_result_text()

    def write_non_action_flags(self) -> dict[str, bool]:
        flags = {flag: False for flag in _NON_ACTION_FLAGS}
        writer = _mapping(self._writer_mapping)
        flags.update(
            {
                key: bool(value)
                for key, value in _mapping(writer.get("non_action_flags")).items()
            }
        )
        for key in _NON_ACTION_FLAGS:
            flags[key] = bool(flags.get(key, False))
        return flags

    def disabled_future_actions(self) -> dict[str, str]:
        return dict(_DISABLED_FUTURE_ACTIONS)

    def safety_guidance_text(self) -> str:
        return "\n".join(_SAFETY_TEXT)

    def rendered_text(self) -> str:
        return "\n".join(
            (
                super().rendered_text(),
                self.target_text(),
                self.write_gate_text(),
                self.safety_guidance_text(),
            )
        )

    def _insert_write_controls(self) -> None:
        layout = self.layout()
        if layout is None:
            return
        group = QtWidgets.QGroupBox("Explicit write gates", self)
        group.setObjectName(
            "oswOptionalSolverPluginManifestReloadAcceptancePersistenceWriteGates"
        )
        form = QtWidgets.QFormLayout(group)
        self.target_display_label = QtWidgets.QLabel("not_set", group)
        self.target_display_label.setObjectName(
            "oswReloadAcceptancePersistenceWriteTargetDisplay"
        )
        self.write_gate_label = QtWidgets.QLabel("", group)
        self.write_gate_label.setObjectName(
            "oswReloadAcceptancePersistenceWriteGateSummary"
        )
        self.allow_replace_check = QtWidgets.QCheckBox("Allow explicit replace", group)
        self.allow_replace_check.setObjectName(
            "oswReloadAcceptancePersistenceWriteAllowReplace"
        )
        self.acknowledgement_check = QtWidgets.QCheckBox(
            "I acknowledge this is a local review-record write only.",
            group,
        )
        self.acknowledgement_check.setObjectName(
            "oswReloadAcceptancePersistenceWriteAcknowledged"
        )
        self.confirmation_check = QtWidgets.QCheckBox(
            "I confirm the explicit write request.",
            group,
        )
        self.confirmation_check.setObjectName(
            "oswReloadAcceptancePersistenceWriteConfirmed"
        )
        dry_run_button = QtWidgets.QPushButton("Dry-run", group)
        dry_run_button.setObjectName("oswReloadAcceptancePersistenceWriteDryRun")
        write_button = QtWidgets.QPushButton("Write review record", group)
        write_button.setObjectName("oswReloadAcceptancePersistenceWriteSubmit")

        self.allow_replace_check.toggled.connect(self.set_allow_replace)
        self.acknowledgement_check.toggled.connect(self.set_acknowledged)
        self.confirmation_check.toggled.connect(self.set_confirmed)
        dry_run_button.clicked.connect(self.run_dry_run)
        write_button.clicked.connect(self.write_persistence_record)

        form.addRow("Target", self.target_display_label)
        form.addRow("Gates", self.write_gate_label)
        form.addRow(self.allow_replace_check)
        form.addRow(self.acknowledgement_check)
        form.addRow(self.confirmation_check)
        form.addRow(dry_run_button, write_button)
        layout.insertWidget(1, group)

    def _refresh_write_controls(self) -> None:
        if hasattr(self, "target_display_label"):
            self.target_display_label.setText(self._target_display or "not_set")
        if hasattr(self, "write_gate_label"):
            self.write_gate_label.setText(self.write_gate_text())
        if hasattr(self, "allow_replace_check"):
            self.allow_replace_check.blockSignals(True)
            self.allow_replace_check.setChecked(self._allow_replace)
            self.allow_replace_check.blockSignals(False)
        if hasattr(self, "acknowledgement_check"):
            self.acknowledgement_check.blockSignals(True)
            self.acknowledgement_check.setChecked(self._acknowledged)
            self.acknowledgement_check.blockSignals(False)
        if hasattr(self, "confirmation_check"):
            self.confirmation_check.blockSignals(True)
            self.confirmation_check.setChecked(self._confirmed)
            self.confirmation_check.blockSignals(False)

    def _invalidate_dry_run(self, *, clear: bool = False) -> None:
        self._generation += 1
        self._dry_run_generation = None
        if clear:
            self._last_dry_run = {}

    def _dry_run_is_fresh(self) -> bool:
        return (
            bool(self._last_dry_run)
            and self._dry_run_generation == self._generation
            and str(self._last_dry_run.get("status", "")) == "planned"
            and bool(self._last_dry_run.get("planned", False))
            and not _sequence(self._last_dry_run.get("blockers"))
        )

    def _write_gate_blocker(self) -> Mapping[str, object] | None:
        target_display = self._target_display
        if not self._target_path:
            return _blocked_result(
                code=_NO_TARGET,
                message="Explicit target path is required before write.",
                target_display=target_display,
                dry_run=False,
            )
        if not self._last_dry_run:
            return _blocked_result(
                code=_DRY_RUN_REQUIRED,
                message="A successful dry-run is required before write.",
                target_display=target_display,
                dry_run=False,
            )
        if not self._dry_run_is_fresh():
            return _blocked_result(
                code=_STALE_DRY_RUN,
                message="Dry-run is stale after target or view-model change.",
                target_display=target_display,
                dry_run=False,
            )
        if not self._acknowledged:
            return _blocked_result(
                code=_ACK_REQUIRED,
                message="Explicit acknowledgement is required before write.",
                target_display=target_display,
                dry_run=False,
            )
        if not self._confirmed:
            return _blocked_result(
                code=_CONFIRM_REQUIRED,
                message="Explicit confirmation is required before write.",
                target_display=target_display,
                dry_run=False,
            )
        return None

    def _build_request(
        self,
        *,
        dry_run: bool,
        acknowledged: bool,
    ) -> ReloadAcceptancePersistenceWriteRequest:
        return ReloadAcceptancePersistenceWriteRequest(
            persistence_viewmodel=self._view_model,
            target_path=self._target_path,
            dry_run=dry_run,
            allow_replace=self._allow_replace,
            caller_acknowledged_persistence_write=acknowledged,
            expected_payload_kind=RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND,
            expected_schema_version=RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION,
            safety_review_id="osw-exp-132-gui-write",
            request_context="gui_explicit_target_dry_run_first_write",
        )

    def _writer(self) -> object:
        source = self._writer_source
        if source is None:
            return OptionalSolverPluginManifestReloadAcceptancePersistenceWriter()
        if hasattr(source, "write"):
            return source
        if callable(source):
            writer = source()
            if hasattr(writer, "write"):
                return writer
        raise TypeError("Writer dependency must provide a write(request) method.")


def _blocked_result(
    *,
    code: str,
    message: str,
    target_display: str,
    dry_run: bool,
) -> dict[str, object]:
    return {
        "status": "blocked",
        "target_display": target_display,
        "target_redacted": bool(target_display),
        "dry_run": dry_run,
        "planned": False,
        "written": False,
        "bytes_count": 0,
        "sha256": "",
        "payload_kind": RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND,
        "payload_schema_version": RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION,
        "diagnostics": (
            {
                "severity": "error",
                "code": code,
                "message": message,
                "section": "gui_write",
                "blocker": True,
                "suggested_fix": "Satisfy explicit GUI write gates.",
            },
        ),
        "blockers": (code,),
        "warnings": (),
        "non_action_flags": _safe_non_action_flags(False),
        "payload": {},
        "write_performed": False,
        "persistence_write_performed": False,
        "runtime_reload_acceptance_performed": False,
        "project_schema_mutated": False,
    }


def _safe_non_action_flags(persistence_write_performed: bool) -> dict[str, bool]:
    flags = {flag: False for flag in _NON_ACTION_FLAGS}
    flags["persistence_write_performed"] = bool(persistence_write_performed)
    return flags


def _object_to_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    return {}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    if value is None:
        return ()
    return (value,)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _redacted_target(value: str) -> str:
    text = value.replace("\\", "/").strip()
    if not text:
        return ""
    if "://" in text:
        return "<redacted-external-url>"
    leaf = text.rstrip("/").rsplit("/", 1)[-1]
    return leaf or "<redacted-target>"


__all__ = [
    "OptionalSolverPluginManifestReloadAcceptancePersistenceWritePanel",
]
