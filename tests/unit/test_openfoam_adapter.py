from __future__ import annotations

from pathlib import Path

import pytest

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.health import PluginHealthStatus
from osw.plugins.manifest import PluginType
from osw.solvers.openfoam.adapter import OpenFoamCavityTemplateAdapter
from osw.solvers.openfoam.case_generator import OpenFoamCavityConfig


def test_openfoam_adapter_follows_solver_plugin_contract() -> None:
    adapter = OpenFoamCavityTemplateAdapter()

    assert isinstance(adapter, SolverAdapterPlugin)
    assert adapter.manifest.type is PluginType.SOLVER_ADAPTER
    assert adapter.id == "osw.solvers.openfoam.cavity_template"
    assert "prepare_case" in adapter.capabilities
    assert "execute" not in adapter.capabilities
    assert adapter.health().status == PluginHealthStatus.OK


def test_adapter_prepare_case_writes_template_without_running_openfoam(
    tmp_path: Path,
) -> None:
    adapter = OpenFoamCavityTemplateAdapter()

    prepared = adapter.prepare_case(
        {
            "case": OpenFoamCavityConfig(case_name="cavity_case"),
            "output_dir": tmp_path,
        }
    )

    assert prepared["solver"] == "OpenFOAM"
    assert prepared["adapter_id"] == "osw.solvers.openfoam.cavity_template"
    assert prepared["execution_mode"] == "prepare_only"
    assert prepared["case_dir"] == str(tmp_path / "cavity_case")
    assert prepared["run_command_preview"] == ["blockMesh", "icoFoam"]
    assert "system/controlDict" in prepared["files"]
    assert (tmp_path / "cavity_case" / "system" / "controlDict").exists()
    assert any("prepares a cavity template" in item for item in prepared["limitations"])


def test_adapter_requires_cavity_config_parameter(tmp_path: Path) -> None:
    adapter = OpenFoamCavityTemplateAdapter()

    with pytest.raises(TypeError, match="OpenFoamCavityConfig"):
        adapter.prepare_case({"case": object(), "output_dir": tmp_path})
