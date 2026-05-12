"""Extract FigureDataset records from explicit runner workspaces."""

from __future__ import annotations

from pathlib import Path

from .figure_dataset import FigureDataset, is_supported_figure_path


def extract_figure_paths(workspace: str | Path) -> tuple[Path, ...]:
    workspace_path = Path(workspace).expanduser().resolve()
    if not workspace_path.exists() or not workspace_path.is_dir():
        return ()
    return tuple(
        path
        for path in sorted(workspace_path.rglob("*"))
        if path.is_file() and is_supported_figure_path(path)
    )


def extract_figure_dataset(
    workspace: str | Path,
    *,
    dataset_id: str = "workspace-figures",
    source: str | None = None,
) -> FigureDataset:
    workspace_path = Path(workspace).expanduser().resolve()
    return FigureDataset.from_image_paths(
        extract_figure_paths(workspace_path),
        dataset_id=dataset_id,
        source=source or str(workspace_path),
    )
