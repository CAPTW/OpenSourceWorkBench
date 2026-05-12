"""Plugin health checks that avoid loading heavy optional integrations."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from enum import Enum

from .manifest import PluginManifest


class PluginHealthStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class PluginHealth:
    status: PluginHealthStatus
    messages: tuple[str, ...] = field(default_factory=tuple)


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


def _requirement_available(requirement: str) -> bool:
    module_name = requirement.split("[", 1)[0].split(">=", 1)[0].split("==", 1)[0]
    module_name = module_name.replace("-", "_").strip()
    if not module_name:
        return False
    return importlib.util.find_spec(module_name) is not None
