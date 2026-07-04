from __future__ import annotations

from pathlib import Path

from helpers import assert_text_matches_golden

from osw.solvers.openfoam.case_generator import (
    OpenFoamCavityConfig,
    OpenFoamDuctConfig,
    generate_cavity_case,
    generate_duct_case,
)
from osw.solvers.openfoam.model import OpenFOAMPropertyFileLayout

FOUNDATION = OpenFOAMPropertyFileLayout.FOUNDATION_V11_PLUS_PHYSICAL_PROPERTIES


def test_cavity_foundation_v12_physical_properties_matches_golden(tmp_path: Path) -> None:
    generated = generate_cavity_case(
        OpenFoamCavityConfig(property_file_layout=FOUNDATION),
        tmp_path,
    )
    relative_paths = set(generated.relative_paths)

    assert "constant/physicalProperties" in relative_paths
    assert "constant/transportProperties" not in relative_paths

    expected = (
        Path(__file__).parent / "cavity_foundation_v12" / "constant" / "physicalProperties"
    ).read_text(encoding="utf-8")
    actual = (generated.root / "constant" / "physicalProperties").read_text(encoding="utf-8")
    assert_text_matches_golden(
        actual,
        expected,
        label="openfoam/cavity_foundation_v12/constant/physicalProperties",
        replacements=((generated.root, "<CASE_ROOT>"), (tmp_path, "<TMP>")),
    )


def test_duct_foundation_v12_physical_properties_matches_golden(tmp_path: Path) -> None:
    generated = generate_duct_case(
        OpenFoamDuctConfig(property_file_layout=FOUNDATION),
        tmp_path,
    )
    relative_paths = set(generated.relative_paths)

    assert "constant/physicalProperties" in relative_paths
    assert "constant/transportProperties" not in relative_paths
    # The duct's laminar turbulenceProperties file is unaffected by the layout.
    assert "constant/turbulenceProperties" in relative_paths

    expected = (
        Path(__file__).parent / "duct_foundation_v12" / "constant" / "physicalProperties"
    ).read_text(encoding="utf-8")
    actual = (generated.root / "constant" / "physicalProperties").read_text(encoding="utf-8")
    assert_text_matches_golden(
        actual,
        expected,
        label="openfoam/duct_foundation_v12/constant/physicalProperties",
        replacements=((generated.root, "<CASE_ROOT>"), (tmp_path, "<TMP>")),
    )
