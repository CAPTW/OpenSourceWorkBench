"""Optional Matplotlib bridge for lightweight FigureDataset display/export."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path

from osw.core.diagnostics import DiagnosticReport
from osw.scripts.mscript.figure_dataset import (
    FigureDataset,
    FigureFormat,
    FigureRecord,
)


class MatplotlibUnavailableError(RuntimeError):
    """Raised when the optional Matplotlib visualization extra is unavailable."""


@dataclass(frozen=True)
class ImageDisplayRecord:
    path: Path
    status: str
    format: str = ""
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "status": self.status,
            "format": self.format,
            "diagnostics": self.diagnostics.to_dict(),
        }


def matplotlib_available() -> bool:
    return importlib.util.find_spec("matplotlib") is not None


def is_matplotlib_available() -> bool:
    return matplotlib_available()


def load_image_for_display(path: str | Path) -> ImageDisplayRecord:
    image_path = Path(path)
    diagnostics = DiagnosticReport()
    if not image_path.exists():
        diagnostics.add_warning(
            "image-display-missing",
            f"Image artifact is missing: {image_path}",
            hint="Regenerate the figure artifact or choose a different file.",
            path=image_path,
        )
        return ImageDisplayRecord(image_path, "missing", diagnostics=diagnostics)
    if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg", ".pdf"}:
        diagnostics.add_warning(
            "image-display-unsupported-format",
            f"Image display format is not directly previewable: {image_path.suffix}",
            hint="Use PNG or SVG for direct GUI preview.",
            path=image_path,
        )
        return ImageDisplayRecord(
            image_path,
            "unsupported",
            image_path.suffix.lower().lstrip("."),
            diagnostics,
        )
    return ImageDisplayRecord(
        image_path,
        "available",
        image_path.suffix.lower().lstrip("."),
        diagnostics,
    )


def create_placeholder_plot_record(title: str, message: str) -> FigureRecord:
    diagnostics = DiagnosticReport()
    diagnostics.add_info(
        "figure-placeholder",
        message,
        hint="Provide a PNG/SVG/PDF artifact to show a rendered figure.",
    )
    return FigureRecord(
        figure_id="placeholder",
        title=title,
        format=FigureFormat.UNKNOWN,
        diagnostics=diagnostics,
        metadata={"placeholder": True, "message": message},
    )


def render_basic_xy_plot(
    x: tuple[float, ...],
    y: tuple[float, ...],
    out_path: str | Path,
    *,
    title: str = "Figure",
) -> FigureRecord:
    if len(x) != len(y):
        msg = "Matplotlib figure export requires x and y arrays with the same length."
        raise ValueError(msg)
    plt = _load_pyplot()
    target = Path(out_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots()
    axis.plot(x, y)
    axis.set_title(title)
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)
    return FigureRecord(
        figure_id=target.stem,
        title=title,
        image_path=target,
        raw_plot_data={"x": list(x), "y": list(y)},
        reproducible_python="fig, ax = plt.subplots(); ax.plot(x, y)",
    )


def export_line_plot_dataset(
    *,
    x: tuple[float, ...],
    y: tuple[float, ...],
    output_dir: str | Path,
    figure_id: str = "figure-1",
    title: str = "Figure",
) -> FigureDataset:
    output_path = Path(output_dir).expanduser().resolve()
    png_record = render_basic_xy_plot(
        x,
        y,
        output_path / f"{figure_id}.png",
        title=title,
    )
    svg_record = render_basic_xy_plot(
        x,
        y,
        output_path / f"{figure_id}.svg",
        title=title,
    )
    return FigureDataset(
        dataset_id=f"{figure_id}-dataset",
        figures=(
            FigureRecord.from_dict(
                {
                    **png_record.to_dict(),
                    "figure_id": f"{figure_id}-png",
                }
            ),
            FigureRecord.from_dict(
                {
                    **svg_record.to_dict(),
                    "figure_id": f"{figure_id}-svg",
                    "vector_path": svg_record.to_dict()["image_path"],
                    "image_path": "",
                }
            ),
        ),
        source="matplotlib",
        engine="python",
    )


def _load_pyplot() -> object:
    if not matplotlib_available():
        msg = "Matplotlib is not installed. Install the optional viz extra to export plots."
        raise MatplotlibUnavailableError(msg)
    import matplotlib

    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    return plt
