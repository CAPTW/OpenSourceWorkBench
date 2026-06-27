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
    / "optional_solver_plugin_manifest_discovery_refresh_panel.py"
)
VIEWMODEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_discovery_refresh_viewmodel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_discovery_refresh_gui_implementation.md"
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
            OptionalSolverPluginManifestDiscoveryRefreshPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        assert PackagePanel is OptionalSolverPluginManifestDiscoveryRefreshPanel
        panel = OptionalSolverPluginManifestDiscoveryRefreshPanel()

        assert panel.objectName() == (
            "oswOptionalSolverPluginManifestDiscoveryRefreshPanel"
        )
        assert panel.windowTitle() == (
            "Optional Solver Plugin Manifest Discovery Refresh"
        )
        # No activation state supplied -> refresh unavailable + diagnostic.
        assert "readiness=unavailable_no_activation_state" in panel.summary_text()
        assert "state=refresh_unavailable" in panel.summary_text()
        assert panel.source_rows_text() == "No discovery sources."
        assert (
            "OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED"
            in panel.diagnostics_text()
        )
        # Honesty flags are all false.
        for flag in (
            "discovery_execution_performed=False",
            "validation_execution_performed=False",
            "solver_execution_performed=False",
            "dependency_installation_performed=False",
            "network_fetch_performed=False",
            "plugin_package_import_performed=False",
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
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput as Src,
            OptionalSolverPluginManifestDiscoveryRefreshViewModel as VM,
            build_optional_solver_plugin_manifest_discovery_refresh_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_discovery_refresh_viewmodel import (
            DISCOVERY_REFRESH_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in DISCOVERY_REFRESH_REQUIRED_ACKS}

        # Built-in-only mode renders.
        bi = Panel(view_model=VM.built_in_only(built_in_source_count=2))
        assert "readiness=built_in_only_ready" in bi.summary_text()
        assert "mode=built_in_only_refresh" in bi.summary_text()
        assert "built_in=2" in bi.summary_text()
        assert "built_in" in bi.source_rows_text()

        # A rich mix exercises sources, deactivated, conflicts, unsafe, badges.
        rich = Panel(view_model=build(
            [
                Src(stack_id="builtin_0", source_type="built_in",
                    trust_label="built_in", is_untrusted=False, built_in=True,
                    built_in_relationship="built-in (authoritative by default)"),
                Src(stack_id="good", source_reference="C:/users/x/good.json"),
                Src(stack_id="gmsh", has_conflict=True,
                    source_reference="C:/users/x/gmsh.json"),
                Src(stack_id="bad", has_unsafe_claim=True,
                    unsafe_claim_indicators=("certification claim",),
                    source_reference="C:/users/x/bad.json"),
                Src(stack_id="old", activation_state="deactivated",
                    source_reference="C:/users/x/old.json"),
            ],
            acknowledgements=allacks, refresh_requested=True,
        ))
        sources = rich.source_rows_text()
        # Discovery source rows render (included/excluded states).
        assert "good" in sources and "active_candidate_included" in sources
        assert "conflict_blocked" in sources
        assert "unsafe_claim_blocked" in sources
        assert "deactivated_excluded" in sources
        # Redacted references (no path separators in the reference column).
        good_line = [ln for ln in sources.split(chr(10)) if ln.startswith("good | ")][0]
        ref_cell = good_line.split(" | ")[4]
        assert "/" not in ref_cell and chr(92) not in ref_cell
        assert good_line.split(" | ")[17] == "yes"  # redacted flag

        # Summary counts render.
        assert "built_in=1" in rich.summary_text()
        assert "active=3" in rich.summary_text()
        assert "included=1" in rich.summary_text()
        assert "deactivated_excluded=1" in rich.summary_text()
        assert "conflict_blocked=1" in rich.summary_text()
        assert "unsafe_claim_blocked=1" in rich.summary_text()

        # Deactivated rows render with non-failure / non-uninstall semantics.
        drt = rich.deactivated_rows_text()
        assert "old" in drt
        assert "not a validation failure" in drt.lower()
        assert "not uninstall" in drt.lower()
        assert "not file deletion" in drt.lower()

        # Acknowledgement rows render (all satisfied here).
        art = rich.acknowledgement_rows_text()
        assert "refresh_not_validation" in art
        assert "untrusted_manifest_source" in art

        # Diagnostics + OSPMG_DISCOVERY_REFRESH_* codes render.
        diags = rich.diagnostics_text()
        assert "OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED" in diags
        assert "OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM" in diags
        assert "OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED" in diags
        assert "OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION" in diags

        # Conflict rows + built-ins-win policy render.
        conf = rich.conflict_rows_text()
        assert "gmsh" in conf
        assert "built-ins win by default" in conf.lower()

        # Unsafe claim rows render.
        uns = rich.unsafe_claim_rows_text()
        assert "bad" in uns and "certification claim" in uns

        # Trust/provenance: badges + untrusted/authoritative/certification text.
        trust = rich.trust_text()
        assert "source_type=" in trust  # at least one badge line
        assert (
            "user-selected and plugin-provided manifests are untrusted by default"
            in trust.lower()
        )
        assert "built-in manifests are authoritative by default" in trust.lower()
        assert "trust label is not certification" in trust.lower()
        assert "discovery inclusion is not validation evidence" in trust.lower()

        # Missing-acknowledgement blocker state renders.
        blocked = Panel(view_model=build(
            [Src(stack_id="user_stack", source_reference="C:/x/m.json")],
            acknowledgements={}, refresh_requested=True,
        ))
        assert "readiness=blocked_acknowledgement" in blocked.summary_text()
        assert "state=refresh_blocked" in blocked.summary_text()
        assert "OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED" in blocked.diagnostics_text()
        assert "OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE" in blocked.diagnostics_text()
        bart = blocked.acknowledgement_rows_text()
        assert "yes | no | yes" in bart  # required | satisfied | blocking

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_ready_and_result_preview_are_not_validation_evidence() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput as Src,
            OptionalSolverPluginManifestDiscoveryRefreshViewModel as VM,
            build_optional_solver_plugin_manifest_discovery_refresh_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_discovery_refresh_viewmodel import (
            DISCOVERY_REFRESH_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in DISCOVERY_REFRESH_REQUIRED_ACKS}

        ready = Panel(view_model=build(
            [Src(stack_id="user_stack", source_reference="C:/x/m.json")],
            acknowledgements=allacks, refresh_requested=True,
        ))
        assert "readiness=ready_preview_only" in ready.summary_text()
        assert "refresh_ready=True" in ready.summary_text()
        assert "Refresh-ready is not validation evidence." in ready.safety_text()
        assert "discovery inclusion is not validation evidence" in (
            ready.trust_text().lower()
        )

        rp = Panel(view_model=VM.result_preview(
            [Src(stack_id="user_stack", source_reference="C:/x/m.json")],
            acknowledgements=allacks,
        ))
        assert "readiness=result_preview" in rp.summary_text()
        assert "state=refresh_result_preview" in rp.summary_text()
        assert "Refresh-ready is not validation evidence." in rp.safety_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_unsafe_actions_disabled_future_only_and_safety_boundary() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput as Src,
            build_optional_solver_plugin_manifest_discovery_refresh_viewmodel as build,
        )
        from osw.experimental.optional_solvers.plugin_manifest_discovery_refresh_viewmodel import (
            DISCOVERY_REFRESH_REQUIRED_ACKS,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        allacks = {a: True for a in DISCOVERY_REFRESH_REQUIRED_ACKS}
        panel = Panel(view_model=build(
            [Src(stack_id="user_stack", source_reference="C:/x/m.json")],
            acknowledgements=allacks, refresh_requested=True,
        ))

        action_text = panel.action_state_text()
        for name in (
            "run_discovery",
            "run_validation",
            "install_dependency",
            "execute_solver",
            "close_issue",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "unavailable" in line and "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        # Future-only (but available) refresh/include/exclude actions stay disabled.
        for name in (
            "request_refresh",
            "built_in_only_refresh",
            "include_activated_candidates",
            "exclude_deactivated_candidates",
            "export_redacted_summary",
        ):
            line = action_text.split(name + ": ", 1)[1].split(chr(10))[0]
            assert "disabled" in line and "future" in line
            assert name in panel.disabled_action_reasons()
        # No action is actionable without an injected callback.
        assert panel.available_action_names() == ()

        # Safety boundary: discovery refresh is not install / not solver execution.
        safety = panel.safety_text()
        assert "Discovery refresh is not validation." in safety
        assert "Discovery refresh is not dependency installation." in safety
        assert "Discovery refresh is not solver execution." in safety
        assert "Discovery refresh is not issue closure." in safety
        assert "No runtime discovery integration." in safety
        assert "No passive discovery behavior change." in safety

        # In-memory redacted summary accessor writes nothing and stays honest.
        summary_dump = panel.redacted_summary_text()
        assert "discovery_execution_performed: False" in summary_dump
        assert "not_validation_evidence: True" in summary_dump

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
        from osw.gui.dialogs.optional_solver_plugin_manifest_discovery_refresh_panel import (
            OptionalSolverPluginManifestDiscoveryRefreshPanel as Panel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput as Src,
            build_optional_solver_plugin_manifest_discovery_refresh_viewmodel as build,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        src = Src(stack_id="user_stack", source_reference="C:/x/m.json")
        rebuilds = []

        def callback(acks):
            rebuilds.append(dict(acks))
            return build([src], acknowledgements=acks, refresh_requested=True)

        panel = Panel(
            view_model=build([src], acknowledgements={}, refresh_requested=True),
            acknowledgement_callback=callback,
        )
        # With a callback, acknowledge actions become widget-local enabled.
        assert "acknowledge_refresh_not_validation: available; enabled; current" in (
            panel.action_state_text()
        )
        assert "acknowledge_refresh_not_validation" in panel.available_action_names()
        assert "readiness=blocked_acknowledgement" in panel.summary_text()

        # Apply ALL required acknowledgements; readiness becomes ready.
        for row in panel._view_model.acknowledgement_rows:
            panel.apply_acknowledgement(row.acknowledgement_id, True)
        assert "readiness=ready_preview_only" in panel.summary_text()
        assert rebuilds, "callback must have been invoked"
        assert panel.acknowledgement_state()  # widget-local only

        # A panel without a callback ignores toggles (display-only, no rebuild).
        display_only = Panel(
            view_model=build([src], acknowledgements={}, refresh_requested=True),
        )
        before = display_only.summary_text()
        display_only.apply_acknowledgement("refresh_not_validation", True)
        assert display_only.summary_text() == before
        assert display_only.acknowledgement_state() == {}

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_existing_activation_and_explicit_import_panels_still_construct() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_activation_panel import (
            OptionalSolverPluginManifestActivationPanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_explicit_import_panel import (
            OptionalSolverPluginManifestExplicitImportPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        activation = OptionalSolverPluginManifestActivationPanel()
        assert "preview_available=False" in activation.summary_text()
        assert "Activation is not validation." in activation.safety_text()

        importer = OptionalSolverPluginManifestExplicitImportPanel()
        assert "selected_sources=0" in importer.summary_text()
        assert "Preview is not activation." in importer.safety_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_discovery_refresh_viewmodel_has_no_pyside_or_qt_import() -> None:
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
        "no runtime discovery integration",
        "no passive discovery behavior change",
        "no activation persistence",
        "no discovery execution",
        "no solver execution",
        "no dependency install",
        "no issue mutation",
        "no release mutation",
        "trust label is not certification",
        "discovery inclusion is not validation evidence",
    ):
        assert phrase in text
