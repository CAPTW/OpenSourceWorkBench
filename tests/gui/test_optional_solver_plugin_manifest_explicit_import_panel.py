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
    / "optional_solver_plugin_manifest_explicit_import_panel.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_explicit_import_gui_implementation.md"
)

PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None


def _source() -> str:
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


def test_module_import_initial_state_and_action_guidance() -> None:
    _run_gui_script(
        """
        from PySide6 import QtWidgets
        from osw.gui.dialogs import (
            OptionalSolverPluginManifestExplicitImportPanel as PackagePanel,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_explicit_import_panel import (
            OptionalSolverPluginManifestExplicitImportPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        panel = OptionalSolverPluginManifestExplicitImportPanel()

        assert PackagePanel is OptionalSolverPluginManifestExplicitImportPanel
        assert panel.objectName() == "oswOptionalSolverPluginManifestExplicitImportPanel"
        assert panel.windowTitle() == "Preview Plugin Manifest JSON"
        assert "selected_sources=0" in panel.summary_text()
        assert panel.source_rows_text() == "No sources selected."
        assert "Preview is not activation." in panel.safety_text()
        assert "Preview is not validation." in panel.safety_text()
        assert "Preview is not solver execution." in panel.safety_text()
        assert "choose_explicit_json_files: available; enabled; current" in (
            panel.action_state_text()
        )
        for name in (
            "activate_manifest",
            "run_discovery_with_plugin_manifests",
            "run_validation",
            "install_solver",
            "close_issue",
        ):
            assert f"{name}: unavailable; disabled; future" in panel.action_state_text()
            assert name in panel.disabled_action_reasons()
        assert "No GUI export" in panel.disabled_action_reasons()["export_redacted_summary"]

        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_choose_cancel_and_path_validation_use_injected_callables(tmp_path: Path) -> None:
    _run_gui_script(
        f"""
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_explicit_import_panel import (
            OptionalSolverPluginManifestExplicitImportPanel,
        )
        from osw.experimental.optional_solvers import (
            OptionalSolverPluginManifestLoadReport,
            load_optional_solver_plugin_manifest_json,
        )

        root = Path.cwd()
        fixture = (
            root
            / "tests"
            / "fixtures"
            / "optional_solvers"
            / "plugin_manifests"
            / "valid_project_local_manifest.json"
        )
        temp_dir = Path(r"{tmp_path}")
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

        calls = []
        selected = temp_dir / "manifest.json"
        selected.write_text("{{}}", encoding="utf-8")

        def loader(path):
            calls.append(path)
            return load_optional_solver_plugin_manifest_json(fixture)

        panel = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: selected,
            loader=loader,
        )
        panel.choose_button.click()
        assert calls == [str(selected)]
        assert "accepted=1" in panel.summary_text()
        assert "project_local_stack" in panel.accepted_rows_text()
        before = panel.summary_text()
        panel._file_chooser = lambda: None
        panel.choose_manifest_json()
        assert panel.summary_text() == before
        assert "OSPMG_IMPORT_CANCELLED" not in panel.import_diagnostics_text()

        def fail_loader(_path):
            raise AssertionError("loader must not run before path validation")

        wrong_ext = temp_dir / "manifest.txt"
        wrong_ext.write_text("{{}}", encoding="utf-8")
        ext_panel = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: wrong_ext,
            loader=fail_loader,
        )
        ext_panel.choose_manifest_json()
        assert "OSPMG_IMPORT_UNSUPPORTED_EXTENSION" in ext_panel.diagnostics_text()

        missing = temp_dir / "missing.json"
        missing_panel = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: missing,
            loader=fail_loader,
        )
        missing_panel.choose_manifest_json()
        assert "OSPMG_IMPORT_FILE_MISSING" in missing_panel.diagnostics_text()

        large = temp_dir / "large.json"
        large.write_text("{{}}", encoding="utf-8")
        large_panel = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: large,
            loader=fail_loader,
            max_file_size_bytes=1,
        )
        large_panel.choose_manifest_json()
        assert "OSPMG_IMPORT_FILE_TOO_LARGE" in large_panel.diagnostics_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_loader_report_states_and_trust_labels_render(tmp_path: Path) -> None:
    _run_gui_script(
        f"""
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.gui.dialogs.optional_solver_plugin_manifest_explicit_import_panel import (
            OptionalSolverPluginManifestExplicitImportPanel,
        )
        from osw.experimental.optional_solvers import load_optional_solver_plugin_manifest_json

        root = Path.cwd()
        fixtures = root / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"
        valid = fixtures / "valid_project_local_manifest.json"
        duplicate = fixtures / "duplicate_stack_plugin_manifest.json"
        bundled = fixtures / "invalid_bundled_solver_claim.json"
        temp_dir = Path(r"{tmp_path}")
        selected = temp_dir / "manifest.json"
        selected.write_text("{{}}", encoding="utf-8")
        broken = temp_dir / "broken.json"
        broken.write_text("{{not valid json", encoding="utf-8")
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

        accepted = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: selected,
            loader=lambda _path: load_optional_solver_plugin_manifest_json(valid),
        )
        accepted.choose_manifest_json()
        assert "project_local_stack" in accepted.accepted_rows_text()
        assert "source_type=project_local" in accepted.trust_text()
        assert "trust_label=reviewed_project" in accepted.trust_text()
        assert "User-selected manifests are untrusted by default." in accepted.trust_text()
        assert "Third-party/plugin manifests are not trusted by default." in accepted.trust_text()
        assert "Trust label is not certification." in accepted.trust_text()
        assert "Preview is not installation." in accepted.safety_text()

        rejected = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: selected,
            loader=lambda _path: load_optional_solver_plugin_manifest_json(bundled),
        )
        rejected.choose_manifest_json()
        assert "bundled_claim_stack" in rejected.rejected_rows_text()
        assert "OSPL_BUNDLED_SOLVER_CLAIM" in rejected.diagnostics_text()
        assert "OSPMG_IMPORT_SCHEMA_INVALID" in rejected.diagnostics_text()

        conflict = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: selected,
            loader=lambda _path: load_optional_solver_plugin_manifest_json(duplicate),
        )
        conflict.choose_manifest_json()
        assert "Built-in manifests win by default." in conflict.conflict_rows_text()
        assert "Plugin override is disabled by default." in conflict.conflict_rows_text()
        assert "OSPMG_IMPORT_CONFLICT" in conflict.diagnostics_text()

        invalid = OptionalSolverPluginManifestExplicitImportPanel(
            file_chooser=lambda: broken,
            loader=lambda path: load_optional_solver_plugin_manifest_json(path),
        )
        invalid.choose_manifest_json()
        assert "OSPMG_IMPORT_INVALID_JSON" in invalid.diagnostics_text()
        assert "rejected=1" in invalid.summary_text()

        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_existing_display_only_panel_still_works() -> None:
    _run_gui_script(
        """
        from pathlib import Path
        from PySide6 import QtWidgets
        from osw.experimental.optional_solvers import (
            build_optional_solver_plugin_manifest_gui_viewmodel,
            load_optional_solver_plugin_manifest_json,
        )
        from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
            OptionalSolverPluginManifestPanel,
        )

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        fixture = (
            Path.cwd()
            / "tests"
            / "fixtures"
            / "optional_solvers"
            / "plugin_manifests"
            / "valid_project_local_manifest.json"
        )
        panel = OptionalSolverPluginManifestPanel(
            build_optional_solver_plugin_manifest_gui_viewmodel(
                load_optional_solver_plugin_manifest_json(fixture)
            )
        )
        assert "accepted=1" in panel.summary_text()
        assert "project_local_stack" in panel.accepted_rows_text()
        panel.close()
        panel.deleteLater()
        app.processEvents()
        app.quit()
        """
    )


def test_source_has_no_solver_dependency_or_issue_release_mutation_paths() -> None:
    source = _source()
    for phrase in (
        "QProcess",
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
    ):
        assert phrase not in source


def test_source_imports_no_optional_solver_packages_or_network_clients() -> None:
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
    tree = ast.parse(_source())
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
        "preview-only",
        "no activation",
        "no discovery execution",
        "no solver execution",
        "no dependency installation",
        "no issue mutation",
        "no release mutation",
        "trust label is not certification",
    ):
        assert phrase in text
