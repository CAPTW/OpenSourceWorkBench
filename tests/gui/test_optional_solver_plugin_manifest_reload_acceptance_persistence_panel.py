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
    / "optional_solver_plugin_manifest_reload_acceptance_persistence_panel.py"
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


def test_lazy_export_inert_construction_and_unavailable_guidance() -> None:
    _run_gui_script(
        """
        import builtins
        from importlib import import_module
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadAcceptancePersistencePanel
            as PackagePanel,
        )
        module = import_module(
            "osw.gui.dialogs."
            "optional_solver_plugin_manifest_reload_acceptance_persistence_panel"
        )
        Panel = module.OptionalSolverPluginManifestReloadAcceptancePersistencePanel

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        original_open = builtins.open

        def blocked_open(*args, **kwargs):
            raise AssertionError("panel construction attempted file IO")

        builtins.open = blocked_open
        try:
            assert PackagePanel is Panel
            panel = Panel()
        finally:
            builtins.open = original_open

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestReloadAcceptancePersistencePanel"
        )
        assert panel.windowTitle() == (
            "Optional Solver Plugin Manifest Reload Acceptance Persistence Review"
        )
        assert "state=no_acceptance_viewmodel" in panel.summary_text()
        assert "readiness=acceptance_missing" in panel.summary_text()
        assert "persistence_requested=no" in panel.summary_text()
        assert "no_runtime_acceptance=yes" in panel.summary_text()
        assert "no_project_schema_mutation=yes" in panel.summary_text()
        assert "no_validation_evidence=yes" in panel.summary_text()
        assert "no_validation_failure=yes" in panel.summary_text()
        assert "no_activation=yes" in panel.summary_text()
        assert "no_trust_restoration=yes" in panel.summary_text()
        assert "no_issue_release_mutation=yes" in panel.summary_text()
        assert "no_certification=yes" in panel.summary_text()
        assert "writer_result | not_supplied" in panel.writer_result_text()
        assert panel.available_action_names() == []
        assert "choose_target" in panel.disabled_action_reasons()
        assert "write_persistence_record" in panel.action_state_text()
        assert "persist_acceptance_record" in panel.action_state_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_UNAVAILABLE" in (
            panel.diagnostics_text()
        )
        assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_GUI_DRY_RUN_NOT_WRITE" in (
            panel.diagnostics_text()
        )

        safety = panel.safety_text()
        assert "Display-only persistence GUI review panel." in safety
        assert "Panel construction is not runtime reload acceptance." in safety
        assert "Refresh is not runtime reload acceptance." in safety
        assert "Dry-run is not write." in safety
        assert "Dry-run success is not validation success." in safety
        assert "Dry-run success is not validation failure." in safety
        assert "Writer result display is not runtime acceptance." in safety
        assert "Persisted review record is not validation evidence." in safety
        assert "Persisted review record is not validation failure." in safety
        assert "Persisted review record is not ProjectSchema mutation." in safety
        assert "Persisted review record is not trust restoration." in safety
        assert "Persisted review record is not automatic activation." in safety
        assert "does not close issues or mutate releases" in safety
        assert "Trust label is not certification." in safety
        assert "Issues #6 through #11 remain open." in safety
        assert "No target chooser is exposed." in safety
        assert "No writer bridge is exposed." in safety
        assert "No CLI bridge or external process use." in safety
        assert "No reload file reader bridge." in safety

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_ready_viewmodel_and_supplied_writer_mapping_render_all_core_sections(
    tmp_path: Path,
) -> None:
    scratch = str(tmp_path).replace("\\", "/")
    _run_gui_script(
        f"""
        from importlib import import_module
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadAcceptancePersistencePanel as Panel,
        )
        persistence_module = import_module(
            "osw.experimental.optional_solvers."
            "plugin_manifest_reload_acceptance_persistence_viewmodel"
        )
        acceptance_module = import_module(
            "osw.experimental.optional_solvers."
            "plugin_manifest_reload_acceptance_viewmodel"
        )
        reload_module = import_module(
            "osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel"
        )
        PersistenceVM = (
            persistence_module
            .OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
        )
        AcceptanceVM = (
            acceptance_module.OptionalSolverPluginManifestReloadAcceptanceViewModel
        )
        ReloadVM = reload_module.OptionalSolverPluginManifestReloadViewModel
        RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS = (
            persistence_module.RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS
        )
        RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS = (
            persistence_module.RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        scratch = Path({scratch!r})
        before = sorted(child.name for child in scratch.iterdir())
        acceptance = AcceptanceVM.ready_for_future_acceptance(
            ReloadVM.sample_ready_for_review()
        )
        view_model = PersistenceVM.ready_for_future_writer(acceptance)
        original_mapping = view_model.to_mapping()
        writer_mapping = {{
            "status": "planned",
            "target_display": r"C:\\Users\\USER\\private\\reload-state.json",
            "target_redacted": True,
            "dry_run": True,
            "planned": True,
            "written": False,
            "bytes_count": 1234,
            "sha256": "abc123",
            "payload_kind": "optional_solver_reload_acceptance_persistence_record",
            "payload_schema_version": "osw-exp-126-writer",
            "diagnostics": [
                {{
                    "severity": "info",
                    "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED",
                    "message": "dry-run plan only",
                    "section": "writer",
                    "blocker": False,
                    "suggested_fix": "",
                }}
            ],
            "warnings": ["token=sk-secret-value"],
            "blockers": [],
            "non_action_flags": {{
                "persistence_write_performed": False,
                "runtime_reload_acceptance_performed": False,
                "project_schema_mutated": False,
                "validation_executed": False,
                "solver_executed": False,
                "candidate_activated": False,
                "trust_restored": False,
                "issue_mutated": False,
                "release_mutated": False,
                "certification_claimed": False,
            }},
            "write_performed": False,
            "persistence_write_performed": False,
            "runtime_reload_acceptance_performed": False,
            "project_schema_mutated": False,
            "cleanup_performed": False,
            "temp_file_left_behind": False,
            "temp_file_used": False,
            "atomic_replace_performed": False,
        }}
        panel = Panel(view_model=view_model, writer_mapping=writer_mapping)
        rendered = panel.rendered_text()

        assert "state=persistence_ready_future_only" in panel.summary_text()
        assert "readiness=writer_future_only" in panel.summary_text()
        assert "dry_run_plan_state=supplied_writer_result_dry_run_plan" in (
            panel.summary_text()
        )
        assert "ready_for_future_write_plan=yes" in panel.summary_text()
        assert "redacted_target_display | reload-state.json" in (
            panel.target_storage_text()
        )
        assert "C:\\\\Users\\\\USER" not in rendered
        assert "private" not in rendered
        assert "token=sk-secret-value" not in rendered
        assert "<redacted-secret>" in rendered
        assert "dry_run | yes | Dry-run review is not a file write." in (
            panel.dry_run_write_plan_text()
        )
        assert "planned | yes" in panel.writer_result_text()
        assert "written | no" in panel.writer_result_text()
        assert "bytes_count | 1234" in panel.writer_result_text()
        assert "sha256 | abc123" in panel.writer_result_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED" in (
            panel.diagnostics_text()
        )

        ack_text = panel.acknowledgement_rows_text()
        for ack in RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS:
            assert ack in ack_text
        expiry_text = panel.expiry_rows_text()
        for reason in RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS:
            assert reason in expiry_text

        assert "schema_mismatch | no | Schema mismatch is not validation failure." in (
            panel.schema_migration_text()
        )
        assert "separate_from_project_schema | yes" in (
            panel.schema_migration_text()
        )
        assert "raw_paths_hidden_by_default | yes" in panel.redaction_privacy_text()
        assert "full_file_content_displayed | no" in panel.redaction_privacy_text()
        assert "sample-source | sample.json | supplied_acceptance_viewmodel" in (
            panel.provenance_text()
        )
        assert "persisted_active | future_activation_review_required" in (
            panel.candidate_lifecycle_text()
        )
        assert "gui_inspects_referenced_source_files | no" in (
            panel.stale_source_text()
        )
        assert "built_ins_win_by_default | yes" in panel.conflict_text()
        assert "validation_success_claims_blocked | yes" in (
            panel.unsafe_claim_text()
        )
        assert "sample-history | deactivation_history | yes | yes | yes | no" in (
            panel.evidence_history_text()
        )
        assert "runtime_reload_acceptance_performed | no" in (
            panel.non_action_flags_text()
        )
        assert "project_schema_mutated | no" in panel.non_action_flags_text()
        assert "validation_executed | no" in panel.non_action_flags_text()
        assert "solver_executed | no" in panel.non_action_flags_text()
        assert "issue_mutated | no" in panel.non_action_flags_text()
        assert "release_mutated | no" in panel.non_action_flags_text()
        assert "certification_claimed | no" in panel.non_action_flags_text()
        assert "write_persistence_record" in panel.action_state_text()
        assert "claim_certification" in panel.action_state_text()
        assert view_model.to_mapping() == original_mapping
        assert sorted(child.name for child in scratch.iterdir()) == before

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_setters_refresh_without_mutating_or_creating_outputs(tmp_path: Path) -> None:
    scratch = str(tmp_path).replace("\\", "/")
    _run_gui_script(
        f"""
        from importlib import import_module
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadAcceptancePersistencePanel as Panel,
        )
        persistence_module = import_module(
            "osw.experimental.optional_solvers."
            "plugin_manifest_reload_acceptance_persistence_viewmodel"
        )
        acceptance_module = import_module(
            "osw.experimental.optional_solvers."
            "plugin_manifest_reload_acceptance_viewmodel"
        )
        reload_module = import_module(
            "osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel"
        )
        PersistenceVM = (
            persistence_module
            .OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
        )
        AcceptanceVM = (
            acceptance_module.OptionalSolverPluginManifestReloadAcceptanceViewModel
        )
        ReloadVM = reload_module.OptionalSolverPluginManifestReloadViewModel

        class SuppliedWriterResult:
            def __init__(self):
                self.calls = 0

            def to_mapping(self):
                self.calls += 1
                return {{
                    "status": "planned",
                    "target_display": "reload-state.json",
                    "dry_run": True,
                    "planned": True,
                    "written": False,
                    "bytes_count": 99,
                    "sha256": "def456",
                    "diagnostics": [],
                    "warnings": [],
                    "blockers": [],
                    "non_action_flags": {{}},
                }}

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        scratch = Path({scratch!r})
        before = sorted(child.name for child in scratch.iterdir())
        panel = Panel()
        acceptance = AcceptanceVM.ready_for_future_acceptance(
            ReloadVM.sample_ready_for_review()
        )
        view_model = PersistenceVM.ready_for_future_writer(acceptance)
        original = view_model.to_mapping()
        result = SuppliedWriterResult()
        panel.set_view_model(view_model)
        panel.set_writer_result(result)
        panel.refresh()
        assert result.calls == 1
        assert "bytes_count | 99" in panel.writer_result_text()
        assert "sha256 | def456" in panel.writer_result_text()
        assert "state=persistence_ready_future_only" in panel.summary_text()
        assert view_model.to_mapping() == original
        assert sorted(child.name for child in scratch.iterdir()) == before

        panel.set_writer_mapping(None)
        assert "writer_result | not_supplied" in panel.writer_result_text()
        assert sorted(child.name for child in scratch.iterdir()) == before

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_blocked_policy_diagnostics_render_across_review_sections() -> None:
    _run_gui_script(
        """
        from importlib import import_module
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadAcceptancePersistencePanel as Panel,
        )
        persistence_module = import_module(
            "osw.experimental.optional_solvers."
            "plugin_manifest_reload_acceptance_persistence_viewmodel"
        )
        acceptance_module = import_module(
            "osw.experimental.optional_solvers."
            "plugin_manifest_reload_acceptance_viewmodel"
        )
        reload_module = import_module(
            "osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel"
        )
        PersistenceVM = (
            persistence_module
            .OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
        )
        AcceptanceVM = (
            acceptance_module.OptionalSolverPluginManifestReloadAcceptanceViewModel
        )
        ReloadVM = reload_module.OptionalSolverPluginManifestReloadViewModel
        RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS = (
            persistence_module.RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        acceptance = AcceptanceVM.ready_for_future_acceptance(
            ReloadVM.sample_ready_for_review()
        )
        view_model = PersistenceVM.from_acceptance_viewmodel(
            acceptance,
            persistence_requested=True,
            acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
            storage_policy_id="explicit",
            target_display="state.json",
            dry_run_confirmed=True,
            policy_flags={
                "stale_source_requires_repreview": True,
                "conflict_review_required": True,
                "shared_stack_review_required": True,
                "unsafe_claim_blocked": True,
                "unredacted_path_blocked": True,
            },
        )
        panel = Panel(view_model=view_model)

        assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED" in (
            panel.diagnostics_text()
        )
        assert "missing_moved_changed_source_requires_repreview | yes" in (
            panel.stale_source_text()
        )
        assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED" in (
            panel.diagnostics_text()
        )
        assert "conflicts_visible | yes" in panel.conflict_text()
        assert "shared_stack_warnings_visible | yes" in panel.conflict_text()
        assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED" in (
            panel.diagnostics_text()
        )
        assert "unsafe_claims_visible | yes" in panel.unsafe_claim_text()
        assert "unredacted_path_blocked | yes" in panel.redaction_privacy_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_panel_source_keeps_display_only_boundaries() -> None:
    source = _panel_source()
    forbidden_fragments = (
        "QFileDialog",
        "QClipboard",
        "QProcess",
        "osw.cli",
        "plugin_manifest_reload_file_reader",
        "read_optional_solver_plugin_manifest_reload_file",
        "plugin_manifest_state_writer",
        "write_optional_solver_plugin_manifest_state",
        "plugin_manifest_reload_acceptance_persistence_writer",
        "OptionalSolverPluginManifestReloadAcceptancePersistenceWriter",
        "ProjectSchema(",
        "discover_optional_solver_manifests",
        "validate_optional_solver_manifest",
        "requests.",
        "urllib.",
        "httpx.",
        ".write_text(",
        ".write_bytes(",
        ".read_text(",
        ".read_bytes(",
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
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr.lower())

    assert imported_roots.isdisjoint(
        {
            "os",
            "pathlib",
            "subprocess",
            "requests",
            "urllib",
            "httpx",
            "shutil",
            "webbrowser",
            "socket",
        }
    )
    assert not any("cli" in module for module in imported_modules)
    assert not any("writer" in module for module in imported_modules)
    assert called_names.isdisjoint(
        {
            "open",
            "read",
            "write",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "glob",
            "iterdir",
            "listdir",
            "walk",
            "run",
            "popen",
            "discover_optional_solver_manifests",
            "validate_optional_solver_manifest",
            "execute_solver",
        }
    )


def test_no_output_files_are_created_by_gui_tests(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())
    _ = _panel_source()
    assert set(tmp_path.iterdir()) == before
