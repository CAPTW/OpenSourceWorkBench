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
    / "optional_solver_plugin_manifest_persistence_panel.py"
)
VIEWMODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_persistence_viewmodel.py"
)
SCHEMA_MODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_persistence_schema_model.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_persistence_gui_implementation.md"
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


def test_module_import_equivalence_and_empty_state() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestPersistencePanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_persistence_panel import (
            OptionalSolverPluginManifestPersistencePanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        assert PackagePanel is OptionalSolverPluginManifestPersistencePanel
        panel = OptionalSolverPluginManifestPersistencePanel()

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestPersistencePanel"
        )
        assert panel.windowTitle() == (
            "Optional Solver Plugin Manifest Persistence"
        )
        assert "readiness=unavailable_no_state" in panel.summary_text()
        assert "state=persistence_unavailable" in panel.summary_text()
        assert panel.source_rows_text() == "No persistence sources."
        assert panel.candidate_rows_text() == "No persistence candidates."
        assert "OSPMG_PERSISTENCE_NOT_IMPLEMENTED" in panel.diagnostics_text()
        assert "No persistence schema model supplied." in panel.schema_model_text()

        for flag in (
            "persistence_performed=False",
            "file_write_performed=False",
            "settings_file_created=False",
            "runtime_state_file_created=False",
            "schema_file_created=False",
            "project_schema_mutation_performed=False",
            "file_dialog_behavior=False",
            "save_dialog_behavior=False",
            "reload_performed=False",
            "export_performed=False",
            "clipboard_behavior=False",
            "open_output_folder_behavior=False",
            "cli_behavior=False",
            "plugin_package_import_performed=False",
            "directory_scan_performed=False",
            "network_fetch_performed=False",
            "discovery_execution_performed=False",
            "validation_execution_performed=False",
            "solver_execution_performed=False",
            "issue_mutation_performed=False",
            "release_mutation_performed=False",
            "validation_pass_claimed=False",
            "validation_fail_claimed=False",
            "certification_claimed=False",
        ):
            assert flag in panel.summary_text()
            assert flag in panel.non_action_flags_text()

        assert panel.available_action_names() == []
        reasons = panel.disabled_action_reasons()
        assert reasons["save_state"]
        assert reasons["create_settings_file"]
        assert reasons["mutate_project_schema"]
        assert reasons["reload_state"]
        assert reasons["export_summary"]
        assert reasons["run_discovery"]
        assert reasons["run_validation"]
        assert reasons["execute_solver"]
        assert "No runtime persistence behavior." in panel.safety_text()
        assert "No file dialog behavior." in panel.safety_text()
        assert "No open-output-folder behavior." in panel.safety_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_rendering_of_all_sections_and_schema_model_records() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_persistence_panel import (
            OptionalSolverPluginManifestPersistencePanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestPersistenceCandidateInput as C,
            OptionalSolverPluginManifestPersistenceConflictInput as Conflict,
            OptionalSolverPluginManifestPersistenceEvidenceInput as Evidence,
            OptionalSolverPluginManifestPersistenceSchemaInput as Schema,
            OptionalSolverPluginManifestPersistenceSchemaModel,
            OptionalSolverPluginManifestPersistenceSourceInput as Source,
            OptionalSolverPluginManifestPersistenceUnsafeClaimInput as UnsafeClaim,
            build_optional_solver_plugin_manifest_persistence_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel import (
            PERSISTENCE_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {ack: True for ack in PERSISTENCE_REQUIRED_ACKS}
        vm = build(
            [
                C(
                    stack_id="gmsh",
                    source_id="src-gmsh",
                    source_reference="C:/Users/example/gmsh.json",
                    persistence_requested=True,
                    activation_state="active_candidate",
                    deactivation_state="deactivated",
                    reactivation_state="reactivation_requested",
                    discovery_refresh_state="included",
                    deactivation_history_state="deactivated_by_user",
                    reactivation_history_state="requested",
                    historical_evidence_state="skipped_missing",
                ),
                C(
                    stack_id="conflict",
                    source_id="src-conflict",
                    source_reference="C:/Users/example/conflict.json",
                    has_conflict=True,
                    has_shared_stack=True,
                    shared_stack_indicators=("built-in duplicate",),
                    persistence_requested=True,
                ),
                C(
                    stack_id="unsafe",
                    source_id="src-unsafe",
                    source_reference="C:/Users/example/unsafe.json",
                    has_unsafe_claim=True,
                    unsafe_claim_indicators=("certification claim",),
                    persistence_requested=True,
                ),
            ],
            sources=[
                Source(
                    source_id="src-gmsh",
                    source_reference="C:/Users/example/gmsh.json",
                    source_fingerprint_display="sha256:1234",
                    warnings=("caller warning",),
                ),
                Source(
                    source_id="src-conflict",
                    source_reference="C:/Users/example/conflict.json",
                ),
                Source(
                    source_id="src-unsafe",
                    source_reference="C:/Users/example/unsafe.json",
                ),
            ],
            acknowledgements=allacks,
            persistence_requested=True,
            schema=Schema(
                schema_version_display="osw-exp-093-schema-1",
                schema_version_present=True,
            ),
            conflicts=[
                Conflict(
                    stack_id="conflict",
                    built_in_source="builtin",
                    user_plugin_source="plugin",
                    activation_state="active_candidate",
                    persistence_state="persistence_blocked",
                )
            ],
            unsafe_claims=[
                UnsafeClaim(
                    claim_id="claim-1",
                    related="unsafe",
                    claim_text="claims certification",
                )
            ],
            evidence_history=[
                Evidence(
                    stack_id="gmsh",
                    deactivation_history_state="deactivated_by_user",
                    reactivation_history_state="requested",
                    historical_evidence_state="skipped_missing",
                )
            ],
        )
        schema_model = (
            OptionalSolverPluginManifestPersistenceSchemaModel
            .from_persistence_viewmodel(vm)
        )
        panel = Panel(view_model=vm, schema_model=schema_model)

        assert "readiness=blocked_conflict" in panel.summary_text()
        assert "state=persistence_blocked" in panel.summary_text()
        assert "candidates=3" in panel.summary_text()
        assert "sources=3" in panel.summary_text()
        assert "conflicts=2" in panel.summary_text()
        assert "unsafe_claims=2" in panel.summary_text()
        assert "persistence_ready=1" in panel.summary_text()
        assert "persistence_blocked=2" in panel.summary_text()

        sources = panel.source_rows_text()
        assert "src-gmsh" in sources
        assert "gmsh.json" in sources
        assert "sha256:1234" in sources
        assert "caller warning" in sources
        gmsh_source_line = [
            line for line in sources.split(chr(10)) if line.startswith("src-gmsh | ")
        ][0]
        reference_cell = gmsh_source_line.split(" | ")[3]
        assert "/" not in reference_cell and chr(92) not in reference_cell

        candidates = panel.candidate_rows_text()
        assert "gmsh" in candidates and "ready_preview_only" in candidates
        assert "conflict" in candidates and "blocked_conflict" in candidates
        assert "unsafe" in candidates and "blocked_unsafe_claim" in candidates
        assert "persistence_not_validation" in candidates
        assert "OSPMG_PERSISTENCE_CONFLICT_BLOCKED" in candidates
        assert "OSPMG_PERSISTENCE_UNSAFE_CLAIM" in candidates
        assert "skipped_missing" in candidates

        acknowledgements = panel.acknowledgement_rows_text()
        assert "persistence_not_validation" in acknowledgements
        assert "persisted_acknowledgements_may_expire" in acknowledgements
        assert "activation_review_required_after_reload" in acknowledgements
        assert "trust_label_not_certification" in acknowledgements
        assert "yes | yes | no | yes | yes | yes | yes" in acknowledgements

        diagnostics = panel.diagnostics_text()
        for code in (
            "OSPMG_PERSISTENCE_CONFLICT_BLOCKED",
            "OSPMG_PERSISTENCE_UNSAFE_CLAIM",
            "OSPMG_PERSISTENCE_NOT_VALIDATION",
            "OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION",
            "OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION",
            "OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT",
            "OSPMG_PERSISTENCE_FUTURE_GATE",
        ):
            assert code in diagnostics

        redaction = panel.redaction_rows_text()
        assert "gmsh.json" in redaction
        assert "Raw local paths and secret-like content" in redaction
        assert "Source references are redacted by default" in redaction

        schema = panel.schema_migration_rows_text()
        assert "osw-exp-093-schema-1" in schema
        assert "yes | no | not_required" in schema
        assert schema.endswith("no")

        schema_text = panel.schema_model_text()
        assert "schema_model_schema_version=osw-exp-093-schema-1" in schema_text
        assert "schema_model_source_count=3" in schema_text
        assert "schema_model_candidate_count=3" in schema_text
        assert "schema_model_non_action_flags_all_false=True" in (
            panel.non_action_flags_text()
        )
        assert "this_gate_creates_schema_file=False" in schema_text
        assert "not_validation_evidence=True" in schema_text

        conflicts = panel.conflict_rows_text()
        assert "conflict" in conflicts
        assert "Persisted user/plugin state does not override built-ins silently" in (
            conflicts
        )
        assert "Conflicts remain visible after reload" in conflicts

        unsafe = panel.unsafe_claim_rows_text()
        assert "claim-1" in unsafe
        assert "claims certification" in unsafe
        assert "Unsafe claims are not accepted by persistence" in unsafe

        evidence = panel.evidence_history_rows_text()
        assert "gmsh" in evidence
        assert "Persisted state is not validation success" in evidence
        assert "Persisted state is not validation failure" in evidence
        assert "Skipped-missing optional validation remains skipped-missing" in evidence
        assert "Evidence is not deleted or rewritten" in evidence

        trust = panel.trust_text()
        assert (
            "User-selected and plugin-provided manifests are untrusted by default"
            in trust
        )
        assert "Built-in manifests are authoritative by default" in trust
        assert "Trust label is not certification" in trust
        assert "Persisted state is not validation evidence" in trust
        assert "Persistence is not trust restoration" in trust

        summary = panel.redacted_summary_text()
        assert "candidates: 3 item(s)" in summary
        assert "sources: 3 item(s)" in summary
        assert "file_write_performed: False" in summary
        assert "not_validation_evidence: True" in summary

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_blocked_states_for_redaction_schema_stale_conflicts_and_unsafe_claims() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_persistence_panel import (
            OptionalSolverPluginManifestPersistencePanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestPersistenceCandidateInput as C,
            OptionalSolverPluginManifestPersistenceSchemaInput as Schema,
            build_optional_solver_plugin_manifest_persistence_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel import (
            PERSISTENCE_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {ack: True for ack in PERSISTENCE_REQUIRED_ACKS}
        schema = Schema(
            schema_version_display="osw-exp-093-schema-1",
            schema_version_present=True,
        )

        redaction = Panel(view_model=build(
            [C(
                stack_id="raw",
                source_reference="C:/secrets/raw.json",
                raw_reference_supplied=True,
                unredacted_path_supplied=True,
                secret_like_content_blocked=True,
                persistence_requested=True,
            )],
            acknowledgements=allacks,
            persistence_requested=True,
            schema=schema,
        ))
        assert "readiness=blocked_unredacted_path" in redaction.summary_text()
        assert "OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED" in (
            redaction.diagnostics_text()
        )
        assert "yes | raw.json | redacted | yes | no | yes" in (
            redaction.redaction_rows_text()
        )

        missing_schema = Panel(view_model=build(
            [C(stack_id="schema", source_reference="schema.json",
               persistence_requested=True)],
            acknowledgements=allacks,
            persistence_requested=True,
        ))
        assert "readiness=blocked_schema_version" in missing_schema.summary_text()
        assert "OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED" in (
            missing_schema.diagnostics_text()
        )
        assert "not supplied | no | no | not_required" in (
            missing_schema.schema_migration_rows_text()
        )

        migration = Panel(view_model=build(
            [C(stack_id="migration", source_reference="migration.json",
               persistence_requested=True)],
            acknowledgements=allacks,
            persistence_requested=True,
            schema=Schema(
                schema_version_display="old-schema",
                schema_version_present=True,
                migration_required=True,
                migration_status="required",
                migration_notes_display="upgrade required",
            ),
        ))
        assert "readiness=blocked_schema_migration" in migration.summary_text()
        assert "OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED" in (
            migration.diagnostics_text()
        )
        assert "old-schema | yes | yes | required | upgrade required" in (
            migration.schema_migration_rows_text()
        )

        stale = Panel(view_model=build(
            [C(
                stack_id="stale",
                source_reference="C:/Users/example/stale.json",
                stale_source=True,
                stale_source_state="moved",
                repreview_required=True,
                persistence_requested=True,
            )],
            acknowledgements=allacks,
            persistence_requested=True,
            schema=schema,
        ))
        assert "stale_sources=2" in stale.summary_text()
        assert "blocked_stale_source_repreview" in stale.candidate_rows_text()
        assert "OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED" in (
            stale.diagnostics_text()
        )
        assert "moved | yes | stale.json | yes" in stale.stale_source_rows_text()
        assert "not silently trusted" in stale.stale_source_rows_text()

        conflict = Panel(view_model=build(
            [C(stack_id="conflict", has_conflict=True,
               source_reference="conflict.json", persistence_requested=True)],
            acknowledgements=allacks,
            persistence_requested=True,
            schema=schema,
        ))
        assert "readiness=blocked_conflict" in conflict.summary_text()
        assert "yes | Persisted user/plugin state does not override built-ins" in (
            conflict.conflict_rows_text()
        )

        unsafe = Panel(view_model=build(
            [C(stack_id="unsafe", has_unsafe_claim=True,
               unsafe_claim_indicators=("validation-pass claim",),
               source_reference="unsafe.json", persistence_requested=True)],
            acknowledgements=allacks,
            persistence_requested=True,
            schema=schema,
        ))
        assert "readiness=blocked_unsafe_claim" in unsafe.summary_text()
        assert "validation-pass claim" in unsafe.unsafe_claim_rows_text()
        assert "Unsafe claims are not accepted by persistence" in (
            unsafe.unsafe_claim_rows_text()
        )

        for panel in (redaction, missing_schema, migration, stale, conflict, unsafe):
            panel.close()
            panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_acknowledgement_callback_is_widget_local_and_non_persistent() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_persistence_panel import (
            OptionalSolverPluginManifestPersistencePanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestPersistenceCandidateInput as C,
            OptionalSolverPluginManifestPersistenceSchemaInput as Schema,
            build_optional_solver_plugin_manifest_persistence_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel import (
            PERSISTENCE_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        schema = Schema(
            schema_version_display="osw-exp-093-schema-1",
            schema_version_present=True,
        )

        def make_view_model(acks):
            return build(
                [
                    C(
                        stack_id="ready",
                        source_reference="C:/Users/example/ready.json",
                        persistence_requested=True,
                    )
                ],
                acknowledgements=acks,
                persistence_requested=True,
                schema=schema,
            )

        callback_calls = []

        def callback(acks):
            callback_calls.append(dict(acks))
            return make_view_model(acks)

        panel = Panel(view_model=make_view_model({}), acknowledgement_callback=callback)
        assert "readiness=blocked_acknowledgement" in panel.summary_text()
        assert "acknowledge_persistence_not_validation" in (
            panel.available_action_names()
        )
        assert "widget-local; non-persistent" in panel.action_state_text()
        panel.apply_acknowledgement("persistence_not_validation")
        assert panel.acknowledgement_state()["persistence_not_validation"] is True
        assert callback_calls[-1]["persistence_not_validation"] is True
        for acknowledgement_id in PERSISTENCE_REQUIRED_ACKS:
            panel.apply_acknowledgement(acknowledgement_id)
        assert "readiness=ready_preview_only" in panel.summary_text()
        assert "persistence_performed=False" in panel.summary_text()
        assert "file_write_performed=False" in panel.non_action_flags_text()

        display_only = Panel(view_model=make_view_model({}))
        display_only.apply_acknowledgement("persistence_not_validation")
        assert display_only.acknowledgement_state() == {}
        assert display_only.available_action_names() == []
        assert "display-only" in display_only.action_state_text()

        panel.close()
        display_only.close()
        panel.deleteLater()
        display_only.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_panel_source_keeps_side_effect_boundaries() -> None:
    source = _panel_source()
    forbidden_fragments = (
        "QProcess",
        "subprocess",
        "os.system",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
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
        "QFileDialog",
        "QClipboard",
        "setClipboard",
        "webbrowser",
        "requests.",
        "urllib.",
        "httpx.",
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
            "shutil",
            "subprocess",
            "webbrowser",
            "requests",
            "urllib",
            "httpx",
        }
    )
    assert "OptionalSolverPluginManifestPersistenceViewModel" in source
    assert "OptionalSolverPluginManifestPersistenceSchemaModel" in source
    assert "No file dialog behavior." in source
    assert "No save dialog behavior." in source
    assert "No reload behavior." in source
    assert "No export behavior." in source


def test_viewmodel_and_schema_model_remain_qt_free() -> None:
    for path in (VIEWMODEL_SOURCE, SCHEMA_MODEL_SOURCE):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(name.startswith("PySide6") for name in imported)
        assert "QtWidgets" not in source
        assert "QtCore" not in source
        assert "QDialog" not in source


def test_implementation_doc_records_non_action_boundaries() -> None:
    text = IMPLEMENTATION_DOC.read_text(encoding="utf-8")
    required = (
        "OptionalSolverPluginManifestPersistencePanel",
        "view-model/schema-model driven",
        "widget-local and non-persistent",
        "no runtime persistence behavior",
        "no file writes",
        "no settings file creation",
        "no runtime state file creation",
        "no schema file creation",
        "no ProjectSchema mutation",
        "no file dialog",
        "no save dialog",
        "no reload behavior",
        "no export behavior",
        "no clipboard behavior",
        "no open-output-folder behavior",
        "no CLI behavior",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "issues `#6` through `#11` remain open",
    )
    for phrase in required:
        assert phrase in text
