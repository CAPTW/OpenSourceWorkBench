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
    / "optional_solver_plugin_manifest_reload_panel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_gui_implementation.md"
)
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_gui_design.md"
)
VIEWMODEL_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_viewmodel.md"
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


def test_module_import_lazy_export_and_initial_unavailable_view() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_panel import (
            OptionalSolverPluginManifestReloadPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        assert PackagePanel is OptionalSolverPluginManifestReloadPanel
        panel = OptionalSolverPluginManifestReloadPanel()

        assert panel.objectName() == "oswOptionalSolverPluginManifestReloadPanel"
        assert panel.windowTitle() == "Optional Solver Plugin Manifest Reload"
        assert "state=no_reload_request" in panel.summary_text()
        assert "readiness=unavailable_no_payload" in panel.summary_text()
        assert "reload_is_validation_evidence=False" in panel.summary_text()
        assert "reload_is_validation_failure=False" in panel.summary_text()
        assert "reload_restores_trust=False" in panel.summary_text()
        assert "reload_automatically_activates=False" in panel.summary_text()
        assert "reload_runs_discovery=False" in panel.summary_text()
        assert "reload_runs_validation=False" in panel.summary_text()
        assert "reload_executes_solver=False" in panel.summary_text()
        assert "reload_mutates_project_schema=False" in panel.summary_text()
        assert "reload_closes_issue=False" in panel.summary_text()
        assert "reload_mutates_release=False" in panel.summary_text()
        assert "reload_certifies_manifest=False" in panel.summary_text()
        assert panel.source_rows_text() == "No reload sources."
        assert panel.candidate_rows_text() == "No reload candidates."
        assert "OSPMG_RELOAD_TARGET_REQUIRED" in panel.diagnostics_text()
        assert "No file dialog." in panel.safety_text()
        assert "No file reader/parser." in panel.safety_text()
        assert "No runtime reload." in panel.safety_text()
        assert "No automatic activation." in panel.safety_text()
        assert "No trust restoration." in panel.safety_text()
        assert "No ProjectSchema mutation." in panel.safety_text()
        assert "No validation execution." in panel.safety_text()
        assert "No solver execution." in panel.safety_text()
        assert "No certification claim." in panel.safety_text()
        assert "User-selected and plugin-provided manifests are untrusted" in (
            panel.trust_text()
        )
        assert "Trust label is not certification." in panel.trust_text()
        assert panel.available_action_names() == []
        reasons = panel.disabled_action_reasons()
        for action in (
            "read_reload_file",
            "parse_reload_file",
            "migrate_schema",
            "accept_reload_as_trusted",
            "activate_reloaded_candidate",
            "refresh_discovery",
            "validate_solver",
            "execute_solver",
            "install_dependency",
            "uninstall_dependency",
            "uninstall_solver",
            "mutate_project_schema",
            "close_issue",
            "mutate_release",
            "push_tag",
            "upload_asset",
            "claim_validation_success_failure",
            "claim_certification",
        ):
            assert action in reasons
            assert action in panel.action_state_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_ready_view_model_sections_refresh_and_no_file_creation(tmp_path: Path) -> None:
    scratch = str(tmp_path).replace("\\", "/")
    _run_gui_script(
        f"""
        from PySide6 import QtWidgets
        from pathlib import Path
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestReloadViewModel as VM,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_panel import (
            OptionalSolverPluginManifestReloadPanel as Panel,
        )

        scratch = {scratch!r}
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        before = sorted(child.name for child in Path(scratch).iterdir())
        vm = VM.sample_ready_for_review()
        original = vm.to_mapping()
        panel = Panel(view_model=vm)

        assert "state=reload_preview_ready" in panel.summary_text()
        assert "readiness=ready_review_only" in panel.summary_text()
        assert "payload_kind=optional_solver_plugin_manifest_state_writer_state" in (
            panel.summary_text()
        )
        assert "sample-source | user_selected_state | sample.json | yes" in (
            panel.source_rows_text()
        )
        assert "untrusted_user_source" in panel.source_rows_text()
        assert "trust_label_is_certification=no" not in panel.source_rows_text()
        assert "sample-candidate | Sample optional solver" in (
            panel.candidate_rows_text()
        )
        assert "inactive | review_only" in panel.candidate_rows_text()
        assert "reload_not_validation" in panel.acknowledgement_rows_text()
        assert "persisted_acknowledgements_may_expire" in (
            panel.acknowledgement_rows_text()
        )
        assert "reload, source_fingerprint_change, schema_version_change" in (
            panel.acknowledgement_rows_text()
        )
        assert "supported_schema=yes" not in panel.schema_migration_rows_text()
        assert "optional_solver_plugin_manifest_state_writer_state" in (
            panel.schema_migration_rows_text()
        )
        assert "raw_paths_hidden_by_default" not in panel.redaction_rows_text()
        assert "yes | no | yes | no | no | yes | yes" in panel.redaction_rows_text()
        assert panel.stale_source_rows_text() == "No stale-source rows."
        assert panel.conflict_rows_text() == "No conflict rows."
        assert panel.unsafe_claim_rows_text() == "No unsafe-claim rows."
        assert "sample-history | sample-candidate | deactivation_history" in (
            panel.evidence_history_rows_text()
        )
        for code in (
            "OSPMG_RELOAD_NOT_VALIDATION",
            "OSPMG_RELOAD_NOT_TRUST_RESTORE",
            "OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION",
            "OSPMG_RELOAD_NO_DISCOVERY_EXECUTION",
            "OSPMG_RELOAD_NO_PLUGIN_IMPORT",
            "OSPMG_RELOAD_NO_VALIDATION_EXECUTION",
            "OSPMG_RELOAD_NO_SOLVER_EXECUTION",
            "OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED",
        ):
            assert code in panel.diagnostics_text()
        assert "read_reload_file | no | yes" in panel.action_state_text()
        assert "parse_reload_file | no | yes" in panel.action_state_text()
        assert "activate_reloaded_candidate | no | yes" in panel.action_state_text()
        assert "claim_certification | no | yes" in panel.action_state_text()
        assert "sources: 1 item(s)" in panel.redacted_summary_text()
        assert "actions: 24 item(s)" in panel.redacted_summary_text()

        refreshed = VM.unavailable("second supplied view-model")
        panel.set_view_model(refreshed)
        assert "readiness=unavailable_no_payload" in panel.summary_text()
        assert "second supplied view-model" in panel.diagnostics_text()
        assert vm.to_mapping() == original
        after = sorted(child.name for child in Path(scratch).iterdir())
        assert after == before

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_blockers_conflicts_unsafe_claims_evidence_and_trust_render() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers import (
            OSPMG_RELOAD_ACK_EXPIRED,
            OSPMG_RELOAD_ACK_REQUIRED,
            OSPMG_RELOAD_CONFLICT_VISIBLE,
            OSPMG_RELOAD_REDACTION_REQUIRED,
            OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED,
            OSPMG_RELOAD_SCHEMA_UNSUPPORTED,
            OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED,
            OSPMG_RELOAD_SHARED_STACK_VISIBLE,
            OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED,
            OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED,
            OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED,
            RELOAD_REQUIRED_ACKS,
            STATE_WRITER_PAYLOAD_KIND,
            STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
            build_optional_solver_plugin_manifest_reload_viewmodel as build,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_panel import (
            OptionalSolverPluginManifestReloadPanel as Panel,
        )

        def acks():
            return [
                {
                    "acknowledgement_id": ack,
                    "satisfied": True,
                    "expired": False,
                    "expiry_reasons": [
                        "reload",
                        "source_fingerprint_change",
                        "schema_version_change",
                        "unsafe_claim_appearance",
                        "trust_policy_change",
                        "future_discovery_refresh_result",
                    ],
                }
                for ack in RELOAD_REQUIRED_ACKS
            ]

        def payload(**overrides):
            base = {
                "payload_kind": STATE_WRITER_PAYLOAD_KIND,
                "payload_schema_version": STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
                "writer_version": "osw-exp-102",
                "sources": [
                    {
                        "source_id": "built-in",
                        "source_type": "built_in",
                        "source_reference_display": "builtin",
                        "trust_label": "built_in_authoritative",
                    },
                    {
                        "source_id": "plugin",
                        "source_type": "plugin",
                        "source_reference_display": "plugin.json",
                        "trust_label": "untrusted_plugin_manifest",
                    },
                ],
                "candidates": [
                    {
                        "candidate_id": "active",
                        "display_name": "Active candidate",
                        "lifecycle_state": "active",
                        "validation_state": "skipped_missing",
                    },
                    {
                        "candidate_id": "deactivated",
                        "display_name": "Deactivated candidate",
                        "lifecycle_state": "deactivated",
                    },
                    {
                        "candidate_id": "reactivation",
                        "display_name": "Reactivation candidate",
                        "lifecycle_state": "reactivation",
                    },
                    {
                        "candidate_id": "refresh",
                        "display_name": "Refresh candidate",
                        "lifecycle_state": "discovery_refresh",
                    },
                ],
                "acknowledgements": acks(),
                "redaction_privacy": [
                    {
                        "redaction_required": True,
                        "redaction_review_required": False,
                        "unredacted_path_blocked": False,
                        "secret_like_content_blocked": False,
                    }
                ],
                "evidence_history": [
                    {
                        "evidence_id": "history",
                        "candidate_id": "active",
                        "evidence_type": "reactivation_history",
                        "skipped_missing_remains_skipped_missing": True,
                    }
                ],
            }
            base.update(overrides)
            return base

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

        unsupported = Panel(view_model=build(payload(payload_schema_version="old")))
        assert "blocked_schema_unsupported" in unsupported.summary_text()
        assert OSPMG_RELOAD_SCHEMA_UNSUPPORTED in unsupported.diagnostics_text()

        migration = Panel(view_model=build(payload(schema_migration_required=True)))
        assert "blocked_schema_migration_required" in migration.summary_text()
        assert OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED in migration.diagnostics_text()

        redaction = Panel(view_model=build(payload(redaction_privacy=[{
            "redaction_review_required": True,
            "unredacted_path_blocked": True,
            "secret_like_content_blocked": True,
        }])))
        assert "state=redaction_review_required" in redaction.summary_text()
        assert "readiness=blocked_secret_like_content" in redaction.summary_text()
        assert OSPMG_RELOAD_REDACTION_REQUIRED in redaction.diagnostics_text()
        assert OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED in redaction.diagnostics_text()
        assert OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED in redaction.diagnostics_text()
        assert "yes | yes | yes | yes | yes | yes | yes" in (
            redaction.redaction_rows_text()
        )

        missing_ack = Panel(view_model=build(payload(acknowledgements=acks()[1:])))
        assert "blocked_acknowledgement" in missing_ack.summary_text()
        assert OSPMG_RELOAD_ACK_REQUIRED in missing_ack.diagnostics_text()

        expired = acks()
        expired[0]["expired"] = True
        expired_ack = Panel(view_model=build(payload(acknowledgements=expired)))
        assert "blocked_acknowledgement" in expired_ack.summary_text()
        assert OSPMG_RELOAD_ACK_EXPIRED in expired_ack.diagnostics_text()

        stale = Panel(view_model=build(payload(stale_sources=[{
            "source_id": "plugin",
            "stale_source_state": "moved",
            "repreview_required": True,
        }])))
        assert "blocked_stale_source_repreview" in stale.summary_text()
        assert OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED in stale.diagnostics_text()
        assert "plugin | moved | yes | yes | yes | yes" in (
            stale.stale_source_rows_text()
        )

        conflict = Panel(view_model=build(payload(conflicts=[{
            "conflict_id": "conflict",
            "candidate_id": "active",
            "blocker": True,
        }])))
        assert "blocked_conflict" in conflict.summary_text()
        assert OSPMG_RELOAD_CONFLICT_VISIBLE in conflict.diagnostics_text()
        assert "conflict | active | conflict | yes | no" in conflict.conflict_rows_text()

        shared = Panel(view_model=build(payload(conflicts=[{
            "conflict_id": "shared",
            "shared_stack_warning_visible": True,
            "blocker": False,
        }])))
        assert "blocked_shared_stack_warning" in shared.summary_text()
        assert OSPMG_RELOAD_SHARED_STACK_VISIBLE in shared.diagnostics_text()
        assert "shared | none | conflict | yes | no | yes" in (
            shared.conflict_rows_text()
        )

        unsafe = Panel(view_model=build(payload(unsafe_claims=[{
            "claim_id": "validation_success",
            "claim_text": "validation success and certification claim",
        }])))
        assert "unsafe_claim_blocked" in unsafe.summary_text()
        assert OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED in unsafe.diagnostics_text()
        assert "validation_success" in unsafe.unsafe_claim_rows_text()
        assert "validation success and certification claim" in (
            unsafe.unsafe_claim_rows_text()
        )
        assert "yes | yes" in unsafe.unsafe_claim_rows_text()

        ready = Panel(view_model=build(payload()))
        assert "built-in | built_in | builtin" in ready.source_rows_text()
        assert "plugin | plugin | plugin.json" in ready.source_rows_text()
        assert "built_in_authoritative" in ready.source_rows_text()
        assert "untrusted_plugin_manifest" in ready.source_rows_text()
        assert "trust_label_is_certification=False" in ready.trust_text()
        candidates = ready.candidate_rows_text()
        assert "active | Active candidate" in candidates
        assert "future_activation_review_required | yes | no | yes | yes | yes" in (
            candidates
        )
        assert "deactivated_review_state" in candidates
        assert "reactivation | Reactivation candidate" in candidates
        assert "refresh | Refresh candidate" in candidates
        assert "future_discovery_refresh_required" in candidates
        assert "history | active | reactivation_history" in (
            ready.evidence_history_rows_text()
        )
        assert "yes | yes | yes | yes | yes | no | no" in (
            ready.evidence_history_rows_text()
        )

        for panel in (
            unsupported,
            migration,
            redaction,
            missing_ack,
            expired_ack,
            stale,
            conflict,
            shared,
            unsafe,
            ready,
        ):
            panel.close()
            panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_panel_source_keeps_side_effect_boundaries() -> None:
    source = _panel_source()
    forbidden_fragments = (
        "QFileDialog",
        "QClipboard",
        "QProcess",
        "subprocess",
        "webbrowser",
        "requests.",
        "urllib.",
        "httpx.",
        "osw.cli",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "plugin_manifest_discovery",
        "SolverAdapter",
        "ProjectSchema(",
        "pip install",
        "pip uninstall",
        "conda remove",
        "gh issue",
        "gh release",
        ".unlink(",
        ".rmdir(",
        "shutil.rmtree",
        ".write_text(",
        ".write_bytes(",
        "open(",
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
    assert not (
        imported_roots
        & {
            "os",
            "pathlib",
            "json",
            "shutil",
            "subprocess",
            "webbrowser",
            "requests",
            "urllib",
            "httpx",
        }
    )
    assert "OptionalSolverPluginManifestReloadViewModel" in source
    assert "No file dialog." in source
    assert "No file reader/parser." in source
    assert "No runtime reload." in source
    assert "No automatic activation." in source
    assert "No trust restoration." in source
    assert "No ProjectSchema mutation." in source


def test_docs_record_reload_gui_implementation_boundaries() -> None:
    implementation = IMPLEMENTATION_DOC.read_text(encoding="utf-8")
    design = DESIGN_DOC.read_text(encoding="utf-8")
    viewmodel = VIEWMODEL_DOC.read_text(encoding="utf-8")
    required = (
        "OptionalSolverPluginManifestReloadPanel",
        "read-only/review-only",
        "no file dialog",
        "no file reader/parser",
        "no runtime reload behavior",
        "no ProjectSchema mutation",
        "no discovery/validation/solver execution",
        "no automatic activation",
        "no trust restoration",
        "no CLI behavior",
        "no reloadable bundle creation",
        "no export/report file creation",
        "no clipboard behavior",
        "issues `#6` through `#11` remain open",
    )
    for phrase in required:
        assert phrase in implementation
    assert "OSW-EXP-109 implements" in design
    assert "OSW-EXP-109 adds" in viewmodel
