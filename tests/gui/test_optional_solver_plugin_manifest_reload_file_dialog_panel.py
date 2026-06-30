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
    / "optional_solver_plugin_manifest_reload_file_dialog_panel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_gui_file_dialog_implementation.md"
)
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_gui_file_dialog_design.md"
)
GUI_IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_gui_implementation.md"
)
READER_IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_file_reader_implementation.md"
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
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_lazy_export_and_constructor_are_inert() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestReloadFileDialogPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        class Reader:
            def __init__(self):
                self.calls = 0

            def read(self, _request):
                self.calls += 1
                raise AssertionError("constructor must not read files")

        picker_calls = {"count": 0}

        def picker():
            picker_calls["count"] += 1
            raise AssertionError("constructor must not open a picker")

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        reader = Reader()
        panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            file_picker=picker,
            reader=reader,
        )

        assert PackagePanel is OptionalSolverPluginManifestReloadFileDialogPanel
        assert (
            panel.objectName()
            == "oswOptionalSolverPluginManifestReloadFileDialogPanel"
        )
        assert panel.windowTitle() == "Optional Solver Plugin Manifest Reload"
        assert picker_calls["count"] == 0
        assert reader.calls == 0
        assert panel.file_dialog_invocation_count() == 0
        assert panel.has_view_model_preview() is False
        assert "No reload state file selected." in panel.reader_status_text()
        assert "OSPMG_RELOAD_GUI_NO_FILE_SELECTED" in panel.reader_diagnostics_text()
        assert "Selected file: <none>" == panel.selected_file_text()
        for phrase in (
            "Preview only.",
            "No default reload path.",
            "No background reload.",
            "No directory scan.",
            "No network fetch.",
            "No plugin package import.",
            "No CLI bridge.",
            "No project mutation.",
            "No validation or solver execution.",
        ):
            assert phrase in panel.safety_text()
        for action in (
            "accept_reload",
            "validate_plugins",
            "run_solver",
            "activate_candidate",
            "restore_trust",
            "create_export_file",
            "create_report_file",
            "create_reloadable_bundle",
            "attach_report",
            "copy_to_clipboard",
            "open_output_folder",
            "scan_directories",
            "fetch_network_manifest",
            "import_plugin_package",
        ):
            assert action in panel.action_state_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_load_selected_file_uses_reader_and_embeds_reload_review_panel(
    tmp_path: Path,
) -> None:
    root = tmp_path.as_posix()
    _run_gui_script(
        f"""
        import json
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
            build_optional_solver_plugin_manifest_state_writer_payload,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        root = Path({root!r})
        target = root / "private" / "state.json"
        target.parent.mkdir()
        payload = build_optional_solver_plugin_manifest_state_writer_payload(
            {{"summary": {{"readiness": "ready_preview_only"}}}}
        )
        target.write_text(json.dumps(payload), encoding="utf-8")
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            file_picker=lambda: (_ for _ in ()).throw(
                AssertionError("load_selected_file must not open picker")
            )
        )

        assert panel.load_selected_file(target) is True
        assert panel.has_view_model_preview() is True
        assert panel.file_dialog_invocation_count() == 0
        assert "state.json" in panel.selected_file_text()
        assert str(target.parent) not in panel.summary_text()
        assert "OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL" in (
            panel.reader_diagnostics_text()
        )
        assert "optional_solver_plugin_manifest_state_writer_state" in (
            panel.preview_summary_text()
        )
        assert "reload_is_validation_evidence=False" in panel.preview_summary_text()
        assert "reload_runs_validation=False" in panel.preview_summary_text()
        assert "reload_executes_solver=False" in panel.preview_summary_text()
        assert "reload_mutates_project_schema=False" in panel.preview_summary_text()
        assert "accept_reload" in panel.action_state_text()
        assert "execute_solver" in panel.action_state_text()

        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_file_picker_cancel_is_non_error_and_preserves_prior_preview(
    tmp_path: Path,
) -> None:
    root = tmp_path.as_posix()
    _run_gui_script(
        f"""
        import json
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
            build_optional_solver_plugin_manifest_state_writer_payload,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        target = Path({root!r}) / "reload-state.json"
        payload = build_optional_solver_plugin_manifest_state_writer_payload(
            {{"summary": {{"readiness": "ready_preview_only"}}}}
        )
        target.write_text(json.dumps(payload), encoding="utf-8")
        picks = [target, None]

        def picker():
            return picks.pop(0)

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestReloadFileDialogPanel(file_picker=picker)

        assert panel.open_file_dialog() is True
        ready_summary = panel.preview_summary_text()
        assert panel.file_dialog_invocation_count() == 1
        assert panel.has_view_model_preview() is True

        assert panel.open_file_dialog() is False
        assert panel.file_dialog_invocation_count() == 2
        assert panel.has_view_model_preview() is True
        assert panel.preview_summary_text() == ready_summary
        assert "selection cancelled" in panel.reader_status_text().lower()
        assert "OSPMG_RELOAD_GUI_SELECTION_CANCELLED" in (
            panel.reader_diagnostics_text()
        )
        assert "No file was selected and no file was read." in (
            panel.reader_diagnostics_text()
        )

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_reader_blockers_render_before_view_model_construction(
    tmp_path: Path,
) -> None:
    root = tmp_path.as_posix()
    _run_gui_script(
        f"""
        import json
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
            build_optional_solver_plugin_manifest_state_writer_payload,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        root = Path({root!r})
        bad_json = root / "bad.json"
        bad_json.write_text("{{bad json", encoding="utf-8")
        mismatch = root / "mismatch.json"
        payload = build_optional_solver_plugin_manifest_state_writer_payload(
            {{"summary": {{"readiness": "ready_preview_only"}}}}
        )
        payload["payload_kind"] = "wrong"
        mismatch.write_text(json.dumps(payload), encoding="utf-8")

        factory_calls = {{"count": 0}}

        def view_model_factory(_mapping, _source_label):
            factory_calls["count"] += 1
            raise AssertionError("blocked reader result must not build a view-model")

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            view_model_factory=view_model_factory
        )

        blocked_cases = (
            (root / "missing.json", "OSPMG_RELOAD_READER_FILE_MISSING"),
            (root, "OSPMG_RELOAD_READER_NOT_REGULAR_FILE"),
            (bad_json, "OSPMG_RELOAD_READER_JSON_PARSE_ERROR"),
            (mismatch, "OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH"),
        )
        for path, code in blocked_cases:
            assert panel.load_selected_file(path) is False
            assert panel.has_view_model_preview() is False
            assert code in panel.reader_diagnostics_text()
            assert str(root) not in panel.summary_text()

        assert factory_calls["count"] == 0

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_blocked_followup_keeps_prior_preview_but_updates_reader_diagnostics(
    tmp_path: Path,
) -> None:
    root = tmp_path.as_posix()
    _run_gui_script(
        f"""
        import json
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
            build_optional_solver_plugin_manifest_state_writer_payload,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        root = Path({root!r})
        good = root / "good.json"
        bad = root / "bad.json"
        payload = build_optional_solver_plugin_manifest_state_writer_payload(
            {{"summary": {{"readiness": "ready_preview_only"}}}}
        )
        good.write_text(json.dumps(payload), encoding="utf-8")
        bad.write_text("[1, 2, 3]", encoding="utf-8")
        factory_calls = {{"count": 0}}

        def view_model_factory(mapping, source_label):
            from osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel import (
                OptionalSolverPluginManifestReloadViewModel,
            )
            factory_calls["count"] += 1
            return OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(
                mapping,
                source_label=source_label,
            )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            view_model_factory=view_model_factory
        )

        assert panel.load_selected_file(good) is True
        ready_summary = panel.preview_summary_text()
        assert factory_calls["count"] == 1

        assert panel.load_selected_file(bad) is False
        assert panel.has_view_model_preview() is True
        assert panel.preview_summary_text() == ready_summary
        assert factory_calls["count"] == 1
        assert "OSPMG_RELOAD_READER_ROOT_NOT_OBJECT" in panel.reader_diagnostics_text()
        assert "bad.json" in panel.selected_file_text()
        assert str(root) not in panel.summary_text()

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_injected_dependency_errors_are_internal_gui_diagnostics(
    tmp_path: Path,
) -> None:
    root = tmp_path.as_posix()
    _run_gui_script(
        f"""
        import json
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
            build_optional_solver_plugin_manifest_state_writer_payload,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        root = Path({root!r})
        target = root / "state.json"
        payload = build_optional_solver_plugin_manifest_state_writer_payload(
            {{"summary": {{"readiness": "ready_preview_only"}}}}
        )
        target.write_text(json.dumps(payload), encoding="utf-8")

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        picker_panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            file_picker=lambda: (_ for _ in ()).throw(RuntimeError(str(root)))
        )
        assert picker_panel.open_file_dialog() is False
        assert "OSPMG_RELOAD_GUI_FILE_PICKER_ERROR" in (
            picker_panel.reader_diagnostics_text()
        )
        assert str(root) not in picker_panel.summary_text()

        class Reader:
            def read(self, _request):
                raise RuntimeError(str(root))

        reader_panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            reader=Reader()
        )
        assert reader_panel.load_selected_file(target) is False
        assert "OSPMG_RELOAD_GUI_READER_ERROR" in (
            reader_panel.reader_diagnostics_text()
        )
        assert str(root) not in reader_panel.summary_text()

        vm_panel = OptionalSolverPluginManifestReloadFileDialogPanel(
            view_model_factory=lambda _mapping, _source: (_ for _ in ()).throw(
                RuntimeError(str(root))
            )
        )
        assert vm_panel.load_selected_file(target) is False
        assert "OSPMG_RELOAD_GUI_VIEWMODEL_ERROR" in (
            vm_panel.reader_diagnostics_text()
        )
        assert vm_panel.has_view_model_preview() is False
        assert str(root) not in vm_panel.summary_text()

        for panel in (picker_panel, reader_panel, vm_panel):
            panel.close()
            panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_clear_preview_is_local_and_non_mutating(tmp_path: Path) -> None:
    root = tmp_path.as_posix()
    _run_gui_script(
        f"""
        import json
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers.plugin_manifest_state_writer import (
            build_optional_solver_plugin_manifest_state_writer_payload,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_reload_file_dialog_panel import (
            OptionalSolverPluginManifestReloadFileDialogPanel,
        )

        root = Path({root!r})
        target = root / "state.json"
        payload = build_optional_solver_plugin_manifest_state_writer_payload(
            {{"summary": {{"readiness": "ready_preview_only"}}}}
        )
        target.write_text(json.dumps(payload), encoding="utf-8")
        before = sorted(path.name for path in root.iterdir())

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestReloadFileDialogPanel()
        assert panel.load_selected_file(target) is True
        assert panel.has_view_model_preview() is True
        panel.clear_preview()

        assert panel.has_view_model_preview() is False
        assert "No reload state file selected." in panel.reader_status_text()
        assert "Selected file: <none>" == panel.selected_file_text()
        assert "OSPMG_RELOAD_GUI_NO_FILE_SELECTED" in panel.reader_diagnostics_text()
        assert sorted(path.name for path in root.iterdir()) == before

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_panel_source_keeps_side_effect_boundaries() -> None:
    source = _panel_source()
    forbidden_fragments = (
        "subprocess",
        "QProcess",
        "QClipboard",
        "webbrowser",
        "requests.",
        "urllib.",
        "httpx.",
        "socket.",
        "osw.cli",
        "ProjectSchema",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "plugin_manifest_discovery",
        "SolverAdapter",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
        ".unlink(",
        ".rmdir(",
        ".replace(",
        ".glob(",
        ".rglob(",
        ".iterdir(",
        "os.walk",
        "os.scandir",
        "pip install",
        "pip uninstall",
        "conda remove",
        "gh issue",
        "gh release",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source, fragment

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    for module in imported_modules:
        root = module.split(".", 1)[0]
        assert root not in {
            "os",
            "json",
            "shutil",
            "subprocess",
            "webbrowser",
            "requests",
            "urllib",
            "httpx",
            "socket",
        }, module
        assert not module.startswith(
            (
                "osw.cli",
                "osw.core",
                "osw.plugins",
                "osw.solvers",
                "osw.post",
            )
        ), module

    assert "QtWidgets.QFileDialog.getOpenFileName" in source
    assert "OptionalSolverPluginManifestReloadFileReader" in source
    assert "OptionalSolverPluginManifestReloadFileReadRequest" in source
    assert "OptionalSolverPluginManifestReloadViewModel.from_payload_mapping" in source
    assert "OptionalSolverPluginManifestReloadPanel" in source


def test_docs_record_reload_gui_file_dialog_implementation_boundaries() -> None:
    implementation = IMPLEMENTATION_DOC.read_text(encoding="utf-8")
    design = DESIGN_DOC.read_text(encoding="utf-8")
    gui_implementation = GUI_IMPLEMENTATION_DOC.read_text(encoding="utf-8")
    reader_implementation = READER_IMPLEMENTATION_DOC.read_text(encoding="utf-8")

    required = (
        "OptionalSolverPluginManifestReloadFileDialogPanel",
        "explicit file-dialog action",
        "OptionalSolverPluginManifestReloadFileReader",
        "OptionalSolverPluginManifestReloadPanel",
        "OptionalSolverPluginManifestReloadViewModel.from_payload_mapping",
        "no native dialog on construction",
        "cancelled selection is non-error",
        "reader blockers suppress view-model construction",
        "diagnostics render before the reload review panel",
        "no default reload path",
        "no background reload",
        "no directory scan",
        "no network fetch",
        "no plugin package import",
        "no CLI subprocess",
        "no ProjectSchema mutation",
        "no validation execution",
        "no solver execution",
        "no automatic activation",
        "no trust restoration",
        "issues `#6` through `#11` remain open",
    )
    for phrase in required:
        assert phrase in implementation, phrase

    assert "OSW-EXP-117 implements" in design
    assert "OSW-EXP-117 adds" in gui_implementation
    assert "GUI consumer added in OSW-EXP-117" in reader_implementation
