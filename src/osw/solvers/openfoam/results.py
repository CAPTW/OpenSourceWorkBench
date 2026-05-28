"""ResultDataset bridge for OpenFOAM residual summaries."""

from __future__ import annotations

from osw.core.result_dataset import (
    ResultDataset,
    ResultField,
    ResultRow,
    ResultSummaryValue,
)
from osw.solvers.openfoam.model import OpenFOAMResidualSummary, OpenFOAMRunResult


def openfoam_residuals_to_result_dataset(
    summary: OpenFOAMResidualSummary,
    *,
    run_result: OpenFOAMRunResult | None = None,
    dataset_id: str = "",
    solver: str = "",
) -> ResultDataset:
    """Convert parsed residuals into the lightweight OSW ResultDataset contract."""

    fields = tuple(series.field for series in summary.series)
    max_rows = max((len(series.values) for series in summary.series), default=0)
    rows: list[ResultRow] = []
    for row_index in range(max_rows):
        values: dict[str, float] = {}
        for series in summary.series:
            if row_index < len(series.values):
                values[series.field] = float(series.values[row_index])
        rows.append(ResultRow(entity_id=row_index + 1, values=values))

    residual_field = (
        ResultField(
            name="residuals",
            location="global",
            components=fields,
            rows=tuple(rows),
            unit="",
        ),
    ) if fields else ()
    summaries = tuple(
        ResultSummaryValue(
            name=f"final_residual_{field}",
            value=value,
            unit="",
            source_field=field,
        )
        for field, value in sorted(summary.final_residuals.items())
    )
    run_id = getattr(run_result, "run_id", "") if run_result is not None else ""
    return ResultDataset(
        dataset_id=dataset_id or f"openfoam_{run_id or 'residuals'}",
        source="openfoam",
        solver=solver or getattr(run_result, "solver", "OpenFOAM"),
        analysis_type="incompressible_cfd_residuals",
        fields=residual_field,
        summaries=summaries,
        warnings=tuple(message.message for message in summary.diagnostics.warnings()),
        metadata={
            "run_id": run_id,
            "case_dir": str(getattr(run_result, "case_dir", "")) if run_result else "",
            "iteration_count": summary.iteration_count,
            "converged": summary.converged,
            "diagnostics": summary.diagnostics.to_dict(),
        },
    )


def result_dataset_from_openfoam_run(result: OpenFOAMRunResult) -> ResultDataset:
    """Build a ResultDataset from an OpenFOAMRunResult residual summary."""

    summary = result.residual_summary or OpenFOAMResidualSummary()
    return openfoam_residuals_to_result_dataset(
        summary,
        run_result=result,
        solver=result.solver,
    )
