from __future__ import annotations

from pathlib import Path

import pytest

from osw.solvers.openfoam.case_generator import (
    OpenFoamCaseGenerator,
    OpenFoamCaseTemplateError,
    OpenFoamCavityConfig,
    generate_cavity_case,
)

EXPECTED_CAVITY_FILES = {
    "0/U",
    "0/p",
    "constant/transportProperties",
    "system/blockMeshDict",
    "system/controlDict",
    "system/fvSchemes",
    "system/fvSolution",
}


def test_cavity_case_generator_writes_required_openfoam_files(tmp_path: Path) -> None:
    generated = generate_cavity_case(
        OpenFoamCavityConfig(
            case_name="cavity_demo",
            length=0.1,
            cells=(12, 8, 1),
            viscosity=0.01,
            end_time=0.5,
            delta_t=0.005,
            write_interval=0.1,
        ),
        tmp_path,
    )

    assert generated.root == tmp_path / "cavity_demo"
    assert set(generated.relative_paths) == EXPECTED_CAVITY_FILES
    assert not generated.warnings
    assert "application     icoFoam;" in _read(generated.root, "system/controlDict")
    assert "nu              [0 2 -1 0 0 0 0] 0.01;" in _read(
        generated.root,
        "constant/transportProperties",
    )
    assert "hex (0 1 2 3 4 5 6 7) (12 8 1) simpleGrading (1 1 1)" in _read(
        generated.root,
        "system/blockMeshDict",
    )
    assert "movingWall" in _read(generated.root, "0/U")
    assert "uniform (1 0 0)" in _read(generated.root, "0/U")


def test_missing_boundary_config_warns_and_uses_default_cavity_boundaries(
    tmp_path: Path,
) -> None:
    generator = OpenFoamCaseGenerator()
    config = OpenFoamCavityConfig(case_name="defaulted_boundaries", boundaries=None)

    report = generator.validate(config)
    generated = generator.generate(config, tmp_path)

    assert report.has_warnings
    assert "Boundary configuration is missing" in report.friendly_summary()
    assert any("default lid-driven cavity boundaries" in warning for warning in generated.warnings)
    assert "movingWall" in _read(generated.root, "0/U")
    assert "fixedWalls" in _read(generated.root, "0/p")


def test_invalid_cavity_dimensions_are_reported_clearly(tmp_path: Path) -> None:
    config = OpenFoamCavityConfig(case_name="invalid", length=0.0)

    with pytest.raises(OpenFoamCaseTemplateError, match="Cavity length must be positive"):
        OpenFoamCaseGenerator().generate(config, tmp_path)


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")
