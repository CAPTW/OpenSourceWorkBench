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
    / "optional_solver_plugin_manifest_reactivation_panel.py"
)
VIEWMODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_reactivation_viewmodel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reactivation_gui_implementation.md"
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
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_module_import_equivalence_and_empty_state() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReactivationPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reactivation_panel import (
            OptionalSolverPluginManifestReactivationPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        assert PackagePanel is OptionalSolverPluginManifestReactivationPanel
        panel = OptionalSolverPluginManifestReactivationPanel()

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestReactivationPanel"
        )
        assert panel.windowTitle() == "Optional Solver Plugin Manifest Reactivation"
        assert "readiness=unavailable_no_deactivation_state" in panel.summary_text()
        assert panel.candidate_rows_text() == "No reactivation candidates."
        assert "OSPMG_REACTIVATION_DEACTIVATED_REQUIRED" in panel.diagnostics_text()
        for flag in (
            "reactivation_performed=False",
            "automatic_activation_performed=False",
            "trust_restoration_performed=False",
            "file_restore_performed=False",
            "file_rewrite_performed=False",
            "file_deletion_performed=False",
            "dependency_installation_performed=False",
            "dependency_uninstall_performed=False",
            "solver_uninstall_performed=False",
            "discovery_execution_performed=False",
            "validation_execution_performed=False",
            "solver_execution_performed=False",
            "issue_mutation_performed=False",
            "release_mutation_performed=False",
            "certification_claimed=False",
        ):
            assert flag in panel.summary_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_rendering_of_all_sections() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_reactivation_panel import (
            OptionalSolverPluginManifestReactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestReactivationCandidateInput as C,
            OptionalSolverPluginManifestReactivationViewModel as VM,
            build_optional_solver_plugin_manifest_reactivation_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_reactivation_viewmodel import (
            REACTIVATION_ALWAYS_REQUIRED_ACKS, ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in REACTIVATION_ALWAYS_REQUIRED_ACKS}

        rich = Panel(view_model=build(
            [
                C(stack_id="bi", source_type="built_in", trust_label="built_in",
                  is_untrusted=False, built_in=True,
                  built_in_relationship="built-in (authoritative by default)"),
                C(stack_id="good", source_reference="C:/users/x/good.json",
                  historical_evidence_state="skipped_missing"),
                C(stack_id="good2", source_reference="C:/users/x/good2.json"),
            ],
            acknowledgements=allacks,
        ))

        # Summary counts render (built-in excluded from the reactivation universe).
        s = rich.summary_text()
        assert "deactivated=2" in s
        assert "reactivation_candidates=2" in s
        assert "deactivation_history_retained=True" in s
        assert "evidence_retained=True" in s

        # Candidate rows render with redaction + states.
        cands = rich.candidate_rows_text()
        assert "good" in cands and "reactivation_ready" in cands
        good_line = [ln for ln in cands.split(chr(10)) if ln.startswith("good | ")][0]
        assert good_line.split(" | ")[4] == "good.json"  # redacted reference
        assert good_line.split(" | ")[19] == "yes"  # redacted flag

        # Acknowledgement rows render.
        art = rich.acknowledgement_rows_text()
        assert "reactivation_not_validation" in art
        assert "reactivation_requires_activation_review" in art

        # Diagnostics + OSPMG_REACTIVATION_* codes render.
        diags = rich.diagnostics_text()
        assert "OSPMG_REACTIVATION_HISTORY_RETAINED" in diags
        assert "OSPMG_REACTIVATION_REVIEW_REQUIRED" in diags
        assert "OSPMG_REACTIVATION_FUTURE_GATE" in diags
        assert "OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED" in diags

        # Evidence rows render with retention semantics.
        ev = rich.evidence_rows_text()
        assert "good" in ev
        assert "skipped-missing" in ev.lower()
        assert "not validation success" in ev.lower()
        assert "not validation failure reversal" in ev.lower()

        # Trust/provenance text.
        trust = rich.trust_text()
        assert "source_type=" in trust
        assert (
            "user-selected and plugin-provided manifests are untrusted by default"
            in trust.lower()
        )
        assert "built-in manifests are authoritative by default" in trust.lower()
        assert "trust label is not certification" in trust.lower()
        assert "a reactivation state is not validation evidence" in trust.lower()

        # Conflict rows + built-ins-win policy.
        conf = Panel(view_model=build(
            [C(stack_id="gmsh", has_conflict=True)], acknowledgements=allacks))
        assert "readiness=blocked_conflict" in conf.summary_text()
        cshared = conf.shared_stack_rows_text()
        assert "gmsh" in cshared
        assert "does not override built-ins" in cshared.lower()
        assert "OSPMG_REACTIVATION_CONFLICT_BLOCKED" in conf.diagnostics_text()

        # Stale-source/re-preview rows.
        stale = Panel(view_model=build(
            [C(stack_id="s", stale_source=True, source_reference="C:/x/m.json")],
            acknowledgements=allacks))
        assert "readiness=blocked_stale_source_repreview" in stale.summary_text()
        srows = stale.stale_source_rows_text()
        assert "s |" in srows
        assert "not silently trusted" in srows.lower()
        assert "no file io" in srows.lower()
        assert "no file restoration" in srows.lower()
        assert "OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED" in stale.diagnostics_text()

        # Blocked-acknowledgement view.
        blocked = Panel(view_model=build([C(stack_id="user")], acknowledgements={}))
        assert "readiness=blocked_acknowledgement" in blocked.summary_text()
        assert "OSPMG_REACTIVATION_ACK_REQUIRED" in blocked.diagnostics_text()
        assert "yes | no | yes" in blocked.acknowledgement_rows_text()

        # Future-activation-required view renders distinctly.
        future = Panel(view_model=VM.all_future_activation_required(
            [C(stack_id="user")], acknowledgements=allacks))
        assert "readiness=future_activation_required" in future.summary_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_ready_state_is_not_activation_trust_or_validation() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_reactivation_panel import (
            OptionalSolverPluginManifestReactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestReactivationCandidateInput as C,
            build_optional_solver_plugin_manifest_reactivation_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_reactivation_viewmodel import (
            REACTIVATION_ALWAYS_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in REACTIVATION_ALWAYS_REQUIRED_ACKS}
        ready = Panel(view_model=build(
            [C(stack_id="user", source_reference="C:/x/m.json")], acknowledgements=allacks))

        assert "readiness=ready_non_persistent" in ready.summary_text()
        assert "reactivation_performed=False" in ready.summary_text()
        safety = ready.safety_text()
        assert "Reactivation is not automatic activation." in safety
        assert "Reactivation is not trust restoration." in safety
        assert "Reactivation is not validation success." in safety
        assert "Reactivation is not validation failure reversal." in safety
        assert "Reactivation is not dependency installation." in safety
        assert "Reactivation is not solver execution." in safety
        assert "a reactivation state is not validation evidence" in ready.trust_text().lower()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_unsafe_actions_disabled_future_only() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_reactivation_panel import (
            OptionalSolverPluginManifestReactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestReactivationCandidateInput as C,
            build_optional_solver_plugin_manifest_reactivation_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_reactivation_viewmodel import (
            REACTIVATION_ALWAYS_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in REACTIVATION_ALWAYS_REQUIRED_ACKS}
        panel = Panel(view_model=build(
            [C(stack_id="user", source_reference="C:/x/m.json")], acknowledgements=allacks))

        action_text = panel.action_state_text()
        for name in (
            "run_discovery",
            "run_validation",
            "install_dependency",
            "uninstall_dependency",
            "uninstall_solver",
            "execute_solver",
            "close_issue",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "unavailable" in line and "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        # Reactivate/route/request remain future-only (disabled) — no auto-activation.
        for name in (
            "request_reactivation",
            "reactivate_candidate",
            "route_to_activation_review",
            "export_redacted_summary",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        assert panel.available_action_names() == ()

        dump = panel.redacted_summary_text()
        assert "automatic_activation_performed: False" in dump
        assert "trust_restoration_performed: False" in dump
        assert "not_validation_evidence: True" in dump

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_acknowledgement_callback_is_widget_local_and_non_persistent() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_reactivation_panel import (
            OptionalSolverPluginManifestReactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestReactivationCandidateInput as C,
            build_optional_solver_plugin_manifest_reactivation_viewmodel as build,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cand = C(stack_id="user", source_reference="C:/x/m.json")
        rebuilds = []

        def callback(acks):
            rebuilds.append(dict(acks))
            return build([cand], acknowledgements=acks)

        panel = Panel(
            view_model=build([cand], acknowledgements={}),
            acknowledgement_callback=callback,
        )
        assert "acknowledge_reactivation_not_validation: available; enabled; current" in (
            panel.action_state_text()
        )
        assert "acknowledge_reactivation_not_validation" in panel.available_action_names()
        assert "readiness=blocked_acknowledgement" in panel.summary_text()

        for row in panel._view_model.acknowledgement_rows:
            panel.apply_acknowledgement(row.acknowledgement_id, True)
        assert "readiness=ready_non_persistent" in panel.summary_text()
        assert rebuilds, "callback must have been invoked"
        assert panel.acknowledgement_state()

        display_only = Panel(view_model=build([cand], acknowledgements={}))
        before = display_only.summary_text()
        display_only.apply_acknowledgement("reactivation_not_validation", True)
        assert display_only.summary_text() == before
        assert display_only.acknowledgement_state() == {}

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_existing_panels_still_construct() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_deactivation_panel import (
            OptionalSolverPluginManifestDeactivationPanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        deactivation = OptionalSolverPluginManifestDeactivationPanel()
        assert "readiness=unavailable_no_activation_state" in deactivation.summary_text()
        assert "Deactivation is not file deletion." in deactivation.safety_text()

        refresh = OptionalSolverPluginManifestDiscoveryRefreshPanel()
        assert "readiness=unavailable_no_activation_state" in refresh.summary_text()

        activation = OptionalSolverPluginManifestActivationPanel()
        assert "preview_available=False" in activation.summary_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_reactivation_viewmodel_has_no_pyside_or_qt_import() -> None:
    tree = ast.parse(VIEWMODEL_SOURCE.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    for module in {m.lower() for m in modules}:
        assert "pyside" not in module
        assert "pyqt" not in module
        assert not module.startswith("qt")


def test_panel_source_has_no_unsafe_or_mutation_paths() -> None:
    source = _panel_source()
    for phrase in (
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
    ):
        assert phrase not in source


def test_panel_source_imports_no_optional_solver_packages_or_network_clients() -> None:
    optional_import_names = {
        "gmsh",
        "meshio",
        "pyvista",
        "vtk",
        "CoolProp",
        "cantera",
        "requests",
        "urllib",
        "socket",
        "http",
        "shutil",
    }
    tree = ast.parse(_panel_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(optional_import_names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in optional_import_names


def test_docs_mention_non_actions_and_future_gates() -> None:
    assert IMPLEMENTATION_DOC.exists()
    text = IMPLEMENTATION_DOC.read_text(encoding="utf-8").lower()
    assert "non-actions" in text
    assert "future gates" in text
    for phrase in (
        "view-model driven",
        "no reactivation persistence",
        "no automatic activation",
        "no trust restoration",
        "no file restore",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "no issue mutation",
        "no release mutation",
        "trust label is not certification",
        "reactivation state is not validation evidence",
    ):
        assert phrase in text
