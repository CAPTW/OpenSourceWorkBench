from __future__ import annotations

from pathlib import Path

import pytest

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginType
from osw.solvers.openfoam.adapter import OpenFoamDuctTemplateAdapter
from osw.solvers.openfoam.case_generator import (
    OpenFoamCaseTemplateError,
    OpenFoamDuctCaseGenerator,
    OpenFoamDuctConfig,
    OpenFoamDuctPatchConfig,
    generate_duct_case,
)
from osw.solvers.openfoam.residuals import OpenFoamResidualParser

EXPECTED_DUCT_FILES = {
    "0/U",
    "0/p",
    "constant/transportProperties",
    "constant/turbulenceProperties",
    "system/blockMeshDict",
    "system/controlDict",
    "system/fvSchemes",
    "system/fvSolution",
}


def test_duct_case_generator_writes_required_case_files(tmp_path: Path) -> None:
    generated = generate_duct_case(
        OpenFoamDuctConfig(
            case_name="duct_demo",
            solver="icoFoam",
            length=2.0,
            height=0.25,
            depth=0.05,
            cells=(16, 4, 2),
            inlet_velocity=(2.5, 0.0, 0.0),
            outlet_pressure=101325.0,
            viscosity=1.5e-5,
            end_time=2.0,
            delta_t=0.01,
            write_interval=0.5,
        ),
        tmp_path,
    )

    assert generated.root == tmp_path / "duct_demo"
    assert set(generated.relative_paths) == EXPECTED_DUCT_FILES
    assert not generated.warnings
    assert "application     icoFoam;" in _read(generated.root, "system/controlDict")
    assert "uniform (2.5 0 0)" in _read(generated.root, "0/U")
    assert "outlet" in _read(generated.root, "0/p")
    assert "uniform 101325" in _read(generated.root, "0/p")
    assert "nu              [0 2 -1 0 0 0 0] 1.5e-05;" in _read(
        generated.root,
        "constant/transportProperties",
    )
    assert "hex (0 1 2 3 4 5 6 7) (16 4 2) simpleGrading (1 1 1)" in _read(
        generated.root,
        "system/blockMeshDict",
    )


def test_missing_duct_patch_names_warn_and_use_defaults(tmp_path: Path) -> None:
    config = OpenFoamDuctConfig(
        case_name="duct_defaults",
        patches=OpenFoamDuctPatchConfig(inlet="", outlet="", walls=(), front_and_back=""),
    )
    generator = OpenFoamDuctCaseGenerator()

    report = generator.validate(config)
    generated = generator.generate(config, tmp_path)

    assert report.has_warnings
    summary = report.friendly_summary()
    assert "Inlet patch name is missing" in summary
    assert "Outlet patch name is missing" in summary
    assert "Wall patch name is missing" in summary
    assert "Front/back patch name is missing" in summary
    assert "default inlet" in " ".join(generated.warnings)
    assert "inlet" in _read(generated.root, "0/U")
    assert "outlet" in _read(generated.root, "0/p")
    assert "walls" in _read(generated.root, "system/blockMeshDict")


def test_invalid_duct_solver_choice_is_reported_clearly(tmp_path: Path) -> None:
    config = OpenFoamDuctConfig(case_name="bad_solver", solver="rhoPimpleFoam")

    with pytest.raises(OpenFoamCaseTemplateError, match="Unsupported duct solver"):
        OpenFoamDuctCaseGenerator().generate(config, tmp_path)


def test_duct_adapter_prepares_case_without_running_openfoam(tmp_path: Path) -> None:
    adapter = OpenFoamDuctTemplateAdapter()

    prepared = adapter.prepare_case(
        {
            "case": OpenFoamDuctConfig(case_name="duct_case"),
            "output_dir": tmp_path,
        }
    )

    assert isinstance(adapter, SolverAdapterPlugin)
    assert adapter.manifest.type is PluginType.SOLVER_ADAPTER
    assert adapter.id == "osw.solvers.openfoam.duct_template"
    assert "execute" not in adapter.capabilities
    assert prepared["execution_mode"] == "prepare_only"
    assert prepared["case_dir"] == str(tmp_path / "duct_case")
    assert prepared["run_command_preview"] == ["blockMesh", "simpleFoam"]
    assert "system/controlDict" in prepared["files"]
    assert (tmp_path / "duct_case" / "system" / "controlDict").exists()


def test_residual_parser_interface_extracts_common_solver_lines() -> None:
    text = "\n".join(
        [
            "Time = 12",
            (
                "smoothSolver:  Solving for Ux, Initial residual = 0.1, "
                "Final residual = 0.01, No Iterations 2"
            ),
            (
                "GAMG:  Solving for p, Initial residual = 0.2, "
                "Final residual = 0.02, No Iterations 4"
            ),
        ]
    )

    series = OpenFoamResidualParser().parse_text(text)

    assert series.fields == ("Ux", "p")
    assert series.points[0].time == 12.0
    assert series.points[0].field == "Ux"
    assert series.points[0].initial_residual == 0.1
    assert series.points[0].final_residual == 0.01
    assert series.points[0].solver_iterations == 2
    assert series.to_dict()["points"][1]["field"] == "p"


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")
