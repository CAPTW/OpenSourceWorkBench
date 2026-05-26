from __future__ import annotations

import json
from pathlib import Path

from osw.plugins.state import PluginStateStore


def test_plugin_enable_disable_state_round_trips(tmp_path: Path) -> None:
    state_path = tmp_path / "plugin-state.json"
    store = PluginStateStore(state_path)

    store.set_enabled("osw.demo", False)

    restored = PluginStateStore(state_path)
    assert not restored.is_enabled("osw.demo")
    assert restored.is_enabled("osw.other")


def test_corrupt_state_file_falls_back_with_diagnostic(tmp_path: Path) -> None:
    state_path = tmp_path / "plugin-state.json"
    state_path.write_text("{not-json", encoding="utf-8")

    store = PluginStateStore(state_path)

    assert store.is_enabled("osw.demo")
    assert store.diagnostics
    assert store.diagnostics[0].code == "plugin-state-unreadable"


def test_configured_executable_path_persists(tmp_path: Path) -> None:
    state_path = tmp_path / "plugin-state.json"
    executable = tmp_path / "solver.exe"
    executable.write_text("", encoding="utf-8")
    store = PluginStateStore(state_path)

    store.set_executable_path("ccx", executable)

    restored = PluginStateStore(state_path)
    assert restored.get_executable_path("ccx") == str(executable)
    assert restored.executable_paths() == {"ccx": str(executable)}


def test_legacy_enablement_shape_is_read(tmp_path: Path) -> None:
    state_path = tmp_path / "plugin-state.json"
    state_path.write_text(json.dumps({"osw.disabled": False}), encoding="utf-8")

    store = PluginStateStore(state_path)

    assert not store.is_enabled("osw.disabled")
