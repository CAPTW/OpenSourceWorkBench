from __future__ import annotations

from pathlib import Path

from helpers import assert_text_matches_golden
from osw.solvers.openfoam.case_generator import OpenFoamCavityConfig, generate_cavity_case

GOLDEN_FILES = (
    "0/U",
    "0/p",
    "constant/transportProperties",
    "system/blockMeshDict",
    "system/controlDict",
    "system/fvSchemes",
    "system/fvSolution",
)


def test_cavity_template_matches_golden_fixture(tmp_path: Path) -> None:
    generated = generate_cavity_case(OpenFoamCavityConfig(), tmp_path)
    expected_root = Path(__file__).parent / "cavity"

    for relative_path in GOLDEN_FILES:
        expected = (expected_root / relative_path).read_text(encoding="utf-8")
        actual = (generated.root / relative_path).read_text(encoding="utf-8")
        assert_text_matches_golden(
            actual,
            expected,
            label=f"openfoam/cavity/{relative_path}",
            replacements=((generated.root, "<CASE_ROOT>"), (tmp_path, "<TMP>")),
        )
