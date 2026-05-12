"""Optional Matplotlib bridge for lightweight FigureDataset export."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from osw.scripts.mscript.figure_dataset import FigureDataset, FigureRecord


class MatplotlibUnavailableError(RuntimeError):
    """Raised when the optional Matplotlib visualization extra is unavailable."""


def is_matplotlib_available() -> bool:
    return importlib.util.find_spec("matplotlib") is not None


def export_line_plot_dataset(
    *,
    x: tuple[float, ...],
    y: tuple[float, ...],
    output_dir: str | Path,
    figure_id: str = "figure-1",
    title: str = "Figure",
) -> FigureDataset:
    if len(x) != len(y):
        msg = "Matplotlib figure export requires x and y arrays with the same length."
        raise ValueError(msg)

    plt = _load_pyplot()
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    png_path = output_path / f"{figure_id}.png"
    svg_path = output_path / f"{figure_id}.svg"

    fig, axis = plt.subplots()
    axis.plot(x, y)
    axis.set_title(title)
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    fig.tight_layout()
    fig.savefig(png_path)
    fig.savefig(svg_path)
    plt.close(fig)

    raw_plot_data = {"x": list(x), "y": list(y)}
    reproducible_python = "fig, ax = plt.subplots(); ax.plot(x, y)"
    return FigureDataset(
        dataset_id=f"{figure_id}-dataset",
        figures=(
            FigureRecord(
                figure_id=f"{figure_id}-png",
                title=title,
                image_path=png_path,
                axes=("x", "y"),
                raw_plot_data=raw_plot_data,
                reproducible_python=reproducible_python,
            ),
            FigureRecord(
                figure_id=f"{figure_id}-svg",
                title=title,
                image_path=svg_path,
                axes=("x", "y"),
                raw_plot_data=raw_plot_data,
                reproducible_python=reproducible_python,
            ),
        ),
        source="matplotlib",
    )


def _load_pyplot() -> object:
    if not is_matplotlib_available():
        msg = "Matplotlib is not installed. Install the optional viz extra to export plots."
        raise MatplotlibUnavailableError(msg)
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    return plt
