from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from osw.post.matplotlib_scene import (
    create_placeholder_plot_record,
    load_image_for_display,
    matplotlib_available,
    render_basic_xy_plot,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "figures"


def test_module_imports_without_matplotlib() -> None:
    assert isinstance(matplotlib_available(), bool)


def test_placeholder_figure_record_has_diagnostic() -> None:
    record = create_placeholder_plot_record("Plot", "No image artifact was available.")

    assert record.metadata["placeholder"] is True
    assert record.diagnostics.messages[0].code == "figure-placeholder"


def test_load_image_for_display_reports_missing() -> None:
    record = load_image_for_display(FIXTURES / "missing.png")

    assert record.status == "missing"
    assert record.diagnostics.messages


def test_load_image_for_display_accepts_existing_svg() -> None:
    record = load_image_for_display(FIXTURES / "simple_plot.svg")

    assert record.status == "available"
    assert record.format == "svg"


def test_render_basic_xy_plot_if_matplotlib_available(tmp_path: Path) -> None:
    if importlib.util.find_spec("matplotlib") is None:
        pytest.skip("Matplotlib optional viz extra is not installed.")

    record = render_basic_xy_plot(
        (0.0, 1.0, 2.0),
        (0.0, 1.0, 4.0),
        tmp_path / "plot.png",
        title="Simple",
    )

    assert record.image_path is not None
    assert record.image_path.exists()
    assert record.raw_plot_data is not None
