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
    / "optional_solver_plugin_manifest_activation_panel.py"
)
VIEWMODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_activation_viewmodel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_activation_gui_implementation.md"
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
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_empty_state_and_disabled_unsafe_actions() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestActivationPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestActivationPanel()

        assert PackagePanel is OptionalSolverPluginManifestActivationPanel
        assert panel.objectName() == "oswOptionalSolverPluginManifestActivationPanel"
        assert panel.windowTitle() == "Optional Solver Plugin Manifest Activation"
        assert "preview_available=False" in panel.summary_text()
        assert "preview_required=1" in panel.summary_text()
        assert panel.candidate_rows_text() == "No activation candidates."
        # Empty/no-preview surfaces the preview-required diagnostic.
        assert "OSPMG_ACTIVATION_PREVIEW_REQUIRED" in panel.diagnostics_text()
        # Safety boundary text.
        assert "Activation is not validation." in panel.safety_text()
        assert "Activation is not dependency installation." in panel.safety_text()
        assert "Activation is not solver execution." in panel.safety_text()
        assert "No activation persistence." in panel.safety_text()
        # Unsafe actions are disabled/future-only.
        action_text = panel.action_state_text()
        for name in (
            "activate_candidate",
            "deactivate_candidate",
            "run_discovery_with_activated_manifests",
            "run_validation",
            "install_dependency",
            "execute_solver",
            "close_issue",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        assert "persistent activation is not implemented" in action_text.lower()
        assert "solver execution is unavailable" in action_text.lower()
        # Without an injected callback, acknowledge toggles are disabled too.
        assert "acknowledge_untrusted_source" in panel.disabled_action_reasons()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_candidate_acknowledgement_diagnostic_and_conflict_rendering() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestActivationCandidateInput as Cand,
            build_optional_solver_plugin_manifest_activation_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_activation_viewmodel import (
            ACK_UNTRUSTED_SOURCE, ACK_NO_VALIDATION_PASS, ACK_NO_DEPENDENCY_INSTALL,
            ACK_NO_SOLVER_EXECUTION, ACK_NO_ISSUE_CLOSURE, ACK_NO_CERTIFICATION,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        all_acks = {
            ACK_UNTRUSTED_SOURCE: True, ACK_NO_VALIDATION_PASS: True,
            ACK_NO_DEPENDENCY_INSTALL: True, ACK_NO_SOLVER_EXECUTION: True,
            ACK_NO_ISSUE_CLOSURE: True, ACK_NO_CERTIFICATION: True,
        }

        # Untrusted, blocked-on-acknowledgements candidate (redacted reference).
        blocked = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="user_stack", source_reference="C:/secret/x/m.json")],
                acknowledgements={}, requested_stack_ids=["user_stack"],
            )
        )
        candidates = blocked.candidate_rows_text()
        assert "user_stack" in candidates
        assert "blocked_acknowledgement" in candidates
        ref_cell = candidates.split(" | ")[4]
        assert "/" not in ref_cell and "\\\\" not in ref_cell
        assert "untrusted_source" in blocked.acknowledgement_rows_text()
        assert "OSPMG_ACTIVATION_UNTRUSTED_SOURCE" in blocked.diagnostics_text()
        assert "OSPMG_ACTIVATION_ACK_REQUIRED" in blocked.diagnostics_text()
        assert "Trust label is not certification." in blocked.trust_text()
        assert "User-selected and plugin-provided manifests are untrusted by default." in (
            blocked.trust_text()
        )

        # Ready candidate (all acks satisfied) is still not validation evidence.
        ready = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="user_stack", source_reference="C:/x/m.json")],
                acknowledgements=all_acks, requested_stack_ids=["user_stack"],
            )
        )
        assert "ready" in ready.candidate_rows_text().split(" | ")[7]
        assert "active candidate is not validation evidence" in ready.trust_text().lower()

        # Active candidate renders and is explicitly not validation evidence.
        active = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="user_stack", source_reference="C:/x/m.json")],
                active_stack_ids=["user_stack"],
            )
        )
        assert "active_candidate" in active.candidate_rows_text()
        assert "activation_performed=True" in active.summary_text()

        # Deactivated candidate renders.
        deactivated = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="user_stack", source_reference="C:/x/m.json")],
                deactivated_stack_ids=["user_stack"],
            )
        )
        assert "deactivated" in deactivated.candidate_rows_text()
        assert "OSPMG_ACTIVATION_DEACTIVATED" in deactivated.diagnostics_text()

        # Schema blocker.
        schema = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="s", has_schema_blocker=True)],
                requested_stack_ids=["s"],
            )
        )
        assert "OSPMG_ACTIVATION_SCHEMA_BLOCKED" in schema.diagnostics_text()

        # Unsafe claim blocker.
        unsafe = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="u", has_unsafe_claim=True,
                      unsafe_claim_indicators=("certification claim",))],
                requested_stack_ids=["u"],
            )
        )
        assert "OSPMG_ACTIVATION_UNSAFE_CLAIM" in unsafe.diagnostics_text()

        # Conflict blocker + built-ins-win policy.
        conflict = OptionalSolverPluginManifestActivationPanel(
            view_model=build(
                [Cand(stack_id="gmsh", has_conflict=True)],
                requested_stack_ids=["gmsh"],
            )
        )
        assert "gmsh" in conflict.conflict_rows_text()
        assert "built-ins win by default" in conflict.conflict_rows_text().lower()
        assert "OSPMG_ACTIVATION_CONFLICT_BLOCKED" in conflict.diagnostics_text()

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
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestActivationCandidateInput as Cand,
            build_optional_solver_plugin_manifest_activation_viewmodel as build,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cand = Cand(stack_id="user_stack", source_reference="C:/x/m.json")
        rebuilds = []

        def callback(acks):
            rebuilds.append(dict(acks))
            return build([cand], acknowledgements=acks, requested_stack_ids=["user_stack"])

        panel = OptionalSolverPluginManifestActivationPanel(
            view_model=build([cand], acknowledgements={}, requested_stack_ids=["user_stack"]),
            acknowledgement_callback=callback,
        )
        # With a callback, acknowledge actions are enabled (widget-local).
        assert "acknowledge_untrusted_source: available; enabled; current" in (
            panel.action_state_text()
        )
        # Apply all required acknowledgements; readiness becomes ready.
        for row in panel._view_model.acknowledgement_rows:
            panel.apply_acknowledgement(row.acknowledgement_id, True)
        assert "ready" in panel.candidate_rows_text().split(" | ")[7]
        assert rebuilds, "callback must have been invoked"
        # Widget-local acknowledgement state only; nothing persisted globally.
        assert panel.acknowledgement_state()

        # A panel without a callback ignores acknowledgement toggles (display-only).
        display_only = OptionalSolverPluginManifestActivationPanel(
            view_model=build([cand], acknowledgements={}, requested_stack_ids=["user_stack"]),
        )
        before = display_only.candidate_rows_text()
        display_only.apply_acknowledgement("untrusted_source", True)
        assert display_only.candidate_rows_text() == before
        assert display_only.acknowledgement_state() == {}

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_existing_explicit_import_panel_still_works() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_explicit_import_panel import (
            OptionalSolverPluginManifestExplicitImportPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestExplicitImportPanel()
        assert "selected_sources=0" in panel.summary_text()
        assert "Preview is not activation." in panel.safety_text()
        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_activation_viewmodel_has_no_pyside_or_qt_import() -> None:
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
        "activate_plugin",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "pip install",
        "conda install",
        "gh issue",
        "gh release",
        "create_release",
        "upload_asset",
        "git tag",
        ".write_text(",
        ".write_bytes(",
        "open(",
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
        "no activation persistence",
        "no discovery execution",
        "no solver execution",
        "no dependency installation",
        "no issue mutation",
        "no release mutation",
        "trust label is not certification",
    ):
        assert phrase in text
