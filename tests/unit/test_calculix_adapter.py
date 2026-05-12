from __future__ import annotations

from pathlib import Path

from osw.core.materials import IsotropicElastic, Material
from osw.core.units import Quantity
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.health import PluginHealthStatus
from osw.plugins.manifest import PluginType
from osw.solvers.calculix.adapter import CalculixLinearStaticAdapter
from osw.solvers.calculix.input_deck import (
    CalculixBoundaryCondition,
    CalculixLinearStaticCase,
    CalculixLoad,
    CalculixNodeSet,
)


def cantilever_case() -> CalculixLinearStaticCase:
    return CalculixLinearStaticCase(
        case_id="cantilever",
        mesh=MeshData(
            points=(
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (1.0, 0.2, 0.0),
                (0.0, 0.2, 0.0),
                (0.0, 0.0, 0.2),
                (1.0, 0.0, 0.2),
                (1.0, 0.2, 0.2),
                (0.0, 0.2, 0.2),
            ),
            cells=(MeshCellBlock("hexahedron", ((0, 1, 2, 3, 4, 5, 6, 7),)),),
        ),
        material=Material(
            material_id="steel",
            name="Steel",
            density=Quantity(7850.0, "kg/m^3"),
            elastic=IsotropicElastic(
                young_modulus=Quantity(210_000_000_000.0, "Pa"),
                poisson_ratio=0.3,
            ),
        ),
        node_sets=(
            CalculixNodeSet("FIXED", (1, 4, 5, 8)),
            CalculixNodeSet("TIP", (2, 3, 6, 7)),
        ),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),
        ),
        loads=(
            CalculixLoad.force(
                name="tip-force",
                node_set="TIP",
                dof=2,
                value=-100.0,
            ),
        ),
    )


def test_calculix_adapter_follows_solver_plugin_contract() -> None:
    adapter = CalculixLinearStaticAdapter()

    assert isinstance(adapter, SolverAdapterPlugin)
    assert adapter.manifest.type is PluginType.SOLVER_ADAPTER
    assert adapter.id == "osw.solvers.calculix.linear_static"
    assert "prepare_case" in adapter.capabilities
    assert adapter.health().status == PluginHealthStatus.OK


def test_adapter_prepare_case_writes_input_deck_without_executing_solver(tmp_path: Path) -> None:
    output_path = tmp_path / "cantilever.inp"
    adapter = CalculixLinearStaticAdapter()

    prepared = adapter.prepare_case(
        {
            "case": cantilever_case(),
            "output_path": output_path,
        }
    )

    assert prepared["execution_mode"] == "prepare_only"
    assert prepared["input_deck_path"] == str(output_path)
    assert prepared["solver"] == "CalculiX"
    assert prepared["run_command_preview"] == ["ccx", "cantilever"]
    assert output_path.exists()
    assert "*STEP, NAME=linear_static" in output_path.read_text(encoding="utf-8")
