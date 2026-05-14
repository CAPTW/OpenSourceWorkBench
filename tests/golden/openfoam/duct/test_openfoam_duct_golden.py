from __future__ import annotations

from pathlib import Path

from osw.solvers.openfoam.case_generator import OpenFoamDuctConfig, generate_duct_case

GOLDEN_FILES = (
    "0/U",
    "0/p",
    "constant/transportProperties",
    "constant/turbulenceProperties",
    "system/blockMeshDict",
    "system/controlDict",
    "system/fvSchemes",
    "system/fvSolution",
)


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def test_duct_template_matches_golden_fixture(tmp_path: Path) -> None:
    generated = generate_duct_case(OpenFoamDuctConfig(), tmp_path)
    expected_root = Path(__file__).parent

    for relative_path in GOLDEN_FILES:
        expected = (expected_root / relative_path).read_text(encoding="utf-8")
        actual = (generated.root / relative_path).read_text(encoding="utf-8")
        assert normalize(actual) == normalize(expected), relative_path
