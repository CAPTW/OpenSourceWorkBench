"""Figure capture helpers for explicit M-script runner outputs."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from osw.solvers.runner import RunResult

from .figure_dataset import FigureDataset
from .workspace_extractor import extract_figure_dataset


def capture_existing_figures(
    paths: Sequence[str | Path],
    *,
    dataset_id: str = "figures",
    source: str = "",
) -> FigureDataset:
    return FigureDataset.from_image_paths(paths, dataset_id=dataset_id, source=source)


def capture_octave_figures(
    result: RunResult,
    *,
    dataset_id: str = "octave-figures",
) -> FigureDataset:
    workspace = _octave_workspace_from_result(result)
    if workspace is None:
        return FigureDataset(
            dataset_id=dataset_id,
            source=str(result.artifact_dir),
            notes=("No Octave workspace artifact was available for figure capture.",),
        )
    return extract_figure_dataset(workspace, dataset_id=dataset_id, source="GNU Octave workspace")


def _octave_workspace_from_result(result: RunResult) -> Path | None:
    for artifact in result.artifacts:
        if artifact.kind == "octave_workspace" and artifact.path.exists():
            return artifact.path
    fallback = result.artifact_dir / "octave_workspace"
    if fallback.exists():
        return fallback
    return None
