"""Unit tests for algorithm-aware OpenFOAM ``pFinal`` generation (issue #19).

These tests never run OpenFOAM, never resolve OpenFOAM executables, and never
touch the network. They exercise only deterministic template generation and the
CLI dispatch surface.
"""

from __future__ import annotations

from pathlib import Path

from osw.cli.main import main
from osw.solvers.openfoam.case_generator import (
    OpenFoamCavityConfig,
    OpenFoamDuctConfig,
    generate_cavity_case,
    generate_duct_case,
)
from osw.solvers.openfoam.model import OpenFOAMPropertyFileLayout

LEGACY = OpenFOAMPropertyFileLayout.LEGACY_TRANSPORT_PROPERTIES
FOUNDATION = OpenFOAMPropertyFileLayout.FOUNDATION_V11_PLUS_PHYSICAL_PROPERTIES

FVSOLUTION = "system/fvSolution"
TRANSPORT = "constant/transportProperties"
PHYSICAL = "constant/physicalProperties"

# The exact pFinal solver entry generated for PISO/icoFoam cases.
PFINAL_BLOCK = (
    "    pFinal\n"
    "    {\n"
    "        $p;\n"
    "        relTol          0;\n"
    "    }\n"
)


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Cavity (always icoFoam / PISO)                                              #
# --------------------------------------------------------------------------- #


def test_foundation_cavity_fvsolution_has_pfinal(tmp_path: Path) -> None:
    generated = generate_cavity_case(
        OpenFoamCavityConfig(property_file_layout=FOUNDATION), tmp_path
    )
    fv = _read(generated.root, FVSOLUTION)

    assert PFINAL_BLOCK in fv
    # p is preserved and pFinal reuses it via the OpenFOAM $p macro.
    assert "    p\n    {\n        solver          PCG;" in fv
    assert "$p;" in fv
    # The final corrector uses relTol 0.
    assert "        relTol          0;" in fv


def test_foundation_cavity_still_emits_physical_properties(tmp_path: Path) -> None:
    generated = generate_cavity_case(
        OpenFoamCavityConfig(property_file_layout=FOUNDATION), tmp_path
    )
    paths = set(generated.relative_paths)

    assert PHYSICAL in paths
    assert TRANSPORT not in paths
    assert "nu              [0 2 -1 0 0 0 0] 0.01;" in _read(generated.root, PHYSICAL)


def test_legacy_cavity_property_file_preserved_and_still_has_pfinal(tmp_path: Path) -> None:
    generated = generate_cavity_case(OpenFoamCavityConfig(), tmp_path)
    paths = set(generated.relative_paths)

    # Legacy layout keeps transportProperties (OSW-EXP-142 behavior unchanged)...
    assert TRANSPORT in paths
    assert PHYSICAL not in paths
    # ...and the cavity is always icoFoam/PISO, so pFinal is present regardless
    # of the property-file layout.
    assert PFINAL_BLOCK in _read(generated.root, FVSOLUTION)


def test_cavity_pfinal_appears_between_p_and_u(tmp_path: Path) -> None:
    fv = _read(generate_cavity_case(OpenFoamCavityConfig(), tmp_path).root, FVSOLUTION)
    p_idx = fv.index("    p\n    {")
    pfinal_idx = fv.index("    pFinal\n    {")
    u_idx = fv.index("    U\n    {")
    assert p_idx < pfinal_idx < u_idx


# --------------------------------------------------------------------------- #
# Duct (simpleFoam default = SIMPLE; icoFoam = PISO)                          #
# --------------------------------------------------------------------------- #


def test_default_duct_simplefoam_has_no_pfinal(tmp_path: Path) -> None:
    generated = generate_duct_case(OpenFoamDuctConfig(), tmp_path)
    fv = _read(generated.root, FVSOLUTION)

    assert "SIMPLE\n{" in fv
    assert "pFinal" not in fv


def test_default_duct_property_files_intact(tmp_path: Path) -> None:
    # Default duct (legacy layout) keeps transportProperties + turbulenceProperties.
    legacy = generate_duct_case(OpenFoamDuctConfig(), tmp_path / "legacy")
    legacy_paths = set(legacy.relative_paths)
    assert TRANSPORT in legacy_paths
    assert PHYSICAL not in legacy_paths
    assert "constant/turbulenceProperties" in legacy_paths

    # Foundation duct (simpleFoam) emits physicalProperties and still no pFinal.
    foundation = generate_duct_case(
        OpenFoamDuctConfig(property_file_layout=FOUNDATION), tmp_path / "foundation"
    )
    foundation_paths = set(foundation.relative_paths)
    assert PHYSICAL in foundation_paths
    assert TRANSPORT not in foundation_paths
    assert "pFinal" not in _read(foundation.root, FVSOLUTION)


def test_icofoam_duct_has_pfinal(tmp_path: Path) -> None:
    generated = generate_duct_case(OpenFoamDuctConfig(solver="icoFoam"), tmp_path)
    fv = _read(generated.root, FVSOLUTION)

    assert "PISO\n{" in fv
    assert PFINAL_BLOCK in fv


def test_icofoam_foundation_duct_has_pfinal_and_physical_properties(tmp_path: Path) -> None:
    generated = generate_duct_case(
        OpenFoamDuctConfig(solver="icoFoam", property_file_layout=FOUNDATION), tmp_path
    )
    paths = set(generated.relative_paths)
    assert PHYSICAL in paths
    assert TRANSPORT not in paths
    assert PFINAL_BLOCK in _read(generated.root, FVSOLUTION)


# --------------------------------------------------------------------------- #
# CLI surface                                                                 #
# --------------------------------------------------------------------------- #


def test_cli_cavity_generation_emits_pfinal(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "cav"
    code = main(
        [
            "openfoam-write-case",
            "--template",
            "cavity",
            "--out-dir",
            str(out_dir),
            "--property-file-layout",
            "foundation_v11_plus",
        ]
    )
    capsys.readouterr()

    assert code == 0
    assert (out_dir / "constant" / "physicalProperties").exists()
    assert PFINAL_BLOCK in (out_dir / "system" / "fvSolution").read_text(encoding="utf-8")


def test_cli_duct_simplefoam_has_no_pfinal(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "duct"
    code = main(["openfoam-write-case", "--template", "duct", "--out-dir", str(out_dir)])
    capsys.readouterr()

    assert code == 0
    assert "pFinal" not in (out_dir / "system" / "fvSolution").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# No live solver execution                                                    #
# --------------------------------------------------------------------------- #


def test_case_generator_source_has_no_solver_execution() -> None:
    """The generator must never spawn OpenFOAM; fvSolution is pure text."""

    from osw.solvers.openfoam import case_generator

    source = Path(case_generator.__file__).read_text(encoding="utf-8")
    for forbidden in ("subprocess", "os.system", "Popen", "check_call", "check_output"):
        assert forbidden not in source, forbidden
