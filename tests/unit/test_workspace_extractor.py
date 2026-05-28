from __future__ import annotations

from pathlib import Path

from osw.scripts.mscript.mat_model import MatFileSummary, MatVariableSummary
from osw.scripts.mscript.workspace_extractor import (
    extract_workspace_summary,
    extract_workspace_summary_from_artifacts,
    mat_summary_to_workspace_variables,
    summarize_csv,
    summarize_json_variables,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "figures"


def test_summarize_csv_counts_rows_and_columns() -> None:
    summary = summarize_csv(FIXTURES / "table_data.csv")

    assert summary.name == "table_data"
    assert summary.type_name == "table"
    assert summary.shape == (3, 2)
    assert summary.metadata["columns"] == ["x", "y"]


def test_summarize_json_variables_reads_declared_variables() -> None:
    variables = summarize_json_variables(FIXTURES / "workspace_summary.json")

    assert {variable.name for variable in variables} == {"x", "temperature"}
    assert variables[0].shape == (1, 3)


def test_extract_workspace_summary_from_mixed_artifacts() -> None:
    variables = extract_workspace_summary_from_artifacts(
        (FIXTURES / "table_data.csv", FIXTURES / "workspace_summary.json")
    )

    assert {variable.name for variable in variables} >= {"table_data", "x"}


def test_corrupt_json_produces_diagnostic(tmp_path: Path) -> None:
    corrupt = tmp_path / "workspace_summary.json"
    corrupt.write_text("{not-json", encoding="utf-8")

    result = extract_workspace_summary((corrupt,))

    assert result.variables == ()
    assert result.diagnostics.messages
    assert result.diagnostics.messages[0].code == "workspace-summary-unreadable"


def test_large_csv_summary_only_keeps_preview_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "large.csv"
    csv_path.write_text(
        "a,b\n" + "\n".join(f"{index},{index * index}" for index in range(50)),
        encoding="utf-8",
    )

    summary = summarize_csv(csv_path)

    assert summary.shape == (50, 2)
    assert summary.metadata["preview_row_count"] == 3
    assert "49" not in summary.preview


def test_mat_summary_converts_to_workspace_variables() -> None:
    mat_summary = MatFileSummary(
        source_path="data.mat",
        variables=(
            MatVariableSummary(
                "temperature",
                shape=(3,),
                dtype="float64",
                is_numeric=True,
                kind="numeric",
                preview="[300, 325, 350]",
            ),
        ),
    )

    variables = mat_summary_to_workspace_variables(mat_summary)

    assert variables[0].name == "temperature"
    assert variables[0].type_name == "numeric"
    assert variables[0].metadata["is_numeric"] is True
