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
    / "optional_solver_plugin_manifest_deactivation_panel.py"
)
VIEWMODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_deactivation_viewmodel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_deactivation_gui_implementation.md"
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
            OptionalSolverPluginManifestDeactivationPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_deactivation_panel import (
            OptionalSolverPluginManifestDeactivationPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        assert PackagePanel is OptionalSolverPluginManifestDeactivationPanel
        panel = OptionalSolverPluginManifestDeactivationPanel()

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestDeactivationPanel"
        )
        assert panel.windowTitle() == "Optional Solver Plugin Manifest Deactivation"
        # No activation state supplied -> deactivation unavailable + diagnostic.
        assert "readiness=unavailable_no_activation_state" in panel.summary_text()
        assert panel.candidate_rows_text() == "No deactivation candidates."
        assert "OSPMG_DEACTIVATION_ACTIVE_REQUIRED" in panel.diagnostics_text()
        # Honesty flags are all false.
        for flag in (
            "deactivation_performed=False",
            "file_deletion_performed=False",
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
        from osw.gui.dialogs.optional_solver_plugin_manifest_deactivation_panel import (
            OptionalSolverPluginManifestDeactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDeactivationCandidateInput as C,
            OptionalSolverPluginManifestDeactivationViewModel as VM,
            build_optional_solver_plugin_manifest_deactivation_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_deactivation_viewmodel import (
            DEACTIVATION_ALWAYS_REQUIRED_ACKS, ACK_CONFLICT_OR_SHARED_STACK_WARNING,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in DEACTIVATION_ALWAYS_REQUIRED_ACKS}
        allacks_shared = {**allacks, ACK_CONFLICT_OR_SHARED_STACK_WARNING: True}

        rich = Panel(view_model=build(
            [
                C(stack_id="bi", source_type="built_in", trust_label="built_in",
                  is_untrusted=False, built_in=True,
                  built_in_relationship="built-in (authoritative by default)"),
                C(stack_id="good", source_reference="C:/users/x/good.json"),
                C(stack_id="gmsh", has_shared_stack=True,
                  shared_stack_indicators=("dup",), source_reference="C:/users/x/gmsh.json"),
                C(stack_id="old", deactivated=True, activation_state="deactivated",
                  historical_evidence_state="skipped_missing",
                  source_reference="C:/users/x/old.json"),
            ],
            acknowledgements=allacks_shared,
        ))

        # Summary counts render.
        s = rich.summary_text()
        assert "active=2" in s  # good + gmsh
        assert "deactivated=1" in s
        assert "deactivation_candidates=3" in s  # excludes built-in
        assert "evidence_retained_count=1" in s

        # Candidate rows render (states + redaction).
        cands = rich.candidate_rows_text()
        assert "good" in cands and "active_candidate" in cands
        assert "old" in cands and "deactivated" in cands
        good_line = [ln for ln in cands.split(chr(10)) if ln.startswith("good | ")][0]
        assert good_line.split(" | ")[4] == "good.json"  # redacted reference
        assert good_line.split(" | ")[15] == "yes"  # redacted flag

        # Acknowledgement rows render.
        art = rich.acknowledgement_rows_text()
        assert "not_file_deletion" in art
        assert "deactivation_history_visible" in art

        # Diagnostics + OSPMG_DEACTIVATION_* codes render.
        diags = rich.diagnostics_text()
        assert "OSPMG_DEACTIVATION_SHARED_STACK_WARNING" in diags
        assert "OSPMG_DEACTIVATION_DEACTIVATED" in diags
        assert "OSPMG_DEACTIVATION_EVIDENCE_RETAINED" in diags
        assert "OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED" in diags

        # Shared-stack rows + built-ins-win policy render.
        shared = rich.shared_stack_rows_text()
        assert "gmsh" in shared
        assert "does not deactivate built-ins" in shared.lower()
        gmsh_shared = [ln for ln in shared.split(chr(10)) if ln.startswith("gmsh | ")][0]
        assert gmsh_shared.split(" | ")[5] == "yes"  # built-ins win

        # Evidence rows render.
        ev = rich.evidence_rows_text()
        assert "old" in ev
        assert "skipped_missing" in ev
        assert "skipped-missing" in ev.lower()
        assert "not a validation failure" in ev.lower()

        # Trust/provenance + untrusted/authoritative/certification text.
        trust = rich.trust_text()
        assert "source_type=" in trust
        assert (
            "user-selected and plugin-provided manifests are untrusted by default"
            in trust.lower()
        )
        assert "built-in manifests are authoritative by default" in trust.lower()
        assert "trust label is not certification" in trust.lower()
        assert "a deactivated state is not validation evidence" in trust.lower()

        # Blocked-acknowledgement view renders.
        blocked = Panel(view_model=build(
            [C(stack_id="user", source_reference="C:/x/m.json")], acknowledgements={}))
        assert "readiness=blocked_acknowledgement" in blocked.summary_text()
        assert "OSPMG_DEACTIVATION_ACK_REQUIRED" in blocked.diagnostics_text()
        assert "yes | no | yes" in blocked.acknowledgement_rows_text()

        # Deactivation-ready view is explicitly non-persistent.
        ready = Panel(view_model=build(
            [C(stack_id="user", source_reference="C:/x/m.json")], acknowledgements=allacks))
        assert "readiness=ready_non_persistent" in ready.summary_text()
        assert "deactivation_performed=False" in ready.summary_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_deactivated_state_is_not_deletion_uninstall_or_validation() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_deactivation_panel import (
            OptionalSolverPluginManifestDeactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDeactivationCandidateInput as C,
            OptionalSolverPluginManifestDeactivationViewModel as VM,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        d = Panel(view_model=VM.all_deactivated([C(stack_id="user")]))
        assert "readiness=deactivated" in d.summary_text()
        cands = d.candidate_rows_text()
        assert "deactivated" in cands
        diags = d.diagnostics_text()
        assert "OSPMG_DEACTIVATION_NOT_VALIDATION" in diags
        assert "OSPMG_DEACTIVATION_NOT_FILE_DELETE" in diags
        assert "OSPMG_DEACTIVATION_NOT_UNINSTALL" in diags
        safety = d.safety_text()
        assert "Deactivation is not file deletion." in safety
        assert "Deactivation is not dependency uninstall." in safety
        assert "Deactivation is not solver uninstall." in safety
        assert "Deactivation is not a validation failure." in safety
        assert "Deactivation is not solver execution." in safety
        # deactivated state is not validation evidence.
        assert "a deactivated state is not validation evidence" in d.trust_text().lower()
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
        from osw.gui.dialogs.optional_solver_plugin_manifest_deactivation_panel import (
            OptionalSolverPluginManifestDeactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDeactivationCandidateInput as C,
            build_optional_solver_plugin_manifest_deactivation_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_deactivation_viewmodel import (
            DEACTIVATION_ALWAYS_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in DEACTIVATION_ALWAYS_REQUIRED_ACKS}
        panel = Panel(view_model=build(
            [C(stack_id="user", source_reference="C:/x/m.json")], acknowledgements=allacks))

        action_text = panel.action_state_text()
        # Unsafe actions are unavailable, disabled, and future-only.
        for name in (
            "run_discovery",
            "run_validation",
            "uninstall_dependency",
            "uninstall_solver",
            "execute_solver",
            "close_issue",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "unavailable" in line and "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        # Deactivate/reactivate/request remain future-only (disabled).
        for name in (
            "request_deactivation",
            "deactivate_candidate",
            "reactivate_candidate",
            "export_redacted_summary",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        # No action is actionable without an injected callback.
        assert panel.available_action_names() == ()

        # In-memory redacted summary writes nothing and stays honest.
        dump = panel.redacted_summary_text()
        assert "file_deletion_performed: False" in dump
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
        from osw.gui.dialogs.optional_solver_plugin_manifest_deactivation_panel import (
            OptionalSolverPluginManifestDeactivationPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDeactivationCandidateInput as C,
            build_optional_solver_plugin_manifest_deactivation_viewmodel as build,
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
        assert "acknowledge_not_file_deletion: available; enabled; current" in (
            panel.action_state_text()
        )
        assert "acknowledge_not_file_deletion" in panel.available_action_names()
        assert "readiness=blocked_acknowledgement" in panel.summary_text()

        # Apply ALL required acknowledgements; readiness becomes ready.
        for row in panel._view_model.acknowledgement_rows:
            panel.apply_acknowledgement(row.acknowledgement_id, True)
        assert "readiness=ready_non_persistent" in panel.summary_text()
        assert rebuilds, "callback must have been invoked"
        assert panel.acknowledgement_state()  # widget-local only

        # A panel without a callback ignores toggles (display-only, no rebuild).
        display_only = Panel(view_model=build([cand], acknowledgements={}))
        before = display_only.summary_text()
        display_only.apply_acknowledgement("not_file_deletion", True)
        assert display_only.summary_text() == before
        assert display_only.acknowledgement_state() == {}

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_existing_activation_and_discovery_refresh_panels_still_construct() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        activation = OptionalSolverPluginManifestActivationPanel()
        assert "preview_available=False" in activation.summary_text()
        assert "Activation is not validation." in activation.safety_text()

        refresh = OptionalSolverPluginManifestDiscoveryRefreshPanel()
        assert "readiness=unavailable_no_activation_state" in refresh.summary_text()
        assert "Refresh-ready is not validation evidence." in refresh.safety_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_deactivation_viewmodel_has_no_pyside_or_qt_import() -> None:
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
        "no deactivation persistence",
        "no file deletion",
        "no dependency uninstall",
        "no solver uninstall",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "no issue mutation",
        "no release mutation",
        "trust label is not certification",
        "deactivated state is not validation evidence",
    ):
        assert phrase in text
