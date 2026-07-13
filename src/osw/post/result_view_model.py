"""Viewer-ready result dataset catalog and adapter helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any

from osw.core.boundary_curve import BoundaryCurve
from osw.core.result_dataset import (
    ResultArtifactRef,
    ResultCatalog,
    ResultDataset,
    ResultDatasetKind,
    ResultDatasetSummary,
    ResultField,
    ResultRow,
    ResultScalar,
    ResultSeries,
    ResultSummaryValue,
    ResultTable,
)
from osw.mesh.mesh_model import MeshInfo
from osw.scripts.mscript.figure_dataset import FigureDataset
from osw.scripts.mscript.mat_model import MatFileSummary, MatReadResult

MAX_PREVIEW_ROWS = 50
MAX_PREVIEW_POINTS = 200


@dataclass(frozen=True)
class ResultFigureRef:
    figure_id: str
    title: str = ""
    path: str = ""
    format: str = ""
    source: str = ""
    exists: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "path": self.path,
            "format": self.format,
            "source": self.source,
            "exists": self.exists,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ResultFigureRef:
        path = str(data.get("path", ""))
        return cls(
            figure_id=str(data.get("figure_id", "")),
            title=str(data.get("title", "")),
            path=path,
            format=str(data.get("format", "")),
            source=str(data.get("source", "")),
            exists=bool(data.get("exists", Path(path).exists() if path else False)),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultViewModel:
    dataset_id: str
    title: str
    kind: str
    source: str = ""
    scalars: tuple[ResultScalar, ...] = field(default_factory=tuple)
    series: tuple[ResultSeries, ...] = field(default_factory=tuple)
    tables: tuple[ResultTable, ...] = field(default_factory=tuple)
    figures: tuple[ResultFigureRef, ...] = field(default_factory=tuple)
    artifacts: tuple[ResultArtifactRef, ...] = field(default_factory=tuple)
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    empty_state_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "scalars", tuple(self.scalars))
        object.__setattr__(self, "series", tuple(self.series))
        object.__setattr__(self, "tables", tuple(self.tables))
        object.__setattr__(self, "figures", tuple(self.figures))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "kind": self.kind,
            "source": self.source,
            "scalars": [scalar.to_dict() for scalar in self.scalars],
            "series": [series.to_dict() for series in self.series],
            "tables": [table.to_dict() for table in self.tables],
            "figures": [figure.to_dict() for figure in self.figures],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": list(self.diagnostics),
            "empty_state_message": self.empty_state_message,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ResultCatalogViewSummary:
    catalog_id: str
    project_name: str = ""
    dataset_count: int = 0
    kind_counts: tuple[tuple[str, int], ...] = field(default_factory=tuple)
    selected_dataset_id: str = ""
    selected_title: str = ""
    source_summary: str = "No sources recorded."
    diagnostics_count: int = 0
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    empty_state_message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind_counts", tuple(self.kind_counts))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))


@dataclass(frozen=True)
class ResultDatasetViewDetails:
    dataset_id: str
    title: str
    kind: str
    source_kind: str
    source: str
    scalar_count: int = 0
    series_count: int = 0
    table_count: int = 0
    figure_count: int = 0
    artifact_count: int = 0
    field_count: int = 0
    diagnostics_count: int = 0
    handoff_hints: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    report_compatible: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "handoff_hints", tuple(str(item) for item in self.handoff_hints))
        object.__setattr__(self, "limitations", tuple(str(item) for item in self.limitations))


def result_catalog_from_result_datasets(
    datasets: Iterable[ResultDataset | Mapping[str, Any]],
    *,
    catalog_id: str = "result-catalog",
    project_name: str = "",
    selected_dataset_id: str = "",
) -> ResultCatalog:
    normalized = tuple(
        dataset if isinstance(dataset, ResultDataset) else ResultDataset.from_dict(dataset)
        for dataset in datasets
    )
    return ResultCatalog(
        catalog_id=catalog_id,
        project_name=project_name,
        datasets=normalized,
        selected_dataset_id=selected_dataset_id,
    )


def result_catalog_from_project(
    project: object,
    *,
    extra_datasets: Iterable[ResultDataset | Mapping[str, Any]] = (),
    figure_datasets: Iterable[FigureDataset] = (),
) -> ResultCatalog:
    datasets: list[ResultDataset] = []
    project_name = str(getattr(getattr(project, "metadata", None), "name", "") or "")
    for mesh in getattr(project, "mesh_refs", getattr(project, "meshes", ())) or ():
        mesh_info_payload = getattr(mesh, "mesh_info", None)
        if isinstance(mesh_info_payload, Mapping):
            datasets.append(mesh_info_to_view_dataset(MeshInfo.from_dict(mesh_info_payload)))
        elif getattr(mesh, "node_count", None) is not None or getattr(mesh, "cell_count", None):
            datasets.append(_mesh_ref_to_view_dataset(mesh))
    for script in getattr(project, "script_refs", getattr(project, "scripts", ())) or ():
        metadata = getattr(script, "metadata", {}) or {}
        mat_summary = metadata.get("mat_summary") if isinstance(metadata, Mapping) else None
        if isinstance(mat_summary, Mapping):
            datasets.append(mat_summary_to_view_dataset(MatFileSummary.from_dict(mat_summary)))
    for curve in getattr(project, "boundary_curves", ()) or ():
        datasets.append(boundary_curve_to_view_dataset(curve))
    for figure_dataset in figure_datasets:
        datasets.append(figure_dataset_to_view_dataset(figure_dataset))
    datasets.extend(
        dataset if isinstance(dataset, ResultDataset) else ResultDataset.from_dict(dataset)
        for dataset in extra_datasets
    )
    return ResultCatalog(
        catalog_id=f"{project_name or 'project'}-results",
        project_name=project_name,
        datasets=tuple(datasets),
    )


def result_dataset_summary(dataset: ResultDataset) -> ResultDatasetSummary:
    view_model = result_dataset_to_view_model(dataset)
    return ResultDatasetSummary(
        dataset_id=dataset.dataset_id,
        title=view_model.title,
        kind=view_model.kind,
        source=dataset.source,
        scalar_count=len(view_model.scalars),
        series_count=len(view_model.series),
        table_count=len(view_model.tables),
        figure_count=len(view_model.figures),
        artifact_count=len(view_model.artifacts),
        warning_count=len(dataset.warnings)
        + sum(1 for item in view_model.diagnostics if "warning" in item.casefold()),
        diagnostics=view_model.diagnostics,
        metadata={"solver": dataset.solver, "analysis_type": dataset.analysis_type},
    )


def summarize_result_catalog_for_view(
    catalog: ResultCatalog | Mapping[str, Any],
) -> ResultCatalogViewSummary:
    normalized = catalog if isinstance(catalog, ResultCatalog) else ResultCatalog.from_dict(catalog)
    summaries = tuple(result_dataset_summary(dataset) for dataset in normalized.datasets)
    kind_counts: dict[str, int] = {}
    sources: list[str] = []
    selected_title = ""
    for summary in summaries:
        kind_counts[summary.kind] = kind_counts.get(summary.kind, 0) + 1
        if summary.source:
            sources.append(summary.source)
        if summary.dataset_id == normalized.selected_dataset_id:
            selected_title = summary.title
    if not selected_title and summaries:
        selected_title = summaries[0].title
    source_summary = ", ".join(dict.fromkeys(sources[:3])) if sources else "No sources recorded."
    if len(sources) > 3:
        source_summary += f" (+{len(sources) - 3} more)"
    empty = "" if summaries else "No result catalog is loaded."
    return ResultCatalogViewSummary(
        catalog_id=normalized.catalog_id,
        project_name=normalized.project_name,
        dataset_count=len(summaries),
        kind_counts=tuple(sorted(kind_counts.items())),
        selected_dataset_id=normalized.selected_dataset_id,
        selected_title=selected_title,
        source_summary=source_summary,
        diagnostics_count=len(normalized.diagnostics),
        diagnostics=normalized.diagnostics,
        empty_state_message=empty,
    )


def summarize_result_dataset_for_view(
    dataset: ResultDataset | Mapping[str, Any],
    *,
    field_count: int = 0,
) -> ResultDatasetViewDetails:
    normalized = dataset if isinstance(dataset, ResultDataset) else ResultDataset.from_dict(dataset)
    view_model = result_dataset_to_view_model(normalized)
    source_kind = _source_kind(normalized.source)
    handoffs = _handoff_hints(view_model, field_count=field_count)
    limitations = _dataset_limitations(view_model.kind)
    report_compatible = bool(
        view_model.scalars
        or view_model.series
        or view_model.tables
        or view_model.figures
        or view_model.diagnostics
    )
    return ResultDatasetViewDetails(
        dataset_id=normalized.dataset_id,
        title=view_model.title,
        kind=view_model.kind,
        source_kind=source_kind,
        source=normalized.source,
        scalar_count=len(view_model.scalars),
        series_count=len(view_model.series),
        table_count=len(view_model.tables),
        figure_count=len(view_model.figures),
        artifact_count=len(view_model.artifacts),
        field_count=field_count,
        diagnostics_count=len(view_model.diagnostics),
        handoff_hints=handoffs,
        limitations=limitations,
        report_compatible=report_compatible,
    )


def result_dataset_to_view_model(dataset: ResultDataset | Mapping[str, Any]) -> ResultViewModel:
    normalized = dataset if isinstance(dataset, ResultDataset) else ResultDataset.from_dict(dataset)
    kind = _dataset_kind(normalized)
    scalars = _scalars_from_dataset(normalized)
    series = _series_from_dataset(normalized)
    tables = _tables_from_dataset(normalized)
    figures = _figures_from_dataset(normalized)
    artifacts = _artifacts_from_dataset(normalized)
    diagnostics = [*normalized.warnings, *_diagnostics_from_metadata(normalized.metadata)]
    diagnostics.extend(
        f"Missing artifact: {artifact.path}"
        for artifact in artifacts
        if artifact.path and not artifact.exists
    )
    title = _dataset_title(normalized, kind)
    empty = ""
    if not any((scalars, series, tables, figures, artifacts)):
        empty = "No result summaries are available for this dataset."
    return ResultViewModel(
        dataset_id=normalized.dataset_id,
        title=title,
        kind=kind,
        source=normalized.source,
        scalars=scalars,
        series=series,
        tables=tables,
        figures=figures,
        artifacts=artifacts,
        diagnostics=tuple(dict.fromkeys(diagnostics)),
        empty_state_message=empty,
        metadata=dict(normalized.metadata),
    )


def calculix_result_to_view_dataset(parsed_results: object) -> ResultDataset:
    module = import_module("osw.solvers.calculix.result_parser")
    return module.calculix_results_to_result_dataset(parsed_results)


def openfoam_residuals_to_view_dataset(summary: object) -> ResultDataset:
    module = import_module("osw.solvers.openfoam.results")
    return module.openfoam_residuals_to_result_dataset(summary)


def figure_dataset_to_view_dataset(dataset: FigureDataset) -> ResultDataset:
    figure_rows = tuple(
        (
            record.figure_id,
            record.title,
            record.image_format,
            str(record.primary_path or ""),
            record.source_script,
            record.source_run_id,
        )
        for record in dataset.figures
    )
    variable_rows = tuple(
        (
            variable.name,
            variable.type_name,
            "x".join(str(item) for item in variable.shape),
            variable.dtype,
            variable.source,
        )
        for variable in dataset.workspace_variables
    )
    return ResultDataset(
        dataset_id=dataset.dataset_id,
        source=dataset.source_file or dataset.source or dataset.source_run_id,
        solver="M-Script",
        analysis_type="figure_dataset",
        summaries=(
            ResultSummaryValue("figure_count", len(dataset.figures), "", "FigureDataset"),
            ResultSummaryValue(
                "workspace_variable_count",
                len(dataset.workspace_variables),
                "",
                "FigureDataset",
            ),
        ),
        warnings=tuple(message.message for message in dataset.diagnostics.warnings()),
        metadata={
            "kind": ResultDatasetKind.FIGURE_DATASET.value,
            "figures": [record.to_dict() for record in dataset.figures],
            "figure_rows": {
                "columns": ["ID", "Title", "Format", "Path", "Script", "Run"],
                "rows": figure_rows,
            },
            "workspace_variables": [
                variable.to_dict() for variable in dataset.workspace_variables
            ],
            "workspace_rows": {
                "columns": ["Name", "Type", "Shape", "DType", "Source"],
                "rows": variable_rows,
            },
            "artifacts": [artifact.to_dict() for artifact in dataset.artifacts],
            "diagnostics": dataset.diagnostics.to_dict(),
        },
    )


def mat_summary_to_view_dataset(summary: MatFileSummary | MatReadResult) -> ResultDataset:
    mat_summary = summary.summary if isinstance(summary, MatReadResult) else summary
    rows = tuple(
        (
            variable.name,
            variable.kind,
            variable.display_shape,
            variable.dtype,
            variable.preview,
        )
        for variable in mat_summary.variables
    )
    return ResultDataset(
        dataset_id=Path(mat_summary.source_path).stem or "mat-workspace",
        source=mat_summary.source_path,
        solver="MAT",
        analysis_type="workspace_variables",
        summaries=(
            ResultSummaryValue("variable_count", len(mat_summary.variables), "", "MAT"),
        ),
        warnings=tuple(message.message for message in mat_summary.diagnostics.warnings()),
        metadata={
            "kind": ResultDatasetKind.MAT_WORKSPACE.value,
            "mat_version": mat_summary.version,
            "variables": [variable.to_dict() for variable in mat_summary.variables],
            "workspace_rows": {
                "columns": ["Name", "Kind", "Shape", "DType", "Preview"],
                "rows": rows,
            },
            "diagnostics": mat_summary.diagnostics.to_dict(),
        },
    )


def boundary_curve_to_view_dataset(curve: BoundaryCurve) -> ResultDataset:
    rows = tuple(
        ResultRow(index + 1, {"x": x_value, "y": y_value})
        for index, (x_value, y_value) in enumerate(
            zip(curve.x_values, curve.y_values, strict=False)
        )
    )
    return ResultDataset(
        dataset_id=curve.curve_id,
        source=getattr(curve.source, "source_file", "") if curve.source is not None else "",
        solver="BoundaryCurve",
        analysis_type=curve.kind,
        fields=(
            ResultField(
                name="boundary_curve",
                location="curve",
                components=("x", "y"),
                rows=rows,
                unit=f"{curve.x_unit}/{curve.y_unit}",
            ),
        ),
        summaries=(
            ResultSummaryValue("point_count", curve.point_count, "points", "BoundaryCurve"),
        ),
        warnings=tuple(message.message for message in curve.diagnostics.warnings()),
        metadata={
            "kind": ResultDatasetKind.BOUNDARY_CURVE.value,
            "curve": curve.to_dict(),
            "x_unit": curve.x_unit,
            "y_unit": curve.y_unit,
            "interpolation": curve.interpolation,
            "diagnostics": curve.diagnostics.to_dict(),
        },
    )


def mesh_info_to_view_dataset(mesh_info: MeshInfo) -> ResultDataset:
    cell_rows = tuple(
        (block.cell_type, str(block.count), str(block.order or ""))
        for block in mesh_info.cell_blocks
    )
    return ResultDataset(
        dataset_id=Path(mesh_info.source_path).stem or "mesh-summary",
        source=mesh_info.source_path,
        solver="Mesh",
        analysis_type="mesh_summary",
        summaries=(
            ResultSummaryValue("node_count", mesh_info.node_count, "nodes", "MeshInfo"),
            ResultSummaryValue(
                "element_count",
                mesh_info.element_count,
                "elements",
                "MeshInfo",
            ),
        ),
        warnings=mesh_info.warnings,
        metadata={
            "kind": ResultDatasetKind.MESH_SUMMARY.value,
            "mesh_info": mesh_info.to_dict(),
            "cell_rows": {
                "columns": ["Cell Type", "Count", "Order"],
                "rows": cell_rows,
            },
        },
    )


def _mesh_ref_to_view_dataset(mesh_ref: object) -> ResultDataset:
    path = str(getattr(mesh_ref, "path", ""))
    dataset_id = str(getattr(mesh_ref, "id", "") or Path(path).stem)
    return ResultDataset(
        dataset_id=dataset_id,
        source=path,
        solver="Mesh",
        analysis_type="mesh_summary",
        summaries=(
            ResultSummaryValue(
                "node_count",
                float(getattr(mesh_ref, "node_count", 0) or 0),
                "nodes",
                "MeshRef",
            ),
            ResultSummaryValue(
                "element_count",
                float(getattr(mesh_ref, "cell_count", 0) or 0),
                "elements",
                "MeshRef",
            ),
        ),
        warnings=(str(getattr(mesh_ref, "quality_summary", "")),)
        if getattr(mesh_ref, "quality_summary", "")
        else (),
        metadata={"kind": ResultDatasetKind.MESH_SUMMARY.value},
    )


def _dataset_kind(dataset: ResultDataset) -> str:
    metadata_kind = str(dataset.metadata.get("kind", ""))
    if metadata_kind:
        return metadata_kind
    solver = dataset.solver.casefold()
    analysis_type = dataset.analysis_type.casefold()
    source = dataset.source.casefold()
    if "calculix" in solver:
        return ResultDatasetKind.CALCULIX_SUMMARY.value
    if "openfoam" in solver or "residual" in analysis_type or "openfoam" in source:
        return ResultDatasetKind.OPENFOAM_RESIDUALS.value
    if "field" in analysis_type:
        return ResultDatasetKind.FIELD_DATASET.value
    if "coolprop" in solver and "sweep" in analysis_type:
        return ResultDatasetKind.COOLPROP_SWEEP.value
    if "coolprop" in solver:
        return ResultDatasetKind.COOLPROP_PROPERTY.value
    if "cantera" in solver:
        return ResultDatasetKind.CANTERA_REACTOR.value
    if "figure" in analysis_type:
        return ResultDatasetKind.FIGURE_DATASET.value
    if "workspace" in analysis_type or solver == "mat":
        return ResultDatasetKind.MAT_WORKSPACE.value
    return ResultDatasetKind.UNKNOWN.value


def _dataset_title(dataset: ResultDataset, kind: str) -> str:
    title = str(dataset.metadata.get("title", ""))
    if title:
        return title
    if kind == ResultDatasetKind.OPENFOAM_RESIDUALS.value:
        return "OpenFOAM Residuals"
    if kind == ResultDatasetKind.FIELD_DATASET.value:
        return "Field Dataset"
    if kind == ResultDatasetKind.CALCULIX_SUMMARY.value:
        return "CalculiX Result Summary"
    if kind == ResultDatasetKind.COOLPROP_PROPERTY.value:
        return "CoolProp Properties"
    if kind == ResultDatasetKind.COOLPROP_SWEEP.value:
        return "CoolProp Sweep"
    if kind == ResultDatasetKind.CANTERA_REACTOR.value:
        return "Cantera 0D Reactor"
    if kind == ResultDatasetKind.FIGURE_DATASET.value:
        return "Figure Dataset"
    if kind == ResultDatasetKind.MAT_WORKSPACE.value:
        return "MAT Workspace Variables"
    if kind == ResultDatasetKind.BOUNDARY_CURVE.value:
        return "Boundary Curve"
    if kind == ResultDatasetKind.MESH_SUMMARY.value:
        return "Mesh Summary"
    return dataset.dataset_id or "Result Dataset"


def _source_kind(source: str) -> str:
    if not source:
        return "not recorded"
    suffix = Path(source).suffix.lower().lstrip(".")
    if suffix:
        return suffix
    if "/" in source or "\\" in source:
        return "path"
    return "identifier"


def _handoff_hints(view_model: ResultViewModel, *, field_count: int) -> tuple[str, ...]:
    hints = []
    hints.append(
        "Shown in Plot Viewer" if view_model.series else "Plot Viewer: no series data"
    )
    hints.append(
        "Shown in Table Viewer" if view_model.tables else "Table Viewer: no table data"
    )
    hints.append(
        "Shown in Field Viewer" if field_count else "Field Viewer: summary only"
    )
    hints.append(
        "Figure handoff" if view_model.figures else "Figure handoff: no figures"
    )
    hints.append("Report compatible")
    return tuple(hints)


def _dataset_limitations(kind: str) -> tuple[str, ...]:
    limitations = [
        "Viewer inspection is summary-first and does not execute solvers or scripts.",
    ]
    if kind == ResultDatasetKind.FIELD_DATASET.value:
        limitations.extend(
            [
                "Full CalculiX FRD contour parsing is not implemented in this slice.",
                "OpenFOAM field parsing is not implemented in this slice.",
                "Field Viewer live vector-glyph rendering, streamlines, and "
                "animation remain deferred; Mesh Viewer glyph controls/state "
                "are preview-only.",
            ]
        )
    return tuple(limitations)


def _scalars_from_dataset(dataset: ResultDataset) -> tuple[ResultScalar, ...]:
    return tuple(
        ResultScalar(
            name=summary.name,
            value=summary.value,
            unit=summary.unit,
            source=summary.source_field,
        )
        for summary in dataset.summaries
    )


def _series_from_dataset(dataset: ResultDataset) -> tuple[ResultSeries, ...]:
    series: list[ResultSeries] = []
    curve_payload = dataset.metadata.get("curve")
    if isinstance(curve_payload, Mapping):
        x_values = tuple(float(item) for item in curve_payload.get("x_values", ()) or ())
        y_values = tuple(float(item) for item in curve_payload.get("y_values", ()) or ())
        if x_values and y_values:
            return (
                ResultSeries(
                    name=str(curve_payload.get("name", "Boundary curve")),
                    x_values=x_values[:MAX_PREVIEW_POINTS],
                    y_values=y_values[:MAX_PREVIEW_POINTS],
                    x_unit=str(dataset.metadata.get("x_unit", "")),
                    y_unit=str(dataset.metadata.get("y_unit", "")),
                    source=dataset.source,
                ),
            )
    for field_item in dataset.fields:
        rows = field_item.rows[:MAX_PREVIEW_POINTS]
        x_values = _series_x_values(dataset, field_item, rows)
        series_units = dataset.metadata.get("series_units", {})
        if not isinstance(series_units, Mapping):
            series_units = {}
        for component in field_item.components:
            y_values = tuple(
                float(row.values[component])
                for row in rows
                if component in row.values
            )
            if not y_values:
                continue
            series.append(
                ResultSeries(
                    name=(
                        component
                        if field_item.name
                        in {"residuals", "coolprop_sweep", "cantera_reactor"}
                        else f"{field_item.name}.{component}"
                    ),
                    x_values=x_values[: len(y_values)],
                    y_values=y_values,
                    x_unit=_series_x_unit(dataset, field_item),
                    y_unit=str(series_units.get(component, field_item.unit)),
                    source=field_item.name,
                )
            )
    return tuple(series)


def _tables_from_dataset(dataset: ResultDataset) -> tuple[ResultTable, ...]:
    tables: list[ResultTable] = []
    for field_item in dataset.fields:
        tables.append(_field_to_result_table(dataset, field_item))
    if dataset.summaries:
        tables.append(
            ResultTable(
                table_id=f"{dataset.dataset_id}-summaries",
                title="Scalar summaries",
                columns=("Name", "Value", "Unit", "Source"),
                rows=tuple(
                    (
                        summary.name,
                        f"{summary.value:.12g}",
                        summary.unit,
                        summary.source_field,
                    )
                    for summary in dataset.summaries
                ),
            )
        )
    for key, default_title in (
        ("workspace_rows", "Workspace variables"),
        ("figure_rows", "Figures"),
        ("cell_rows", "Mesh cell types"),
        ("field_rows", "Field arrays"),
        ("property_rows", "CHM property table"),
        ("reactor_rows", "Cantera reactor time history"),
    ):
        rows_payload = dataset.metadata.get(key)
        if isinstance(rows_payload, Mapping):
            tables.append(_payload_table(dataset.dataset_id, key, default_title, rows_payload))
    return tuple(tables)


def _series_x_values(
    dataset: ResultDataset,
    field_item: ResultField,
    rows: tuple[ResultRow, ...],
) -> tuple[float, ...]:
    if field_item.name == "coolprop_sweep":
        values = dataset.metadata.get("sweep_values", ())
        if values:
            return tuple(float(item) for item in values)[: len(rows)]
    if field_item.name == "cantera_reactor":
        values = dataset.metadata.get("time_values", ())
        if values:
            return tuple(float(item) for item in values)[: len(rows)]
    return tuple(float(row.entity_id) for row in rows)


def _series_x_unit(dataset: ResultDataset, field_item: ResultField) -> str:
    if field_item.name == "residuals":
        return "iteration"
    if field_item.name == "coolprop_sweep":
        return str(dataset.metadata.get("sweep_unit", ""))
    if field_item.name == "cantera_reactor":
        return str(dataset.metadata.get("time_unit", "s"))
    return ""


def _field_to_result_table(dataset: ResultDataset, field_item: ResultField) -> ResultTable:
    columns = ("entity_id", *field_item.components)
    rows = tuple(
        (
            str(row.entity_id),
            *(_format_cell(row.values.get(component)) for component in field_item.components),
        )
        for row in field_item.rows[:MAX_PREVIEW_ROWS]
    )
    return ResultTable(
        table_id=f"{dataset.dataset_id}-{field_item.name}",
        title=field_item.name,
        columns=columns,
        rows=rows,
        truncated=len(field_item.rows) > MAX_PREVIEW_ROWS,
    )


def _payload_table(
    dataset_id: str,
    key: str,
    default_title: str,
    payload: Mapping[str, object],
) -> ResultTable:
    return ResultTable(
        table_id=f"{dataset_id}-{key}",
        title=str(payload.get("title", default_title)),
        columns=tuple(str(item) for item in payload.get("columns", ()) or ()),
        rows=tuple(
            tuple(str(cell) for cell in row)
            for row in payload.get("rows", ()) or ()
        )[:MAX_PREVIEW_ROWS],
        truncated=bool(payload.get("truncated", False)),
    )


def _figures_from_dataset(dataset: ResultDataset) -> tuple[ResultFigureRef, ...]:
    figures = []
    for item in dataset.metadata.get("figures", ()) or ():
        if not isinstance(item, Mapping):
            continue
        path = str(
            item.get("image_path")
            or item.get("vector_path")
            or item.get("pdf_path")
            or item.get("data_path")
            or ""
        )
        figures.append(
            ResultFigureRef(
                figure_id=str(item.get("figure_id", "")),
                title=str(item.get("title", "")),
                path=path,
                format=str(item.get("format", "")),
                source=str(item.get("source_script", item.get("source_run_id", ""))),
                exists=Path(path).exists() if path else False,
                metadata=dict(item.get("metadata", {}) or {}),
            )
        )
    return tuple(figures)


def _artifacts_from_dataset(dataset: ResultDataset) -> tuple[ResultArtifactRef, ...]:
    artifacts: list[ResultArtifactRef] = []
    for item in dataset.metadata.get("artifacts", ()) or ():
        if isinstance(item, Mapping):
            artifacts.append(ResultArtifactRef.from_dict(item))
    for figure in _figures_from_dataset(dataset):
        if figure.path:
            artifacts.append(
                ResultArtifactRef.from_path(
                    figure.path,
                    role="figure",
                    format=figure.format,
                    source=figure.source,
                )
            )
    return tuple(_dedupe_artifacts(artifacts))


def _diagnostics_from_metadata(metadata: Mapping[str, Any]) -> tuple[str, ...]:
    diagnostics = metadata.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        return ()
    messages = []
    for message in diagnostics.get("messages", ()) or ():
        if not isinstance(message, Mapping):
            continue
        severity = str(message.get("severity", "")).upper()
        code = str(message.get("code", ""))
        text = str(message.get("message", ""))
        messages.append(f"{severity} {code}: {text}".strip())
    return tuple(messages)


def _dedupe_artifacts(
    artifacts: Sequence[ResultArtifactRef],
) -> tuple[ResultArtifactRef, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[ResultArtifactRef] = []
    for artifact in artifacts:
        key = (artifact.path, artifact.role)
        if key in seen:
            continue
        seen.add(key)
        unique.append(artifact)
    return tuple(unique)


def _format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


__all__ = [
    "ResultFigureRef",
    "ResultCatalogViewSummary",
    "ResultDatasetViewDetails",
    "ResultViewModel",
    "boundary_curve_to_view_dataset",
    "calculix_result_to_view_dataset",
    "figure_dataset_to_view_dataset",
    "mat_summary_to_view_dataset",
    "mesh_info_to_view_dataset",
    "openfoam_residuals_to_view_dataset",
    "result_catalog_from_project",
    "result_catalog_from_result_datasets",
    "result_dataset_summary",
    "result_dataset_to_view_model",
    "summarize_result_catalog_for_view",
    "summarize_result_dataset_for_view",
]
