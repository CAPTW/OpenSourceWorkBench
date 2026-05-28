from __future__ import annotations

import json
from pathlib import Path

from osw.scripts.mscript.mat_model import (
    MatFileSummary,
    MatFileVersion,
    MatReadResult,
    MatReadStatus,
    MatTablePreview,
    MatVariableKind,
    MatVariableSummary,
)


def test_mat_variable_summary_serializes() -> None:
    summary = MatVariableSummary(
        "x",
        kind=MatVariableKind.NUMERIC,
        type_name="ndarray",
        shape=(3,),
        dtype="float64",
        size=3,
        is_numeric=True,
        preview="[0, 1, 2]",
        min_value=0.0,
        max_value=2.0,
        mean_value=1.0,
        source_file="data.mat",
    )

    loaded = MatVariableSummary.from_dict(summary.to_dict())

    assert loaded == summary
    assert loaded.display_shape == "3"


def test_mat_table_preview_serializes_and_exports_csv(tmp_path: Path) -> None:
    preview = MatTablePreview(
        variable_name="table2d",
        columns=("a", "b"),
        rows=(("1", "2"), ("3", "4")),
        row_count=2,
        column_count=2,
    )

    loaded = MatTablePreview.from_dict(preview.to_dict())
    output = loaded.export_csv(tmp_path / "table.csv")

    assert loaded == preview
    assert output.read_text(encoding="utf-8").splitlines() == ["a,b", "1,2", "3,4"]


def test_mat_file_summary_and_read_result_json_round_trip() -> None:
    variable = MatVariableSummary("x", (3,), "float64", True, kind="numeric")
    summary = MatFileSummary(
        source_path=Path("numeric_arrays.mat"),
        version=MatFileVersion.V4,
        variables=(variable,),
    )
    result = MatReadResult(MatReadStatus.OK, summary)

    payload = json.loads(json.dumps(result.to_dict()))
    loaded = MatReadResult.from_dict(payload)

    assert loaded.status == "ok"
    assert loaded.summary.source_path == "numeric_arrays.mat"
    assert loaded.summary.variables[0].name == "x"
