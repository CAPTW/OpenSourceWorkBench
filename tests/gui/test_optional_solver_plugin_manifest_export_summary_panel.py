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
    / "optional_solver_plugin_manifest_export_summary_panel.py"
)
VIEWMODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_export_summary_viewmodel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_export_summary_gui_implementation.md"
)
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_export_summary_gui_design.md"
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


def test_module_import_and_initial_unavailable_view() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestExportSummaryPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_export_summary_panel import (
            OptionalSolverPluginManifestExportSummaryPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        assert PackagePanel is OptionalSolverPluginManifestExportSummaryPanel
        panel = OptionalSolverPluginManifestExportSummaryPanel()

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestExportSummaryPanel"
        )
        assert panel.windowTitle() == (
            "Optional Solver Plugin Manifest Export Summary"
        )
        assert "readiness=unavailable_no_state" in panel.summary_text()
        assert "state=export_summary_unavailable" in panel.summary_text()
        assert "export_performed=False" in panel.summary_text()
        assert "file_write_performed=False" in panel.summary_text()
        assert "export_file_created=False" in panel.summary_text()
        assert "clipboard_performed=False" in panel.summary_text()
        assert "report_attachment_performed=False" in panel.summary_text()
        assert "reloadable_bundle_created=False" in panel.summary_text()
        assert "persistence_performed=False" in panel.summary_text()
        assert "settings_file_created=False" in panel.summary_text()
        assert "runtime_state_file_created=False" in panel.summary_text()
        assert "schema_file_created=False" in panel.summary_text()
        assert "project_schema_mutation_performed=False" in panel.summary_text()
        assert "cli_behavior_added=False" in panel.summary_text()
        assert "reload_behavior_added=False" in panel.summary_text()
        assert "validation_success_claimed=False" in panel.summary_text()
        assert "validation_failure_claimed=False" in panel.summary_text()
        assert "issue_closure_claimed=False" in panel.summary_text()
        assert "certification_claimed=False" in panel.summary_text()
        assert "file_dialog_behavior=False" in panel.summary_text()
        assert "save_dialog_behavior=False" in panel.summary_text()
        assert "open_output_folder_behavior=False" in panel.summary_text()

        assert "header | Export Summary" in panel.section_rows_text()
        assert panel.source_rows_text() == "No export-summary sources."
        assert panel.candidate_rows_text() == "No export-summary candidates."
        assert "export_not_validation" in panel.acknowledgement_rows_text()
        assert "OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED" in panel.diagnostics_text()
        assert "OSPMG_EXPORT_SUMMARY_GUI_" not in panel.diagnostics_text()
        assert "User-selected and plugin-provided manifests are untrusted" in (
            panel.trust_text()
        )
        assert "Export summary is not validation evidence." in panel.safety_text()
        assert "No file export." in panel.safety_text()
        assert "No file writes." in panel.safety_text()
        assert "No clipboard behavior." in panel.safety_text()
        assert "No report attachment." in panel.safety_text()
        assert "No reloadable bundle creation." in panel.safety_text()
        assert "No ProjectSchema mutation." in panel.safety_text()
        assert "No discovery execution." in panel.safety_text()
        assert "No validation execution." in panel.safety_text()
        assert "No solver execution." in panel.safety_text()

        assert panel.available_action_names() == []
        reasons = panel.disabled_action_reasons()
        for action in (
            "write_export_file",
            "copy_to_clipboard",
            "attach_to_report",
            "create_reloadable_bundle",
            "persist_state",
            "mutate_project_schema",
            "reload_state",
            "run_discovery",
            "run_validation",
            "install_dependency",
            "uninstall_dependency",
            "uninstall_solver",
            "execute_solver",
            "close_issue",
            "mutate_release",
            "push_tag",
            "upload_asset",
        ):
            assert action in reasons
            assert "disabled" in panel.action_state_text()
        assert "display-only" in panel.action_state_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_rendering_of_export_summary_records_and_policies() -> None:
    _run_gui_script(
        """
        from types import SimpleNamespace as N

        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_export_summary_viewmodel import (
            EXPORT_SUMMARY_REQUIRED_ACKS,
            OptionalSolverPluginManifestExportSummaryCandidateRow as CandidateRow,
            OptionalSolverPluginManifestExportSummarySourceRow as SourceRow,
            OptionalSolverPluginManifestExportSummaryViewModel as VM,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_export_summary_panel import (
            OptionalSolverPluginManifestExportSummaryPanel as Panel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {ack: True for ack in EXPORT_SUMMARY_REQUIRED_ACKS}
        vm = VM.from_records(
            sources=[
                N(
                    source_id="builtin",
                    source_type="built_in",
                    source_label="Built-in manifest",
                    source_reference_display="builtin source",
                    trust_label="built_in",
                    built_in_authoritative=True,
                    source_fingerprint_display="sha256:builtin",
                ),
                N(
                    source_id="plugin",
                    source_type="plugin_provided_manifest",
                    source_label="Plugin manifest",
                    source_reference="C:/Users/example/plugin.json",
                    trust_label="untrusted_plugin_manifest",
                    persisted_state_kind="preview",
                    stale_source_state="stale",
                    repreview_required=True,
                    raw_reference_blocked=True,
                    secret_like_content_blocked=True,
                    diagnostics=(
                        "OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED",
                    ),
                ),
            ],
            candidates=[
                N(
                    stack_id="builtin",
                    display_name="Built-in solver",
                    source_id="builtin",
                    source_type="built_in",
                    trust_label="built_in",
                    activation_state="active_builtin",
                    deactivation_state="retained",
                    reactivation_state="not_requested",
                    discovery_refresh_state="not_run",
                    persistence_state="not_persisted",
                    export_summary_state="ready_preview_only",
                    historical_evidence_state="skipped_missing",
                    built_in_authoritative=True,
                ),
                N(
                    stack_id="plugin",
                    display_name="Plugin solver",
                    source_id="plugin",
                    source_type="plugin_provided_manifest",
                    trust_label="untrusted_plugin_manifest",
                    activation_state="inactive_preview",
                    deactivation_state="deactivated_by_user",
                    reactivation_state="reactivation_requested",
                    discovery_refresh_state="not_run",
                    persistence_state="not_persisted",
                    export_summary_state="blocked_conflict",
                    stale_source_state="stale",
                    repreview_required=True,
                    redaction_status="review_required",
                    shared_stack_indicators=("built-in duplicate",),
                    deactivation_history_state="deactivated_by_user",
                    reactivation_history_state="requested",
                    historical_evidence_state="skipped_missing",
                    validation_evidence_state="not_validation_evidence",
                    source_reference_display="C:/Users/example/plugin.json",
                ),
            ],
            acknowledgements=allacks,
            redaction_rows=[
                N(
                    raw_reference_supplied=True,
                    display_reference="C:/Users/example/plugin.json",
                    redaction_status="review_required",
                    redaction_required=True,
                    unredacted_path_blocked=True,
                    redaction_reviewed=False,
                    secret_like_content_blocked=True,
                    privacy_warning="Raw local paths are blocked.",
                )
            ],
            stale_source_rows=[
                N(
                    stale_source_state="moved",
                    repreview_required=True,
                    source_reference_display="C:/Users/example/plugin.json",
                )
            ],
            conflicts=[
                N(
                    stack_id="plugin",
                    built_in_source_id="builtin",
                    user_or_plugin_source_id="plugin",
                    active_source_state="active_builtin",
                    deactivated_source_state="deactivated_by_user",
                    reactivation_source_state="requested",
                    persistence_state="not_persisted",
                    export_summary_state="conflict_visible",
                )
            ],
            unsafe_claims=[
                N(
                    claim_id="claim-1",
                    related_candidate_id="plugin",
                    related_source_id="plugin",
                    claim_text="validation-pass and certification claim",
                )
            ],
            evidence_history=[
                N(
                    stack_id="plugin",
                    deactivation_history_retained=True,
                    reactivation_history_retained=True,
                    historical_validation_evidence_retained=True,
                    skipped_missing_remains_skipped_missing=True,
                )
            ],
            limitations=[
                N(
                    limitation_id="lim-1",
                    title="Review only",
                    message="Export summary GUI is review-only.",
                    related_section="summary",
                    related_candidate_id="plugin",
                )
            ],
            summary_kind="session_summary",
            state_scope="session_only",
            generated_by_display="OSW test",
            schema_version_display="osw-exp-097-preview",
        )
        panel = Panel(view_model=vm)

        assert "summary_kind=session_summary" in panel.summary_text()
        assert "state_scope=session_only" in panel.summary_text()
        assert "generated_by=OSW test" in panel.summary_text()
        assert "schema_version=osw-exp-097-preview" in panel.summary_text()
        assert "sources=2" in panel.summary_text()
        assert "candidates=2" in panel.summary_text()
        assert "acknowledgements=15" in panel.summary_text()
        assert "conflicts=2" in panel.summary_text()
        assert "unsafe_claims=1" in panel.summary_text()
        assert "stale_sources=2" in panel.summary_text()
        assert "redaction_required=2" in panel.summary_text()
        assert "limitations=" in panel.summary_text()

        sections = panel.section_rows_text()
        for section in (
            "sources | Sources And Provenance",
            "candidates | Candidate State",
            "acknowledgements | Acknowledgements",
            "diagnostics | Diagnostics",
            "redaction | Redaction And Privacy",
            "stale_sources | Stale Sources And Re-Preview",
            "conflicts | Conflicts And Shared Stacks",
            "unsafe_claims | Unsafe Claims",
            "evidence_history | Evidence And History",
            "limitations | Limitations",
            "actions | Actions",
        ):
            assert section in sections

        sources = panel.source_rows_text()
        assert "builtin | built_in | Built-in manifest" in sources
        assert "plugin | plugin_provided_manifest | Plugin manifest" in sources
        assert "plugin.json" in sources
        assert "untrusted_plugin_manifest" in sources
        assert "yes | yes | yes" in sources
        assert "sha256:builtin" in sources

        candidates = panel.candidate_rows_text()
        assert "builtin | Built-in solver | builtin | built_in | built_in" in (
            candidates
        )
        assert "plugin | Plugin solver | plugin | plugin_provided_manifest" in (
            candidates
        )
        assert "inactive_preview" in candidates
        assert "deactivated_by_user" in candidates
        assert "reactivation_requested" in candidates
        assert "not_run" in candidates
        assert "not_persisted" in candidates
        assert "not_validation_evidence" in candidates
        assert "built-in duplicate" in candidates
        assert "skipped_missing" in candidates
        assert "no | no | no" in candidates

        acknowledgements = panel.acknowledgement_rows_text()
        for ack in (
            "export_not_validation",
            "export_not_persistence",
            "export_not_reloadable_bundle",
            "export_not_trust_restoration",
            "export_not_install",
            "export_no_solver_execution",
            "export_not_issue_closure",
            "export_not_release_mutation",
            "redaction_reviewed",
            "unredacted_paths_blocked",
            "stale_source_requires_repreview",
            "untrusted_source_remains_untrusted",
            "no_discovery_execution",
            "no_plugin_package_import",
            "trust_label_not_certification",
        ):
            assert ack in acknowledgements
        assert "yes | yes | no" in acknowledgements

        diagnostics = panel.diagnostics_text()
        for code in (
            "OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED",
            "OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED",
            "OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED",
            "OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM",
            "OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED",
            "OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED",
            "OSPMG_EXPORT_SUMMARY_NOT_VALIDATION",
            "OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION",
            "OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION",
            "OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT",
        ):
            assert code in diagnostics

        redaction = panel.redaction_rows_text()
        assert "plugin.json" in redaction
        assert "review_required" in redaction
        assert "yes | yes | no | yes" in redaction
        assert "Fingerprints are not trust signals." in panel.safety_text()

        stale = panel.stale_source_rows_text()
        assert "moved | yes | plugin.json | yes" in stale
        assert "old preview data is not silently trusted" in stale
        assert "no file IO performed" in stale
        assert "no file restoration performed" in stale
        assert "no file rewrite performed" in stale
        assert "no file deletion performed" in stale

        conflicts = panel.conflict_rows_text()
        assert "plugin | builtin | plugin" in conflicts
        assert "yes | yes | yes | yes" in conflicts

        unsafe = panel.unsafe_claim_rows_text()
        assert "claim-1 | plugin | plugin | validation-pass" in unsafe
        assert "yes | Unsafe claims are not accepted" in unsafe
        assert unsafe.endswith("no")

        evidence = panel.evidence_history_rows_text()
        assert "plugin | yes | yes | yes | yes | no | no | no | no | yes" in (
            evidence
        )

        limitations = panel.limitation_rows_text()
        assert "lim-1 | Review only | Export summary GUI is review-only." in (
            limitations
        )
        assert "yes" in limitations

        trust = panel.trust_text()
        assert "User-selected and plugin-provided manifests are untrusted" in trust
        assert "Built-in manifests are authoritative by default." in trust
        assert "Trust label is not certification." in trust
        assert "Export summary is not validation evidence." in trust
        assert "Export summary is not validation success." in trust
        assert "Export summary is not validation failure." in trust
        assert "Export summary is not persistence." in trust
        assert "Export summary is not a reloadable bundle." in trust
        assert "Export summary is not automatic activation." in trust
        assert "Export summary is not trust restoration." in trust

        non_actions = panel.non_action_flags_text()
        for flag in (
            "export_performed=False",
            "file_write_performed=False",
            "export_file_created=False",
            "clipboard_performed=False",
            "report_attachment_performed=False",
            "reloadable_bundle_created=False",
            "persistence_performed=False",
            "settings_file_created=False",
            "runtime_state_file_created=False",
            "schema_file_created=False",
            "project_schema_mutation_performed=False",
            "cli_behavior_added=False",
            "reload_behavior_added=False",
            "automatic_activation_performed=False",
            "trust_restoration_performed=False",
            "file_restoration_performed=False",
            "file_rewrite_performed=False",
            "file_deletion_performed=False",
            "dependency_installation_performed=False",
            "dependency_uninstall_performed=False",
            "solver_uninstall_performed=False",
            "plugin_package_import_performed=False",
            "directory_scan_performed=False",
            "network_fetch_performed=False",
            "discovery_execution_performed=False",
            "validation_execution_performed=False",
            "solver_execution_performed=False",
            "issue_mutation_performed=False",
            "release_mutation_performed=False",
            "tag_mutation_performed=False",
            "asset_mutation_performed=False",
            "version_bump_performed=False",
            "validation_success_claimed=False",
            "validation_failure_claimed=False",
            "issue_closure_claimed=False",
            "certification_claimed=False",
            "file_dialog_behavior=False",
            "save_dialog_behavior=False",
            "source_behavior_mutation=False",
        ):
            assert flag in non_actions

        redacted = panel.redacted_summary_text()
        assert "sources: 2 item(s)" in redacted
        assert "candidates: 2 item(s)" in redacted
        assert "non_action_flags.file_write_performed: False" in redacted
        assert "not_validation_evidence: True" in redacted

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_blocked_states_and_widget_local_acknowledgements() -> None:
    _run_gui_script(
        """
        from types import SimpleNamespace as N

        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_export_summary_viewmodel import (
            EXPORT_SUMMARY_REQUIRED_ACKS,
            OptionalSolverPluginManifestExportSummaryCandidateRow as CandidateRow,
            OptionalSolverPluginManifestExportSummarySourceRow as SourceRow,
            OptionalSolverPluginManifestExportSummaryViewModel as VM,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_export_summary_panel import (
            OptionalSolverPluginManifestExportSummaryPanel as Panel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

        def make_view_model(acks):
            return VM.from_records(
                sources=[
                    SourceRow(
                        source_id="ready-src",
                        source_type="built_in",
                        source_reference_display="ready manifest",
                        source_reference_redacted=False,
                        trust_label="built_in",
                    )
                ],
                candidates=[
                    CandidateRow(
                        stack_id="ready",
                        source_id="ready-src",
                        source_type="built_in",
                        source_reference_display="ready manifest",
                        source_reference_redacted=False,
                        trust_label="built_in",
                    )
                ],
                acknowledgements=acks,
                export_summary_requested=True,
            )

        blocked = Panel(view_model=make_view_model({}))
        assert "readiness=blocked_acknowledgement" in blocked.summary_text()
        assert "OSPMG_EXPORT_SUMMARY_ACK_REQUIRED" in blocked.diagnostics_text()
        assert "yes | no | no | yes" in blocked.acknowledgement_rows_text()

        callback_calls = []

        def callback(acks):
            callback_calls.append(dict(acks))
            return make_view_model(acks)

        panel = Panel(view_model=make_view_model({}), acknowledgement_callback=callback)
        assert "acknowledge_export_not_validation" in panel.available_action_names()
        assert "widget-local; non-persistent" in panel.action_state_text()
        panel.apply_acknowledgement("export_not_validation")
        assert panel.acknowledgement_state()["export_not_validation"] is True
        assert callback_calls[-1]["export_not_validation"] is True
        for acknowledgement_id in EXPORT_SUMMARY_REQUIRED_ACKS:
            panel.apply_acknowledgement(acknowledgement_id)
        assert "readiness=ready_preview_only" in panel.summary_text()
        assert "export_performed=False" in panel.summary_text()
        assert "file_write_performed=False" in panel.non_action_flags_text()

        display_only = Panel(view_model=make_view_model({}))
        display_only.apply_acknowledgement("export_not_validation")
        assert display_only.acknowledgement_state() == {}
        assert display_only.available_action_names() == []
        assert "display-only" in display_only.action_state_text()

        redaction = Panel(
            view_model=VM.redaction_required("C:/Users/example/token-secret.json")
        )
        assert "blocked_unredacted_path" in redaction.summary_text()
        assert "secret-like" in redaction.redaction_rows_text()
        assert "OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED" in (
            redaction.diagnostics_text()
        )

        stale_acks = {ack: True for ack in EXPORT_SUMMARY_REQUIRED_ACKS}
        stale_acks["stale_source_requires_repreview"] = False
        stale = Panel(
            view_model=VM.from_records(
                sources=[
                    SourceRow(
                        source_id="stale-source",
                        source_reference_display="stale manifest",
                        source_reference_redacted=False,
                        stale_source_state="stale",
                        repreview_required=True,
                    )
                ],
                acknowledgements=stale_acks,
                export_summary_requested=True,
            )
        )
        assert "blocked_stale_source_repreview" in stale.summary_text()
        assert "old preview data is not silently trusted" in (
            stale.stale_source_rows_text()
        )
        assert "no file IO performed" in stale.stale_source_rows_text()

        unsafe = Panel(view_model=VM.unsafe_claim_blocked(
            claim_text="claim validation success"
        ))
        assert "blocked_unsafe_claim" in unsafe.summary_text()
        assert "claim validation success" in unsafe.unsafe_claim_rows_text()
        assert "no" in unsafe.unsafe_claim_rows_text()

        for item in (blocked, panel, display_only, redaction, stale, unsafe):
            item.close()
            item.deleteLater()
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
        "QFileDialog",
        "QClipboard",
        "setClipboard",
        "webbrowser",
        "requests.",
        "urllib.",
        "httpx.",
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
    assert "OptionalSolverPluginManifestExportSummaryViewModel" in source
    assert "No file export." in source
    assert "No file writes." in source
    assert "No clipboard behavior." in source
    assert "No report attachment." in source
    assert "No reloadable bundle creation." in source
    assert "No ProjectSchema mutation." in source


def test_export_summary_viewmodel_remains_qt_free() -> None:
    source = VIEWMODEL_SOURCE.read_text(encoding="utf-8")
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


def test_docs_record_implementation_and_non_action_boundaries() -> None:
    implementation = IMPLEMENTATION_DOC.read_text(encoding="utf-8")
    design = DESIGN_DOC.read_text(encoding="utf-8")
    required = (
        "OptionalSolverPluginManifestExportSummaryPanel",
        "view-model driven",
        "widget-local and non-persistent",
        "no file export",
        "no file writes",
        "no export file creation",
        "no report file creation",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no reloadable bundle creation",
        "no runtime persistence behavior",
        "no settings file creation",
        "no runtime state file creation",
        "no schema file creation",
        "no ProjectSchema mutation",
        "no CLI behavior",
        "no reload behavior",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "issues `#6` through `#11` remain open",
    )
    for phrase in required:
        assert phrase in implementation
    assert "OSW-EXP-099 implements" in design
    assert "OSPMG_EXPORT_SUMMARY_GUI_" in design
