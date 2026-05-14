from __future__ import annotations

from pathlib import Path

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginType
from osw.solvers.su2.adapter import Su2BasicAdapter
from osw.solvers.su2.config import Su2SimulationConfig


def test_su2_adapter_follows_solver_adapter_contract() -> None:
    adapter = Su2BasicAdapter()
    manifest = adapter.manifest

    assert isinstance(adapter, SolverAdapterPlugin)
    assert manifest.id == "osw.solvers.su2.basic"
    assert manifest.type is PluginType.SOLVER_ADAPTER
    assert "validate" in manifest.capabilities
    assert "prepare_case" in manifest.capabilities
    assert "cfg_generator" in manifest.capabilities
    assert "dry_run" in manifest.capabilities
    assert "execute" not in manifest.capabilities


def test_su2_adapter_prepares_cfg_without_running_solver(tmp_path: Path) -> None:
    adapter = Su2BasicAdapter()
    config = Su2SimulationConfig(case_name="case_a", mesh_filename="mesh.su2")

    prepared = adapter.prepare_case({"case": config, "output_dir": tmp_path})

    config_path = Path(prepared["config_path"])
    assert config_path == tmp_path / "case_a.cfg"
    assert config_path.exists()
    assert prepared["solver"] == "SU2"
    assert prepared["execution_mode"] == "prepare_only"
    assert prepared["mesh_reference"] == "mesh.su2"
    assert prepared["run_command_preview"] == ["SU2_CFD", "case_a.cfg"]
