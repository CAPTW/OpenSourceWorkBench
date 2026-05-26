"""Plugin contract surface tests."""

from __future__ import annotations

from pathlib import Path

from osw.plugins.base import (
    CADImporterPlugin,
    MeshGeneratorPlugin,
    MeshImporterPlugin,
    PostProcessorPlugin,
    PropertyModelPlugin,
    ReportPlugin,
    ScriptImporterPlugin,
    SolverAdapterPlugin,
    WorkbenchPlugin,
)
from osw.plugins.manifest import PluginManifest
from osw.plugins.registry import PluginRegistry


def _manifest(plugin_id: str, plugin_type: str) -> PluginManifest:
    return PluginManifest.from_dict(
        {
            "id": plugin_id,
            "name": plugin_id,
            "version": "0.1.0",
            "domain": "GENERAL",
            "type": plugin_type,
            "license": "MIT",
            "capabilities": ["contract_test"],
        }
    )


def test_contract_classes_are_importable() -> None:
    assert WorkbenchPlugin
    assert CADImporterPlugin
    assert MeshImporterPlugin
    assert MeshGeneratorPlugin
    assert SolverAdapterPlugin
    assert ScriptImporterPlugin
    assert PropertyModelPlugin
    assert PostProcessorPlugin
    assert ReportPlugin


def test_fake_solver_adapter_satisfies_minimal_contract(tmp_path: Path) -> None:
    class FakeSolver(SolverAdapterPlugin):
        manifest = _manifest("osw.fake.solver", "solver_adapter")
        supported_problem_types = ("linear_static",)

        def validate(self, project: object) -> list[str]:
            return []

        def generate_case(self, project: object, case_dir: str | Path) -> Path:
            return Path(case_dir)

        def run(self, case_dir: str | Path, runner: object) -> object:
            raise RuntimeError("Execution requires the future runner boundary.")

        def parse_results(self, case_dir: str | Path) -> dict[str, str]:
            return {"case_dir": str(case_dir)}

    plugin = FakeSolver()

    assert plugin.id == "osw.fake.solver"
    assert plugin.supported_problem_types == ("linear_static",)
    assert plugin.generate_case(object(), tmp_path) == tmp_path


def test_fake_script_preview_does_not_run_file_code(tmp_path: Path) -> None:
    sentinel = tmp_path / "executed.txt"
    script = tmp_path / "script.m"
    script.write_text(f"!echo executed > {sentinel}\nplot(x, y)\n", encoding="utf-8")

    class FakeScriptImporter(ScriptImporterPlugin):
        manifest = _manifest("osw.fake.script", "script_importer")
        supported_extensions = ("m",)

        def preview(self, path: str | Path) -> dict[str, object]:
            return {"path": str(path), "will_execute": False}

        def validate_script(self, path: str | Path) -> list[str]:
            return []

        def import_script(self, path: str | Path) -> dict[str, object]:
            return {"path": str(path)}

    preview = FakeScriptImporter().preview(script)

    assert preview["will_execute"] is False
    assert not sentinel.exists()


def test_workbench_plugin_registers_with_registry() -> None:
    class FakePlugin(WorkbenchPlugin):
        manifest = _manifest("osw.fake.base", "ui_extension")

    registry = PluginRegistry()

    FakePlugin().register(registry)

    assert registry.get("osw.fake.base").name == "osw.fake.base"
