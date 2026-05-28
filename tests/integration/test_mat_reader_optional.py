from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from osw.scripts.mscript.mat_model import MatReadStatus
from osw.scripts.mscript.mat_reader import export_variable_to_csv, read_mat_file


def scipy_available() -> bool:
    return importlib.util.find_spec("scipy") is not None


def hdf5_available() -> bool:
    return (
        importlib.util.find_spec("hdf5storage") is not None
        or importlib.util.find_spec("h5py") is not None
    )


def test_optional_scipy_mat_round_trip(tmp_path: Path) -> None:
    if not scipy_available():
        pytest.skip("scipy optional mscript extra is not installed.")

    import numpy as np
    from scipy.io import savemat

    mat_path = tmp_path / "generated.mat"
    savemat(
        mat_path,
        {
            "x": np.array([0.0, 1.0, 2.0]),
            "table2d": np.array([[1.0, 2.0], [3.0, 4.0]]),
        },
    )

    result = read_mat_file(mat_path)
    export = export_variable_to_csv(mat_path, "x", tmp_path / "x.csv")

    assert result.ok
    assert set(result.variable_names) == {"x", "table2d"}
    assert export.ok
    assert Path(export.output_path).read_text(encoding="utf-8").strip()


def test_v73_missing_optional_dependency_diagnostic(tmp_path: Path) -> None:
    if hdf5_available():
        pytest.skip("hdf5 optional support is installed; tree summary is covered by unit paths.")

    mat_path = tmp_path / "v73.mat"
    mat_path.write_bytes(b"\x89HDF\r\n\x1a\nplaceholder")

    result = read_mat_file(mat_path)

    assert result.status == MatReadStatus.DEPENDENCY_MISSING.value
    assert "MAT v7.3" in result.diagnostics.summary()
