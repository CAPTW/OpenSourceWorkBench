from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from osw.scripts.mscript.mat_model import MatReadStatus
from osw.scripts.mscript.mat_reader import export_variable_to_csv

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mat"


def scipy_available() -> bool:
    return importlib.util.find_spec("scipy") is not None


def test_export_reports_dependency_when_scipy_missing(tmp_path: Path) -> None:
    if scipy_available():
        pytest.skip("dependency-missing behavior is specific to environments without scipy.")

    result = export_variable_to_csv(FIXTURES / "numeric_arrays.mat", "x", tmp_path / "x.csv")

    assert result.status == MatReadStatus.DEPENDENCY_MISSING.value
    assert result.diagnostics.has_errors
    assert "SciPy" in result.diagnostics.summary()


def test_export_1d_and_2d_numeric_variables_when_scipy_available(tmp_path: Path) -> None:
    if not scipy_available():
        pytest.skip("scipy optional mscript extra is not installed.")

    x_result = export_variable_to_csv(FIXTURES / "numeric_arrays.mat", "x", tmp_path / "x.csv")
    table_result = export_variable_to_csv(
        FIXTURES / "numeric_arrays.mat",
        "table2d",
        tmp_path / "table2d.csv",
    )

    assert x_result.ok
    assert Path(x_result.output_path).read_text(encoding="utf-8").splitlines()[0] == "x"
    assert table_result.ok
    assert Path(table_result.output_path).read_text(encoding="utf-8").splitlines()[0] == (
        "table2d_1,table2d_2"
    )


def test_export_missing_variable_is_friendly(tmp_path: Path) -> None:
    result = export_variable_to_csv(
        FIXTURES / "numeric_arrays.mat",
        "missing",
        tmp_path / "missing.csv",
    )

    if result.status == MatReadStatus.DEPENDENCY_MISSING.value:
        assert "SciPy" in result.diagnostics.summary()
    else:
        assert result.status == MatReadStatus.ERROR.value
        assert "missing" in result.diagnostics.summary()
