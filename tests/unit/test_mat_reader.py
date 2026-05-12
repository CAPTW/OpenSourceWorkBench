from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from osw.scripts.mscript.mat_reader import MatReader, export_mat_variable_csv, read_mat_file


def scipy_available() -> bool:
    return importlib.util.find_spec("scipy") is not None


def write_sample_mat(path: Path) -> None:
    if not scipy_available():
        pytest.skip("scipy optional mscript extra is not installed.")

    import numpy as np
    from scipy.io import savemat

    savemat(
        path,
        {
            "time": np.array([0.0, 0.5, 1.0]),
            "stress": np.array([[1.0, 2.0], [3.0, 4.0]]),
            "title": "cantilever",
        },
    )


def test_mat_sample_loads_and_summarizes_numeric_arrays(tmp_path: Path) -> None:
    mat_path = tmp_path / "sample.mat"
    write_sample_mat(mat_path)

    preview = read_mat_file(mat_path)

    assert not preview.diagnostics.has_errors
    assert preview.variable_names == ("stress", "time", "title")
    stress = preview.variable("stress")
    assert stress.shape == (2, 2)
    assert stress.is_numeric is True
    assert stress.dtype.startswith("float")
    assert "2x2" in stress.display_shape
    assert preview.variable("title").is_numeric is False


def test_table_preview_and_csv_export_for_numeric_array(tmp_path: Path) -> None:
    mat_path = tmp_path / "sample.mat"
    write_sample_mat(mat_path)
    preview = read_mat_file(mat_path)

    table = preview.table_preview("stress")
    output = export_mat_variable_csv(preview, "stress", tmp_path / "stress.csv")

    assert table.columns == ("col_0", "col_1")
    assert table.rows == (("1.0", "2.0"), ("3.0", "4.0"))
    assert output.read_text(encoding="utf-8").splitlines() == [
        "col_0,col_1",
        "1.0,2.0",
        "3.0,4.0",
    ]


def test_missing_scipy_gives_friendly_diagnostic(tmp_path: Path) -> None:
    mat_path = tmp_path / "sample.mat"
    mat_path.write_bytes(b"MATLAB 5.0 MAT-file placeholder")

    preview = MatReader(scipy_loadmat=None).read(mat_path)

    assert preview.variables == ()
    assert preview.diagnostics.has_errors
    assert "scipy" in preview.diagnostics.summary().lower()
    assert "python -m pip install -e .[mscript]" in preview.diagnostics.summary()


def test_v73_hdf5_path_is_explicit_and_non_crashing(tmp_path: Path) -> None:
    mat_path = tmp_path / "v73.mat"
    mat_path.write_bytes(b"\x89HDF\r\n\x1a\nplaceholder")

    preview = MatReader(scipy_loadmat=None, hdf5storage_loadmat=None).read(mat_path)

    assert preview.format_version == "7.3"
    assert preview.variables == ()
    assert preview.diagnostics.has_warnings
    assert "MAT v7.3" in preview.diagnostics.summary()
    assert "hdf5storage" in preview.diagnostics.summary()


def test_invalid_extension_returns_friendly_error(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("not a mat file", encoding="utf-8")

    preview = read_mat_file(path)

    assert preview.diagnostics.has_errors
    assert "Only .mat files" in preview.diagnostics.summary()
