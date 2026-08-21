"""Deterministic explicit export surfaces for one mesh-diagnostics result."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .quality import MeshQualityAnalysis

MESH_DIAGNOSTICS_REPORT_SCHEMA = "osw.mesh_diagnostics_report.v1"


@dataclass(frozen=True, slots=True)
class MeshDiagnosticsReportSummary:
    """Portable advisory summary; contains no native actor or VTK identities."""

    schema: str
    analysis: MeshQualityAnalysis
    mesh_ref: str = ""
    claim: str = "Mesh diagnostics are advisory and do not certify solver suitability."

    def to_dict(self) -> dict[str, Any]:
        analysis = self.analysis
        summary = analysis.mesh_summary
        statistics = analysis.statistics
        return {
            "schema": self.schema,
            "claim": self.claim,
            "mesh_ref": self.mesh_ref,
            "mesh": {
                "fingerprint_schema": summary.mesh_fingerprint.schema,
                "fingerprint": summary.mesh_fingerprint.digest,
                "point_count": summary.point_count,
                "cell_count": summary.cell_count,
                "block_count": summary.block_count,
                "cell_type_distribution": {
                    key: value for key, value in summary.cell_type_distribution
                },
                "surface_cell_count": summary.surface_cell_count,
                "volume_cell_count": summary.volume_cell_count,
                "quality_covered_topology_count": summary.quality_supported_count,
                "quality_uncovered_topology_count": summary.quality_uncovered_count,
                "covered_topology_types": list(summary.supported_quality_types),
                "uncovered_topology_types": list(summary.uncovered_quality_types),
                "invalid_cell_count": summary.invalid_cell_count,
                "referenced_point_count": summary.referenced_point_count,
                "orphan_point_count": summary.orphan_point_count,
                "bounds": {
                    "minimum": list(summary.bounds.minimum),
                    "maximum": list(summary.bounds.maximum),
                    "extents": list(summary.extents),
                    "diagonal": summary.diagonal,
                },
            },
            "quality": {
                "result_schema": analysis.schema,
                "status": analysis.status.value,
                "metric_schema": analysis.metric_schema,
                "metric_label": analysis.metric_label,
                "metric_direction": analysis.metric_direction,
                "metric_semantics": analysis.metric_semantics,
                "provider_schema": analysis.provider_schema,
                "provider_version": analysis.provider_version,
                "threshold": analysis.threshold,
                "degenerate_epsilon": analysis.degenerate_epsilon,
                "range_mode": analysis.range_mode,
                "display_range": list(analysis.display_range),
                "covered_count": analysis.covered_count,
                "uncovered_count": analysis.uncovered_count,
                "invalid_count": analysis.invalid_count,
                "coverage_ratio": (
                    analysis.covered_count / analysis.cell_count if analysis.cell_count else 0.0
                ),
                "bad_count": analysis.bad_count,
                "inverted_count": sum(
                    record.category.value == "inverted" for record in analysis.records
                ),
                "degenerate_count": sum(
                    record.category.value == "degenerate" for record in analysis.records
                ),
                "threshold_bad_count": sum(
                    record.category.value == "threshold_bad" for record in analysis.records
                ),
                "acceptable_count": sum(
                    record.category.value == "acceptable" for record in analysis.records
                ),
                "digest": analysis.digest,
                "bad_canonical_cell_ids": list(analysis.bad_cell_keys),
                "invalid_canonical_cell_ids": [
                    record.stable_cell_key
                    for record in analysis.records
                    if record.status.value == "INVALID"
                ],
                "uncovered_canonical_cell_ids": [
                    record.stable_cell_key
                    for record in analysis.records
                    if record.status.value == "UNCOVERED"
                ],
                "statistics": _statistics_dict(statistics),
                "by_topology": [
                    {
                        "cell_type": item.cell_type,
                        "total_count": item.total_count,
                        "covered_count": item.covered_count,
                        "uncovered_count": item.uncovered_count,
                        "invalid_count": item.invalid_count,
                        "bad_count": item.bad_count,
                        "statistics": _statistics_dict(item.statistics),
                    }
                    for item in analysis.topology_summaries
                ],
                "diagnostics": list(analysis.diagnostics),
            },
            "cells": [
                {
                    "stable_cell_key": record.stable_cell_key,
                    "backend_index": record.backend_index,
                    "cell_type": record.cell_type,
                    "block_ordinal": record.block_ordinal,
                    "cell_ordinal": record.cell_ordinal,
                    "status": record.status.value,
                    "category": record.category.value,
                    "value": record.value,
                    "reason": record.reason,
                }
                for record in analysis.records
            ],
        }


def build_mesh_diagnostics_report_summary(
    analysis: MeshQualityAnalysis,
    *,
    mesh_ref: str | None = None,
) -> MeshDiagnosticsReportSummary:
    return MeshDiagnosticsReportSummary(
        MESH_DIAGNOSTICS_REPORT_SCHEMA,
        analysis,
        str(analysis.mesh_ref if mesh_ref is None else mesh_ref),
    )


def render_mesh_diagnostics_json(summary: MeshDiagnosticsReportSummary) -> str:
    return (
        json.dumps(
            summary.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )


def render_mesh_diagnostics_csv(summary: MeshDiagnosticsReportSummary) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        (
            "canonical_cell_id",
            "mesh_fingerprint",
            "block_index",
            "local_cell_index",
            "global_cell_index",
            "cell_type",
            "metric_id",
            "quality_status",
            "quality_value",
            "threshold_classification",
            "analysis_status",
            "diagnostic_reason",
        )
    )
    analysis = summary.analysis
    for record in analysis.records:
        writer.writerow(
            (
                record.stable_cell_key,
                analysis.mesh_fingerprint.digest,
                record.block_ordinal,
                record.cell_ordinal,
                record.backend_index,
                record.cell_type,
                analysis.metric_schema,
                record.status.value,
                "" if record.value is None else format(record.value, ".17g"),
                record.category.value,
                analysis.status.value,
                record.reason,
            )
        )
    return stream.getvalue()


def write_mesh_diagnostics_json(
    path: str | Path,
    summary: MeshDiagnosticsReportSummary,
) -> Path:
    target = Path(path)
    target.write_text(render_mesh_diagnostics_json(summary), encoding="utf-8", newline="\n")
    return target


def write_mesh_diagnostics_csv(
    path: str | Path,
    summary: MeshDiagnosticsReportSummary,
) -> Path:
    target = Path(path)
    target.write_text(render_mesh_diagnostics_csv(summary), encoding="utf-8", newline="\n")
    return target


def _statistics_dict(statistics: object) -> dict[str, Any]:
    return {
        "count": getattr(statistics, "count", 0),
        "minimum": getattr(statistics, "minimum", None),
        "maximum": getattr(statistics, "maximum", None),
        "mean": getattr(statistics, "mean", None),
        "median": getattr(statistics, "median", None),
        "population_stddev": getattr(statistics, "population_stddev", None),
        "p05": getattr(statistics, "p05", None),
        "p25": getattr(statistics, "p25", None),
        "p75": getattr(statistics, "p75", None),
        "p95": getattr(statistics, "p95", None),
        "percentile_method": getattr(statistics, "percentile_method", ""),
    }


__all__ = [
    "MESH_DIAGNOSTICS_REPORT_SCHEMA",
    "MeshDiagnosticsReportSummary",
    "build_mesh_diagnostics_report_summary",
    "render_mesh_diagnostics_csv",
    "render_mesh_diagnostics_json",
    "write_mesh_diagnostics_csv",
    "write_mesh_diagnostics_json",
]
