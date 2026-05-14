"""Plugin health checks that avoid loading heavy optional integrations."""

from __future__ import annotations

import importlib.util
import json
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .discovery import iter_manifest_paths
from .manifest import PluginManifest

EXECUTABLE_CAPABILITY_PREFIXES = ("requires_executable:", "executable:")
SAMPLE_PROJECT_CAPABILITY_PREFIXES = ("sample_project:", "sample-project:")


class PluginHealthStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class PluginHealth:
    status: PluginHealthStatus
    messages: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PluginExecutableStatus:
    executable: str
    configured_path: str = ""
    available: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "executable": self.executable,
            "configured_path": self.configured_path,
            "available": self.available,
            "message": self.message,
        }


@dataclass(frozen=True)
class PluginHealthRecord:
    plugin_id: str
    display_name: str
    version: str
    plugin_type: str
    domain: str
    status: str
    dependency_status: str
    dependency_messages: tuple[str, ...] = field(default_factory=tuple)
    executable_status: tuple[PluginExecutableStatus, ...] = field(default_factory=tuple)
    sample_project_reference: str = ""
    last_health_check_status: str = "not-run"
    last_run_status: str = "not-run"
    enabled: bool = True
    valid: bool = True
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "display_name": self.display_name,
            "version": self.version,
            "plugin_type": self.plugin_type,
            "domain": self.domain,
            "status": self.status,
            "dependency_status": self.dependency_status,
            "dependency_messages": list(self.dependency_messages),
            "executable_status": [item.to_dict() for item in self.executable_status],
            "sample_project_reference": self.sample_project_reference,
            "last_health_check_status": self.last_health_check_status,
            "last_run_status": self.last_run_status,
            "enabled": self.enabled,
            "valid": self.valid,
            "source": self.source,
        }

    @property
    def executable_messages(self) -> tuple[str, ...]:
        return tuple(item.message for item in self.executable_status if item.message)


@dataclass(frozen=True)
class InvalidPluginHealthRecord:
    source: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": Path(self.source).stem or "<invalid>",
            "display_name": Path(self.source).name or "Invalid plugin",
            "version": "",
            "plugin_type": "",
            "domain": "",
            "status": PluginHealthStatus.ERROR.value,
            "dependency_status": PluginHealthStatus.ERROR.value,
            "dependency_messages": [self.message],
            "executable_status": [],
            "sample_project_reference": "",
            "last_health_check_status": "checked",
            "last_run_status": "not-run",
            "enabled": False,
            "valid": False,
            "source": self.source,
        }


PluginHealthRow = PluginHealthRecord | InvalidPluginHealthRecord


def check_manifest_health(manifest: PluginManifest) -> PluginHealth:
    errors: list[str] = []
    warnings: list[str] = []

    for requirement in manifest.requires:
        if not _requirement_available(requirement):
            errors.append(f"Required dependency is missing: {requirement}")

    for requirement in manifest.optional_requires:
        if not _requirement_available(requirement):
            warnings.append(f"Optional dependency is missing: {requirement}")

    if errors:
        return PluginHealth(PluginHealthStatus.ERROR, tuple(errors))
    if warnings:
        return PluginHealth(PluginHealthStatus.WARNING, tuple(warnings))
    return PluginHealth(PluginHealthStatus.OK)


def collect_plugin_health_records(
    local_paths: Iterable[str | Path],
    *,
    executable_paths: Mapping[str, str | Path] | None = None,
) -> tuple[PluginHealthRow, ...]:
    records: list[PluginHealthRow] = []
    seen_ids: set[str] = set()
    for root in local_paths:
        for manifest_path in iter_manifest_paths(root):
            try:
                manifest = PluginManifest.load(manifest_path)
            except Exception as exc:
                records.append(
                    InvalidPluginHealthRecord(
                        source=str(manifest_path),
                        message=f"Invalid plugin manifest {manifest_path}: {exc}",
                    )
                )
                continue
            if manifest.id in seen_ids:
                records.append(
                    InvalidPluginHealthRecord(
                        source=str(manifest_path),
                        message=f"Duplicate plugin id: {manifest.id}",
                    )
                )
                continue
            seen_ids.add(manifest.id)
            records.append(
                build_plugin_health_record(
                    manifest,
                    source=str(manifest_path),
                    executable_paths=executable_paths,
                )
            )
    return tuple(records)


