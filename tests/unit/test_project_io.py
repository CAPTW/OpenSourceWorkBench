"""ProjectSchema JSON/YAML IO tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.project_io import (
    load_project,
    load_project_json,
    load_project_yaml,
    save_project_json,
    save_project_yaml,
)
from osw.core.validation import ProjectSchemaError


def test_json_round_trip_preserves_demo_project(tmp_path: Path) -> None:
    project = create_heatsink_flow_demo_project()
    path = tmp_path / "heatsink.osw.json"

    save_project_json(project, path)
    loaded = load_project_json(path)

    assert loaded.metadata.name == "HeatSink_Flow"
    assert loaded.to_dict() == project.to_dict()


def test_load_project_dispatches_json(tmp_path: Path) -> None:
    project = create_heatsink_flow_demo_project()
    path = tmp_path / "heatsink.osw.json"

    save_project_json(project, path)

    assert load_project(path).metadata.name == "HeatSink_Flow"


def test_yaml_round_trip_if_pyyaml_available(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    project = create_heatsink_flow_demo_project()
    path = tmp_path / "heatsink.osw.yaml"

    save_project_yaml(project, path)
    loaded = load_project_yaml(path)

    assert loaded.to_dict() == project.to_dict()


def test_yaml_missing_dependency_is_friendly(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ModuleNotFoundError("No module named 'yaml'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ProjectSchemaError, match="YAML project IO requires"):
        save_project_yaml(create_heatsink_flow_demo_project(), "demo.osw.yaml")


def test_missing_file_gives_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(ProjectSchemaError, match="does not exist"):
        load_project_json(tmp_path / "missing.osw.json")


def test_invalid_project_file_gives_friendly_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.osw.json"
    path.write_text("{not valid", encoding="utf-8")

    with pytest.raises(ProjectSchemaError, match="Could not parse JSON project file"):
        load_project_json(path)
