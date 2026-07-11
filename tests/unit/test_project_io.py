"""ProjectSchema JSON/YAML IO tests."""

from __future__ import annotations

import json
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
from osw.core.project_schema import Project, ProjectMetadata
from osw.core.report_asset import ReportAssetPathKind, ReportScreenshotAsset
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


def _typed_path_project() -> Project:
    return Project(
        metadata=ProjectMetadata(name="Typed paths"),
        schema_version="0.2",
        report_screenshots=[
            ReportScreenshotAsset(
                id="shot-1",
                path="screenshots/scene.png",
                path_kind=ReportAssetPathKind.PROJECT_RELATIVE,
            )
        ],
    )


def test_json_round_trip_preserves_explicit_path_kind(tmp_path: Path) -> None:
    path = tmp_path / "typed.osw.json"

    save_project_json(_typed_path_project(), path)
    loaded = load_project_json(path)

    assert loaded.schema_version == "0.2"
    assert loaded.report_screenshots[0].path_kind is ReportAssetPathKind.PROJECT_RELATIVE
    assert loaded.to_dict()["report_screenshots"][0]["path_kind"] == "project_relative"


def test_yaml_round_trip_preserves_explicit_path_kind(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    path = tmp_path / "typed.osw.yaml"

    save_project_yaml(_typed_path_project(), path)
    loaded = load_project_yaml(path)

    assert loaded.schema_version == "0.2"
    assert loaded.report_screenshots[0].path_kind is ReportAssetPathKind.PROJECT_RELATIVE


@pytest.mark.parametrize("format_name", ["json", "yaml"])
@pytest.mark.parametrize("bad_kind", [None, True, 3, [], {}])
def test_json_and_yaml_reject_the_same_non_string_path_kind_types(
    tmp_path: Path,
    format_name: str,
    bad_kind: object,
) -> None:
    payload = {
        "schema_version": "0.2",
        "metadata": {"name": "Malformed typed path"},
        "report_screenshots": [
            {
                "id": "shot-1",
                "path": "screenshots/scene.png",
                "path_kind": bad_kind,
            }
        ],
    }
    path = tmp_path / f"malformed.osw.{format_name}"
    if format_name == "json":
        path.write_text(json.dumps(payload), encoding="utf-8")
        loader = load_project_json
    else:
        yaml = pytest.importorskip("yaml")
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        loader = load_project_yaml

    with pytest.raises(ProjectSchemaError, match="path_kind"):
        loader(path)


@pytest.mark.parametrize("format_name", ["json", "yaml"])
@pytest.mark.parametrize("bad_path", [None, True, 3, [], {}, "", "   "])
def test_json_and_yaml_reject_the_same_malformed_explicit_path_types(
    tmp_path: Path,
    format_name: str,
    bad_path: object,
) -> None:
    payload = {
        "schema_version": "0.2",
        "metadata": {"name": "Malformed typed path"},
        "report_screenshots": [
            {
                "id": "shot-1",
                "path": bad_path,
                "path_kind": "legacy_raw",
            }
        ],
    }
    path = tmp_path / f"malformed-path.osw.{format_name}"
    if format_name == "json":
        path.write_text(json.dumps(payload), encoding="utf-8")
        loader = load_project_json
    else:
        yaml = pytest.importorskip("yaml")
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        loader = load_project_yaml

    with pytest.raises(ProjectSchemaError, match="path"):
        loader(path)
