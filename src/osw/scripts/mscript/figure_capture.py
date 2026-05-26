"""Normalize explicit M-script runner artifacts into FigureDataset records."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.solvers.runner import RunResult

from .figure_dataset import (
    FigureDataset,
    FigureFormat,
    FigureRecord,
    classify_extension,
    new_dataset_id,
)
from .workspace_extractor import extract_workspace_summary

FIGURE_ARTIFACT_EXTENSIONS = {
    ".png",
    ".svg",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".csv",
    ".json",
}
IGNORED_RUN_ARTIFACT_NAMES = {"stdout.txt", "stderr.txt", "run_summary.json"}


def discover_figure_artifacts(
    workspace_dir: str | Path,
    run_result: object | None = None,
) -> tuple[Path, ...]:
    """Discover reportable figure/data artifacts without executing code."""

    discovered: list[Path] = []
    for artifact in getattr(run_result, "artifacts", ()) if run_result is not None else ():
        path = Path(getattr(artifact, "path", ""))
        if _is_candidate_artifact(path):
            discovered.append(path)

    workspace = Path(workspace_dir).expanduser()
    if workspace.exists() and workspace.is_dir():
        discovered.extend(
            path
            for path in sorted(workspace.rglob("*"))
            if _is_candidate_artifact(path)
        )
    return _dedupe_paths(discovered)


def classify_figure_artifact(path: str | Path) -> FigureFormat:
    """Classify a figure/data artifact by extension only."""

    return classify_extension(path)


def figure_record_from_artifact(
    path: str | Path,
    *,
    source_run_id: str | None = None,
    source_script: str | None = None,
) -> FigureRecord:
    artifact_path = Path(path)
    diagnostics = DiagnosticReport()
    figure_format = classify_figure_artifact(artifact_path)
    if not artifact_path.exists():
        diagnostics.add_warning(
            "figure-artifact-missing",
            f"Figure artifact does not exist: {artifact_path}",
            hint="Regenerate the run or remove the stale figure reference.",
            path=artifact_path,
        )
    if figure_format is FigureFormat.UNKNOWN:
        diagnostics.add_warning(
            "figure-artifact-unknown-format",
            f"Unrecognized figure artifact format: {artifact_path.suffix or '<none>'}",
            hint="Use PNG, SVG, PDF, JPG, or CSV for reportable figure artifacts.",
            path=artifact_path,
        )
    return FigureRecord(
        figure_id=_figure_id_from_path(artifact_path),
        title=_title_from_stem(artifact_path.stem),
        source_script=str(source_script or ""),
        source_run_id=str(source_run_id or ""),
        image_path=artifact_path if figure_format in {FigureFormat.PNG, FigureFormat.JPG} else None,
        vector_path=artifact_path if figure_format is FigureFormat.SVG else None,
        pdf_path=artifact_path if figure_format is FigureFormat.PDF else None,
        data_path=artifact_path if figure_format is FigureFormat.CSV else None,
        format=figure_format,
        diagnostics=diagnostics,
        metadata={"exists": artifact_path.exists()},
    )


def figure_dataset_from_artifacts(
    paths: Iterable[str | Path],
    *,
    source_script: str | None = None,
    source_run_id: str | None = None,
    dataset_id: str | None = None,
    engine: str = "imported",
) -> FigureDataset:
    diagnostics = DiagnosticReport()
    records: list[FigureRecord] = []
    artifacts: list[RunArtifact] = []
    artifact_paths = _dedupe_paths(Path(path) for path in paths)
    for path in artifact_paths:
        figure_format = classify_figure_artifact(path)
        if not path.exists():
            diagnostics.add_warning(
                "figure-artifact-missing",
                f"Figure artifact does not exist: {path}",
                hint="Check the run workspace or regenerate artifacts.",
                path=path,
            )
        elif figure_format is FigureFormat.UNKNOWN:
            diagnostics.add_warning(
                "figure-artifact-unknown-format",
                f"Ignored unrecognized figure artifact: {path.name}",
                hint="Use PNG, SVG, PDF, JPG, CSV, or JSON summary artifacts.",
                path=path,
            )
        if figure_format in {
            FigureFormat.PNG,
            FigureFormat.SVG,
            FigureFormat.PDF,
            FigureFormat.JPG,
            FigureFormat.CSV,
        }:
            record = figure_record_from_artifact(
                path,
                source_run_id=source_run_id,
                source_script=source_script,
            )
            diagnostics.extend(record.diagnostics)
            records.append(record)
            artifacts.append(
                RunArtifact(
                    path,
                    "figure_artifact",
                    "FigureDataset source artifact.",
                    format=figure_format.value,
                )
            )

    workspace_result = extract_workspace_summary(artifact_paths)
    diagnostics.extend(workspace_result.diagnostics)
    return FigureDataset(
        dataset_id=dataset_id or new_dataset_id("figure-dataset"),
        figures=tuple(records),
        source=str(source_script or ""),
        source_file=str(source_script or ""),
        source_run_id=str(source_run_id or ""),
        engine=engine,
        workspace_variables=workspace_result.variables,
        diagnostics=diagnostics,
        artifacts=tuple(artifacts),
        warnings=tuple(message.message for message in diagnostics.warnings()),
    )


def figure_dataset_from_octave_result(
    result: object,
    *,
    source_script: str | None = None,
    dataset_id: str | None = None,
) -> FigureDataset:
    workspace = _octave_workspace_from_result(result)
    paths = discover_figure_artifacts(workspace or ".", run_result=result)
    dataset = figure_dataset_from_artifacts(
        paths,
        source_script=source_script or str(getattr(result, "script_path", "")),
        source_run_id=str(getattr(result, "run_id", "")),
        dataset_id=dataset_id or f"{getattr(result, 'run_id', '') or 'octave'}-figures",
        engine="octave",
    )
    return FigureDataset(
        dataset_id=dataset.dataset_id,
        figures=dataset.figures,
        source=dataset.source,
        notes=dataset.notes,
        source_file=dataset.source_file,
        source_run_id=dataset.source_run_id,
        engine=dataset.engine,
        workspace_variables=dataset.workspace_variables,
        stdout=str(getattr(result, "stdout", "")),
        stderr=str(getattr(result, "stderr", "")),
        warnings=dataset.warnings,
        diagnostics=dataset.diagnostics,
        artifacts=dataset.artifacts,
        created_at=dataset.created_at,
        metadata={
            **dataset.metadata,
            "run_status": str(
                getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
            ),
        },
    )


def capture_existing_figures(
    paths: Sequence[str | Path],
    *,
    dataset_id: str = "figures",
    source: str = "",
) -> FigureDataset:
    return figure_dataset_from_artifacts(
        paths,
        source_script=source,
        dataset_id=dataset_id,
        engine="imported",
    )


def capture_octave_figures(
    result: RunResult | object,
    *,
    dataset_id: str = "octave-figures",
) -> FigureDataset:
    return figure_dataset_from_octave_result(result, dataset_id=dataset_id)


def generate_thumbnail(
    record: FigureRecord,
    output_dir: str | Path,
    *,
    size: tuple[int, int] = (240, 180),
) -> FigureRecord:
    diagnostics = DiagnosticReport()
    source = record.image_path
    if source is None or not source.exists():
        diagnostics.add_warning(
            "thumbnail-source-missing",
            f"Thumbnail source image is missing for {record.figure_id}.",
            hint="Only existing raster images can be thumbnailed.",
        )
        return _record_with_thumbnail_diagnostics(record, diagnostics)

    try:
        from PIL import Image
    except ModuleNotFoundError:
        diagnostics.add_warning(
            "pillow-unavailable",
            "Pillow is not installed; thumbnail generation was skipped.",
            hint="Install Pillow or the optional visualization extra to create thumbnails.",
        )
        return _record_with_thumbnail_diagnostics(record, diagnostics)

    target_dir = Path(output_dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = target_dir / f"{record.figure_id}_thumb.png"
    with Image.open(source) as image:
        image.thumbnail(size)
        image.save(thumbnail_path)
    return FigureRecord.from_dict(
        {
            **record.to_dict(),
            "thumbnail_path": str(thumbnail_path),
            "diagnostics": diagnostics.to_dict(),
        }
    )


def export_figure_dataset_json(dataset: FigureDataset, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dataset.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target


def load_figure_dataset_json(path: str | Path) -> FigureDataset:
    return FigureDataset.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def octave_save_figures_snippet(
    *,
    formats: Sequence[str] = ("png", "svg", "pdf"),
    basename: str = "osw_figure",
) -> str:
    """Return an opt-in Octave snippet for users/tests to save open figures."""

    lines = [
        "% OSW opt-in figure export helper. Use only in an isolated workspace.",
        "figs = findall(0, 'type', 'figure');",
        "for idx = 1:numel(figs)",
        "  figure(figs(idx));",
    ]
    for fmt in formats:
        fmt_text = str(fmt).lower().lstrip(".")
        lines.append(
            f"  print(['{basename}_' num2str(idx) '.{fmt_text}'], '-d{fmt_text}');"
        )
    lines.append("end")
    return "\n".join(lines)


def _octave_workspace_from_result(result: object) -> Path | None:
    workspace_dir = str(getattr(result, "workspace_dir", ""))
    if workspace_dir:
        workspace = Path(workspace_dir)
        if workspace.exists():
            return workspace
    for artifact in getattr(result, "artifacts", ()):
        if getattr(artifact, "kind", getattr(artifact, "role", "")) == "octave_workspace":
            path = Path(getattr(artifact, "path", ""))
            if path.exists():
                return path
    artifact_dir = getattr(result, "artifact_dir", None)
    if artifact_dir is not None:
        fallback = Path(artifact_dir) / "octave_workspace"
        if fallback.exists():
            return fallback
    return None


def _record_with_thumbnail_diagnostics(
    record: FigureRecord,
    diagnostics: DiagnosticReport,
) -> FigureRecord:
    combined = DiagnosticReport(list(record.diagnostics.messages))
    combined.extend(diagnostics)
    return FigureRecord.from_dict({**record.to_dict(), "diagnostics": combined.to_dict()})


def _is_candidate_artifact(path: Path) -> bool:
    if not path.name or path.name in IGNORED_RUN_ARTIFACT_NAMES:
        return False
    if not path.exists() or not path.is_file():
        return False
    if path.suffix.lower() == ".json" and path.name not in {
        "workspace.json",
        "variables.json",
        "workspace_summary.json",
    }:
        return False
    return path.suffix.lower() in FIGURE_ARTIFACT_EXTENSIONS


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    deduped: dict[str, Path] = {}
    for path in paths:
        deduped[str(path)] = path
    return tuple(deduped.values())


def _figure_id_from_path(path: Path) -> str:
    stem = path.stem or "figure"
    suffix = path.suffix.lower().lstrip(".")
    return f"{stem}-{suffix}" if suffix and suffix != "png" else stem


def _title_from_stem(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip() or "figure"
