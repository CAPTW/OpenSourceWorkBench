"""JSON and YAML project file IO for OSW ProjectSchema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .project_schema import Project, project_from_dict, project_to_dict
from .validation import ProjectSchemaError


def load_project(path: str | Path) -> Project:
    return project_from_dict(_load_mapping_from_path(Path(path)))


def save_project(project: Project, path: str | Path) -> None:
    target = Path(path)
    target.write_text(_dump_mapping_for_path(target, project_to_dict(project)), encoding="utf-8")


def project_from_file(path: str | Path) -> Project:
    return load_project(path)


def load_project_json(path: str | Path) -> Project:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectSchemaError(f"Project file does not exist: {source}") from exc
    except OSError as exc:
        raise ProjectSchemaError(f"Could not read project file {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectSchemaError(f"Could not parse JSON project file {source}: {exc}") from exc
    return project_from_dict(data)


def save_project_json(project: Project, path: str | Path) -> None:
    target = Path(path)
    target.write_text(
        f"{json.dumps(project_to_dict(project), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )


def load_project_yaml(path: str | Path) -> Project:
    yaml = _import_yaml()
    source = Path(path)
    try:
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectSchemaError(f"Project file does not exist: {source}") from exc
    except OSError as exc:
        raise ProjectSchemaError(f"Could not read project file {source}: {exc}") from exc
    except Exception as exc:
        raise ProjectSchemaError(f"Could not parse YAML project file {source}: {exc}") from exc
    return project_from_dict(data)


def save_project_yaml(project: Project, path: str | Path) -> None:
    yaml = _import_yaml()
    target = Path(path)
    target.write_text(
        yaml.safe_dump(project_to_dict(project), sort_keys=False),
        encoding="utf-8",
    )


def project_to_file(project: Project, path: str | Path) -> None:
    save_project(project, path)


def _load_mapping_from_path(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return project_to_dict(load_project_json(path))
    if suffix in {".yaml", ".yml"}:
        return project_to_dict(load_project_yaml(path))
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProjectSchemaError(f"Project file does not exist: {path}") from exc
    except OSError as exc:
        raise ProjectSchemaError(f"Could not read project file {path}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProjectSchemaError(f"Could not parse project file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProjectSchemaError(f"Project file {path} must contain a mapping.")
    return data


def _dump_mapping_for_path(path: Path, data: dict[str, Any]) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return f"{json.dumps(data, indent=2, sort_keys=True)}\n"
    if suffix in {".yaml", ".yml"}:
        yaml = _import_yaml()
        return yaml.safe_dump(data, sort_keys=False)
    return f"{json.dumps(data, indent=2, sort_keys=True)}\n"


def _import_yaml() -> Any:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise ProjectSchemaError(
            "YAML project IO requires the optional PyYAML package. "
            "Install PyYAML or use JSON project files."
        ) from exc
    return yaml