def plugin_health_records_as_json(records: Iterable[PluginHealthRow]) -> str:
    return json.dumps([record.to_dict() for record in records], indent=2, sort_keys=True)


def plugin_health_records_as_text(records: Iterable[PluginHealthRow]) -> str:
    lines = ["OSW plugin health"]
    rows = tuple(records)
    if not rows:
        lines.append("No local plugin manifests discovered.")
        return "\n".join(lines)

    for record in rows:
        data = record.to_dict()
        lines.append(
            f"- {data['plugin_id']} [{data['status']}]: "
            f"{data['display_name']} ({data['plugin_type'] or 'unknown'})"
        )
        lines.append(f"  dependency status: {data['dependency_status']}")
        for message in data["dependency_messages"]:
            lines.append(f"  dependency: {message}")
        for executable in data["executable_status"]:
            lines.append(f"  executable: {executable['message']}")
        if data["sample_project_reference"]:
            lines.append(f"  sample project: {data['sample_project_reference']}")
        lines.append(f"  last health check: {data['last_health_check_status']}")
        lines.append(f"  last run: {data['last_run_status']}")
        if data["source"]:
            lines.append(f"  source: {data['source']}")
    return "\n".join(lines)


def build_plugin_health_record(
    manifest: PluginManifest,
    *,
    enabled: bool = True,
    valid: bool = True,
    source: str = "",
    executable_paths: Mapping[str, str | Path] | None = None,
    last_health_check_status: str = "checked",
    last_run_status: str = "not-run",
) -> PluginHealthRecord:
    dependency_health = check_manifest_health(manifest)
    executable_status = _executable_status(manifest, executable_paths or {})
    status = _combine_status(dependency_health.status, executable_status)

    return PluginHealthRecord(
        plugin_id=manifest.id,
        display_name=manifest.name,
        version=manifest.version,
        plugin_type=manifest.type.value,
        domain=manifest.domain,
        status=status.value,
        dependency_status=dependency_health.status.value,
        dependency_messages=dependency_health.messages,
        executable_status=executable_status,
        sample_project_reference=_sample_project_reference(manifest),
        last_health_check_status=last_health_check_status,
        last_run_status=last_run_status,
        enabled=enabled,
        valid=valid,
        source=source,
    )


def _requirement_available(requirement: str) -> bool:
    module_name = requirement.split("[", 1)[0].split(">=", 1)[0].split("==", 1)[0]
    module_name = module_name.replace("-", "_").strip()
    if not module_name:
        return False
    return importlib.util.find_spec(module_name) is not None


def _combine_status(
    dependency_status: PluginHealthStatus,
    executable_status: tuple[PluginExecutableStatus, ...],
) -> PluginHealthStatus:
    if dependency_status is PluginHealthStatus.ERROR:
        return PluginHealthStatus.ERROR
    if any(not item.available for item in executable_status):
        return PluginHealthStatus.WARNING
    return dependency_status


def _executable_status(
    manifest: PluginManifest,
    executable_paths: Mapping[str, str | Path],
) -> tuple[PluginExecutableStatus, ...]:
    statuses: list[PluginExecutableStatus] = []
    for executable in _required_executables(manifest):
        configured_path = executable_paths.get(executable)
        configured_path_text = str(configured_path) if configured_path is not None else ""
        configured_exists = configured_path is not None and Path(configured_path).exists()
        found_path = shutil.which(executable)
        available = configured_exists or bool(found_path)
        message = (
            f"Executable available: {executable}"
            if available
            else (
                "Executable not configured or found: "
                f"{executable}. Set the path in Plugin Manager before preparing runs."
            )
        )
        statuses.append(
            PluginExecutableStatus(
                executable=executable,
                configured_path=configured_path_text,
                available=available,
                message=message,
            )
        )
    return tuple(statuses)


def _required_executables(manifest: PluginManifest) -> tuple[str, ...]:
    executables: list[str] = []
    for capability in manifest.capabilities:
        for prefix in EXECUTABLE_CAPABILITY_PREFIXES:
            if capability.startswith(prefix):
                executable = capability.removeprefix(prefix).strip()
                if executable:
                    executables.append(executable)
    return tuple(executables)


def _sample_project_reference(manifest: PluginManifest) -> str:
    for capability in manifest.capabilities:
        for prefix in SAMPLE_PROJECT_CAPABILITY_PREFIXES:
            if capability.startswith(prefix):
                return capability.removeprefix(prefix).strip()
    return ""
