"""Persistent plugin enablement and executable path state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.plugins.errors import PluginDiagnostic


@dataclass
class PluginStateStore:
    """Small JSON-backed state store for plugin GUI preferences.

    The store deliberately stays independent of PySide6 so plugin settings can
    be exercised by CLI and unit tests. Without a path it behaves as an
    in-memory store, which is useful for dialog smoke tests.
    """

    path: str | Path | None = None
    default_enabled: bool = True
    _disabled_plugin_ids: set[str] = field(default_factory=set, init=False)
    _executable_paths: dict[str, str] = field(default_factory=dict, init=False)
    _diagnostics: list[PluginDiagnostic] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._path = Path(self.path) if self.path is not None else None
        self.load()

    @property
    def diagnostics(self) -> tuple[PluginDiagnostic, ...]:
        return tuple(self._diagnostics)

    def is_enabled(self, plugin_id: str) -> bool:
        if not plugin_id:
            return self.default_enabled
        if self.default_enabled:
            return plugin_id not in self._disabled_plugin_ids
        return plugin_id in self._enabled_plugin_ids_from_disabled_mode()

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        if not plugin_id:
            return
        if enabled:
            self._disabled_plugin_ids.discard(plugin_id)
        else:
            self._disabled_plugin_ids.add(plugin_id)
        self.save()

    def disabled_plugin_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._disabled_plugin_ids))

    def set_executable_path(self, name: str, path: str | Path | None) -> None:
        key = self._normalize_name(name)
        if not key:
            return
        text = "" if path is None else str(path).strip()
        if text:
            self._executable_paths[key] = text
        else:
            self._executable_paths.pop(key, None)
        self.save()

    def get_executable_path(self, name: str) -> str | None:
        return self._executable_paths.get(self._normalize_name(name))

    def executable_paths(self) -> dict[str, str]:
        return dict(self._executable_paths)

    def to_dict(self) -> dict[str, Any]:
        return {
            "disabled_plugin_ids": sorted(self._disabled_plugin_ids),
            "executable_paths": dict(sorted(self._executable_paths.items())),
        }

    def load(self) -> None:
        self._disabled_plugin_ids.clear()
        self._executable_paths.clear()
        if self._path is None or not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._diagnostics.append(
                PluginDiagnostic.warning(
                    "plugin-state-unreadable",
                    f"Plugin state could not be read; using defaults: {exc}",
                    source=str(self._path),
                )
            )
            return
        self._load_mapping(data)

    def save(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _load_mapping(self, data: object) -> None:
        if not isinstance(data, dict):
            self._diagnostics.append(
                PluginDiagnostic.warning(
                    "plugin-state-invalid",
                    "Plugin state file must contain a JSON object; using defaults.",
                    source=str(self._path or ""),
                )
            )
            return

        if "disabled_plugin_ids" in data or "executable_paths" in data:
            disabled = data.get("disabled_plugin_ids", [])
            if isinstance(disabled, list | tuple):
                self._disabled_plugin_ids = {str(item) for item in disabled if str(item)}
            executable_paths = data.get("executable_paths", {})
            if isinstance(executable_paths, dict):
                self._executable_paths = {
                    self._normalize_name(key): str(value)
                    for key, value in executable_paths.items()
                    if self._normalize_name(key) and str(value).strip()
                }
            return

        # Backward-compatible state shape from the pre-binding GUI model:
        # {"plugin.id": true/false}
        self._disabled_plugin_ids = {
            str(plugin_id)
            for plugin_id, enabled in data.items()
            if isinstance(enabled, bool) and not enabled
        }

    def _enabled_plugin_ids_from_disabled_mode(self) -> set[str]:
        return set()

    @staticmethod
    def _normalize_name(name: object) -> str:
        return str(name).strip().lower()
