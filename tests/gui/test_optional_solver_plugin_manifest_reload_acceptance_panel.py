from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "gui"
    / "dialogs"
    / "optional_solver_plugin_manifest_reload_acceptance_panel.py"
)

PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None


def _panel_source() -> str:
    return PANEL_SOURCE.read_text(encoding="utf-8")


def _run_gui_script(script: str) -> str:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    pythonpath = str(REPO_ROOT / "src")
    if env.get("PYTHONPATH"):
        pythonpath = pythonpath + os.pathsep + env["PYTHONPATH"]
    env["PYTHONPATH"] = pythonpath
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_lazy_export_inert_construction_and_initial_guidance() -> None:
    _run_gui_script(
        """
        import builtins
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadAcceptancePanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_panel import (
            OptionalSolverPluginManifestReloadAcceptancePanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        original_open = builtins.open

        def blocked_open(*args, **kwargs):
            raise AssertionError("panel construction attempted file IO")

        builtins.open = blocked_open
        try:
            assert PackagePanel is OptionalSolverPluginManifestReloadAcceptancePanel
            panel = OptionalSolverPluginManifestReloadAcceptancePanel()
        finally:
            builtins.open = original_open

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestReloadAcceptancePanel"
        )
        assert panel.windowTitle() == (
            "Optional Solver Plugin Manifest Reload Acceptance"
        )
        assert "state=no_preview" in panel.summary_text()
        assert "readiness=unavailable_no_preview" in panel.summary_text()
        assert "no_validation=yes" in panel.summary_text()
        assert "no_validation_failure=yes" in panel.summary_text()
        assert "no_project_schema_mutation=yes" in panel.summary_text()
        assert "no_persistence_write=yes" in panel.summary_text()
        assert "no_activation=yes" in panel.summary_text()
        assert "no_trust_restoration=yes" in panel.summary_text()
        assert "no_discovery=yes" in panel.summary_text()
        assert "no_solver_execution=yes" in panel.summary_text()
        assert "no_issue_release_mutation=yes" in panel.summary_text()
        assert "no_certification=yes" in panel.summary_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING" in panel.diagnostics_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING" in panel.blocker_rows_text()
        assert panel.available_action_names() == []

        for action in (
            "request_acceptance",
            "accept_for_session_review",
            "accept_as_trusted",
            "activate_reloaded_candidate",
            "refresh_discovery",
            "validate_solver",
            "execute_solver",
            "install_dependency",
            "uninstall_dependency",
            "uninstall_solver",
            "mutate_project_schema",
            "persist_state",
            "create_export_summary",
            "create_report_file",
            "create_reloadable_bundle",
            "copy_to_clipboard",
            "attach_to_report",
            "open_output_folder",
            "close_issue",
            "mutate_release",
            "push_tag",
            "upload_asset",
            "claim_validation_success",
            "claim_validation_failure",
            "claim_certification",
        ):
            assert action in panel.disabled_action_reasons()
            assert action in panel.action_state_text()

        safety = panel.safety_text()
        assert "Preview success is not acceptance." in safety
        assert "File selection is not acceptance." in safety
        assert "Panel construction is not acceptance." in safety
        assert "Acceptance readiness is not validation evidence." in safety
        assert "Acceptance readiness is not validation failure." in safety
        assert "Accepted state is not trust restoration." in safety
        assert "Accepted state is not automatic activation." in safety
        assert "Accepted state is not ProjectSchema state." in safety
        assert "Accepted state is not persistence." in safety
        assert "Accepted state does not close issues or mutate releases." in safety
        assert "Trust label is not certification." in safety
        assert "No persisted state file access." in safety
        assert "No reader call." in safety
        assert "No CLI bridge." in safety
        assert "Issues #6 through #11 remain open." in safety

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_ready_and_accepted_states_render_without_outputs(tmp_path: Path) -> None:
    scratch = str(tmp_path).replace("\\", "/")
    _run_gui_script(
        f"""
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel import (
            OptionalSolverPluginManifestReloadAcceptanceViewModel as AcceptanceVM,
            RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS,
            RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        )
        from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
            OptionalSolverPluginManifestReloadViewModel as ReloadVM,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_panel import (
            OptionalSolverPluginManifestReloadAcceptancePanel as Panel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        scratch = Path({scratch!r})
        before = sorted(child.name for child in scratch.iterdir())
        reload_vm = ReloadVM.sample_ready_for_review()
        original = reload_vm.to_mapping()
        ready_vm = AcceptanceVM.from_reload_viewmodel(
            reload_vm,
            requested=True,
            acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        )
        panel = Panel(view_model=ready_vm)

        assert "state=ready_for_future_acceptance" in panel.summary_text()
        assert "readiness=ready_future_only" in panel.summary_text()
        assert "ready_future_only=yes" in panel.summary_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_READY" in panel.diagnostics_text()
        assert "sample-source" in panel.provenance_text()
        assert "untrusted_user_source" in panel.provenance_text()
        assert "payload_kind_required | yes" in panel.schema_migration_text()
        assert "schema_mismatch_is_validation_failure | no" in (
            panel.schema_migration_text()
        )
        assert "raw_paths_hidden_by_default | yes" in panel.redaction_privacy_text()
        assert "persisted_active | future_activation_review_required" in (
            panel.candidate_lifecycle_text()
        )
        assert "skipped_missing_remains_skipped_missing" in (
            panel.candidate_lifecycle_text()
        )
        assert "implemented_reload_acceptance | no | safe false boundary" in (
            panel.non_action_flags_text()
        )
        assert "runtime_reload_acceptance_performed | no" in (
            panel.non_action_flags_text()
        )
        assert "validation_executed | no" in panel.non_action_flags_text()
        assert "solver_executed | no" in panel.non_action_flags_text()
        assert "candidate_activated | no" in panel.non_action_flags_text()
        assert "trust_restored | no" in panel.non_action_flags_text()
        assert "issue_mutated | no" in panel.non_action_flags_text()
        assert "release_mutated | no" in panel.non_action_flags_text()
        assert "certification_claimed | no" in panel.non_action_flags_text()

        ack_text = panel.acknowledgement_rows_text()
        for ack in RELOAD_ACCEPTANCE_REQUIRED_ACKS:
            assert ack in ack_text
        expiry_text = panel.expiry_rows_text()
        for reason in RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS:
            assert reason in expiry_text

        accepted_vm = AcceptanceVM.accepted_for_session_review(reload_vm)
        panel.set_view_model(accepted_vm)
        accepted = panel.accepted_state_text()
        assert "accepted-for-session-review" in accepted
        assert "yes | session_review_only | yes | no | no | no | no | no" in (
            accepted
        )
        assert "accepted_for_session_review=yes" in panel.summary_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW" in (
            panel.diagnostics_text()
        )
        assert reload_vm.to_mapping() == original
        after = sorted(child.name for child in scratch.iterdir())
        assert after == before

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_blocker_diagnostics_and_future_review_requirements_render() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel import (
            OptionalSolverPluginManifestReloadAcceptanceViewModel as AcceptanceVM,
            RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        )
        from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
            OptionalSolverPluginManifestReloadViewModel as ReloadVM,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_panel import (
            OptionalSolverPluginManifestReloadAcceptancePanel as Panel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        reload_vm = ReloadVM.sample_ready_for_review()

        def panel_for(**kwargs):
            vm = AcceptanceVM.from_reload_viewmodel(
                reload_vm,
                requested=True,
                acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
                **kwargs,
            )
            return Panel(view_model=vm)

        missing_ack = Panel(
            view_model=AcceptanceVM.from_reload_viewmodel(
                reload_vm,
                requested=True,
                acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS[:-1],
            )
        )
        assert "blocked_acknowledgement" in missing_ack.summary_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED" in (
            missing_ack.diagnostics_text()
        )

        reader_blocked = panel_for(reader_diagnostics=("reader-blocker",))
        assert "blocked_reader" in reader_blocked.summary_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED" in (
            reader_blocked.blocker_rows_text()
        )

        viewmodel_blocked = Panel(
            view_model=AcceptanceVM.from_reload_viewmodel(
                ReloadVM.blocked(diagnostics=("OSPMG_RELOAD_CUSTOM_BLOCKER",)),
                requested=True,
                acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
            )
        )
        assert "blocked_viewmodel" in viewmodel_blocked.summary_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED" in (
            viewmodel_blocked.diagnostics_text()
        )

        policy_expectations = {
            "stale_source_requires_repreview": (
                "OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED",
                "blocked_stale_source_repreview",
                "Stale sources require re-preview",
            ),
            "conflict_review_required": (
                "OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED",
                "blocked_conflict_review",
                "Conflicts and shared-stack warnings",
            ),
            "shared_stack_review_required": (
                "OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED",
                "blocked_shared_stack_review",
                "Conflicts and shared-stack warnings",
            ),
            "unsafe_claim_blocked": (
                "OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED",
                "blocked_unsafe_claim",
                "Unsafe validation, issue, release",
            ),
            "unsupported_schema": (
                "OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED",
                "blocked_schema_unsupported",
                "unsupported_schema_blocks | yes",
            ),
            "migration_required": (
                "OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED",
                "blocked_migration_required",
                "migration_required_blocks | yes",
            ),
            "unredacted_path_blocked": (
                "OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED",
                "blocked_unredacted_path",
                "unredacted_path_blocked | yes",
            ),
            "secret_like_value_blocked": (
                "OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED",
                "blocked_secret_like_value",
                "secret_like_value_blocked | yes",
            ),
            "trust_policy_changed": (
                "OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED",
                "blocked_policy_change",
                "OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED",
            ),
            "source_fingerprint_changed": (
                "OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED",
                "blocked_policy_change",
                "OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED",
            ),
            "policy_changed": (
                "OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED",
                "blocked_policy_change",
                "OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED",
            ),
        }
        panels = [missing_ack, reader_blocked, viewmodel_blocked]
        for flag, (code, readiness, section_phrase) in policy_expectations.items():
            panel = panel_for(policy_flags={flag: True})
            panels.append(panel)
            assert readiness in panel.summary_text()
            assert code in panel.diagnostics_text()
            assert code in panel.blocker_rows_text()
            assert section_phrase in panel.rendered_text()

        future = panel_for(
            policy_flags={
                "future_activation_review_required": True,
                "future_discovery_refresh_required": True,
            }
        )
        panels.append(future)
        assert "OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED" in (
            future.diagnostics_text()
        )
        assert "OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED" in (
            future.diagnostics_text()
        )
        assert "future_activation_review_required=yes" in future.summary_text()
        assert "future_discovery_refresh_required=yes" in future.summary_text()

        for panel in panels:
            panel.close()
            panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_redacts_raw_paths_and_secret_like_strings_from_rendered_text() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel import (
            OptionalSolverPluginManifestReloadAcceptanceViewModel as AcceptanceVM,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_acceptance_panel import (
            OptionalSolverPluginManifestReloadAcceptancePanel as Panel,
        )

        class SuppliedViewModel:
            def __init__(self, mapping):
                self._mapping = mapping

            def to_mapping(self):
                return self._mapping

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        mapping = AcceptanceVM.unavailable().to_mapping()
        mapping["source_provenance"] = [
            {
                "source_id": "local-source",
                "source_display": r"C:\\Users\\USER\\private\\payload.json",
                "source_reference_redacted": True,
                "provenance_label": "caller_supplied_payload",
                "trust_label": "untrusted_user_source",
                "source_fingerprint_changed": False,
                "user_plugin_sources_untrusted_by_default": True,
                "built_ins_authoritative_by_default": False,
                "trust_label_is_certification": False,
            }
        ]
        mapping["diagnostics"] = [
            {
                "severity": "error",
                "code": "OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED",
                "message": "token=sk-test-value",
                "blocker": True,
                "related": r"C:\\Users\\USER\\private\\payload.json",
                "suggested_fix": "Remove token=sk-test-value",
            }
        ]
        panel = Panel(view_model=SuppliedViewModel(mapping))
        rendered = panel.rendered_text()
        assert "C:\\\\Users\\\\USER" not in rendered
        assert "private" not in rendered
        assert "sk-test-value" not in rendered
        assert "token=sk-test-value" not in rendered
        assert "payload.json" in rendered
        assert "<redacted-secret>" in rendered
        assert "trust label is not certification" in rendered.lower()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_panel_source_keeps_no_side_effect_boundaries() -> None:
    source = _panel_source()
    forbidden_fragments = (
        "QFileDialog",
        "QClipboard",
        "QProcess",
        "subprocess",
        "osw.cli",
        "plugin_manifest_reload_file_reader",
        "read_optional_solver_plugin_manifest_reload_file",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "plugin_manifest_discovery",
        "ProjectSchema(",
        "SolverAdapter",
        "requests.",
        "urllib.",
        "httpx.",
        ".write_text(",
        ".write_bytes(",
        ".unlink(",
        ".rmdir(",
        "shutil.rmtree",
        "mkdir(",
        "pip install",
        "pip uninstall",
        "conda remove",
        "gh issue",
        "gh release",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    forbidden_imports = {
        "os",
        "pathlib",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "shutil",
        "webbrowser",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
