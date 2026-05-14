from __future__ import annotations

import importlib
import json
from pathlib import Path

from osw.plugins.health import (
    PluginHealthStatus,
    build_plugin_health_record,
    collect_plugin_health_records,
    plugin_health_records_as_json,
    plugin_health_records_as_text,
)
from osw.plugins.manifest import PluginManifest

cli_main = importlib.import_module("osw.cli.main")


def _manifest_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "demo.health",
        "name": "Demo Health Plugin",
        "version": "0.1.0",
        "domain": "solver",
        "type": "solver_adapter",
        "license": "MIT",
        "input_formats": [],
        "output_formats": [],
        "requires": [],
        "optional_requires": [],
        "capabilities": ["prepare_case", "validate"],
    }
    data.update(overrides)
    return data


def _write_manifest(path: Path, **overrides: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_manifest_data(**overrides)), encoding="utf-8")
    return path


def test_health_record_serializes_dependency_executable_and_sample_status() -> None:
    manifest = PluginManifest.from_dict(
        _manifest_data(
            requires=["osw_missing_dependency_for_health_test"],
            capabilities=[
                "prepare_case",
                "requires_executable:osw-missing-exe-for-health-test",
                "sample_project:examples/demo_health",
            ],
        )
    )

    record = build_plugin_health_record(manifest)
    data = record.to_dict()

    assert record.status == PluginHealthStatus.ERROR.value
    assert data["dependency_status"] == PluginHealthStatus.ERROR.value
    assert data["dependency_messages"] == [
        "Required dependency is missing: osw_missing_dependency_for_health_test"
    ]
    assert data["executable_status"][0]["available"] is False
    assert "osw-missing-exe-for-health-test" in data["executable_status"][0]["message"]
    assert data["sample_project_reference"] == "examples/demo_health"
    assert data["last_health_check_status"] == "checked"
    assert data["last_run_status"] == "not-run"


def test_health_record_uses_configured_executable_path(tmp_path: Path) -> None:
    executable = tmp_path / "solver.exe"
    executable.write_text("", encoding="utf-8")
    manifest = PluginManifest.from_dict(
        _manifest_data(capabilities=["requires_executable:demo-solver"])
    )

    record = build_plugin_health_record(
        manifest,
        executable_paths={"demo-solver": executable},
    )

    assert record.status == PluginHealthStatus.OK.value
    assert record.executable_status[0].available
    assert record.executable_status[0].configured_path == str(executable)


def test_collect_plugin_health_records_reports_invalid_and_duplicate_manifests(
    tmp_path: Path,
) -> None:
    _write_manifest(tmp_path / "plugins" / "a" / "osw-plugin.json", id="demo.dup")
    _write_manifest(tmp_path / "plugins" / "b" / "osw-plugin.json", id="demo.dup")
    invalid = tmp_path / "plugins" / "invalid" / "osw-plugin.json"
    invalid.parent.mkdir(parents=True)
    invalid.write_text(json.dumps({"id": "bad.plugin"}), encoding="utf-8")

    records = collect_plugin_health_records([tmp_path / "plugins"])
    text = plugin_health_records_as_text(records)

    assert len(records) == 3
    assert "Duplicate plugin id: demo.dup" in text
    assert "Invalid plugin manifest" in text


def test_plugin_health_json_output_includes_status(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "plugins" / "demo" / "osw-plugin.json")

    records = collect_plugin_health_records([tmp_path / "plugins"])
    data = json.loads(plugin_health_records_as_json(records))

    assert data[0]["plugin_id"] == "demo.health"
    assert data[0]["status"] == "ok"
    assert data[0]["last_run_status"] == "not-run"


def test_cli_plugin_health_reports_local_manifest(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    empty_default = tmp_path / "empty-default"
    _write_manifest(
        tmp_path / "plugins" / "demo" / "osw-plugin.json",
        optional_requires=["osw_missing_optional_for_cli_test"],
    )
    monkeypatch.setattr(cli_main, "DEFAULT_PLUGIN_INSTALL_ROOT", empty_default)

    exit_code = cli_main.main(["plugin-health", "--plugin-path", str(tmp_path / "plugins")])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "OSW plugin health" in output
    assert "demo.health" in output
    assert "Optional dependency is missing: osw_missing_optional_for_cli_test" in output


def test_cli_plugin_health_json_reports_empty_default(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(cli_main, "DEFAULT_PLUGIN_INSTALL_ROOT", tmp_path / "empty")

    exit_code = cli_main.main(["plugin-health", "--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert json.loads(output) == []
